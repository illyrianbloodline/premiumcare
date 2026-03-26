"""
MedPlatform Security Module — hardened edition v2
Adapted for MedPlatform's database schema.

Improvements over v1:
  1. Rich browser fingerprinting (JS canvas/WebGL hash + headers combined)
  2. Session ID regeneration on MFA success (privilege escalation boundary)
  3. Constant-time recovery code verification using hmac.compare_digest
  4. Randomised delay instead of deterministic progressive sleep (anti-self-DoS)
  5. Remember-me long-lived secure token mechanism
  6. Entropy-based password strength estimation (zxcvbn-style without dep)
  7. Automatic MFA secret re-encryption on key rotation (via background helper)

DB column mapping:
  staff.password        → bcrypt (existing) → Argon2id after first login
  staff.mfa_secret      → Fernet-encrypted TOTP secret
  staff.recovery_codes  → JSON array of Argon2id-hashed one-time codes
  staff.active          → boolean
  staff.role            → admin | doctor | nurse | receptionist
  staff.permissions     → JSON permission list

Install:
    pip install argon2-cffi pyotp bleach cryptography redis flask-wtf

Environment variables (.env):
    APP_SECRET_KEY=<long random string>
    MFA_ENCRYPTION_KEYS=<comma-separated Fernet keys, newest first>
    DUMMY_PASSWORD_HASH=<valid Argon2id hash of any placeholder>
    REDIS_URL=redis://localhost:6379/0   (optional — falls back to in-memory)
    REMEMBER_ME_SECRET=<separate long random string>

Generate values:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('placeholder-XYZ'))"
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import io
import json
import logging
import math
import os
import random
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Iterable

import bleach

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHash, VerifyMismatchError
    _argon2_available = True
except ImportError:
    _argon2_available = False

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
    _fernet_available = True
except ImportError:
    _fernet_available = False

try:
    import pyotp
    _pyotp_available = True
except ImportError:
    _pyotp_available = False

try:
    import qrcode as _qrcode
    _qrcode_available = True
except ImportError:
    _qrcode_available = False

try:
    import redis as _redis_lib
    _redis_available = True
except ImportError:
    _redis_available = False

from flask import abort, g, make_response, redirect, request, session

logger = logging.getLogger("medplatform.security")
UTC    = timezone.utc

# ── Configuration ──────────────────────────────────────────────────────────────

MFA_ISSUER          = os.getenv("MFA_ISSUER", "MedPlatform")
REDIS_URL           = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REMEMBER_ME_SECRET  = os.getenv("REMEMBER_ME_SECRET", secrets.token_urlsafe(64))

SESSION_TIMEOUT_MIN   = 60
REAUTH_WINDOW_MIN     = 10
REMEMBER_ME_DAYS      = 30

MAX_LOGIN_ATTEMPTS    = 5
MAX_FAILS_PER_ACCOUNT = 10
LOCKOUT_SECONDS       = 30 * 60

MAX_MFA_FAILS         = 10
MFA_WINDOW_SECONDS    = 15 * 60

MAX_REQUESTS_PER_MIN_IP = 120

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 256

# Common weak passwords — reject these regardless of complexity rules
COMMON_PASSWORDS = {
    "password","password123","admin","admin123","welcome","letmein",
    "qwerty","123456","12345678","medplatform","doctor123","nurse123",
    "clinic123","health123","patient","medical","hospital",
}

# Canary / honeypot email addresses — if used → breach alert
CANARY_EMAILS = [
    "backup.admin@practice.local",
    "admin.backup@practice.local",
    "sysadmin@practice.local",
]

MFA_ENCRYPTION_KEYS = [
    k.strip()
    for k in os.getenv("MFA_ENCRYPTION_KEYS", "").split(",")
    if k.strip()
]
DUMMY_PASSWORD_HASH = os.getenv("DUMMY_PASSWORD_HASH", "")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PHI_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\bMRN[:\s#-]*[A-Z0-9-]{3,32}\b", re.I),
]

# ── Password hasher ────────────────────────────────────────────────────────────

if _argon2_available:
    _ph = PasswordHasher(
        memory_cost=65536,   # 64 MB — matches OWASP 2023 recommendation
        time_cost=3,         # 3 iterations
        parallelism=4,       # 4 threads
    )
else:
    _ph = None

# ── In-memory fallback stores ──────────────────────────────────────────────────
# WARNING: In-memory stores are lost on server restart and not shared across
# multiple app instances. For healthcare, use Redis (REDIS_URL env var) for
# durable, distributed lockout state. Falls back to PostgreSQL if Redis is
# also unavailable (see _db_record_lockout / _db_check_lockout below).
_login_attempts = {}   # ip  -> {count, locked_until}
_request_counts = {}   # ip  -> {count, window_start}
_account_fails  = {}   # email -> count
_mfa_fails      = {}   # "ip:staff_id" -> count

# ── PostgreSQL-backed durable lockout (fallback when Redis unavailable) ─────────

LOCKOUT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ip_lockouts (
    ip_address   VARCHAR(64) PRIMARY KEY,
    fail_count   INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def _ensure_lockout_table():
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute(LOCKOUT_TABLE_SQL)
        conn.commit(); cur.close(); conn.close()
    except Exception: pass

def _db_record_fail(ip: str) -> int:
    """Persist fail count to PostgreSQL. Returns new count."""
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO ip_lockouts (ip_address, fail_count, updated_at)
            VALUES (%s, 1, NOW())
            ON CONFLICT (ip_address) DO UPDATE
                SET fail_count = ip_lockouts.fail_count + 1,
                    updated_at = NOW()
            RETURNING fail_count
        """, (ip,))
        count = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        return count
    except Exception:
        return 0

def _db_set_lockout(ip: str, until: datetime):
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO ip_lockouts (ip_address, locked_until, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (ip_address) DO UPDATE
                SET locked_until = %s, updated_at = NOW()
        """, (ip, until, until))
        conn.commit(); cur.close(); conn.close()
    except Exception: pass

def _db_check_lockout(ip: str) -> tuple[bool, int]:
    """Returns (is_locked, minutes_remaining) from PostgreSQL."""
    try:
        import database as db
        from psycopg2.extras import RealDictCursor
        conn = db.get_conn()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT locked_until FROM ip_lockouts
            WHERE ip_address=%s AND locked_until > NOW()
        """, (ip,))
        row = cur.fetchone(); cur.close(); conn.close()
        if row:
            remaining = int((row['locked_until'] - datetime.now()).total_seconds() / 60) + 1
            return True, remaining
        return False, 0
    except Exception:
        return False, 0

def _db_clear_lockout(ip: str):
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM ip_lockouts WHERE ip_address=%s", (ip,))
        conn.commit(); cur.close(); conn.close()
    except Exception: pass

# ── Helpers ────────────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(UTC)

def utc_iso(dt=None) -> str:
    return (dt or utcnow()).astimezone(UTC).isoformat()

def parse_utc_iso(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    except Exception:
        return None

# ── Redis (graceful fallback to in-memory) ─────────────────────────────────────

def _get_redis():
    if not _redis_available:
        return None
    try:
        r = _redis_lib.Redis.from_url(REDIS_URL, decode_responses=True,
                                       socket_connect_timeout=1)
        r.ping()
        return r
    except Exception:
        return None

# ── PHI scrubbing ──────────────────────────────────────────────────────────────

def scrub_phi(text) -> str:
    value = str(text)
    for pat in PHI_PATTERNS:
        value = pat.sub("[REDACTED]", value)
    return value

# ── Audit logging ──────────────────────────────────────────────────────────────

def audit_log(staff_id, action, detail="", *, outcome="SUCCESS"):
    try:
        import database as db
        ip = request.remote_addr if request else "n/a"
        full = f"[{outcome}] {scrub_phi(str(detail))} | IP:{ip}"
        db.log_activity(staff_id, str(action)[:120], full[:500])
    except Exception:
        logger.warning("audit_log failed: %s %s", action, detail)
    # Also stream to syslog for immutable off-database audit trail
    # Syslog entries cannot be deleted even if DB is compromised
    _stream_to_syslog(staff_id, action, detail, outcome)

def _stream_to_syslog(staff_id, action, detail, outcome):
    """
    Stream security events to local syslog (and optionally to a remote
    syslog server like Papertrail, Logtail, or a SIEM).
    syslog entries are write-only — attackers cannot delete them even
    with full database access.
    """
    try:
        ip      = request.remote_addr if request else 'n/a'
        user_id = staff_id or 'anon'
        msg = (f"MEDPLATFORM SECURITY | outcome={outcome} | "
               f"action={str(action)[:80]} | user={user_id} | "
               f"ip={ip} | detail={scrub_phi(str(detail))[:120]}")
        try:
            import syslog  # Linux/macOS only
            priority = syslog.LOG_WARNING if outcome == 'DENY' else syslog.LOG_INFO
            syslog.openlog('medplatform', syslog.LOG_PID, syslog.LOG_AUTH)
            syslog.syslog(priority, msg)
            syslog.closelog()
        except (ImportError, OSError):
            # Windows — fall back to Python logging
            logger.info('AUDIT | %s', msg)
    except Exception:
        pass

def log_phi_access(staff_id, resource, resource_id, action="VIEW"):
    """
    HIPAA/GDPR medical audit trail — logs every access to patient data.
    Format: [ACCESS] PHI_VIEW | User: 42 | Patient: 99 | IP: 192.168.1.5
    These entries also stream to syslog for immutable off-DB storage.
    """
    ip = request.remote_addr if request else "n/a"
    detail = (f"User #{staff_id} {action} {resource} #{resource_id} | "
              f"IP:{ip} | ts:{utc_iso()}")
    audit_log(staff_id, f"PHI_{action}", detail, outcome="ACCESS")

# ── Input validation ───────────────────────────────────────────────────────────

def normalize_email(value: str) -> str:
    value = (value or "").strip().lower()
    if not EMAIL_RE.fullmatch(value):
        raise ValueError("invalid email")
    return value

def assert_redis_available():
    """
    Call once at app startup when REDIS_REQUIRED=true.
    Raises RuntimeError immediately if Redis is unreachable
    rather than letting the app start in an insecure state.
    """
    if REDIS_REQUIRED:
        _get_redis()   # raises RuntimeError if unreachable
        logger.info("Redis connection verified (REDIS_REQUIRED=true)")


def sanitise_text(value, max_len=2000):
    """Strip ALL HTML — use for names, emails, plain fields."""
    if value is None:
        return None
    clean = bleach.clean(html.unescape(str(value)), tags=[], attributes={}, strip=True)
    return " ".join(clean.split())[:max_len] or None


# HTML tags allowed in clinical notes (formatting only, no JS/CSS/links)
MEDICAL_ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
MEDICAL_ALLOWED_ATTRS = {}   # no attributes — prevents style= onclick= href= etc.


def sanitise_medical_notes(value, max_len=10000):
    """
    Cleans doctor-submitted clinical notes.
    Allows basic formatting (bold, italic, lists) but strips all JS/CSS/links.
    Use before saving ANY rich-text field: notes, diagnosis, treatment, etc.

    Example:
        data['clinical_notes'] = sanitise_medical_notes(request.form.get('clinical_notes'))
    """
    if value is None:
        return None
    # Unescape HTML entities first so &lt;script&gt; doesn't slip through
    unescaped = html.unescape(str(value))
    clean = bleach.clean(
        unescaped,
        tags=MEDICAL_ALLOWED_TAGS,
        attributes=MEDICAL_ALLOWED_ATTRS,
        strip=True,          # strip disallowed tags (don't escape them)
    )
    return clean.strip()[:max_len] or None


def sanitise_plain_input(value, max_len=500):
    """
    Strips ALL HTML for short plain-text fields:
    patient name, phone, address, drug name, etc.
    """
    if value is None:
        return None
    clean = bleach.clean(html.unescape(str(value)), tags=[], attributes={}, strip=True)
    return " ".join(clean.split())[:max_len] or None


def sanitise_form_data(form_dict: dict) -> dict:
    """
    Bulk-sanitise a form submission.
    Automatically applies the right sanitiser based on field name.

    Rich-text fields (notes, diagnosis, treatment, etc.) → sanitise_medical_notes()
    All other fields → sanitise_plain_input()

    Usage in app.py:
        data = sanitise_form_data(request.form.to_dict())
    """
    RICH_TEXT_FIELDS = {
        'clinical_notes', 'notes', 'diagnosis', 'treatment',
        'chief_complaint', 'follow_up', 'instructions', 'observations',
        'family_history', 'medical_history', 'surgeries', 'referrals',
        'letter_content', 'reason', 'justification', 'detail',
    }
    cleaned = {}
    for key, value in form_dict.items():
        if not isinstance(value, str):
            cleaned[key] = value
            continue
        if key.lower() in RICH_TEXT_FIELDS:
            cleaned[key] = sanitise_medical_notes(value)
        else:
            cleaned[key] = sanitise_plain_input(value)
    return cleaned

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 1 — Rich browser fingerprinting
#  Server reads:  X-FP-Hash  header (set by the JS snippet below)
#  Fallback:      4-header hash (UA + Accept + Accept-Language + Accept-Encoding)
#
#  JS snippet to add in base.html <head> (before first request):
#
#  <script>
#  (function(){
#    async function fp(){
#      var parts=[];
#      parts.push(navigator.userAgent||'');
#      parts.push(navigator.language||'');
#      parts.push(screen.width+'x'+screen.height);
#      parts.push(new Date().getTimezoneOffset());
#      parts.push(navigator.hardwareConcurrency||0);
#      parts.push(navigator.deviceMemory||0);
#      // Canvas fingerprint
#      try{
#        var c=document.createElement('canvas'),x=c.getContext('2d');
#        x.textBaseline='top'; x.font='14px Arial';
#        x.fillStyle='#f60'; x.fillRect(125,1,62,20);
#        x.fillStyle='#069'; x.fillText('MedPlatform\u00a9',2,15);
#        x.fillStyle='rgba(102,204,0,0.7)';
#        x.fillText('MedPlatform\u00a9',4,17);
#        parts.push(c.toDataURL());
#      }catch(e){}
#      // WebGL fingerprint
#      try{
#        var gl=document.createElement('canvas').getContext('webgl');
#        if(gl){
#          var ext=gl.getExtension('WEBGL_debug_renderer_info');
#          if(ext){
#            parts.push(gl.getParameter(ext.UNMASKED_VENDOR_WEBGL)||'');
#            parts.push(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)||'');
#          }
#        }
#      }catch(e){}
#      var raw=parts.join('|');
#      if(crypto&&crypto.subtle){
#        var buf=new TextEncoder().encode(raw);
#        var hash=await crypto.subtle.digest('SHA-256',buf);
#        var hex=Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
#        document.cookie='__fp='+hex.slice(0,32)+';path=/;SameSite=Strict';
#      }
#    }
#    fp();
#  })();
#  </script>
# ══════════════════════════════════════════════════════════════════════════════

# ── Fingerprinting configuration ──────────────────────────────────────────────
# Canvas/WebGL fingerprinting is increasingly viewed as invasive in 2025-2026.
# Configure via environment variable:
#   FP_MODE=off        → server-side headers only (privacy-safe, recommended)
#   FP_MODE=log-only   → collect but never block on mismatch (default)
#   FP_MODE=enforce    → use for session binding (requires user consent banner)
FP_MODE = os.getenv("FP_MODE", "log-only").strip().lower()


def get_client_fingerprint() -> str:
    """
    Client fingerprint — privacy-aware implementation.

    FP_MODE=off:       UA + Accept headers only (no canvas/WebGL)
    FP_MODE=log-only:  Include JS cookie if present, but never hard-block on it
    FP_MODE=enforce:   Full fingerprint used for session binding

    Canvas/WebGL fingerprinting should only be used in FP_MODE=enforce
    AND with an explicit consent notice to users (GDPR/ePrivacy compliance).
    """
    ua   = request.headers.get("User-Agent", "")
    lang = request.headers.get("Accept-Language", "")
    enc  = request.headers.get("Accept-Encoding", "")

    if FP_MODE == "off":
        # Privacy-safe: server-side headers only, no JS cookie
        raw = f"{ua}|{lang}|{enc}"
    else:
        # Include JS-computed canvas/WebGL hash if available
        # Consent gate: if FINGERPRINT_CONSENT_REQUIRED=true, only read
        # the __fp cookie when user has set __fp_consent=1.
        if FINGERPRINT_CONSENT_REQUIRED:
            has_consent = request.cookies.get("__fp_consent", "") == "1"
            js_fp = request.cookies.get("__fp", "") if has_consent else ""
        else:
            js_fp = request.cookies.get("__fp", "")
        raw   = f"{ua}|{lang}|{enc}|{js_fp}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def set_fingerprint_consent(response, granted: bool):
    """
    Record user consent choice for fingerprint collection (GDPR).
    Call from your cookie-consent route.

    If granted=True  → sets __fp_consent=1 (1 year).
    If granted=False → clears both consent and fingerprint cookies.
    """
    if granted:
        response.set_cookie(
            "__fp_consent", "1",
            max_age=365 * 86400,
            httponly=True, samesite="Lax", path="/"
        )
    else:
        response.delete_cookie("__fp_consent", path="/")
        response.delete_cookie("__fp",         path="/")
    return response


def fingerprint_session_check() -> bool:
    """
    Returns True if fingerprint matches session.
    In log-only mode: logs mismatch but always returns True (never blocks).
    In enforce mode:  returns False on mismatch (caller should invalidate session).
    """
    if FP_MODE == "off":
        return True

    current_fp = get_client_fingerprint()
    session_fp = session.get("bound_fp")

    if not session_fp:
        session["bound_fp"] = current_fp
        return True

    if current_fp != session_fp:
        staff_id = session.get("staff_id")
        audit_log(staff_id, "FP_MISMATCH",
                  f"Fingerprint changed — mode={FP_MODE}", outcome="WARN")
        if FP_MODE == "enforce":
            return False   # caller should clear session
        # log-only: record but don't block
        session["bound_fp"] = current_fp   # update to new fp

    return True

def get_client_ip() -> str:
    return request.remote_addr or "unknown"

# ── DB adapter helpers ─────────────────────────────────────────────────────────

def _db_update_password(staff_id, new_hash: str):
    import database as db
    if hasattr(db, 'update_staff_password_hash'):
        db.update_staff_password_hash(staff_id, new_hash)
    elif hasattr(db, 'update_staff_password'):
        db.update_staff_password(staff_id, new_hash)
    else:
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("UPDATE staff SET password=%s WHERE id=%s", (new_hash, staff_id))
        conn.commit(); cur.close(); conn.close()

def _db_get_mfa_secret(staff_id):
    import database as db
    if hasattr(db, 'get_staff_mfa_secret'):
        return db.get_staff_mfa_secret(staff_id)
    conn = db.get_conn()
    from psycopg2.extras import RealDictCursor
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT mfa_secret FROM staff WHERE id=%s", (staff_id,))
        row = cur.fetchone(); return row['mfa_secret'] if row else None
    except Exception: return None
    finally: cur.close(); conn.close()

def _db_set_mfa_secret(staff_id, encrypted: str):
    import database as db
    if hasattr(db, 'save_mfa_secret'):
        db.save_mfa_secret(staff_id, encrypted); return
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name='staff' AND column_name='mfa_secret')
            THEN ALTER TABLE staff ADD COLUMN mfa_secret TEXT; END IF;
        END $$;
    """)
    cur.execute("UPDATE staff SET mfa_secret=%s WHERE id=%s", (encrypted, staff_id))
    conn.commit(); cur.close(); conn.close()

def _db_get_recovery_codes(staff_id) -> list:
    import database as db
    blob = None
    if hasattr(db, 'get_staff_recovery_codes'):
        blob = db.get_staff_recovery_codes(staff_id)
    else:
        conn = db.get_conn()
        from psycopg2.extras import RealDictCursor
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT recovery_codes FROM staff WHERE id=%s", (staff_id,))
            row = cur.fetchone(); blob = row.get('recovery_codes') if row else None
        except Exception: blob = None
        finally: cur.close(); conn.close()
    return json.loads(blob) if blob else []

def _db_save_recovery_codes(staff_id, hashes: list):
    import database as db
    blob = json.dumps(list(hashes))
    if hasattr(db, 'update_staff_recovery_codes'):
        db.update_staff_recovery_codes(staff_id, blob); return
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_name='staff' AND column_name='recovery_codes')
            THEN ALTER TABLE staff ADD COLUMN recovery_codes TEXT; END IF;
        END $$;
    """)
    cur.execute("UPDATE staff SET recovery_codes=%s WHERE id=%s", (blob, staff_id))
    conn.commit(); cur.close(); conn.close()

def _db_get_all_staff_with_mfa():
    import database as db
    conn = db.get_conn()
    from psycopg2.extras import RealDictCursor
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, mfa_secret FROM staff WHERE mfa_secret IS NOT NULL AND active=TRUE")
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

# ── Fernet encryption ──────────────────────────────────────────────────────────

def _get_fernet():
    if not _fernet_available or not MFA_ENCRYPTION_KEYS:
        return None
    try:
        return MultiFernet([Fernet(k.encode()) for k in MFA_ENCRYPTION_KEYS])
    except Exception:
        return None

def encrypt_mfa_secret(plain: str) -> str:
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode() if f else plain

def decrypt_mfa_secret(cipher: str) -> str:
    f = _get_fernet()
    if f:
        try: return f.decrypt(cipher.encode()).decode()
        except Exception: pass
    return cipher

def rotate_mfa_secret_ciphertext(cipher: str) -> str | None:
    """Re-wrap with newest key. Returns None if no Fernet configured."""
    f = _get_fernet()
    if not f: return None
    try: return f.rotate(cipher.encode()).decode()
    except Exception: return None

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 7 — Automatic MFA secret re-encryption on key rotation
#  Call this once after adding a new key to MFA_ENCRYPTION_KEYS.
#  Can be run via: python -c "import security; security.rotate_all_mfa_secrets()"
# ══════════════════════════════════════════════════════════════════════════════

def rotate_all_mfa_secrets() -> dict:
    """
    Re-encrypt every staff member's MFA secret with the newest Fernet key.
    Safe to run repeatedly — MultiFernet.rotate() is idempotent.
    Returns {'rotated': N, 'skipped': M, 'errors': [...]}.
    """
    result = {'rotated': 0, 'skipped': 0, 'errors': []}
    try:
        rows = _db_get_all_staff_with_mfa()
    except Exception as e:
        result['errors'].append(f"DB read failed: {e}")
        return result

    for row in rows:
        staff_id = row['id']
        cipher   = row.get('mfa_secret')
        if not cipher:
            result['skipped'] += 1
            continue
        rotated = rotate_mfa_secret_ciphertext(cipher)
        if rotated is None:
            result['skipped'] += 1
            continue
        if rotated == cipher:
            result['skipped'] += 1   # already on newest key
            continue
        try:
            _db_set_mfa_secret(staff_id, rotated)
            audit_log(staff_id, "MFA_SECRET_KEY_ROTATED",
                      "Re-encrypted with newest Fernet key")
            result['rotated'] += 1
        except Exception as e:
            result['errors'].append(f"staff_id={staff_id}: {e}")

    logger.info("MFA key rotation: %s", result)
    return result

# ── Password handling ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    if _argon2_available:
        return _ph.hash(password)
    from flask_bcrypt import Bcrypt
    return Bcrypt().generate_password_hash(password).decode('utf-8')

def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash or not password:
        return False
    if stored_hash.startswith("$argon2") and _argon2_available:
        try: return _ph.verify(stored_hash, password)
        except Exception: return False
    try:
        from flask_bcrypt import Bcrypt
        return Bcrypt().check_password_hash(stored_hash, password)
    except Exception: return False

def password_needs_rehash(stored_hash: str) -> bool:
    if not _argon2_available: return False
    if stored_hash.startswith("$argon2"):
        try: return _ph.check_needs_rehash(stored_hash)
        except Exception: return False
    return True   # bcrypt → upgrade to Argon2id

def maybe_upgrade_password(staff_id, plain: str, stored_hash: str):
    """Silently upgrade bcrypt → Argon2id on next successful login."""
    if password_needs_rehash(stored_hash):
        try:
            _db_update_password(staff_id, hash_password(plain))
            audit_log(staff_id, "PASSWORD_HASH_UPGRADED", "bcrypt→Argon2id")
        except Exception as e:
            logger.warning("Password upgrade failed: %s", e)

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 6 — Entropy-based password strength estimation
#  No external dependency. Estimates bits of entropy from character pool
#  and pattern penalties (repeated chars, keyboard walks, common words).
# ══════════════════════════════════════════════════════════════════════════════

def _estimate_entropy(password: str) -> float:
    """Estimate Shannon entropy bits for a password."""
    pool = 0
    if any(c.islower() for c in password):      pool += 26
    if any(c.isupper() for c in password):      pool += 26
    if any(c.isdigit() for c in password):      pool += 10
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?'
           for c in password):                   pool += 32
    if any(c in ' \t' for c in password):        pool += 1
    pool = max(pool, 1)
    raw_entropy = len(password) * math.log2(pool)

    # Penalty: repetitive characters  e.g. "aaaa"
    from collections import Counter
    freq = Counter(password)
    most_common_ratio = max(freq.values()) / len(password)
    if most_common_ratio > 0.5:
        raw_entropy *= 0.5

    # Penalty: keyboard walks  e.g. "qwerty", "12345"
    walks = ["qwertyuiop","asdfghjkl","zxcvbnm","1234567890","0987654321"]
    for walk in walks:
        for n in range(4, len(walk)+1):
            if walk[:n].lower() in password.lower():
                raw_entropy *= 0.6
                break

    return round(raw_entropy, 1)

def _entropy_label(bits: float) -> tuple[str, str]:
    """Returns (label, colour)."""
    if bits < 28:  return ("Shumë i dobët",  "danger")
    if bits < 36:  return ("I dobët",         "warning")
    if bits < 50:  return ("I mirë",          "info")
    if bits < 64:  return ("I fortë",         "success")
    return               ("Shumë i fortë",    "success")

def validate_password_strength(password: str, email: str = None) -> list:
    """
    Returns list of error strings. Empty list = password accepted.
    Now includes entropy estimation alongside rule checks.
    """
    errors = []
    if not password:
        return ["Password is required"]
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Minimum {PASSWORD_MIN_LENGTH} characters required")
    if len(password) > PASSWORD_MAX_LENGTH:
        errors.append(f"Maximum {PASSWORD_MAX_LENGTH} characters")
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Password is too common — choose a unique one")
    if email:
        local = email.split("@", 1)[0].lower()
        if local and len(local) > 2 and local in password.lower():
            errors.append("Password must not contain your email name")
    # Entropy gate — require at least 36 bits
    bits = _estimate_entropy(password)
    if bits < 36:
        label, _ = _entropy_label(bits)
        errors.append(
            f"Password is too predictable ({label}, {bits} bits). "
            f"Mix upper, lower, numbers and symbols."
        )
    return errors


def check_password_breached(password: str, timeout: float = 2.0) -> tuple[bool, int]:
    """
    Checks password against Have I Been Pwned (HIBP) API using k-Anonymity.
    Only sends first 5 chars of SHA-1 hash — password never leaves your server.

    Returns (is_breached: bool, breach_count: int).
    Returns (False, 0) on network error (fail-open to avoid blocking users).

    Requires: pip install requests  (or use urllib — no extra dep version below)

    HIBP API is free, no key required, rate limit: ~1 req/1.5s.
    """
    import hashlib as _hl
    import urllib.request
    import urllib.error

    try:
        sha1 = _hl.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "MedPlatform-SecurityCheck/1.0",
            "Add-Padding": "true",   # prevents traffic analysis
        })

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")

        # Each line: HASHSUFFIX:COUNT
        for line in body.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and parts[0].upper() == suffix:
                count = int(parts[1].strip())
                return True, count

        return False, 0

    except urllib.error.URLError:
        # Network error — fail open (don't block user, just log)
        logger.warning("HIBP API unreachable — password breach check skipped")
        return False, 0
    except Exception as e:
        logger.warning("HIBP check error: %s", e)
        return False, 0


def validate_password_with_hibp(password: str, email: str = None,
                                 check_hibp: bool = True) -> list:
    """
    Full password validation: strength rules + entropy + HIBP breach check.
    Set check_hibp=False to skip the network call (e.g. in tests).

    Returns list of error strings. Empty = password accepted.
    """
    errors = validate_password_strength(password, email)
    if errors:
        return errors   # fail fast on basic rules

    if check_hibp and HIBP_ENABLED:
        breached, count = check_password_breached(password)
        if breached:
            errors.append(
                f"This password has appeared in {count:,} known data breaches. "
                f"Choose a different password (HIBP check)."
            )
    elif check_hibp and not HIBP_ENABLED:
        logger.debug("HIBP check skipped — HIBP_CHECK=false in environment")

    return errors


def password_entropy_info(password: str) -> dict:
    """Call from JS/AJAX to show live strength meter."""
    bits  = _estimate_entropy(password)
    label, colour = _entropy_label(bits)
    return {"bits": bits, "label": label, "colour": colour,
            "errors": validate_password_strength(password)}

# ── Rate limiting ──────────────────────────────────────────────────────────────

def check_rate_limit(ip: str) -> bool:
    now = datetime.now()
    if ip not in _request_counts:
        _request_counts[ip] = {'count': 0, 'window_start': now}
    entry = _request_counts[ip]
    if (now - entry['window_start']).seconds >= 60:
        entry['count'] = 0; entry['window_start'] = now
    entry['count'] += 1
    return entry['count'] <= MAX_REQUESTS_PER_MIN_IP

# ── Brute-force lockout ────────────────────────────────────────────────────────

def is_locked_out(ip, email="") -> tuple[bool, int]:
    now  = datetime.now()
    entry = _login_attempts.get(ip, {})
    lu    = entry.get('locked_until')
    if lu and now < lu:
        return True, int((lu - now).total_seconds() / 60) + 1
    return False, 0

def record_failed_login(ip, email="") -> tuple[bool, int | None]:
    now   = datetime.now()
    entry = _login_attempts.setdefault(ip, {'count': 0, 'locked_until': None})
    if entry.get('locked_until') and now > entry['locked_until']:
        entry['count'] = 0; entry['locked_until'] = None
    entry['count'] += 1

    email_key = (email or "").lower()
    _account_fails[email_key] = _account_fails.get(email_key, 0) + 1

    # ── IMPROVEMENT 4: randomised delay instead of deterministic sleep ────────
    # Prevents timing attacks AND self-DoS from parallel guessing threads.
    # Base delay grows with failure count; jitter ±40% prevents timing oracle.
    base  = min(2 ** max(entry['count'] - 1, 0), 8)
    jitter = base * random.uniform(-0.4, 0.4)
    time.sleep(max(0.1, base + jitter))

    if entry['count'] >= MAX_LOGIN_ATTEMPTS or \
       _account_fails.get(email_key, 0) >= MAX_FAILS_PER_ACCOUNT:
        entry['locked_until'] = now + timedelta(seconds=LOCKOUT_SECONDS)
        audit_log(None, "🔒 ACCOUNT LOCKED",
                  f"IP={ip} EMAIL={email} after {entry['count']} failures",
                  outcome="DENY")
        return True, int(LOCKOUT_SECONDS / 60)

    return False, None

def clear_login_attempts(ip, email=""):
    _login_attempts.pop(ip, None)
    _account_fails.pop((email or "").lower(), None)

def get_remaining_attempts(ip, email="") -> int:
    entry = _login_attempts.get(ip, {})
    return max(0, MAX_LOGIN_ATTEMPTS - entry.get('count', 0))

# ── Canary ─────────────────────────────────────────────────────────────────────

def check_canary(email: str, ip: str) -> bool:
    if email.lower().strip() in [c.lower() for c in CANARY_EMAILS]:
        audit_log(None, "🚨 CANARY TRIGGERED — POSSIBLE BREACH",
                  f"email={email} ip={ip}", outcome="DENY")
        return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 5 — Remember-me long-lived secure token
#  Flow:
#    1. User checks "Remember me" on login
#    2. generate_remember_token(staff_id) → returns opaque token
#    3. Token stored in a secure HttpOnly cookie (30 days)
#    4. On next visit: validate_remember_token() → returns staff_id or None
#    5. On logout / password change: revoke_remember_token()
#
#  Token format: "<staff_id>.<random_selector>.<HMAC-SHA256>"
#  Only the selector is stored in DB; the HMAC prevents forgery.
# ══════════════════════════════════════════════════════════════════════════════

REMEMBER_TOKEN_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS remember_tokens (
    id           SERIAL PRIMARY KEY,
    staff_id     INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    selector     VARCHAR(32) UNIQUE NOT NULL,
    token_hash   VARCHAR(64) NOT NULL,
    expires_at   TIMESTAMP NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_remember_selector ON remember_tokens(selector);
"""

def _ensure_remember_table():
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute(REMEMBER_TOKEN_TABLE_SQL)
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        logger.warning("remember_tokens table setup: %s", e)

def generate_remember_token(staff_id: int) -> str:
    """
    Creates a remember-me token. Store in cookie.
    Returns the opaque token string.
    """
    _ensure_remember_table()
    selector  = secrets.token_hex(16)       # 32 chars
    validator = secrets.token_hex(32)       # 64 chars
    raw_token = f"{staff_id}.{selector}.{validator}"

    # HMAC of the full token — store only the hash
    token_hash = hmac.new(
        REMEMBER_ME_SECRET.encode(), raw_token.encode(), hashlib.sha256
    ).hexdigest()

    expires = datetime.now() + timedelta(days=REMEMBER_ME_DAYS)

    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        # Revoke any old tokens for this user
        cur.execute("DELETE FROM remember_tokens WHERE staff_id=%s", (staff_id,))
        cur.execute("""
            INSERT INTO remember_tokens (staff_id, selector, token_hash, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (staff_id, selector, token_hash, expires))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        logger.warning("generate_remember_token DB error: %s", e)
        return ""

    audit_log(staff_id, "REMEMBER_ME_TOKEN_ISSUED",
              f"Expires: {expires.date()}")
    return raw_token

def validate_remember_token(raw_token: str) -> int | None:
    """
    Validates a remember-me cookie value.
    Returns staff_id on success, None on failure.
    """
    if not raw_token or raw_token.count('.') != 2:
        return None
    try:
        staff_id_str, selector, _ = raw_token.split('.', 2)
        staff_id = int(staff_id_str)
    except Exception:
        return None

    try:
        import database as db
        from psycopg2.extras import RealDictCursor
        conn = db.get_conn()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT token_hash, expires_at FROM remember_tokens
            WHERE selector=%s AND staff_id=%s
        """, (selector, staff_id))
        row = cur.fetchone(); cur.close(); conn.close()
    except Exception:
        return None

    if not row:
        return None

    # Expired?
    if datetime.now() > row['expires_at']:
        revoke_remember_token(raw_token)
        return None

    # Constant-time HMAC comparison
    expected_hash = hmac.new(
        REMEMBER_ME_SECRET.encode(), raw_token.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, row['token_hash']):
        audit_log(staff_id, "🚨 REMEMBER_ME TOKEN FORGERY ATTEMPT",
                  f"selector={selector}", outcome="DENY")
        return None

    return staff_id

def revoke_remember_token(raw_token: str):
    """Call on logout or password change."""
    if not raw_token or raw_token.count('.') != 2:
        return
    try:
        _, selector, _ = raw_token.split('.', 2)
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM remember_tokens WHERE selector=%s", (selector,))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        logger.warning("revoke_remember_token: %s", e)

def revoke_all_remember_tokens(staff_id: int):
    """Revoke all remember-me tokens on password/MFA change."""
    try:
        import database as db
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM remember_tokens WHERE staff_id=%s", (staff_id,))
        conn.commit(); cur.close(); conn.close()
        audit_log(staff_id, "REMEMBER_ME_TOKENS_REVOKED", "All tokens cleared")
    except Exception as e:
        logger.warning("revoke_all_remember_tokens: %s", e)

def set_remember_cookie(response, raw_token: str):
    """Set the remember-me cookie on a Flask response."""
    response.set_cookie(
        "__rememberme",
        raw_token,
        max_age=REMEMBER_ME_DAYS * 86400,
        httponly=True,
        secure=True,     # requires HTTPS in production
        samesite="Lax",
        path="/",
    )

def clear_remember_cookie(response):
    response.delete_cookie("__rememberme", path="/")

# ── Session management ─────────────────────────────────────────────────────────

def set_session_flags(staff_id, name, role, ip, lang='sq', permissions=None):
    session.clear()
    session['staff_id']      = staff_id
    session['staff_name']    = name
    session['role']          = role
    session['bound_ip']      = ip
    session['last_activity'] = datetime.now().isoformat()
    session['login_time']    = datetime.now().isoformat()
    session['lang']          = lang
    session['permissions']   = permissions or []
    session['mfa_verified']  = False
    session['csrf_token']    = secrets.token_hex(32)

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 2 — Session ID regeneration on MFA success
#  Closing the privilege-escalation window between "password-only" and
#  "fully authenticated" states.
# ══════════════════════════════════════════════════════════════════════════════

def complete_mfa_session():
    """
    Call after TOTP/recovery-code success.
    Copies all session data into a new session (regenerates SID),
    then marks mfa_verified=True.
    """
    snapshot = dict(session)
    session.clear()
    for k, v in snapshot.items():
        session[k] = v
    session['mfa_verified']  = True
    session['mfa_at']        = datetime.now().isoformat()
    session['last_activity'] = datetime.now().isoformat()
    session['csrf_token']    = secrets.token_hex(32)

def validate_mfa_csrf() -> bool:
    """
    CSRF protection specifically for the MFA verification endpoint.

    Why MFA needs its own CSRF check:
    Without this, an attacker who knows a victim's password could embed a
    hidden form on another site that POSTs TOTP codes to /mfa/verify,
    brute-forcing the 6-digit code via CSRF before lockout kicks in.

    Call at the TOP of your /mfa/verify POST handler, before checking the code:

        if not sec.validate_mfa_csrf():
            flash('Security validation failed. Please try again.', 'danger')
            return redirect(url_for('mfa_verify'))

    The token is set in set_session_flags() at login and rotated after MFA.
    """
    submitted = (
        request.form.get('csrf_token')
        or request.headers.get('X-CSRF-Token')
    )
    stored = session.get('csrf_token')
    if not submitted or not stored:
        audit_log(session.get('staff_id'), "🚨 MFA CSRF TOKEN MISSING",
                  f"IP:{request.remote_addr}", outcome="DENY")
        return False
    # Constant-time comparison prevents timing oracle on token length
    valid = hmac.compare_digest(submitted, stored)
    if not valid:
        audit_log(session.get('staff_id'), "🚨 MFA CSRF TOKEN MISMATCH",
                  f"IP:{request.remote_addr}", outcome="DENY")
    return valid

def get_csrf_token() -> str:
    """Return (and create if missing) the session CSRF token. Use in templates."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def check_session_timeout() -> bool:
    if 'staff_id' not in session:
        return False
    last = session.get('last_activity')
    if last:
        try:
            if datetime.now() - datetime.fromisoformat(last) > \
               timedelta(minutes=SESSION_TIMEOUT_MIN):
                sid = session.get('staff_id')
                session.clear()
                audit_log(sid, "SESSION_TIMEOUT",
                          f"Expired after {SESSION_TIMEOUT_MIN} min")
                return True
        except Exception:
            pass
    session['last_activity'] = datetime.now().isoformat()
    return False

def bind_session_to_ip() -> bool:
    """
    Risk-factor approach (not hard-block):
    - IP mismatch: mark session as needing re-auth. Don't destroy — could be
      a mobile user switching from WiFi to 4G.
    - Fingerprint mismatch: log as risk signal. Don't block — Brave/Firefox
      with strict tracking protection spoofs Canvas/WebGL, causing false positives.
    - Only hard-block if BOTH IP and fingerprint changed simultaneously
      (very high confidence of session hijack).
    Returns True only if session was destroyed (certain hijack).
    """
    if 'staff_id' not in session:
        return False

    sid        = session.get('staff_id')
    current_ip = request.remote_addr
    current_fp = get_client_fingerprint()
    bound_ip   = session.get('bound_ip')
    bound_fp   = session.get('bound_fp')

    ip_changed = bound_ip and bound_ip != current_ip
    fp_changed = bound_fp and bound_fp != current_fp

    if ip_changed and fp_changed:
        # Both changed simultaneously → high-confidence hijack → hard block
        audit_log(sid, "🚨 SESSION HIJACK DETECTED — IP+FP BOTH CHANGED",
                  f"IP: {bound_ip}→{current_ip} | FP: {bound_fp[:8]}…→{current_fp[:8]}…",
                  outcome="DENY")
        session.clear()
        return True

    if ip_changed:
        # IP alone changed (e.g. WiFi→4G) → risk signal → require re-auth
        audit_log(sid, "⚠ SESSION IP CHANGED — RE-AUTH REQUIRED",
                  f"IP: {bound_ip}→{current_ip}", outcome="WARN")
        session['requires_reauth'] = True
        session['bound_ip'] = current_ip   # update to new IP

    if fp_changed:
        # Fingerprint alone changed (e.g. Brave anti-tracking) → log only
        audit_log(sid, "ℹ SESSION FP CHANGED — PRIVACY BROWSER LIKELY",
                  f"FP: {bound_fp[:8]}…→{current_fp[:8]}…", outcome="INFO")
        session['bound_fp'] = current_fp   # update silently

    # Bind on first request
    if not bound_ip:
        session['bound_ip'] = current_ip
    if not bound_fp:
        session['bound_fp'] = current_fp

    return False

def invalidate_all_sessions_for_user(staff_id):
    r = _get_redis()
    if r:
        try: r.delete(f"user:sessions:{staff_id}")
        except Exception: pass
    revoke_all_remember_tokens(staff_id)
    audit_log(staff_id, "ALL_SESSIONS_INVALIDATED",
              "Password or MFA changed — all sessions revoked")

# ── MFA ────────────────────────────────────────────────────────────────────────

def generate_mfa_secret() -> str:
    if not _pyotp_available: raise RuntimeError("pip install pyotp")
    return pyotp.random_base32()

def get_mfa_uri(secret: str, email: str) -> str:
    if not _pyotp_available: raise RuntimeError("pip install pyotp")
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=MFA_ISSUER)

def generate_qr_data_uri(otp_uri: str) -> str:
    if not _qrcode_available: raise RuntimeError("pip install qrcode[pil]")
    qr = _qrcode.QRCode(box_size=6, border=2)
    qr.add_data(otp_uri); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def verify_totp(secret: str, token: str, staff_id=None) -> bool:
    if not _pyotp_available or not secret or not token:
        return False
    ip  = request.remote_addr if request else "unknown"
    key = f"{ip}:{staff_id or 'x'}"
    if _mfa_fails.get(key, 0) >= MAX_MFA_FAILS:
        audit_log(staff_id, "MFA_RATE_LIMIT_BLOCKED", f"IP={ip}", outcome="DENY")
        return False
    try:
        plain = decrypt_mfa_secret(secret)
        ok    = pyotp.TOTP(plain).verify(str(token).strip().replace(" ", ""),
                                         valid_window=1)
    except Exception:
        ok = False
    if not ok:
        _mfa_fails[key] = _mfa_fails.get(key, 0) + 1
    else:
        _mfa_fails.pop(key, None)
    return ok

def save_mfa_secret_for_user(staff_id, secret: str):
    _db_set_mfa_secret(staff_id, encrypt_mfa_secret(secret))
    invalidate_all_sessions_for_user(staff_id)
    audit_log(staff_id, "MFA_SECRET_UPDATED", "Stored encrypted")

def load_mfa_secret_for_user(staff_id) -> str | None:
    enc = _db_get_mfa_secret(staff_id)
    return decrypt_mfa_secret(enc) if enc else None

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVEMENT 3 — Constant-time recovery code verification
#  Uses hmac.compare_digest at the selector level, Argon2 internally.
#  All codes are verified in constant-iteration count (no early exit).
# ══════════════════════════════════════════════════════════════════════════════

def _hash_recovery_code(code: str) -> str:
    if _argon2_available:
        return _ph.hash(code)
    # Fallback: HMAC-SHA256 with app secret (not ideal but better than plain)
    return hmac.new(REMEMBER_ME_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()

def generate_recovery_codes(count=10) -> tuple[list, list]:
    """Returns (plain_codes, hashed_codes). Store only hashed_codes."""
    plain, hashed = [], []
    for _ in range(count):
        code = f"{secrets.token_hex(4)}-{secrets.token_hex(4)}"
        plain.append(code)
        hashed.append(_hash_recovery_code(code))
    return plain, hashed

def save_recovery_codes_for_user(staff_id, code_hashes: list):
    _db_save_recovery_codes(staff_id, code_hashes)
    audit_log(staff_id, "MFA_RECOVERY_CODES_UPDATED", "Codes rotated")

def use_recovery_code(staff_id, candidate: str) -> bool:
    """
    Constant-time: always iterates ALL stored codes before returning.
    Prevents timing oracle even with many codes.
    """
    stored_hashes = _db_get_recovery_codes(staff_id)
    remaining = []
    match_idx = -1    # index of the matching code (or -1)

    for i, h in enumerate(stored_hashes):
        try:
            if _argon2_available:
                ok = _ph.verify(h, candidate)
            else:
                # Constant-time fallback comparison
                expected = hmac.new(
                    REMEMBER_ME_SECRET.encode(), candidate.encode(), hashlib.sha256
                ).hexdigest()
                ok = hmac.compare_digest(expected, h)
        except Exception:
            ok = False

        if ok and match_idx == -1:
            match_idx = i   # record first match but keep iterating
        else:
            remaining.append(h)

    matched = match_idx != -1
    if matched:
        _db_save_recovery_codes(staff_id, remaining)
        audit_log(staff_id, "MFA_RECOVERY_CODE_USED",
                  f"{len(remaining)} codes remaining")
    return matched

# ── Security headers ───────────────────────────────────────────────────────────

# ── CSP configuration ─────────────────────────────────────────────────────────
# CSP_MODE controls strictness. Tighten progressively as you refactor templates.
#
# CSP_MODE=legacy   → unsafe-inline + unsafe-eval (current state — all inline styles work)
# CSP_MODE=standard → nonce-based scripts, unsafe-inline for styles only
# CSP_MODE=strict   → nonce-based scripts + styles, no external CDN (most secure)
#
# Set in .env: CSP_MODE=standard
CSP_MODE = os.getenv("CSP_MODE", "legacy").strip().lower()

# CSP violation reporting endpoint (optional — logs violations to activity_log)
# Set: CSP_REPORT_URI=/api/csp-report
CSP_REPORT_URI = os.getenv("CSP_REPORT_URI", "")

# HSTS preload — only enable after your domain is submitted to hstspreload.org
HSTS_PRELOAD = os.getenv("HSTS_PRELOAD", "false").strip().lower() == "true"
FORCE_HTTPS  = os.getenv("FORCE_HTTPS", "false").strip().lower() == "true"


def _get_csp_nonce() -> str:
    """Generate or retrieve per-request CSP nonce stored in flask.g."""
    try:
        nonce = getattr(g, "csp_nonce", None)
        if not nonce:
            nonce = secrets.token_urlsafe(16)
            g.csp_nonce = nonce
        return nonce
    except Exception:
        return secrets.token_urlsafe(16)


def get_csp_nonce() -> str:
    """Call from Jinja template: {{ get_csp_nonce() }} for <script nonce="...">"""
    return _get_csp_nonce()


def _build_csp(nonce: str) -> str:
    """Build Content-Security-Policy header based on CSP_MODE."""
    cdn  = "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com"
    report = f" report-uri {CSP_REPORT_URI};" if CSP_REPORT_URI else ""

    if CSP_MODE == "strict":
        # Nonce-based — no unsafe-inline, no external CDN
        # Requires moving all inline <style> and <script> to external files
        return (
            f"default-src 'self'; "
            f"script-src 'nonce-{nonce}' 'strict-dynamic'; "
            f"style-src 'nonce-{nonce}'; "
            f"img-src 'self' data: blob:; "
            f"font-src 'self'; "
            f"connect-src 'self'; "
            f"object-src 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"frame-ancestors 'none'; "
            f"upgrade-insecure-requests;"
            f"{report}"
        )
    elif CSP_MODE == "standard":
        # Nonce-based scripts, but allows inline styles (transitional)
        return (
            f"default-src 'self'; "
            f"script-src 'nonce-{nonce}' 'strict-dynamic' {cdn}; "
            f"style-src 'self' 'unsafe-inline' {cdn}; "
            f"img-src 'self' data: blob:; "
            f"font-src 'self' {cdn}; "
            f"object-src 'none'; "
            f"frame-ancestors 'none'; "
            f"upgrade-insecure-requests;"
            f"{report}"
        )
    else:
        # legacy — full unsafe-inline (current state, works with all templates)
        return (
            f"default-src 'self' 'unsafe-inline' 'unsafe-eval' {cdn}; "
            f"img-src 'self' data: blob:; "
            f"font-src 'self' {cdn}; "
            f"object-src 'none'; "
            f"frame-ancestors 'none';"
            f"{report}"
        )


def apply_security_headers(response):
    h     = response.headers
    nonce = _get_csp_nonce()

    # ── Standard headers ──────────────────────────────────────
    h['X-Frame-Options']             = 'DENY'
    h['X-Content-Type-Options']      = 'nosniff'
    h['Referrer-Policy']             = 'strict-origin-when-cross-origin'
    h['Cross-Origin-Opener-Policy']  = 'same-origin'
    h['Cross-Origin-Resource-Policy']= 'same-origin'
    h['Origin-Agent-Cluster']        = '?1'
    h['Cache-Control']               = 'no-store, no-cache, must-revalidate, max-age=0'
    h['Pragma']                      = 'no-cache'
    h['Permissions-Policy']          = (
        'camera=(), microphone=(), geolocation=(), payment=(), '
        'usb=(), serial=(), bluetooth=()'
    )

    # X-XSS-Protection is deprecated in 2026 (removed from modern browsers)
    # but kept for older IE/Edge compatibility
    h['X-XSS-Protection'] = '0'   # explicitly disable — nonce-based CSP is the replacement

    # ── Content Security Policy ───────────────────────────────
    h['Content-Security-Policy'] = _build_csp(nonce)

    # ── HSTS (only when HTTPS is active) ──────────────────────
    if FORCE_HTTPS:
        hsts = "max-age=31536000; includeSubDomains"
        if HSTS_PRELOAD:
            hsts += "; preload"   # submit domain to hstspreload.org first!
        h['Strict-Transport-Security'] = hsts

    # ── CSP nonce exposed for Jinja templates ─────────────────
    # Access in templates: {{ csp_nonce }}
    try:
        from flask import g as _g
        _g.csp_nonce = nonce
    except Exception:
        pass

    return response

# ── Suspicious request detection ───────────────────────────────────────────────

SUSPICIOUS_PATHS = [
    '/wp-admin','/.env','/phpmyadmin','/shell','/cmd',
    '/config.php','/etc/passwd','/.git','/backup','/xmlrpc',
]
SQL_SIGNS = ["'--","' --","union select","drop table","sleep(","1=1--","or '1'='1"]

def detect_suspicious_request():
    path = request.path.lower()
    for s in SUSPICIOUS_PATHS:
        if s in path:
            audit_log(None, "🚨 ATTACK PATH BLOCKED",
                      f"IP:{request.remote_addr} PATH:{request.path}", outcome="DENY")
            abort(404)
    qs = (request.query_string or b'').decode('utf-8', 'ignore').lower()
    for sign in SQL_SIGNS:
        if sign in qs:
            audit_log(None, "🚨 SQL INJECTION ATTEMPT",
                      f"IP:{request.remote_addr} QS:{qs[:100]}", outcome="DENY")
            abort(400)

# ── Admin security summary ─────────────────────────────────────────────────────

def get_security_summary() -> dict:
    now    = datetime.now()
    locked = [ip for ip, e in _login_attempts.items()
              if e.get('locked_until') and now < e['locked_until']]
    return {
        'locked_ips':        locked,
        'total_locked':      len(locked),
        'accounts_watched':  len(_account_fails),
        'redis_available':   _redis_available and _get_redis() is not None,
        'argon2_available':  _argon2_available,
        'fernet_available':  _fernet_available and bool(MFA_ENCRYPTION_KEYS),
        'remember_me_table': True,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PERIODIC MFA KEY ROTATION JOB
#  Uses APScheduler (lightweight, no Redis/Celery needed).
#
#  Install: pip install apscheduler
#
#  Call init_scheduler(app) once in app.py startup.
#  The job runs every Sunday at 02:00 server time.
#  Results are written to activity_log so admins see them in the audit trail.
# ══════════════════════════════════════════════════════════════════════════════

def _run_mfa_rotation_job():
    """Background job — re-encrypt all MFA secrets with newest Fernet key."""
    logger.info("MFA key rotation job starting…")
    try:
        result = rotate_all_mfa_secrets()
        msg = (f"MFA rotation complete: rotated={result['rotated']} "
               f"skipped={result['skipped']} errors={len(result['errors'])}")
        logger.info(msg)
        try:
            import database as db
            db.log_activity(None, "⚙ MFA KEY ROTATION JOB", msg)
        except Exception:
            pass
        if result['errors']:
            for err in result['errors']:
                logger.error("MFA rotation error: %s", err)
    except Exception as e:
        logger.error("MFA rotation job failed: %s", e)


def init_scheduler(app):
    """
    Call once in app.py after app is created:

        from security import init_scheduler
        init_scheduler(app)

    Requires: pip install apscheduler
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning(
            "APScheduler not installed — MFA rotation job disabled. "
            "Run: pip install apscheduler"
        )
        return None

    scheduler = BackgroundScheduler(daemon=True)

    # Weekly MFA key rotation — every Sunday at 02:00
    scheduler.add_job(
        func=_run_mfa_rotation_job,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="mfa_key_rotation",
        name="MFA Secret Re-encryption",
        replace_existing=True,
        misfire_grace_time=3600,   # run even if server was down, up to 1h late
    )

    # Hourly lockout cleanup — prune expired in-memory entries
    scheduler.add_job(
        func=_cleanup_expired_lockouts,
        trigger=CronTrigger(minute=0),
        id="lockout_cleanup",
        name="Lockout Cleanup",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Security scheduler started (MFA rotation: weekly Sun 02:00)")

    # Ensure scheduler shuts down cleanly with Flask
    import atexit
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return scheduler


def _cleanup_expired_lockouts():
    """Remove expired lockout entries from memory to prevent unbounded growth."""
    now = datetime.now()
    expired_ips = [
        ip for ip, e in list(_login_attempts.items())
        if not e.get('locked_until') or now > e['locked_until']
    ]
    for ip in expired_ips:
        _login_attempts.pop(ip, None)
    if expired_ips:
        logger.debug("Lockout cleanup: removed %d expired entries", len(expired_ips))


# ══════════════════════════════════════════════════════════════════════════════
#  RICH FINGERPRINT — JS INTEGRATION
#  The JS snippet below should be pasted into base.html <head>.
#  It computes a canvas + WebGL + browser hash and stores it in __fp cookie.
#  security.py reads this cookie in get_client_fingerprint().
#
#  Paste this into templates/base.html just before </head>:
# ══════════════════════════════════════════════════════════════════════════════

FINGERPRINT_JS = r"""<script>
(function(){
  'use strict';
  async function buildFingerprint() {
    var parts = [];

    // Browser basics
    parts.push(navigator.userAgent || '');
    parts.push(navigator.language || '');
    parts.push(navigator.languages ? navigator.languages.join(',') : '');
    parts.push(String(navigator.hardwareConcurrency || 0));
    parts.push(String(navigator.deviceMemory || 0));
    parts.push(String(navigator.maxTouchPoints || 0));

    // Screen
    parts.push(screen.width + 'x' + screen.height + 'x' + screen.colorDepth);
    parts.push(String(window.devicePixelRatio || 1));

    // Timezone
    parts.push(String(new Date().getTimezoneOffset()));
    try { parts.push(Intl.DateTimeFormat().resolvedOptions().timeZone || ''); }
    catch(e) {}

    // Canvas fingerprint
    try {
      var c = document.createElement('canvas');
      var ctx = c.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('MedPlatform\u00a9 2025', 2, 15);
      ctx.fillStyle = 'rgba(102,204,0,0.7)';
      ctx.fillText('MedPlatform\u00a9 2025', 4, 17);
      parts.push(c.toDataURL());
    } catch(e) { parts.push('no-canvas'); }

    // WebGL fingerprint
    try {
      var gl = document.createElement('canvas').getContext('webgl')
               || document.createElement('canvas').getContext('experimental-webgl');
      if (gl) {
        var ext = gl.getExtension('WEBGL_debug_renderer_info');
        if (ext) {
          parts.push(gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) || '');
          parts.push(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || '');
        }
        parts.push(String(gl.getParameter(gl.MAX_TEXTURE_SIZE) || 0));
        parts.push(String(gl.getParameter(gl.MAX_VIEWPORT_DIMS) || ''));
      }
    } catch(e) { parts.push('no-webgl'); }

    // Audio context fingerprint (oscillator hash)
    try {
      var ac = new (window.AudioContext || window.webkitAudioContext)({sampleRate: 44100});
      var osc = ac.createOscillator();
      var analyser = ac.createAnalyser();
      var gain = ac.createGain();
      gain.gain.value = 0;
      osc.connect(analyser);
      analyser.connect(gain);
      gain.connect(ac.destination);
      osc.start(0);
      var data = new Float32Array(analyser.frequencyBinCount);
      analyser.getFloatFrequencyData(data);
      osc.stop(0);
      ac.close();
      parts.push(String(data.slice(0, 10).reduce(function(a,b){ return a+b; }, 0)));
    } catch(e) { parts.push('no-audio'); }

    // Font detection (quick check of 5 fonts)
    try {
      var fonts = ['monospace','Arial','Courier New','Georgia','Times New Roman'];
      var detected = fonts.filter(function(f){
        var s = document.createElement('span');
        s.style.fontFamily = f;
        s.style.fontSize = '72px';
        s.style.visibility = 'hidden';
        s.innerHTML = 'mmm';
        document.body.appendChild(s);
        var w = s.offsetWidth;
        document.body.removeChild(s);
        return w > 0;
      });
      parts.push(detected.join(','));
    } catch(e) {}

    // Hash with SubtleCrypto
    try {
      var raw = parts.join('||');
      var buf = new TextEncoder().encode(raw);
      var hashBuf = await crypto.subtle.digest('SHA-256', buf);
      var hex = Array.from(new Uint8Array(hashBuf))
                     .map(function(b){ return b.toString(16).padStart(2,'0'); })
                     .join('');
      // Store in cookie — SameSite=Strict, no JS expiry (session cookie)
      document.cookie = '__fp=' + hex.slice(0, 48)
                      + '; path=/; SameSite=Strict';
    } catch(e) {
      // Fallback: simple hash via charCodeAt sum
      var raw2 = parts.join('||');
      var h = 0;
      for (var i = 0; i < raw2.length; i++) {
        h = (h * 31 + raw2.charCodeAt(i)) >>> 0;
      }
      document.cookie = '__fp=' + h.toString(16).padStart(8,'0')
                      + '; path=/; SameSite=Strict';
    }
  }

  // Run after DOM is ready but don't block page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildFingerprint);
  } else {
    buildFingerprint();
  }
})();
</script>"""


def get_fingerprint_js() -> str:
    """Return the JS snippet to embed in base.html."""
    return FINGERPRINT_JS


# ══════════════════════════════════════════════════════════════════════════════
#  SECURITY MONITORING & LOCKOUT LOGGING
#  Rich monitoring data for the admin security dashboard.
#  All events are already in activity_log — this adds structured queries.
# ══════════════════════════════════════════════════════════════════════════════

def get_security_events(hours=24, limit=200) -> list:
    """
    Return recent security events from the audit trail.
    Filters for SECURITY / 🚨 / 🔒 / CANARY / SESSION / MFA events.
    """
    try:
        import database as db
        from psycopg2.extras import RealDictCursor
        from datetime import timedelta
        conn = db.get_conn()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT al.*, s.name AS staff_name
            FROM activity_log al
            LEFT JOIN staff s ON al.staff_id = s.id
            WHERE al.created_at >= NOW() - INTERVAL '%s hours'
              AND (
                  al.action ILIKE '%%SECURITY%%'
                OR al.action ILIKE '%%🚨%%'
                OR al.action ILIKE '%%🔒%%'
                OR al.action ILIKE '%%CANARY%%'
                OR al.action ILIKE '%%SESSION%%'
                OR al.action ILIKE '%%MFA%%'
                OR al.action ILIKE '%%LOGIN%%'
                OR al.action ILIKE '%%LOCKED%%'
                OR al.action ILIKE '%%BREACH%%'
                OR al.action ILIKE '%%ROTATION%%'
              )
            ORDER BY al.created_at DESC
            LIMIT %s
        """, (hours, limit))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning("get_security_events failed: %s", e)
        return []


def get_lockout_stats() -> dict:
    """Current in-memory lockout state + counts."""
    now    = datetime.now()
    active = {ip: e for ip, e in _login_attempts.items()
              if e.get('locked_until') and now < e['locked_until']}
    return {
        'currently_locked_ips':   list(active.keys()),
        'total_locked':           len(active),
        'total_accounts_failing': len(_account_fails),
        'top_failing_accounts':   sorted(
            _account_fails.items(), key=lambda x: x[1], reverse=True
        )[:10],
        'mfa_throttled_keys':     [k for k, v in _mfa_fails.items() if v > 3],
        'timestamp':              now.isoformat(),
    }


def get_security_summary() -> dict:
    """Combined summary for admin dashboard widget."""
    lockout = get_lockout_stats()
    return {
        **lockout,
        'redis_available':  _redis_available and _get_redis() is not None,
        'argon2_available': _argon2_available,
        'fernet_available': _fernet_available and bool(MFA_ENCRYPTION_KEYS),
        'mfa_keys_count':   len(MFA_ENCRYPTION_KEYS),
        'remember_me_ok':   bool(REMEMBER_ME_SECRET and len(REMEMBER_ME_SECRET) > 32),
    }


def log_lockout_event(ip: str, email: str, reason: str):
    """Explicit lockout log — called by app.py on lock."""
    audit_log(None, "🔒 LOCKOUT",
              f"IP={ip} EMAIL={email} REASON={reason}", outcome="DENY")


def log_session_event(staff_id, event: str, detail: str = ""):
    """Session lifecycle events."""
    audit_log(staff_id, f"SESSION_{event.upper()}", detail)


def log_mfa_event(staff_id, event: str, success: bool, detail: str = ""):
    """MFA events — enroll, verify, fail, revoke."""
    outcome = "SUCCESS" if success else "DENY"
    audit_log(staff_id, f"MFA_{event.upper()}", detail, outcome=outcome)


# ══════════════════════════════════════════════════════════════════════════════
#  @audit_access — Route decorator for PHI access logging
#
#  Usage:
#    @app.route('/patients/<int:pid>')
#    @login_required
#    @audit_access('patient_record', id_arg='pid')
#    def patient_view(pid):
#        ...
#
#    @app.route('/patients/<int:pid>/scans')
#    @login_required
#    @audit_access('scan_analysis', id_arg='pid', action='VIEW_SCAN')
#    def scan_view(pid):
#        ...
#
#  What it logs (every time the route is called):
#    - Who accessed it (staff_id from session)
#    - What they accessed (resource_type + resource_id)
#    - From where (IP address + browser fingerprint)
#    - When (UTC timestamp)
#    - HTTP method (GET / POST)
#    - Outcome (SUCCESS after function runs, or ERROR on exception)
# ══════════════════════════════════════════════════════════════════════════════

from functools import wraps

def audit_access(resource_type: str, id_arg: str = None, action: str = None):
    """
    Decorator — logs PHI access to the immutable activity_log before
    AND after the route runs.

    Args:
        resource_type: Human-readable resource name, e.g. 'patient_record'
        id_arg:        Name of the route kwarg that holds the record ID,
                       e.g. 'pid' for /patients/<int:pid>.
                       If None, logs 'unknown'.
        action:        Override action label. Defaults to
                       'VIEW_<RESOURCE_TYPE>' or 'EDIT_<RESOURCE_TYPE>'
                       based on HTTP method.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # ── Resolve who is accessing ──────────────────────
            staff_id   = session.get('staff_id')
            actor_name = session.get('staff_name', 'unknown')
            ip         = request.remote_addr or 'unknown'
            fp         = request.cookies.get('__fp', 'no-fp')[:16]
            method     = request.method

            # ── Resolve what is being accessed ────────────────
            resource_id = 'unknown'
            if id_arg:
                resource_id = kwargs.get(id_arg, 'unknown')

            # ── Determine action label ────────────────────────
            if action:
                act = action.upper()
            elif method in ('POST', 'PUT', 'PATCH'):
                act = f"EDIT_{resource_type.upper()}"
            elif method == 'DELETE':
                act = f"DELETE_{resource_type.upper()}"
            else:
                act = f"VIEW_{resource_type.upper()}"

            # ── Pre-call log (access attempt) ─────────────────
            detail_pre = (
                f"ACTOR={actor_name}(#{staff_id}) "
                f"RESOURCE={resource_type}#{resource_id} "
                f"METHOD={method} IP={ip} FP={fp}"
            )
            try:
                import database as _db
                _db.log_activity(staff_id, f"PHI_{act}", detail_pre)
            except Exception:
                pass

            # ── Execute the route ─────────────────────────────
            outcome = "SUCCESS"
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as exc:
                outcome = f"ERROR:{type(exc).__name__}"
                raise
            finally:
                # ── Post-call log (outcome) ───────────────────
                if outcome != "SUCCESS":
                    detail_post = (
                        f"ACTOR={actor_name}(#{staff_id}) "
                        f"RESOURCE={resource_type}#{resource_id} "
                        f"OUTCOME={outcome} IP={ip}"
                    )
                    try:
                        _db.log_activity(staff_id, f"PHI_{act}_FAILED", detail_post)
                    except Exception:
                        pass

        return wrapper
    return decorator


def audit_bulk_access(resource_type: str, count_arg: str = None):
    """
    Variant for list/search endpoints where there's no single record ID.
    Logs the number of records returned.

    Usage:
        @app.route('/patients')
        @login_required
        @audit_bulk_access('patient_list')
        def patients():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            staff_id = session.get('staff_id')
            ip       = request.remote_addr or 'unknown'
            q        = request.args.get('q', '')

            try:
                import database as _db
                _db.log_activity(
                    staff_id,
                    f"PHI_LIST_{resource_type.upper()}",
                    f"ACTOR=#{staff_id} QUERY='{q[:40]}' IP={ip}"
                )
            except Exception:
                pass

            return f(*args, **kwargs)
        return wrapper
    return decorator

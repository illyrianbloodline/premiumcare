"""
MedPlatform — Security Health Check
=====================================
Fast pre-flight check. Run before starting or deploying the app.

    python health_check.py           # Full check
    python health_check.py --quick   # Env vars + Flask config only (no DB)

Exits with code 1 if any FAIL items found.
"""

import os
import sys
import socket
import subprocess
import argparse
from datetime import datetime, timedelta

# ── ANSI colours ───────────────────────────────────────────────
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
C  = "\033[0m"    # reset
B  = "\033[94m"   # blue

PASS  = f"[{G}PASS{C}]"
FAIL  = f"[{R}FAIL{C}]"
WARN  = f"[{Y}WARN{C}]"
SKIP  = f"[{Y}SKIP{C}]"
INFO  = f"[{B}INFO{C}]"

_issues   = []
_warnings = []

def ok(msg):   print(f"  {PASS} {msg}")
def fail(msg): print(f"  {FAIL} {msg}"); _issues.append(msg)
def warn(msg): print(f"  {WARN} {msg}"); _warnings.append(msg)
def skip(msg): print(f"  {SKIP} {msg}")
def info(msg): print(f"  {INFO} {msg}")

def header(title):
    print(f"\n{Y}[*] {title}...{C}")

# ══════════════════════════════════════════════════════════════
#  1. Environment Variables
# ══════════════════════════════════════════════════════════════

WEAK_DEFAULTS = [
    'change-this', 'admin123', 'secret', 'password',
    'naser1980', 'your-', 'replace-this', 'placeholder',
    'example', 'test', '12345',
]

def check_env_vars():
    header("Checking Environment Variables")

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        warn("python-dotenv not installed — .env file won't be auto-loaded")

    critical = {
        "APP_SECRET_KEY":      (32,  "Long random string for Flask sessions"),
        "MFA_ENCRYPTION_KEYS": (40,  "Fernet key(s) for MFA encryption"),
        "DUMMY_PASSWORD_HASH": (60,  "Argon2id hash for timing-attack prevention"),
        "REMEMBER_ME_SECRET":  (32,  "Long random string for remember-me cookies"),
        "DB_PASSWORD":         (4,   "PostgreSQL password"),
    }

    optional = {
        "REDIS_URL":        "Session store (recommended for production)",
        "SMTP_USER":        "Email sending for patient reports",
        "GROQ_API_KEY":     "AI text analysis",
        "GEMINI_API_KEY":   "AI scan analysis",
    }

    for var, (min_len, desc) in critical.items():
        val = os.getenv(var, "")
        if not val:
            fail(f"{var} not set — {desc}")
        elif len(val) < min_len:
            fail(f"{var} too short ({len(val)} chars, need {min_len}+)")
        elif any(w in val.lower() for w in WEAK_DEFAULTS):
            fail(f"{var} looks like a default/weak value — regenerate it")
        else:
            ok(f"{var} set ({len(val)} chars)")

    for var, desc in optional.items():
        val = os.getenv(var, "")
        if val:
            ok(f"{var} set")
        else:
            warn(f"{var} not set — {desc}")


# ══════════════════════════════════════════════════════════════
#  2. Flask / App Configuration
# ══════════════════════════════════════════════════════════════

def check_flask_config():
    header("Checking Flask Configuration")

    try:
        sys.path.insert(0, os.getcwd())
        os.environ.setdefault("APP_SECRET_KEY", "dummy-for-import-only")

        # Import without running the server
        import importlib
        app_module = importlib.import_module("app")
        app = app_module.app

        checks = [
            ("DEBUG mode",      app.debug,   False, "Must be False in production"),
            ("TESTING mode",    app.testing, False, "Must be False in production"),
            ("SESSION_COOKIE_HTTPONLY",
             app.config.get("SESSION_COOKIE_HTTPONLY", False), True,
             "Prevents JS from reading session cookie"),
            ("SESSION_COOKIE_SAMESITE",
             app.config.get("SESSION_COOKIE_SAMESITE") in ("Lax","Strict"), True,
             "Prevents CSRF via cookie"),
        ]

        lifetime = app.config.get("PERMANENT_SESSION_LIFETIME")
        if lifetime:
            secs = lifetime.total_seconds() if isinstance(lifetime, timedelta) else lifetime
            checks.append((
                "SESSION_LIFETIME ≤ 3600s",
                secs <= 3600, True,
                f"Currently {int(secs)}s"
            ))

        for name, current, expected, note in checks:
            if current == expected:
                ok(f"{name} ✓  ({note})")
            else:
                fail(f"{name} — got {current!r}, expected {expected!r}. {note}")

        # Talisman check
        try:
            from flask_talisman import Talisman
            ok("flask-talisman is installed")
        except ImportError:
            warn("flask-talisman not installed — pip install flask-talisman")

    except ImportError as e:
        skip(f"Could not import app.py: {e}")
    except Exception as e:
        skip(f"Flask config check error: {e}")


# ══════════════════════════════════════════════════════════════
#  3. Fernet Keys
# ══════════════════════════════════════════════════════════════

def check_fernet_keys():
    header("Checking MFA Encryption Keys (Fernet)")

    keys_str = os.getenv("MFA_ENCRYPTION_KEYS", "")
    if not keys_str:
        fail("MFA_ENCRYPTION_KEYS not set — run: python security_admin.py --new-key")
        return

    try:
        from cryptography.fernet import Fernet, MultiFernet
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        fernet = MultiFernet([Fernet(k.encode()) for k in keys])
        # Round-trip test
        token = fernet.encrypt(b"medplatform-test")
        fernet.decrypt(token)
        ok(f"{len(keys)} valid Fernet key(s) — encryption round-trip passed")
        if len(keys) == 1:
            info("Only 1 key — add a second when rotating (keep old key for existing users)")
    except ImportError:
        warn("cryptography not installed — pip install cryptography")
    except Exception as e:
        fail(f"Fernet key invalid: {e}")


# ══════════════════════════════════════════════════════════════
#  4. Argon2 Dummy Hash
# ══════════════════════════════════════════════════════════════

def check_dummy_hash():
    header("Checking Dummy Password Hash (Argon2id)")

    dummy = os.getenv("DUMMY_PASSWORD_HASH", "")
    if not dummy:
        fail("DUMMY_PASSWORD_HASH not set — run: python security_admin.py --dummy-hash")
        return

    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        if not dummy.startswith("$argon2"):
            fail("DUMMY_PASSWORD_HASH does not look like an Argon2id hash")
        else:
            ph.check_needs_rehash(dummy)
            ok("DUMMY_PASSWORD_HASH is a valid Argon2id hash")
    except ImportError:
        warn("argon2-cffi not installed — pip install argon2-cffi")
    except Exception as e:
        fail(f"DUMMY_PASSWORD_HASH invalid: {e}")


# ══════════════════════════════════════════════════════════════
#  5. Database — Connection + Least Privilege + Constraints
# ══════════════════════════════════════════════════════════════

def check_database():
    header("Checking Database (Connection, Privilege, Constraints)")

    try:
        sys.path.insert(0, os.getcwd())
        import database as db
        conn = db.get_conn()
        cur  = conn.cursor()

        # Connection
        cur.execute("SELECT version()")
        ver = cur.fetchone()[0]
        ok(f"Connected — {ver[:55]}")

        # ── Least privilege: is DB user a superuser? ──────────
        cur.execute("SELECT usesuper FROM pg_user WHERE usename = CURRENT_USER")
        row = cur.fetchone()
        if row and row[0]:
            fail("DB user is a Superuser — high risk. Create a restricted user.")
        else:
            ok("DB user is not a Superuser (least privilege ✓)")

        # ── Security constraints ──────────────────────────────
        constraint_checks = [
            ("check_valid_role",        "staff",       "Role constraint"),
            ("check_patient_has_creator","patients",   "Patient creator constraint"),
        ]
        for cname, tname, label in constraint_checks:
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name=%s AND table_name=%s
            """, (cname, tname))
            if cur.fetchone():
                ok(f"{label} ({cname}) ✓")
            else:
                warn(f"{label} missing — run db_hardening.sql")

        # ── Triggers ─────────────────────────────────────────
        trigger_checks = [
            ("trg_protect_admin",    "Admin protection trigger"),
            ("trg_immutable_audit",  "Audit log immutability trigger"),
        ]
        for tname, label in trigger_checks:
            cur.execute("""
                SELECT 1 FROM information_schema.triggers WHERE trigger_name=%s
            """, (tname,))
            if cur.fetchone():
                ok(f"{label} ({tname}) ✓")
            else:
                warn(f"{label} missing — run db_hardening.sql")

        # ── Admin count ───────────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM staff WHERE role='admin' AND active=TRUE")
        admins = cur.fetchone()[0]
        if admins >= 2:
            ok(f"{admins} active admin accounts (good — last-admin protection viable)")
        elif admins == 1:
            warn("Only 1 active admin — create a second before enabling last-admin trigger")
        else:
            fail("No active admin accounts found")

        # ── Canary accounts ───────────────────────────────────
        canaries = [
            "backup.admin@practice.local",
            "admin.backup@practice.local",
            "sysadmin@practice.local",
        ]
        cur.execute("SELECT email FROM staff WHERE email = ANY(%s)", (canaries,))
        found = [r[0] for r in cur.fetchall()]
        if len(found) >= 2:
            ok(f"{len(found)} canary/honeypot accounts set up ✓")
        else:
            warn("Canary accounts not set up — restart app.py to create them")

        cur.close(); conn.close()

    except ImportError as e:
        skip(f"database.py not importable: {e}")
    except Exception as e:
        fail(f"Database check error: {e}")


# ══════════════════════════════════════════════════════════════
#  6. Redis
# ══════════════════════════════════════════════════════════════

def check_redis():
    header("Checking Redis")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        r = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        ok(f"Redis connected at {redis_url}")
    except ImportError:
        warn("redis not installed — pip install redis")
    except Exception as e:
        warn(f"Redis not reachable — sessions use in-memory fallback ({e})")


# ══════════════════════════════════════════════════════════════
#  7. Network Exposure
# ══════════════════════════════════════════════════════════════

def check_network():
    header("Checking Network Exposure")

    for port in [5000, 8000, 8080]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                info(f"Port {port} is free (app not running yet)")
            except OSError:
                warn(f"Port {port} is in use — ensure Nginx/proxy handles SSL termination")

    # Check if app is set to bind globally
    host = os.getenv("FLASK_RUN_HOST", "")
    if host == "0.0.0.0":
        warn("FLASK_RUN_HOST=0.0.0.0 — app will be reachable from all network interfaces")
    else:
        ok("No global bind override detected in environment")


# ══════════════════════════════════════════════════════════════
#  8. HTTPS / TLS readiness
# ══════════════════════════════════════════════════════════════

def check_https():
    header("Checking HTTPS / TLS Readiness")

    force = os.getenv("FORCE_HTTPS", "false").lower()
    if force == "true":
        ok("FORCE_HTTPS=true — Talisman will redirect HTTP → HTTPS")
    else:
        warn("FORCE_HTTPS not true — set to 'true' when SSL is configured")

    # Check for cert file paths (common env var names)
    cert_vars = ["SSL_CERT", "SSL_CERT_FILE", "CERT_FILE", "TLS_CERT"]
    found_cert = any(os.getenv(v) for v in cert_vars)
    if found_cert:
        ok("SSL certificate path configured")
    else:
        info("No SSL cert env vars found — expected if using Nginx for TLS termination")


# ══════════════════════════════════════════════════════════════
#  9. .env and Git safety
# ══════════════════════════════════════════════════════════════

def check_secrets_safety():
    header("Checking Secret File Safety")

    # .gitignore check
    gi = os.path.join(os.getcwd(), ".gitignore")
    if os.path.exists(gi):
        content = open(gi).read()
        if ".env" in content:
            ok(".env is listed in .gitignore")
        else:
            fail(".env is NOT in .gitignore — secrets could be committed to Git")
    else:
        warn(".gitignore not found — create one and add .env")

    # Is .env tracked by git?
    try:
        result = subprocess.run(
            ["git", "ls-files", ".env"],
            capture_output=True, text=True, timeout=3, cwd=os.getcwd()
        )
        if result.stdout.strip():
            fail(".env is tracked by Git — remove: git rm --cached .env")
        else:
            ok(".env is not tracked by Git")
    except Exception:
        info("Git not available or not a repo — manual check needed")

    # .env in current directory
    if os.path.exists(".env"):
        ok(".env file exists")
    else:
        warn(".env file not found — create one with security_admin.py --all")


# ══════════════════════════════════════════════════════════════
#  10. Pinned dependencies
# ══════════════════════════════════════════════════════════════

def check_dependencies():
    header("Checking Pinned Dependencies")

    must_have = [
        "flask", "flask-bcrypt", "psycopg2-binary",
        "argon2-cffi", "cryptography", "pyotp",
        "flask-talisman", "apscheduler",
    ]

    try:
        import importlib.metadata as meta
        for pkg in must_have:
            try:
                ver = meta.version(pkg)
                ok(f"{pkg}=={ver}")
            except meta.PackageNotFoundError:
                fail(f"{pkg} not installed — pip install {pkg}")
    except Exception:
        skip("Could not check installed packages")

    req = os.path.join(os.getcwd(), "requirements.txt")
    if os.path.exists(req):
        lines = [l.strip() for l in open(req) if l.strip() and not l.startswith("#")]
        unpinned = [l for l in lines if "==" not in l and not l.startswith(("-", "#"))]
        if unpinned:
            warn(f"Unpinned in requirements.txt: {', '.join(unpinned[:5])}")
        else:
            ok("All requirements.txt entries are pinned with ==")
    else:
        warn("requirements.txt not found")


# ══════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════

def run(quick=False):
    now = datetime.now().isoformat(timespec="seconds")
    print(f"\033[1m{'═'*55}")
    print(f"  MEDPLATFORM — SECURITY HEALTH CHECK")
    print(f"  {now}")
    print(f"{'═'*55}\033[0m")

    check_env_vars()
    check_fernet_keys()
    check_dummy_hash()
    check_flask_config()

    if not quick:
        check_database()
        check_redis()
        check_network()
        check_https()
        check_secrets_safety()
        check_dependencies()

    # ── Summary ───────────────────────────────────────────────
    print(f"\n\033[1m{'═'*55}")
    print(f"  RESULT")
    print(f"{'═'*55}\033[0m")

    if not _issues and not _warnings:
        print(f"\n  {G}✅ ALL CHECKS PASSED — Safe to deploy{C}\n")
    elif not _issues:
        print(f"\n  {Y}⚠️  {len(_warnings)} warning(s) — review before production:{C}")
        for w in _warnings: print(f"     • {w}")
        print()
    else:
        print(f"\n  {R}❌ {len(_issues)} critical issue(s) — DO NOT deploy:{C}")
        for i in _issues: print(f"     • {i}")
        if _warnings:
            print(f"\n  {Y}⚠️  {len(_warnings)} warning(s):{C}")
            for w in _warnings: print(f"     • {w}")
        print()

    print(f"{'═'*55}\n")
    return 1 if _issues else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedPlatform Security Health Check")
    parser.add_argument("--quick", action="store_true",
                        help="Skip DB, Redis, network checks (env + Flask only)")
    args = parser.parse_args()
    sys.exit(run(quick=args.quick))

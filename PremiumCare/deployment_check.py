"""
MedPlatform — Pre-Deployment Security Check
============================================
Run before starting the app in production:
    python deployment_check.py

Checks:
  1. All required environment variables are set
  2. Secret keys are long enough and not defaults
  3. Database connection and security constraints exist
  4. SSL/HTTPS readiness
  5. Dependency versions are pinned correctly
  6. Redis connectivity (optional but recommended)
  7. MFA encryption keys are valid Fernet keys
  8. Dummy password hash is valid Argon2id
"""

import os
import sys
import subprocess

PASS  = "  ✅"
FAIL  = "  ❌"
WARN  = "  ⚠️ "
INFO  = "  ℹ️ "

issues   = []
warnings = []

def ok(msg):     print(f"{PASS} {msg}")
def fail(msg):   print(f"{FAIL} {msg}"); issues.append(msg)
def warn(msg):   print(f"{WARN} {msg}"); warnings.append(msg)
def info(msg):   print(f"{INFO} {msg}")
def header(msg): print(f"\n{'─'*55}\n  {msg}\n{'─'*55}")


# ── 1. Environment variables ──────────────────────────────────
header("1. Environment Variables")

from dotenv import load_dotenv
load_dotenv()

required_vars = {
    'SECRET_KEY':          ('Security',  32,  "Long random string for Flask sessions"),
    'DB_PASSWORD':         ('Database',  4,   "PostgreSQL password"),
    'MFA_ENCRYPTION_KEYS': ('Security',  40,  "Fernet key(s) for MFA secret encryption"),
    'DUMMY_PASSWORD_HASH': ('Security',  60,  "Argon2id hash for timing-attack prevention"),
    'REMEMBER_ME_SECRET':  ('Security',  32,  "Long random string for remember-me cookies"),
}

weak_defaults = ['change-this', 'admin123', 'secret', 'password', 'naser1980', 'your-']

for var, (category, min_len, desc) in required_vars.items():
    val = os.getenv(var, '')
    if not val:
        fail(f"{var} is not set — {desc}")
    elif len(val) < min_len:
        fail(f"{var} is too short ({len(val)} chars, need {min_len}+)")
    elif any(w in val.lower() for w in weak_defaults):
        fail(f"{var} looks like a default/weak value — change it")
    else:
        ok(f"{var} is set ({len(val)} chars)")

optional_vars = ['REDIS_URL', 'SMTP_USER', 'SMTP_PASSWORD', 'GROQ_API_KEY', 'GEMINI_API_KEY']
for var in optional_vars:
    val = os.getenv(var, '')
    if val:
        ok(f"{var} is set")
    else:
        warn(f"{var} is not set (optional but recommended)")


# ── 2. Fernet key validation ──────────────────────────────────
header("2. MFA Encryption Keys")

keys_str = os.getenv('MFA_ENCRYPTION_KEYS', '')
if keys_str:
    keys = [k.strip() for k in keys_str.split(',') if k.strip()]
    try:
        from cryptography.fernet import Fernet, MultiFernet
        fernet = MultiFernet([Fernet(k.encode()) for k in keys])
        # Test round-trip
        test = fernet.encrypt(b"test").decode()
        fernet.decrypt(test.encode())
        ok(f"{len(keys)} valid Fernet key(s) loaded")
    except Exception as e:
        fail(f"MFA_ENCRYPTION_KEYS are invalid: {e}")
else:
    fail("MFA_ENCRYPTION_KEYS not set — MFA secrets will be stored unencrypted")


# ── 3. Argon2 dummy hash validation ──────────────────────────
header("3. Dummy Password Hash")

dummy = os.getenv('DUMMY_PASSWORD_HASH', '')
if dummy:
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        ph.check_needs_rehash(dummy)
        ok("DUMMY_PASSWORD_HASH is a valid Argon2id hash")
    except Exception as e:
        fail(f"DUMMY_PASSWORD_HASH is invalid: {e}")
else:
    fail("DUMMY_PASSWORD_HASH not set — run: python security_admin.py --dummy-hash")


# ── 4. Database connection & constraints ──────────────────────
header("4. Database Connection & Constraints")

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import database as db
    conn = db.get_conn()
    cur  = conn.cursor()

    # Check connection
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    ok(f"PostgreSQL connected: {version[:50]}")

    # Check role constraint
    cur.execute("""
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'check_valid_role' AND table_name = 'staff'
    """)
    if cur.fetchone():
        ok("Role constraint (check_valid_role) exists")
    else:
        warn("Role constraint missing — run db_hardening.sql")

    # Check admin protection trigger
    cur.execute("""
        SELECT 1 FROM information_schema.triggers
        WHERE trigger_name = 'trg_protect_admin'
    """)
    if cur.fetchone():
        ok("Admin protection trigger (trg_protect_admin) exists")
    else:
        warn("Admin protection trigger missing — run db_hardening.sql")

    # Check audit log immutability trigger
    cur.execute("""
        SELECT 1 FROM information_schema.triggers
        WHERE trigger_name = 'trg_immutable_audit'
    """)
    if cur.fetchone():
        ok("Audit log immutability trigger exists")
    else:
        warn("Audit log immutability trigger missing — run db_hardening.sql")

    # Check active admin count
    cur.execute("SELECT COUNT(*) FROM staff WHERE role='admin' AND active=TRUE")
    admin_count = cur.fetchone()[0]
    if admin_count >= 1:
        ok(f"{admin_count} active admin(s) found")
    else:
        fail("No active admin accounts found")

    cur.close(); conn.close()
except Exception as e:
    fail(f"Database error: {e}")


# ── 5. Redis check ────────────────────────────────────────────
header("5. Redis (Session Store)")

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    import redis
    r = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
    r.ping()
    ok(f"Redis connected at {redis_url}")
except ImportError:
    warn("redis library not installed — pip install redis")
except Exception as e:
    warn(f"Redis not reachable ({e}) — sessions will use in-memory fallback")


# ── 6. HTTPS readiness ────────────────────────────────────────
header("6. HTTPS / SSL")

force_https = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
if force_https:
    ok("FORCE_HTTPS=true — Talisman will redirect HTTP→HTTPS")
else:
    warn("FORCE_HTTPS not set — set to 'true' when deploying with SSL")

# Check if running behind a proxy (Nginx/Apache)
trust_proxy = os.getenv('TRUST_PROXY', 'false').lower() == 'true'
if trust_proxy:
    ok("TRUST_PROXY=true — X-Forwarded-* headers will be trusted")
else:
    info("TRUST_PROXY=false — set to 'true' if behind Nginx/Apache")


# ── 7. Pinned dependencies ────────────────────────────────────
header("7. Dependency Pinning")

critical_packages = {
    'flask': '3.0',
    'flask-bcrypt': '1.0',
    'argon2-cffi': '23.1',
    'cryptography': '42.0',
    'pyotp': '2.9',
    'psycopg2-binary': '2.9',
    'flask-talisman': '1.1',
    'flask-limiter': '3.5',
}

try:
    import importlib.metadata as meta
    for pkg, min_ver in critical_packages.items():
        try:
            installed = meta.version(pkg)
            ok(f"{pkg}=={installed}")
        except meta.PackageNotFoundError:
            fail(f"{pkg} not installed — pip install {pkg}")
except Exception:
    warn("Could not check package versions")

# Check requirements.txt is pinned
req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
if os.path.exists(req_file):
    with open(req_file) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    unpinned = [l for l in lines if '==' not in l and not l.startswith('-')]
    if unpinned:
        warn(f"Unpinned packages in requirements.txt: {unpinned[:5]}")
    else:
        ok("All packages in requirements.txt are pinned with ==")
else:
    warn("requirements.txt not found")


# ── 8. .env in .gitignore ─────────────────────────────────────
header("8. Secret File Safety")

gitignore = os.path.join(os.path.dirname(__file__), '.gitignore')
if os.path.exists(gitignore):
    with open(gitignore) as f:
        content = f.read()
    if '.env' in content:
        ok(".env is in .gitignore")
    else:
        fail(".env is NOT in .gitignore — secrets could be committed to Git!")
else:
    warn(".gitignore not found — create one and add .env to it")

env_in_git = False
try:
    result = subprocess.run(['git', 'ls-files', '.env'],
                            capture_output=True, text=True, timeout=3)
    if result.stdout.strip():
        fail(".env is TRACKED by Git — remove it: git rm --cached .env")
        env_in_git = True
    else:
        ok(".env is not tracked by Git")
except Exception:
    info("Git not available or not a Git repo — manual check needed")


# ── Summary ───────────────────────────────────────────────────
print(f"\n{'═'*55}")
print(f"  DEPLOYMENT CHECK SUMMARY")
print(f"{'═'*55}")

if not issues and not warnings:
    print(f"\n  ✅ ALL CHECKS PASSED — Safe to deploy\n")
elif not issues:
    print(f"\n  ⚠️  {len(warnings)} warning(s) — review before production\n")
    for w in warnings: print(f"     • {w}")
else:
    print(f"\n  ❌ {len(issues)} CRITICAL issue(s) — fix before deploying\n")
    for i in issues: print(f"     • {i}")
    if warnings:
        print(f"\n  ⚠️  {len(warnings)} warning(s):\n")
        for w in warnings: print(f"     • {w}")

print(f"\n{'═'*55}\n")
sys.exit(1 if issues else 0)

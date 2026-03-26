"""
MedPlatform End-to-End Audit Script v1.0
Run from C:\Projects\medplatform\:  python audit.py
"""
import os, re

print("=" * 60)
print("MEDPLATFORM v1.0 — COMPLETE AUDIT")
print("=" * 60)

issues = []
warnings = []

with open('app.py') as f: app_content = f.read()
with open('database.py') as f: db_content = f.read()

# ── 1. TEMPLATES ──────────────────────────────────────────────
print("\n📁 TEMPLATES")
expected = [
    "base.html","login.html","dashboard.html",
    "patients.html","patient_view.html","patient_form.html",
    "patients_archived.html","patients_duplicates.html",
    "calendar.html","appointment_form.html","appointment_slip.html",
    "waiting_room.html",
    "prescriptions.html","prescription_form.html","prescription_print.html",
    "lab_tests.html","lab_test_form.html","vaccinations.html",
    "referrals.html","referral_form.html","referral_print.html",
    "billing.html","invoice_form.html","invoice_print.html",
    "patient_documents.html","recalls.html","reminders_list.html",
    "symptom_analysis.html","scan_analysis.html","reports.html",
    "report_earnings_charges.html","report_earnings_payments.html",
    "report_overdue.html","report_booking.html","report_daily_banking.html",
    "team.html","staff_form.html","activity.html",
]
for t in expected:
    if os.path.exists(f"templates/{t}"):
        print(f"  ✓ {t}")
    else:
        print(f"  ✗ MISSING: {t}")
        issues.append(f"Missing template: {t}")

# ── 2. URL_FOR CHECK ──────────────────────────────────────────
print("\n🔗 URL_FOR (must be 0)")
found = []
for fname in os.listdir('templates'):
    if fname.endswith('.html'):
        with open(f'templates/{fname}') as f:
            for i, line in enumerate(f, 1):
                if 'url_for' in line:
                    found.append(f"{fname}:{i}")
                    issues.append(f"url_for in {fname}:{i}")
print(f"  {'✓ None found' if not found else 'FOUND: ' + str(found)}")

# ── 3. ROUTES ─────────────────────────────────────────────────
print("\n🛣️  ROUTES")
route_checks = [
    ("'/'", 'Dashboard'),
    ("'/login'", 'Login'),
    ("'/patients'", 'Patients'),
    ("'/waiting-room'", 'Waiting Room'),
    ("'/billing'", 'Billing'),
    ("'/recalls'", 'Recalls'),
    ("'/reminders'", 'Reminders'),
    ("'/reports'", 'Reports'),
    ("'/calendar'", 'Calendar'),
    ("'/team'", 'Team'),
    ("'/activity'", 'Activity'),
]
for route, name in route_checks:
    if route in app_content:
        print(f"  ✓ {name} ({route})")
    else:
        print(f"  ✗ MISSING: {name} ({route})")
        issues.append(f"Missing route: {route}")

# ── 4. DB FUNCTIONS ───────────────────────────────────────────
print("\n🗄️  DB FUNCTIONS")
db_fns = [
    'setup','setup_extended','setup_primaryclinic',
    'get_all_patients','get_patient','save_patient',
    'archive_patient','unarchive_patient','merge_patients',
    'get_waiting_room','checkin_patient','update_waiting_status',
    'get_prescriptions','save_prescription',
    'get_lab_tests','save_lab_test',
    'get_invoices','save_invoice','get_invoice',
    'get_vaccinations','save_vaccination',
    'get_referrals','save_referral','get_referral',
    'get_recalls','save_recall',
    'get_reminders','save_reminder',
    'report_earnings_by_charges','report_earnings_by_payments',
    'report_overdue_accounts','report_booking','report_daily_banking',
    'log_activity','get_activity_log',
]
for fn in db_fns:
    if f'def {fn}(' in db_content:
        print(f"  ✓ {fn}()")
    else:
        print(f"  ✗ MISSING: {fn}()")
        issues.append(f"Missing DB function: {fn}()")

# ── 5. SQL TABLES ─────────────────────────────────────────────
print("\n📊 SQL TABLES")
tables = [
    'staff','patients','appointments','activity_log',
    'symptom_analyses','scan_analyses','prescriptions',
    'lab_tests','invoices','invoice_items','patient_documents',
    'waiting_room','vaccinations','referrals','recalls','reminders',
]
for tbl in tables:
    if f'CREATE TABLE IF NOT EXISTS {tbl}' in db_content:
        print(f"  ✓ {tbl}")
    else:
        print(f"  ✗ MISSING: {tbl}")
        issues.append(f"Missing table: {tbl}")

# ── 6. NAVIGATION ─────────────────────────────────────────────
print("\n🧭 NAVIGATION (base.html)")
with open('templates/base.html') as f:
    base = f.read()
nav = [
    ('href="/"','Dashboard'),('href="/patients"','Patients'),
    ('href="/calendar"','Calendar'),('href="/waiting-room"','Waiting Room'),
    ('href="/billing"','Billing'),('href="/recalls"','Recalls'),
    ('href="/reminders"','Reminders'),('href="/reports"','Reports'),
    ('href="/team"','Team'),('href="/logout"','Logout'),
]
for href, name in nav:
    if href in base:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ MISSING: {name}")
        issues.append(f"Missing nav link: {name}")

# ── 7. PATIENT MODULES ────────────────────────────────────────
print("\n🔘 PATIENT MODULE BUTTONS")
with open('templates/patient_view.html') as f:
    pv = f.read()
modules = [
    '/prescriptions','Prescriptions','/labs','Lab Tests',
    '/vaccinations','Vaccinations','/referrals','Referrals',
    '/symptoms','AI Symptoms','/scans','AI Scans',
    '/billing','Billing','/documents','Documents',
    '/recalls','Recalls','/reminders','Reminders',
]
for i in range(0, len(modules), 2):
    path, name = modules[i], modules[i+1]
    if path in pv:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ MISSING: {name}")
        issues.append(f"Missing module button: {name}")

# ── 8. SECURITY ───────────────────────────────────────────────
print("\n🔒 SECURITY")
with open('config.py') as f: cfg = f.read()
if 'change-this' in cfg:
    print("  ⚠ Default SECRET_KEY in config.py — change before production!")
    warnings.append("Default SECRET_KEY")
else:
    print("  ✓ SECRET_KEY customised")
if 'your-anthropic' in cfg:
    print("  ⚠ ANTHROPIC_API_KEY not set in config.py")
    warnings.append("API key not set")
else:
    print("  ✓ ANTHROPIC_API_KEY set")

# ── SUMMARY ───────────────────────────────────────────────────
print("\n" + "=" * 60)
if not issues and not warnings:
    print("✅ ALL CHECKS PASSED — Application is complete!")
elif not issues:
    print(f"✅ No critical issues")
    print(f"🟡 {len(warnings)} warnings:")
    for w in warnings: print(f"   • {w}")
else:
    print(f"🔴 {len(issues)} ISSUES:")
    for i in issues: print(f"   • {i}")
    if warnings:
        print(f"🟡 {len(warnings)} WARNINGS:")
        for w in warnings: print(f"   • {w}")
print("=" * 60)

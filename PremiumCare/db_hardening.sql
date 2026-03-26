-- ============================================================
-- MedPlatform — Database-Level Security Hardening
-- Run once: psql -U medplatform_user -d medplatform -f db_hardening.sql
-- ============================================================

-- ── 1. Role constraint — only known roles allowed ────────────
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'check_valid_role'
        AND table_name = 'staff'
    ) THEN
        ALTER TABLE staff
        ADD CONSTRAINT check_valid_role
        CHECK (role IN ('admin','doctor','nurse','receptionist'));
        RAISE NOTICE 'check_valid_role constraint added';
    ELSE
        RAISE NOTICE 'check_valid_role already exists';
    END IF;
END $$;

-- ── 2. Protect last active admin ─────────────────────────────
CREATE OR REPLACE FUNCTION protect_last_admin()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role = 'admin' THEN
        IF (SELECT COUNT(*) FROM staff
            WHERE role = 'admin' AND active = TRUE AND id != OLD.id) < 1 THEN
            RAISE EXCEPTION
                'Cannot delete or deactivate the last active administrator. '
                'Promote another admin first.';
        END IF;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_protect_admin ON staff;
CREATE TRIGGER trg_protect_admin
BEFORE UPDATE OR DELETE ON staff
FOR EACH ROW WHEN (OLD.role = 'admin')
EXECUTE FUNCTION protect_last_admin();

-- ── 3. Audit log — prevent deletion or modification ──────────
-- Activity log rows should be immutable once written
CREATE OR REPLACE FUNCTION deny_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Activity log records are immutable and cannot be modified or deleted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_immutable_audit ON activity_log;
CREATE TRIGGER trg_immutable_audit
BEFORE UPDATE OR DELETE ON activity_log
FOR EACH ROW
EXECUTE FUNCTION deny_audit_modification();

-- ── 4. Patient data — require created_by ─────────────────────
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'check_patient_has_creator'
        AND table_name = 'patients'
    ) THEN
        -- Only enforce on new rows going forward
        ALTER TABLE patients
        ADD CONSTRAINT check_patient_has_creator
        CHECK (created_by IS NOT NULL);
        RAISE NOTICE 'Patient creator constraint added';
    END IF;
END $$;

-- ── 5. Remember tokens — auto-expire cleanup ─────────────────
-- Create table if not yet created by Python
CREATE TABLE IF NOT EXISTS remember_tokens (
    id           SERIAL PRIMARY KEY,
    staff_id     INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    selector     VARCHAR(32) UNIQUE NOT NULL,
    token_hash   VARCHAR(64) NOT NULL,
    expires_at   TIMESTAMP NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_remember_selector ON remember_tokens(selector);
CREATE INDEX IF NOT EXISTS idx_remember_staff ON remember_tokens(staff_id);

-- Auto-delete expired remember tokens (runs on every INSERT)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM remember_tokens WHERE expires_at < NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cleanup_remember ON remember_tokens;
CREATE TRIGGER trg_cleanup_remember
AFTER INSERT ON remember_tokens
FOR EACH STATEMENT
EXECUTE FUNCTION cleanup_expired_tokens();

-- ── 6. Security events view ───────────────────────────────────
CREATE OR REPLACE VIEW security_events AS
SELECT
    al.id,
    al.created_at,
    s.name  AS staff_name,
    s.email AS staff_email,
    al.action,
    al.detail,
    CASE
        WHEN al.action ILIKE '%CANARY%'   THEN 'CRITICAL'
        WHEN al.action ILIKE '%🚨%'       THEN 'HIGH'
        WHEN al.action ILIKE '%LOCKED%'   THEN 'HIGH'
        WHEN al.action ILIKE '%HIJACK%'   THEN 'CRITICAL'
        WHEN al.action ILIKE '%FAILED%'   THEN 'MEDIUM'
        WHEN al.action ILIKE '%MFA%'      THEN 'MEDIUM'
        ELSE 'INFO'
    END AS severity
FROM activity_log al
LEFT JOIN staff s ON al.staff_id = s.id
WHERE
    al.action ILIKE '%SECURITY%'
    OR al.action ILIKE '%🚨%'
    OR al.action ILIKE '%🔒%'
    OR al.action ILIKE '%CANARY%'
    OR al.action ILIKE '%SESSION%'
    OR al.action ILIKE '%LOGIN%'
    OR al.action ILIKE '%MFA%'
    OR al.action ILIKE '%LOCKED%'
    OR al.action ILIKE '%BREACH%'
ORDER BY al.created_at DESC;

-- ── 7. Failed login spike detection view ─────────────────────
CREATE OR REPLACE VIEW login_spike_alerts AS
SELECT
    substring(detail FROM 'IP:([^\s|]+)') AS ip_address,
    COUNT(*)                               AS failure_count,
    MIN(created_at)                        AS first_seen,
    MAX(created_at)                        AS last_seen,
    COUNT(DISTINCT substring(detail FROM 'EMAIL:([^\s|]+)')) AS distinct_emails
FROM activity_log
WHERE
    action ILIKE '%FAILED%'
    AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY substring(detail FROM 'IP:([^\s|]+)')
HAVING COUNT(*) >= 10
ORDER BY failure_count DESC;

SELECT '✅ DB hardening complete' AS status;

-- ============================================================
-- LEAST PRIVILEGE DATABASE USER
-- Run as superuser/owner, NOT as medplatform_user
-- Creates a restricted app user with only needed permissions
-- ============================================================

-- Create restricted app user (skip if exists)
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'medplatform_app') THEN
        CREATE ROLE medplatform_app LOGIN PASSWORD 'CHANGE_THIS_STRONG_PASSWORD';
        RAISE NOTICE 'Created role medplatform_app';
    END IF;
END $$;

-- Grant CONNECT only to medplatform database
GRANT CONNECT ON DATABASE medplatform TO medplatform_app;
GRANT USAGE ON SCHEMA public TO medplatform_app;

-- Grant only SELECT, INSERT, UPDATE on application tables
-- NO DELETE on most tables, NO DROP, NO TRUNCATE ever
GRANT SELECT, INSERT, UPDATE ON
    staff, patients, appointments, activity_log,
    symptom_analyses, scan_analyses, prescriptions,
    lab_tests, invoices, invoice_items, patient_documents,
    waiting_room, vaccinations, referrals, recalls, reminders,
    visit_notes, patient_forms, medicine_catalog, remember_tokens,
    practice_settings, messages
TO medplatform_app;

-- Allow DELETE only on tables where it's operationally necessary
GRANT DELETE ON remember_tokens TO medplatform_app;      -- token revocation
GRANT DELETE ON waiting_room    TO medplatform_app;      -- discharge patients

-- Grant sequence usage for SERIAL columns
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO medplatform_app;

-- EXPLICITLY DENY dangerous operations (belt and suspenders)
REVOKE DELETE ON
    staff, patients, activity_log, prescriptions,
    visit_notes, symptom_analyses, scan_analyses
FROM medplatform_app;

-- Revoke CREATE and all DDL from app user
REVOKE CREATE ON SCHEMA public FROM medplatform_app;

SELECT '✅ Least-privilege user medplatform_app configured' AS status;

-- ============================================================
-- SUMMARY: Update config.py to use medplatform_app user
-- DB_CONFIG user → 'medplatform_app'
-- DB_CONFIG password → the strong password above
-- ============================================================

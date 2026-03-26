-- ============================================================
-- MedPlatform — Complete Sample Dashboard Data
-- Run: psql -U medplatform_user -d medplatform -f sample_data_dashboard.sql
-- ============================================================

-- ── 1. TODAY'S APPOINTMENTS ────────────────────────────────────────────────
-- Clears today's appointments first then adds 6 new ones
DELETE FROM appointments
WHERE appointment_date = CURRENT_DATE;

INSERT INTO appointments
    (patient_id, doctor_id, appointment_date, start_time, duration_mins,
     appointment_type, notes, status, created_by)
SELECT p.id, 1,
    CURRENT_DATE,
    v.start_time::TIME,
    v.dur,
    v.atype,
    v.notes,
    v.status,
    1
FROM (VALUES
    ('Sarah Thompson',   '08:30', 30, 'Konsultë Standarde',  'Kontroll presioni gjaku. BP 138/88.',          'completed'),
    ('James Kowalski',   '09:00', 45, 'Ndjekje',             'Rishikim diabeti. HbA1c 8.9% — i ngritur.',    'completed'),
    ('Maria Fernandez',  '09:45', 30, 'Pacient i Ri',        'Regjistrim i ri. Astmë e njohur.',             'scheduled'),
    ('Robert Chang',     '10:30', 30, 'Rishikim Vjetor',     'Rishikim vjetor. Guta muajin e kaluar.',       'scheduled'),
    ('Emma Wilson',      '11:00', 15, 'Rinovim Recete',      'Rinovim Sertraline. Humori i përmirësuar.',    'scheduled'),
    ('Ahmed Hassan',     '14:00', 60, 'Procedurë',           'Test spirometrie. FEV1 62% e parashikuar.',    'scheduled'),
    ('Linda Morrison',   '15:00', 30, 'Ndjekje',             'Kontrolli INR. Menaxhim Warfarin.',            'scheduled')
) AS v(pname, start_time, dur, atype, notes, status)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.pname;

SELECT 'Appointments today: ' || COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE;

-- ── 2. WAITING ROOM ────────────────────────────────────────────────────────
DELETE FROM waiting_room;

INSERT INTO waiting_room (patient_id, doctor_id, checked_in_at, reason, status)
SELECT p.id, 1,
    NOW() - (v.mins || ' minutes')::INTERVAL,
    v.reason,
    v.status
FROM (VALUES
    ('Maria Fernandez', 12, 'Konsultë e re — astmë',         'waiting'),
    ('Robert Chang',    35, 'Rishikim vjetor — guta',         'waiting'),
    ('Emma Wilson',     8,  'Rinovim recete — Sertraline',    'with_doctor'),
    ('Ahmed Hassan',    45, 'Spirometri COPD',                'waiting')
) AS v(pname, mins, reason, status)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.pname;

SELECT 'Waiting room: ' || COUNT(*) || ' patients' FROM waiting_room WHERE status IN ('waiting','with_doctor');

-- ── 3. REMINDERS (Kujtesa) ─────────────────────────────────────────────────
DELETE FROM reminders WHERE doctor_id = 1;

INSERT INTO reminders (patient_id, doctor_id, due_date, reason, notes, status)
SELECT p.id, 1, v.due::DATE, v.reason, v.notes, 'pending'
FROM (VALUES
    ('Sarah Thompson',  CURRENT_DATE::TEXT,              'Kontroll BP — medikament i rregulluar javën e kaluar',   'Matje e re BP pas ndryshimit të dozës'),
    ('James Kowalski',  CURRENT_DATE::TEXT,              'HbA1c i ngritur 8.9% — diskutim plani trajtimit',        'Konsideroni referim te endokrinologu'),
    ('Linda Morrison',  CURRENT_DATE::TEXT,              'Kontrolli INR — Warfarin 5mg',                           'Vlera e fundit INR: 2.4, target 2-3'),
    ('Robert Chang',    (CURRENT_DATE+1)::TEXT,          'Rezultate analizash gjaku — kolesterol',                 'Rezultatet e ardhura nga laboratori'),
    ('Ahmed Hassan',    (CURRENT_DATE+2)::TEXT,          'Rishikim X-ray gjoksi',                                  'Raporti i radiologjisë i marrë'),
    ('Emma Wilson',     (CURRENT_DATE-1)::TEXT,          'Ndjekje anksioziteti — 4 javë pas ndryshimit dozës',     'Pyesni për efektet anësore'),
    ('Daniel Nguyen',   (CURRENT_DATE-2)::TEXT,          'Vaksinimi i gripit ende i papërfunduar',                 'Ftojeni për vaksinim')
) AS v(pname, due, reason, notes)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.pname;

SELECT 'Reminders: ' || COUNT(*) || ' pending' FROM reminders WHERE status = 'pending';

-- ── 4. RECALLS (Ndjekje) ───────────────────────────────────────────────────
DELETE FROM recalls WHERE doctor_id = 1;

INSERT INTO recalls (patient_id, doctor_id, result, notes, first_recall_date, status)
SELECT p.id, 1, v.result, v.notes, v.rdate::DATE, 'pending'
FROM (VALUES
    ('James Kowalski',  'HbA1c 8.9% — mbi target',           'Kontrolloni pas 3 muajsh ose referoni',              CURRENT_DATE::TEXT),
    ('Sarah Thompson',  'BP 138/88 pas ndryshimit dozës',     'Kthejeni për matje pas 2 javësh',                    (CURRENT_DATE-3)::TEXT),
    ('Ahmed Hassan',    'X-ray gjoks — hiperinflacion COPD',  'Diskutoni planin e menaxhimit',                      (CURRENT_DATE-1)::TEXT),
    ('Linda Morrison',  'INR 2.4 — brenda target',           'Kontroll mujor INR',                                 (CURRENT_DATE+5)::TEXT)
) AS v(pname, result, notes, rdate)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.pname;

SELECT 'Recalls: ' || COUNT(*) || ' pending' FROM recalls WHERE status = 'pending';

-- ── 5. ABNORMAL LAB RESULTS ────────────────────────────────────────────────
INSERT INTO lab_tests
    (patient_id, doctor_id, test_name, test_type, ordered_date, result_date,
     result_value, reference_range, is_abnormal, notes, status)
SELECT p.id, 1,
    v.test_name, v.test_type,
    (CURRENT_DATE - '7 days'::INTERVAL)::DATE,
    CURRENT_DATE - v.days_ago::INTEGER,
    v.result_val, v.ref_range, TRUE,
    v.notes, 'resulted'
FROM (VALUES
    ('James Kowalski',  'HbA1c',              'Gjak',     0, '8.9%',      '< 7.0%',       'Mbi target — diabeti i pakontrolluar'),
    ('Sarah Thompson',  'Glukozë e agjërimit','Gjak',     1, '7.8 mmol/L','3.9-5.5',      'I ngritur — monitorim i nevojshëm'),
    ('Ahmed Hassan',    'FEV1 Spirometri',    'Funksional',2, '62%',       '> 80%',        'COPD e moderuar e konfirmuar'),
    ('Linda Morrison',  'Kolesterol LDL',     'Gjak',     0, '4.2 mmol/L','< 3.0 mmol/L', 'I ngritur — rishiko statinën')
) AS v(pname, test_name, test_type, days_ago, result_val, ref_range, notes)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.pname
WHERE NOT EXISTS (
    SELECT 1 FROM lab_tests lt
    WHERE lt.patient_id = p.id
    AND lt.test_name = v.test_name
    AND lt.result_date >= CURRENT_DATE - 3
);

SELECT 'Abnormal labs: ' || COUNT(*) FROM lab_tests WHERE is_abnormal = TRUE AND result_date >= CURRENT_DATE - 2;

-- ── 6. EXPIRING PRESCRIPTIONS ──────────────────────────────────────────────
UPDATE prescriptions
SET end_date = CURRENT_DATE + 2
WHERE patient_id IN (
    SELECT id FROM patients WHERE first_name = 'Emma' AND last_name = 'Wilson'
)
AND status = 'active'
AND drug_name ILIKE '%sertraline%';

UPDATE prescriptions
SET end_date = CURRENT_DATE + 1
WHERE patient_id IN (
    SELECT id FROM patients WHERE first_name = 'Sarah' AND last_name = 'Thompson'
)
AND status = 'active'
AND drug_name ILIKE '%metformin%';

-- ── 7. INVOICES (6 months) ─────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM invoices LIMIT 1) THEN
    INSERT INTO invoices (patient_id, doctor_id, invoice_date, due_date, total_amount, amount_paid, status, notes, created_by)
    SELECT p.id, 1,
        (CURRENT_DATE - (n || ' days')::INTERVAL)::DATE,
        (CURRENT_DATE - (n || ' days')::INTERVAL + '30 days'::INTERVAL)::DATE,
        amount, paid,
        CASE WHEN paid >= amount THEN 'paid' WHEN paid > 0 THEN 'partial' ELSE 'unpaid' END,
        'Konsultë', 1
    FROM (VALUES
        (155,85.00,85.00),(150,120.00,120.00),(148,65.00,65.00),(145,200.00,200.00),(142,85.00,85.00),
        (125,85.00,85.00),(122,150.00,150.00),(118,95.00,95.00),(115,85.00,0.00),(112,240.00,240.00),
        (95,85.00,85.00),(92,120.00,120.00),(88,85.00,42.50),(85,175.00,175.00),(82,300.00,300.00),
        (65,85.00,85.00),(62,130.00,130.00),(58,95.00,95.00),(55,85.00,0.00),(52,200.00,200.00),
        (35,85.00,85.00),(32,95.00,95.00),(28,85.00,85.00),(25,150.00,150.00),(22,85.00,0.00),
        (10,85.00,85.00),(8,200.00,200.00),(5,95.00,95.00),(3,85.00,0.00),(1,150.00,75.00)
    ) AS v(n, amount, paid)
    CROSS JOIN (SELECT id FROM patients ORDER BY id LIMIT 1) p;
  END IF;
END $$;

SELECT 'Invoices: €' || SUM(total_amount)::int || ' billed, €' || SUM(amount_paid)::int || ' collected' FROM invoices;

-- ── SUMMARY ────────────────────────────────────────────────────────────────
SELECT '✅ Sample data loaded successfully!' AS status;
SELECT
  (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE) AS appts_today,
  (SELECT COUNT(*) FROM waiting_room WHERE status IN ('waiting','with_doctor')) AS in_waiting,
  (SELECT COUNT(*) FROM reminders WHERE status='pending' AND due_date <= CURRENT_DATE) AS reminders_due,
  (SELECT COUNT(*) FROM recalls WHERE status='pending' AND first_recall_date <= CURRENT_DATE) AS recalls_due,
  (SELECT COUNT(*) FROM lab_tests WHERE is_abnormal=TRUE AND result_date >= CURRENT_DATE-2) AS abnormal_labs,
  (SELECT COUNT(*) FROM invoices) AS total_invoices;

-- ============================================================
-- MedPlatform — Sample Dashboard Data (uses real patient IDs)
-- Run: psql -U medplatform_user -d medplatform -f sample_data_v2.sql
-- ============================================================

-- Show existing patients so we know what we're working with
SELECT id, first_name, last_name FROM patients ORDER BY id LIMIT 10;

-- ── 1. TODAY'S APPOINTMENTS ───────────────────────────────────
DELETE FROM appointments WHERE appointment_date = CURRENT_DATE;

-- Use the first 7 patients found in the DB
INSERT INTO appointments
    (patient_id, doctor_id, appointment_date, start_time, duration_mins,
     appointment_type, notes, status, created_by)
SELECT
    p.id, 1, CURRENT_DATE,
    v.start_time::TIME, v.dur, v.atype, v.notes, v.status, 1
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM patients LIMIT 7
) p
JOIN (VALUES
    (1, '08:30', 30, 'Konsultë Standarde',  'Kontroll presioni gjaku BP 138/88.',        'completed'),
    (2, '09:00', 45, 'Ndjekje',             'Rishikim diabeti HbA1c 8.9% i ngritur.',    'completed'),
    (3, '09:45', 30, 'Pacient i Ri',        'Regjistrim i ri, astmë e njohur.',          'scheduled'),
    (4, '10:30', 30, 'Rishikim Vjetor',     'Rishikim vjetor, guta muajin e kaluar.',    'scheduled'),
    (5, '11:00', 15, 'Rinovim Recete',      'Rinovim Sertraline, humori i përmirësuar.', 'scheduled'),
    (6, '14:00', 60, 'Procedurë',           'Test spirometrie FEV1 62% e parashikuar.',  'scheduled'),
    (7, '15:00', 30, 'Ndjekje',             'Kontrolli INR, menaxhim Warfarin.',         'scheduled')
) AS v(rn, start_time, dur, atype, notes, status) ON p.rn = v.rn;

SELECT 'Appointments today: ' || COUNT(*) AS result FROM appointments WHERE appointment_date = CURRENT_DATE;

-- ── 2. WAITING ROOM ───────────────────────────────────────────
DELETE FROM waiting_room;

INSERT INTO waiting_room (patient_id, doctor_id, checked_in_at, reason, status)
SELECT p.id, 1,
    NOW() - (v.mins || ' minutes')::INTERVAL,
    v.reason, v.status
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM patients LIMIT 4
) p
JOIN (VALUES
    (1, 12, 'Konsultë e re — astmë',       'waiting'),
    (2, 35, 'Rishikim vjetor — guta',       'waiting'),
    (3,  8, 'Rinovim recete Sertraline',    'with_doctor'),
    (4, 45, 'Spirometri COPD',              'waiting')
) AS v(rn, mins, reason, status) ON p.rn = v.rn;

SELECT 'Waiting room: ' || COUNT(*) || ' patients' AS result
FROM waiting_room WHERE status IN ('waiting','with_doctor');

-- ── 3. REMINDERS ─────────────────────────────────────────────
DELETE FROM reminders WHERE doctor_id = 1 AND created_at >= NOW() - INTERVAL '1 minute';
-- safer: delete pending reminders for first 7 patients
DELETE FROM reminders
WHERE patient_id IN (SELECT id FROM patients ORDER BY id LIMIT 7)
AND status = 'pending';

INSERT INTO reminders (patient_id, doctor_id, due_date, reason, notes, status)
SELECT p.id, 1, v.due::DATE, v.reason, v.notes, 'pending'
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM patients LIMIT 7
) p
JOIN (VALUES
    (1, 'Kontroll BP pas ndryshimit dozës',         'Matje e re BP javën e kaluar', CURRENT_DATE::TEXT),
    (2, 'HbA1c 8.9% — diskutim plani trajtimit',   'Konsideroni referim endokrinolog', CURRENT_DATE::TEXT),
    (3, 'Kontrolli INR — Warfarin',                 'Vlera e fundit INR 2.4', CURRENT_DATE::TEXT),
    (4, 'Rezultate analizash gjaku',                'Kolesterol nga laboratori', (CURRENT_DATE-1)::TEXT),
    (5, 'Rishikim X-ray gjoksi',                    'Raporti i radiologjisë', (CURRENT_DATE-2)::TEXT),
    (6, 'Ndjekje anksioziteti 4 javë pas dozës',    'Pyesni për efektet anësore', (CURRENT_DATE-1)::TEXT),
    (7, 'Vaksinimi i gripit i papërfunduar',        'Ftojeni për vaksinim', (CURRENT_DATE-3)::TEXT)
) AS v(rn, reason, notes, due) ON p.rn = v.rn;

SELECT 'Reminders due today/overdue: ' || COUNT(*) AS result
FROM reminders WHERE status='pending' AND due_date <= CURRENT_DATE;

-- ── 4. RECALLS ────────────────────────────────────────────────
DELETE FROM recalls
WHERE patient_id IN (SELECT id FROM patients ORDER BY id LIMIT 4)
AND status = 'pending';

INSERT INTO recalls (patient_id, doctor_id, result, notes, first_recall_date, status)
SELECT p.id, 1, v.result, v.notes, v.rdate::DATE, 'pending'
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM patients LIMIT 4
) p
JOIN (VALUES
    (1, 'HbA1c 8.9% mbi target',          'Kthejeni pas 3 muajsh',             CURRENT_DATE::TEXT),
    (2, 'BP 138/88 pas ndryshimit dozës',  'Matje pas 2 javësh',                (CURRENT_DATE-3)::TEXT),
    (3, 'X-ray gjoks hiperinflacion COPD', 'Diskutoni planin e menaxhimit',     (CURRENT_DATE-1)::TEXT),
    (4, 'INR 2.4 brenda target',           'Kontroll mujor INR',                (CURRENT_DATE+5)::TEXT)
) AS v(rn, result, notes, rdate) ON p.rn = v.rn;

SELECT 'Recalls pending: ' || COUNT(*) AS result FROM recalls WHERE status='pending';

-- ── 5. ABNORMAL LAB RESULTS ───────────────────────────────────
INSERT INTO lab_tests
    (patient_id, doctor_id, test_name, test_type, ordered_date, result_date,
     result_value, reference_range, is_abnormal, notes, status)
SELECT p.id, 1, v.test_name, 'Gjak',
    CURRENT_DATE - 3, CURRENT_DATE - v.days_ago,
    v.result_val, v.ref_range, TRUE, v.notes, 'resulted'
FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM patients LIMIT 4
) p
JOIN (VALUES
    (1, 'HbA1c',           0, '8.9%',        '< 7.0%',   'Diabeti i pakontrolluar'),
    (2, 'Glukozë agjërim', 1, '7.8 mmol/L',  '3.9-5.5',  'I ngritur monitorim'),
    (3, 'Kolesterol LDL',  0, '4.2 mmol/L',  '< 3.0',    'I ngritur rishiko statinën'),
    (4, 'Kreatinë',        1, '142 µmol/L',  '62-115',   'Funksion renal i reduktuar')
) AS v(rn, test_name, days_ago, result_val, ref_range, notes) ON p.rn = v.rn
WHERE NOT EXISTS (
    SELECT 1 FROM lab_tests lt
    WHERE lt.patient_id = p.id AND lt.test_name = v.test_name
    AND lt.result_date >= CURRENT_DATE - 2
);

SELECT 'Abnormal labs (last 2 days): ' || COUNT(*) AS result
FROM lab_tests WHERE is_abnormal=TRUE AND result_date >= CURRENT_DATE - 2;

-- ── 6. INVOICES (6 months history) ───────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM invoices LIMIT 1) THEN
    INSERT INTO invoices
        (patient_id, doctor_id, invoice_date, due_date,
         total_amount, amount_paid, status, notes, created_by)
    SELECT p.id, 1,
        (CURRENT_DATE - (v.n || ' days')::INTERVAL)::DATE,
        (CURRENT_DATE - (v.n || ' days')::INTERVAL + '30 days'::INTERVAL)::DATE,
        v.amt, v.paid,
        CASE WHEN v.paid >= v.amt THEN 'paid'
             WHEN v.paid > 0 THEN 'partial'
             ELSE 'unpaid' END,
        'Konsultë', 1
    FROM (VALUES
        (155,85.00,85.00),(150,120.00,120.00),(145,200.00,200.00),(142,85.00,85.00),
        (125,85.00,85.00),(120,150.00,150.00),(115,85.00,0.00),(110,240.00,240.00),
        (95,85.00,85.00),(90,120.00,120.00),(85,85.00,42.50),(80,300.00,300.00),
        (65,85.00,85.00),(60,175.00,175.00),(55,85.00,0.00),(50,200.00,200.00),
        (35,85.00,85.00),(30,95.00,95.00),(25,85.00,0.00),(20,150.00,150.00),
        (10,85.00,85.00),(8,200.00,200.00),(5,95.00,95.00),(3,85.00,0.00),(1,150.00,75.00)
    ) AS v(n, amt, paid)
    CROSS JOIN (SELECT id FROM patients ORDER BY id LIMIT 1) p;
  END IF;
END $$;

SELECT '€' || SUM(total_amount)::int || ' billed, €' || SUM(amount_paid)::int || ' collected, '
    || COUNT(*) FILTER (WHERE status != 'paid') || ' unpaid' AS invoices_summary
FROM invoices;

-- ── FINAL SUMMARY ─────────────────────────────────────────────
SELECT '✅ All sample data loaded!' AS status;
SELECT
    (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE) AS appts_today,
    (SELECT COUNT(*) FROM waiting_room WHERE status IN ('waiting','with_doctor')) AS in_waiting,
    (SELECT COUNT(*) FROM reminders WHERE status='pending' AND due_date <= CURRENT_DATE) AS reminders_overdue,
    (SELECT COUNT(*) FROM recalls WHERE status='pending') AS recalls_pending,
    (SELECT COUNT(*) FROM lab_tests WHERE is_abnormal=TRUE AND result_date >= CURRENT_DATE-2) AS abnormal_labs;

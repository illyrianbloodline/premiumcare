-- ============================================================
-- MedPlatform — Sample Data using Real Patients
-- Run: psql -U medplatform_user -d medplatform -f sample_real_patients.sql
-- ============================================================

-- ── 1. TODAY'S APPOINTMENTS
DELETE FROM appointments WHERE appointment_date = CURRENT_DATE;

INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, duration_mins, appointment_type, notes, status, created_by)
VALUES
  (1,  1, CURRENT_DATE, '08:00', 30, 'Konsultë Standarde',  'Kontroll BP pas ndryshimit dozës.', 'completed', 1),
  (2,  1, CURRENT_DATE, '08:30', 45, 'Ndjekje',             'Ndjekje pas operacionit polipeve.', 'completed', 1),
  (3,  1, CURRENT_DATE, '09:15', 30, 'Rishikim Vjetor',     'Rishikim vjetor i plotë.', 'completed', 1),
  (4,  1, CURRENT_DATE, '10:00', 30, 'Konsultë Standarde',  'Dhimbje gjuri — artrit i dyshuar.', 'scheduled', 1),
  (5,  1, CURRENT_DATE, '10:30', 15, 'Rinovim Recete',      'Rinovim Metformin 1000mg.', 'scheduled', 1),
  (6,  1, CURRENT_DATE, '11:00', 45, 'Procedurë',           'Injeksion kortikosteroide sup.', 'scheduled', 1),
  (7,  1, CURRENT_DATE, '11:45', 30, 'Ndjekje',             'Kontroll pas pneumonisë.', 'scheduled', 1),
  (8,  1, CURRENT_DATE, '14:00', 30, 'Konsultë Standarde',  'Probleme gjumi dhe ankth.', 'scheduled', 1),
  (9,  1, CURRENT_DATE, '14:30', 30, 'Teste Lab.',          'Rezultate kolesterol dhe TSH.', 'scheduled', 1),
  (10, 1, CURRENT_DATE, '15:00', 45, 'Konsultë Standarde',  'Psoriasis — rishikim ilaçeve.', 'scheduled', 1);

-- ── FUTURE APPOINTMENTS
INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, duration_mins, appointment_type, notes, status, created_by)
VALUES
  (11, 1, CURRENT_DATE+1, '09:00', 30, 'Ndjekje',         'Ndjekje hipertension.', 'scheduled', 1),
  (12, 1, CURRENT_DATE+1, '10:00', 45, 'Rishikim Vjetor', 'Rishikim vjetor Rudolf Fischer.', 'scheduled', 1),
  (13, 1, CURRENT_DATE+2, '08:30', 30, 'Konsultë',        'Dhimbje shpine kronike.', 'scheduled', 1),
  (1,  1, CURRENT_DATE+7, '10:00', 30, 'Ndjekje',         'Kontroll BP pas 4 javësh.', 'scheduled', 1);

-- ── PAST APPOINTMENTS
INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, duration_mins, appointment_type, notes, status, created_by)
VALUES
  (1,  1, CURRENT_DATE-30, '09:00', 30, 'Konsultë', 'BP 148/92 — rritur dozën.', 'completed', 1),
  (2,  1, CURRENT_DATE-14, '10:00', 45, 'Operacion', 'Heqja polipeve — pa komplikime.', 'completed', 1),
  (5,  1, CURRENT_DATE-45, '14:00', 30, 'Ndjekje',  'Diabet nën kontroll HbA1c 6.8%.', 'completed', 1),
  (10, 1, CURRENT_DATE-30, '11:00', 45, 'Konsultë', 'Psoriasis rënduar — ndryshim ilaç.', 'completed', 1),
  (12, 1, CURRENT_DATE-60, '09:00', 30, 'Rishikim', 'Hipertension i kontrolluar.', 'completed', 1);

SELECT 'Takime sot: ' || COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE;

-- ── VISIT NOTES
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
VALUES
  (1, 1, CURRENT_DATE-30, 'Konsultë Standarde', 'completed',
   'Dhimbje koke dhe presion i lartë',
   'Hipertension esencial — I10',
   'Amlodipine 10mg 1x ditë. Reduktim kripës.',
   'Pacienti Anna Müller, 52 vjeç. BP sot 148/92 mmHg. Ankohet për dhimbje koke në mëngjes. Nuk ka pirë ilaçe rregullisht. Diskutuam rëndësinë e trajtimit.',
   'Kontroll BP pas 4 javësh', 1),

  (2, 1, CURRENT_DATE-14, 'Ndjekje', 'completed',
   'Kontroll pas operacionit të polipeve',
   'Rikuperim pas polipektomisë — K63.5',
   'Vazhdim Amoxicillin 500mg. Dietë e lehtë.',
   'Hans Schneider, 67 vjeç. Rikuperim i mirë. Plagët shërohen normalisht. Pa dhimbje. Lëvizjet e zorrës normale.',
   'Kontroll pas 2 javësh', 1),

  (3, 1, CURRENT_DATE-60, 'Rishikim Vjetor', 'completed',
   'Rishikim vjetor rutinë',
   'Shëndet i mirë — Z00.00',
   'Vazhdim statinës. Ushtrime 30 min/ditë.',
   'Maria Weber, 45 vjeç. BP 122/78. Kolesterol LDL 3.4 — pak i ngritur. Glukoza normale. BMI 26.',
   'Rishikim pas 12 muajsh', 1),

  (4, 1, CURRENT_DATE-7, 'Urgjencë', 'completed',
   'Ënjtje dhe dhimbje akute gjuri të majtë',
   'Artrit reaktiv — M02.9',
   'Ibuprofen 400mg 3x ditë. Kompresë akulli. Pushim.',
   'Peter Zimmermann, 58 vjeç. Ënjtje gjuri pas infeksionit fytit. Rreze X normale.',
   'Kontroll pas 1 jave nëse pa përmirësim', 1),

  (5, 1, CURRENT_DATE-45, 'Ndjekje', 'completed',
   'Kontroll diabeti',
   'Diabet tip 2 i kontrolluar — E11.9',
   'Vazhdim Metformin 1000mg 2x ditë.',
   'Sophie Keller, 61 vjeç. HbA1c 6.8% — brenda targetit. Glukoza agjërim 6.2 mmol/L. Pa shenja neuropatie.',
   'HbA1c pas 3 muajsh', 1),

  (6, 1, CURRENT_DATE-21, 'Konsultë Standarde', 'completed',
   'Dhimbje shpine poshtë kronike',
   'Lumbago kronike — M54.5',
   'Fizioterapi 10 seanca. Paracetamol sipas nevojës.',
   'Klaus Brunner, 54 vjeç. MRI: hernie diskale L4-L5 e lehtë. Pa shenja neurologjike.',
   'Nëse pa përmirësim pas fizioterapisë — neurolog', 1),

  (7, 1, CURRENT_DATE-10, 'Ndjekje', 'completed',
   'Kontroll pas pneumonisë',
   'Pneumoni bakteriale në rikuperim — J18.9',
   'Vazhdim antibiotiku 3 ditë. Oksigjen sipas nevojës.',
   'Heidi Lüthi, 73 vjeç. Temperatura normale. Saturimi O2 97%. Zhurmë të reduktuara bazë djathtas.',
   'Rreze X pas 6 javësh', 1),

  (8, 1, CURRENT_DATE-90, 'Konsultë Standarde', 'completed',
   'Ankth dhe probleme gjumi',
   'Çrregullim ankthi — F41.1',
   'Sertraline 50mg 1x ditë. Teknika relaksimi.',
   'Martin Huber, 38 vjeç. Ankth i shtuar 4 muaj. Gjumë i çrregulluar. Pa ideacione suicidale.',
   'Ndjekje pas 4 javësh', 1),

  (10, 1, CURRENT_DATE-30, 'Konsultë Standarde', 'completed',
   'Psoriasis e rënduar',
   'Psoriasis e pllakave — L40.0',
   'Methotrexate 15mg javore. Acid Folik 5mg.',
   'Franz Bauer, 51 vjeç. 40% sipërfaqe trupore e prekur. Ndryshuar te Methotrexate.',
   'Kontroll pas 6 javësh. Teste gjaku.', 1),

  (12, 1, CURRENT_DATE-60, 'Rishikim Vjetor', 'completed',
   'Rishikim vjetor — hipertension',
   'Hipertension esencial i kontrolluar — I10',
   'Vazhdim Amlodipine 5mg + Losartan 50mg.',
   'Rudolf Fischer, 60 vjeç. BP 128/82 — e kontrolluar. Funksioni renal normal. EKG normale.',
   'Rishikim pas 12 muajsh', 1);

SELECT 'Vizita: ' || COUNT(*) FROM visit_notes;

-- ── WAITING ROOM
DELETE FROM waiting_room;
INSERT INTO waiting_room (patient_id, doctor_id, checked_in_at, reason, status)
VALUES
  (4, 1, NOW()-INTERVAL '45 minutes', 'Dhimbje gjuri — takim 10:00',  'waiting'),
  (5, 1, NOW()-INTERVAL '20 minutes', 'Rinovim recete Metformin',      'waiting'),
  (6, 1, NOW()-INTERVAL '5 minutes',  'Injeksion sup — takim 11:00',  'with_doctor'),
  (8, 1, NOW()-INTERVAL '10 minutes', 'Probleme gjumi',               'waiting');

SELECT 'Salla pritjes: ' || COUNT(*) FROM waiting_room WHERE status IN ('waiting','with_doctor');

-- ── REMINDERS
DELETE FROM reminders WHERE patient_id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15);

INSERT INTO reminders (patient_id, doctor_id, due_date, reason, notes, status)
VALUES
  (1,  1, CURRENT_DATE,   'Kontroll BP pas ndryshimit dozës',         'Target < 140/90', 'pending'),
  (5,  1, CURRENT_DATE,   'HbA1c pas 3 muajsh',                       'Target < 7.0%', 'pending'),
  (7,  1, CURRENT_DATE,   'Rreze X konfirmim pastrimi pneumonisë',     'Bërë 10 ditë — kontroll', 'pending'),
  (8,  1, CURRENT_DATE,   'Ndjekje Sertraline 4-javore',               'Pyesni efektet anësore', 'pending'),
  (4,  1, CURRENT_DATE-1, 'Ndjekje gjuri — artrit reaktiv',           'Pa përmirësim → reumatolog', 'pending'),
  (12, 1, CURRENT_DATE-2, 'Kontroll vjetor fundusi syrit',             'Hipertension 8 vjeç', 'pending'),
  (2,  1, CURRENT_DATE+1, 'Kontroll pas operacionit',                  'Plaga duhet kontrolluar', 'pending'),
  (10, 1, CURRENT_DATE+2, 'Teste gjaku para Methotrexate',             'AST/ALT dhe CBC', 'pending'),
  (3,  1, CURRENT_DATE+5, 'Kontroll kolesterol pas dietës',            'LDL ishte 3.4', 'pending'),
  (6,  1, CURRENT_DATE+3, 'Ndjekje fizioterapi shpinë',                'Ka bërë 5/10 seanca', 'pending');

SELECT 'Kujtesa: ' || COUNT(*) FROM reminders WHERE status='pending';

-- ── RECALLS
DELETE FROM recalls WHERE patient_id IN (1,2,3,4,5,6,7,8,10,12);

INSERT INTO recalls (patient_id, doctor_id, result, notes, first_recall_date, status)
VALUES
  (1,  1, 'BP 148/92 mbi target',            'Kontroll pas 4 javësh', CURRENT_DATE, 'pending'),
  (5,  1, 'HbA1c 6.8% kufitar',              'Rishikim pas 3 muajsh', CURRENT_DATE-2, 'pending'),
  (10, 1, 'Psoriasis — ndryshim trajtimi',   'Efektiviteti Methotrexate pas 6 javësh', CURRENT_DATE-1, 'pending'),
  (7,  1, 'Pneumoni — rikuperim',            'Rreze X konfirmimi', CURRENT_DATE+3, 'pending'),
  (12, 1, 'Hipertension i kontrolluar',      'Rishikim vjetor i radhës', CURRENT_DATE+30, 'pending');

SELECT 'Ndjekje: ' || COUNT(*) FROM recalls WHERE status='pending';

-- ── LAB TESTS
INSERT INTO lab_tests (patient_id, doctor_id, test_name, test_type, ordered_date, result_date, result_value, reference_range, is_abnormal, notes, status)
VALUES
  (1,  1, 'Presion Gjaku',  'Klinik', CURRENT_DATE-2,  CURRENT_DATE,   '148/92 mmHg', '< 140/90',     TRUE,  'Mbi target', 'resulted'),
  (3,  1, 'Kolesterol LDL', 'Gjak',   CURRENT_DATE-7,  CURRENT_DATE-5, '3.4 mmol/L',  '< 3.0 mmol/L', TRUE,  'Pak i ngritur', 'resulted'),
  (5,  1, 'HbA1c',          'Gjak',   CURRENT_DATE-14, CURRENT_DATE-10,'6.8%',         '< 6.5%',        TRUE,  'Kufitar', 'resulted'),
  (10, 1, 'AST (SGOT)',     'Gjak',   CURRENT_DATE-3,  CURRENT_DATE-1, '52 U/L',       '10-40 U/L',     TRUE,  'I ngritur — Methotrexate', 'resulted'),
  (7,  1, 'CRP',            'Gjak',   CURRENT_DATE-10, CURRENT_DATE-8, '18 mg/L',      '< 5 mg/L',      TRUE,  'Infeksion aktiv', 'resulted'),
  (12, 1, 'Kreatinë',       'Gjak',   CURRENT_DATE-30, CURRENT_DATE-28,'108 µmol/L',   '62-106 µmol/L', TRUE,  'Pak mbi normë', 'resulted')
ON CONFLICT DO NOTHING;

-- ── PRESCRIPTIONS
INSERT INTO prescriptions (patient_id, doctor_id, drug_name, dosage, frequency, route, start_date, status)
VALUES
  (1,  1, 'Amlodipine',   '10mg',  '1x ditë',                    'Gojë', CURRENT_DATE-30,  'active'),
  (2,  1, 'Amoxicillin',  '500mg', '3x ditë',                    'Gojë', CURRENT_DATE-14,  'active'),
  (3,  1, 'Atorvastatin', '20mg',  '1x natën',                   'Gojë', CURRENT_DATE-60,  'active'),
  (4,  1, 'Ibuprofen',    '400mg', '3x ditë me ushqim',          'Gojë', CURRENT_DATE-7,   'active'),
  (5,  1, 'Metformin',    '1000mg','2x ditë',                    'Gojë', CURRENT_DATE-365, 'active'),
  (6,  1, 'Paracetamol',  '1g',    'Sipas nevojës max 4x/ditë',  'Gojë', CURRENT_DATE-21,  'active'),
  (8,  1, 'Sertraline',   '50mg',  '1x mëngjes',                 'Gojë', CURRENT_DATE-90,  'active'),
  (10, 1, 'Methotrexate', '15mg',  '1x javë',                    'Gojë', CURRENT_DATE-30,  'active'),
  (10, 1, 'Acid Folik',   '5mg',   '1x ditë (jo ditën e MTX)',   'Gojë', CURRENT_DATE-30,  'active'),
  (12, 1, 'Amlodipine',   '5mg',   '1x ditë',                    'Gojë', CURRENT_DATE-365, 'active'),
  (12, 1, 'Losartan',     '50mg',  '1x ditë',                    'Gojë', CURRENT_DATE-365, 'active')
ON CONFLICT DO NOTHING;

SELECT 'Receta aktive: ' || COUNT(*) FROM prescriptions WHERE status='active';

-- ── INVOICES
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM invoices LIMIT 1) THEN
    INSERT INTO invoices (patient_id, doctor_id, invoice_date, due_date, total_amount, amount_paid, status, notes, created_by)
    VALUES
      (1,  1, CURRENT_DATE-30,  CURRENT_DATE,    85.00,  85.00,  'paid',    'Konsultë', 1),
      (2,  1, CURRENT_DATE-14,  CURRENT_DATE+16, 120.00, 120.00, 'paid',    'Operacion', 1),
      (3,  1, CURRENT_DATE-60,  CURRENT_DATE-30, 85.00,  85.00,  'paid',    'Rishikim vjetor', 1),
      (4,  1, CURRENT_DATE-7,   CURRENT_DATE+23, 85.00,  0.00,   'unpaid',  'Urgjencë', 1),
      (5,  1, CURRENT_DATE-45,  CURRENT_DATE-15, 85.00,  85.00,  'paid',    'Ndjekje', 1),
      (6,  1, CURRENT_DATE-21,  CURRENT_DATE+9,  150.00, 75.00,  'partial', 'Procedurë', 1),
      (7,  1, CURRENT_DATE-10,  CURRENT_DATE+20, 85.00,  0.00,   'unpaid',  'Ndjekje', 1),
      (8,  1, CURRENT_DATE-90,  CURRENT_DATE-60, 85.00,  85.00,  'paid',    'Konsultë', 1),
      (10, 1, CURRENT_DATE-30,  CURRENT_DATE,    120.00, 120.00, 'paid',    'Dermatologji', 1),
      (12, 1, CURRENT_DATE-60,  CURRENT_DATE-30, 85.00,  85.00,  'paid',    'Rishikim', 1),
      (9,  1, CURRENT_DATE-5,   CURRENT_DATE+25, 85.00,  0.00,   'unpaid',  'Laborator', 1),
      (11, 1, CURRENT_DATE-15,  CURRENT_DATE+15, 95.00,  95.00,  'paid',    'Konsultë', 1),
      (13, 1, CURRENT_DATE-45,  CURRENT_DATE-15, 85.00,  0.00,   'unpaid',  'Konsultë', 1),
      (14, 1, CURRENT_DATE-20,  CURRENT_DATE+10, 150.00, 150.00, 'paid',    'Procedurë', 1),
      (15, 1, CURRENT_DATE-3,   CURRENT_DATE+27, 85.00,  0.00,   'unpaid',  'EKG', 1);
  END IF;
END $$;

SELECT 'Faturat: €' || COALESCE(SUM(total_amount),0)::int || ' faturuar' FROM invoices;

-- ── FINAL SUMMARY
SELECT '✅ Të gjitha të dhënat u ngarkuan!' AS status;
SELECT
  (SELECT COUNT(*) FROM appointments  WHERE appointment_date = CURRENT_DATE) AS takime_sot,
  (SELECT COUNT(*) FROM visit_notes)                                          AS vizita,
  (SELECT COUNT(*) FROM waiting_room  WHERE status IN ('waiting','with_doctor')) AS ne_pritem,
  (SELECT COUNT(*) FROM reminders     WHERE status='pending')                 AS kujtesa,
  (SELECT COUNT(*) FROM recalls       WHERE status='pending')                 AS ndjekje,
  (SELECT COUNT(*) FROM prescriptions WHERE status='active')                  AS receta,
  (SELECT COUNT(*) FROM lab_tests     WHERE is_abnormal=TRUE)                 AS lab_jonormal;

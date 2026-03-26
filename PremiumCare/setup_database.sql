-- ============================================================
-- MedPlatform v1.0 — Complete Database Setup
-- Run this file to create ALL tables from scratch
-- Usage: psql -U medplatform_user -d medplatform -f setup_database.sql
-- ============================================================

-- ── Staff / Users ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(50) DEFAULT 'doctor',
    specialty   VARCHAR(150),
    phone       VARCHAR(50),
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Patients ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id                SERIAL PRIMARY KEY,
    first_name        VARCHAR(100) NOT NULL,
    last_name         VARCHAR(100) NOT NULL,
    dob               DATE,
    gender            VARCHAR(50),
    blood_type        VARCHAR(10),
    insurance_nr      VARCHAR(100),
    address           TEXT,
    phone             VARCHAR(50),
    email             VARCHAR(150),
    emergency_contact VARCHAR(200),
    family_doctor     VARCHAR(150),
    medical_history   TEXT,
    surgeries         TEXT,
    family_history    TEXT,
    drug_allergies    TEXT,
    env_allergies     TEXT,
    medications       TEXT,
    supplements       TEXT,
    past_medications  TEXT,
    weight            VARCHAR(20),
    height            VARCHAR(20),
    blood_pressure    VARCHAR(20),
    heart_rate        VARCHAR(20),
    temperature       VARCHAR(20),
    oxygen_sat        VARCHAR(20),
    blood_glucose     VARCHAR(20),
    cholesterol       VARCHAR(20),
    notes             TEXT,
    icd_codes         TEXT,
    referrals         TEXT,
    archived          BOOLEAN DEFAULT FALSE,
    created_by        INTEGER REFERENCES staff(id),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Appointments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
    id               SERIAL PRIMARY KEY,
    patient_id       INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id        INTEGER REFERENCES staff(id),
    appointment_date DATE NOT NULL,
    start_time       TIME NOT NULL,
    duration_mins    INTEGER DEFAULT 30,
    appointment_type VARCHAR(100),
    notes            TEXT,
    status           VARCHAR(30) DEFAULT 'scheduled',
    cancelled_by     VARCHAR(30) DEFAULT 'none',
    cancel_reason    TEXT,
    is_recurring     BOOLEAN DEFAULT FALSE,
    recur_group      INTEGER,
    recur_freq       VARCHAR(20),
    recur_end_date   DATE,
    created_by       INTEGER REFERENCES staff(id),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Activity Log ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_log (
    id         SERIAL PRIMARY KEY,
    staff_id   INTEGER REFERENCES staff(id),
    action     TEXT,
    detail     TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── AI Symptom Analyses ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS symptom_analyses (
    id         SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    staff_id   INTEGER REFERENCES staff(id),
    symptoms   TEXT NOT NULL,
    ai_result  TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── AI Scan Analyses ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scan_analyses (
    id         SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    staff_id   INTEGER REFERENCES staff(id),
    scan_type  VARCHAR(50),
    filename   VARCHAR(255),
    ai_result  TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Prescriptions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prescriptions (
    id           SERIAL PRIMARY KEY,
    patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id    INTEGER REFERENCES staff(id),
    drug_name    VARCHAR(200) NOT NULL,
    dosage       VARCHAR(100),
    frequency    VARCHAR(100),
    route        VARCHAR(50),
    start_date   DATE,
    end_date     DATE,
    repeats      INTEGER DEFAULT 0,
    instructions TEXT,
    status       VARCHAR(30) DEFAULT 'active',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Lab Tests ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_tests (
    id              SERIAL PRIMARY KEY,
    patient_id      INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id       INTEGER REFERENCES staff(id),
    test_name       VARCHAR(200) NOT NULL,
    test_type       VARCHAR(100),
    ordered_date    DATE,
    result_date     DATE,
    result_value    TEXT,
    reference_range VARCHAR(100),
    is_abnormal     BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    filename        VARCHAR(255),
    status          VARCHAR(30) DEFAULT 'ordered',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Invoices ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    id           SERIAL PRIMARY KEY,
    patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id    INTEGER REFERENCES staff(id),
    invoice_date DATE NOT NULL,
    due_date     DATE,
    items        TEXT,
    total_amount NUMERIC(10,2) DEFAULT 0,
    amount_paid  NUMERIC(10,2) DEFAULT 0,
    status       VARCHAR(30) DEFAULT 'unpaid',
    notes        TEXT,
    created_by   INTEGER REFERENCES staff(id),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Invoice Items ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoice_items (
    id          SERIAL PRIMARY KEY,
    invoice_id  INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    item_code   VARCHAR(50),
    description TEXT,
    quantity    INTEGER DEFAULT 1,
    unit_price  NUMERIC(10,2) DEFAULT 0,
    gst         NUMERIC(10,2) DEFAULT 0,
    total       NUMERIC(10,2) DEFAULT 0
);

-- ── Patient Documents ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patient_documents (
    id          SERIAL PRIMARY KEY,
    patient_id  INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    uploaded_by INTEGER REFERENCES staff(id),
    doc_type    VARCHAR(100),
    title       VARCHAR(255) NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Waiting Room ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS waiting_room (
    id             SERIAL PRIMARY KEY,
    patient_id     INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id      INTEGER REFERENCES staff(id),
    checked_in_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    reason         VARCHAR(200),
    status         VARCHAR(30) DEFAULT 'waiting',
    notes          TEXT
);

-- ── Vaccinations ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vaccinations (
    id            SERIAL PRIMARY KEY,
    patient_id    INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id     INTEGER REFERENCES staff(id),
    vaccine_name  VARCHAR(200) NOT NULL,
    dose          VARCHAR(50),
    date_given    DATE NOT NULL,
    batch_number  VARCHAR(100),
    next_due_date DATE,
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Referrals ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS referrals (
    id               SERIAL PRIMARY KEY,
    patient_id       INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    referring_doctor INTEGER REFERENCES staff(id),
    referred_to      VARCHAR(200),
    specialty        VARCHAR(150),
    reason           TEXT,
    urgency          VARCHAR(30) DEFAULT 'routine',
    letter_content   TEXT,
    date_created     DATE DEFAULT CURRENT_DATE,
    status           VARCHAR(30) DEFAULT 'draft',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Recalls ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recalls (
    id                 SERIAL PRIMARY KEY,
    patient_id         INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id          INTEGER REFERENCES staff(id),
    result             VARCHAR(200),
    notes              TEXT,
    first_recall_date  DATE,
    first_action       VARCHAR(50),
    second_recall_date DATE,
    second_action      VARCHAR(50),
    third_recall_date  DATE,
    third_action       VARCHAR(50),
    returned_date      DATE,
    status             VARCHAR(30) DEFAULT 'pending',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Reminders ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reminders (
    id             SERIAL PRIMARY KEY,
    patient_id     INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id      INTEGER REFERENCES staff(id),
    due_date       DATE NOT NULL,
    reason         VARCHAR(200),
    notes          TEXT,
    contacted_date DATE,
    contact_action VARCHAR(50),
    returned_date  DATE,
    status         VARCHAR(30) DEFAULT 'pending',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Login Attempts ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS login_attempts (
    id         SERIAL PRIMARY KEY,
    email      VARCHAR(150),
    ip_address VARCHAR(50),
    success    BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Default Admin User ────────────────────────────────────────
-- Password is: admin123
-- (bcrypt hash — change after first login!)
INSERT INTO staff (name, email, password, role)
SELECT 'Administrator',
       'admin@practice.local',
       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm',
       'admin'
WHERE NOT EXISTS (
    SELECT 1 FROM staff WHERE email = 'admin@practice.local'
);

-- ── Verify All Tables Created ─────────────────────────────────
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name 
     AND table_schema = 'public') as columns
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT '✅ Database setup complete! All tables created.' as status;

-- ── Consultation Notes ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS consultation_notes (
    id           SERIAL PRIMARY KEY,
    patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id    INTEGER REFERENCES staff(id),
    visit_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    subjective   TEXT,
    objective    TEXT,
    assessment   TEXT,
    plan         TEXT,
    notes        TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Address Book ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS address_book (
    id         SERIAL PRIMARY KEY,
    type       VARCHAR(20) DEFAULT 'person',
    name       VARCHAR(200) NOT NULL,
    specialty  VARCHAR(150),
    clinic     VARCHAR(200),
    address    TEXT,
    phone      VARCHAR(50),
    fax        VARCHAR(50),
    email      VARCHAR(150),
    notes      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Receipts ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS receipts (
    id             SERIAL PRIMARY KEY,
    invoice_id     INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    patient_id     INTEGER REFERENCES patients(id),
    amount         NUMERIC(10,2) NOT NULL,
    payment_type   VARCHAR(50) DEFAULT 'Cash',
    receipt_date   DATE DEFAULT CURRENT_DATE,
    notes          TEXT,
    created_by     INTEGER REFERENCES staff(id),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Appointment Reminders Log ─────────────────────────────────
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id             SERIAL PRIMARY KEY,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE CASCADE,
    patient_id     INTEGER REFERENCES patients(id),
    method         VARCHAR(20) DEFAULT 'email',
    sent_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(20) DEFAULT 'sent'
);

SELECT 'v1.1 tables created.' as status;

-- ── Internal Messages ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    sender_id   INTEGER REFERENCES staff(id),
    receiver_id INTEGER REFERENCES staff(id),
    subject     VARCHAR(200),
    body        TEXT NOT NULL,
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Sample Patients ────────────────────────────────────────────
INSERT INTO patients (first_name, last_name, dob, gender, blood_type, phone, email,
    medical_history, drug_allergies, medications, weight, height,
    blood_pressure, heart_rate, blood_glucose, created_by)
SELECT * FROM (VALUES
    ('Sarah',   'Thompson', '1982-04-12', 'Female', 'A+',  '0412 345 678', 'sarah.t@email.com',
     'Hypertension, Type 2 Diabetes', 'Penicillin', 'Metformin 500mg, Amlodipine 5mg',
     '72kg', '165cm', '132/84', '78', '7.2', 1),
    ('James',   'Kowalski',  '1957-09-03', 'Male',   'O-',  '0413 456 789', 'j.kowalski@email.com',
     'Type 2 Diabetes, Hyperlipidemia', 'None', 'Atorvastatin 40mg, Insulin glargine',
     '88kg', '178cm', '128/82', '72', '8.9', 1),
    ('Maria',   'Fernandez', '1993-07-21', 'Female', 'B+',  '0414 567 890', 'maria.f@email.com',
     'Asthma', 'Aspirin', 'Salbutamol inhaler',
     '58kg', '162cm', '118/74', '68', '5.1', 1),
    ('Robert',  'Chang',     '1969-11-30', 'Male',   'AB+', '0415 678 901', 'r.chang@email.com',
     'Hypertension, Gout', 'Sulfa drugs', 'Lisinopril 10mg, Allopurinol 300mg',
     '84kg', '175cm', '138/88', '80', '5.4', 1),
    ('Emma',    'Wilson',    '1990-02-14', 'Female', 'A-',  '0416 789 012', 'emma.w@email.com',
     'Anxiety, Migraine', 'None', 'Sertraline 50mg, Sumatriptan 50mg',
     '62kg', '168cm', '112/70', '65', '4.9', 1),
    ('Ahmed',   'Hassan',    '1975-06-08', 'Male',   'O+',  '0417 890 123', 'ahmed.h@email.com',
     'COPD, Hypertension', 'Codeine', 'Salbutamol, Tiotropium, Amlodipine 10mg',
     '79kg', '172cm', '144/90', '82', '5.8', 1),
    ('Linda',   'Morrison',  '1948-03-25', 'Female', 'B-',  '0418 901 234', 'linda.m@email.com',
     'Osteoporosis, Hypothyroidism, AF', 'None', 'Thyroxine 100mcg, Warfarin 5mg, Alendronate',
     '65kg', '158cm', '122/76', '74', '5.6', 1),
    ('Daniel',  'Nguyen',    '2001-12-05', 'Male',   'A+',  '0419 012 345', 'd.nguyen@email.com',
     'None', 'None', 'None',
     '70kg', '180cm', '118/72', '66', '4.7', 1)
) AS v(first_name, last_name, dob, gender, blood_type, phone, email,
       medical_history, drug_allergies, medications, weight, height,
       blood_pressure, heart_rate, blood_glucose, created_by)
WHERE NOT EXISTS (SELECT 1 FROM patients LIMIT 1);

-- ── Sample Appointments (visits) ───────────────────────────────
INSERT INTO appointments
    (patient_id, doctor_id, appointment_date, start_time, duration_mins,
     appointment_type, notes, status, created_by)
SELECT p.id, 1,
    v.appt_date::DATE,
    v.appt_time::TIME,
    v.duration,
    v.appt_type,
    v.notes,
    v.status,
    1
FROM (VALUES
    ('Sarah Thompson',   CURRENT_DATE::TEXT,            '09:00', 30, 'Standard Consultation',  'Blood pressure review. BP reading 138/88. Medication adjusted.', 'completed'),
    ('Sarah Thompson',   (CURRENT_DATE - 30)::TEXT,     '10:00', 30, 'Follow-up',              'Follow-up diabetes management. HbA1c results reviewed.', 'completed'),
    ('Sarah Thompson',   (CURRENT_DATE - 90)::TEXT,     '09:30', 45, 'Annual Review',          'Annual health check. Referral to endocrinologist sent.', 'completed'),
    ('James Kowalski',   CURRENT_DATE::TEXT,            '09:30', 45, 'Follow-up',              'Diabetes management review. HbA1c 8.9% - elevated. Recall issued.', 'scheduled'),
    ('James Kowalski',   (CURRENT_DATE - 45)::TEXT,     '11:00', 30, 'Standard Consultation',  'Cholesterol levels checked. Statin dose increased.', 'completed'),
    ('James Kowalski',   (CURRENT_DATE - 120)::TEXT,    '14:00', 30, 'Standard Consultation',  'Routine check. Blood glucose 9.2 mmol/L.', 'completed'),
    ('Maria Fernandez',  CURRENT_DATE::TEXT,            '10:30', 30, 'New Patient',            'New patient registration. Asthma history noted. Inhaler reviewed.', 'scheduled'),
    ('Robert Chang',     CURRENT_DATE::TEXT,            '11:00', 30, 'Annual Review',          'Annual review. Gout flare last month. Uric acid 480 umol/L.', 'scheduled'),
    ('Robert Chang',     (CURRENT_DATE - 60)::TEXT,     '09:00', 30, 'Urgent',                 'Acute gout attack. Right big toe. Colchicine prescribed.', 'completed'),
    ('Emma Wilson',      CURRENT_DATE::TEXT,            '11:30', 15, 'Prescription Renewal',   'Sertraline renewal. Patient reports improved mood.', 'scheduled'),
    ('Emma Wilson',      (CURRENT_DATE - 14)::TEXT,     '16:00', 30, 'Follow-up',              'Anxiety follow-up. Sleep improving. Continue current medication.', 'completed'),
    ('Ahmed Hassan',     CURRENT_DATE::TEXT,            '14:00', 60, 'Procedure',              'Spirometry test. FEV1 62% predicted. COPD management plan reviewed.', 'scheduled'),
    ('Ahmed Hassan',     (CURRENT_DATE - 21)::TEXT,     '10:00', 30, 'Standard Consultation',  'Breathlessness worsening. Chest X-ray ordered.', 'completed'),
    ('Linda Morrison',   (CURRENT_DATE + 3)::TEXT,      '09:00', 45, 'Follow-up',              'INR check. Warfarin management. DEXA scan results.', 'scheduled'),
    ('Linda Morrison',   (CURRENT_DATE - 7)::TEXT,      '11:30', 30, 'Standard Consultation',  'AF management. Heart rate 88 bpm. Warfarin dose stable.', 'completed'),
    ('Daniel Nguyen',    (CURRENT_DATE + 7)::TEXT,      '10:00', 30, 'Standard Consultation',  'Sports physical for university. All clear.', 'scheduled')
) AS v(patient_name, appt_date, appt_time, duration, appt_type, notes, status)
JOIN patients p ON (p.first_name || ' ' || p.last_name) = v.patient_name
WHERE NOT EXISTS (SELECT 1 FROM appointments LIMIT 1);

-- ── Sample Internal Messages ─────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM messages LIMIT 1) THEN
    INSERT INTO messages (sender_id, receiver_id, subject, body, is_read, created_at) VALUES
    (1, 1, 'Abnormal lab result — James Kowalski',
     'James Kowalski HbA1c came back at 8.9% which is above target range. I have issued a recall and flagged the result as abnormal. Please review medication at next visit and consider referral to endocrinology if no improvement.',
     FALSE, NOW() - INTERVAL '2 hours'),

    (1, 1, 'INR check due — Linda Morrison',
     'Linda Morrison is due for her INR/Warfarin check this week. Last reading was 2.4 (target 2.0-3.0). Appointment is booked for Thursday at 9am. Please have current medication list ready.',
     FALSE, NOW() - INTERVAL '5 hours'),

    (1, 1, 'Chest X-ray results — Ahmed Hassan',
     'Radiology report received for Ahmed Hassan. Findings: Hyperinflation consistent with moderate COPD. No acute consolidation or pneumothorax. No significant change from previous imaging. Recommend continuing current management plan and repeat spirometry in 3 months.',
     TRUE, NOW() - INTERVAL '1 day'),

    (1, 1, 'New patient referral — Maria Fernandez',
     'Received referral from Dr. O Brien for Maria Fernandez, 31F, known asthma. She is booked in today for a new patient appointment at 10:30. Please note aspirin allergy. Referral letter is in her documents.',
     FALSE, NOW() - INTERVAL '3 hours'),

    (1, 1, 'Staff meeting — Friday 3pm',
     'Reminder: monthly staff meeting is this Friday at 3:00pm in the conference room. Agenda includes: QIP audit review, new booking system update, flu vaccine clinic planning for April. Please bring your patient list stats.',
     TRUE, NOW() - INTERVAL '2 days'),

    (1, 1, 'Urgent — Emma Wilson prescription',
     'Emma Wilson called requesting urgent prescription renewal for Sertraline 50mg. She is running out tomorrow. She has an appointment booked at 11:30 today. If you can please have the script ready before she arrives.',
     FALSE, NOW() - INTERVAL '30 minutes');
  END IF;
END $$;

SELECT 'Sample data inserted successfully.' as status;

-- ── Tasks / Work Routing ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tasks (
    id           SERIAL PRIMARY KEY,
    patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    created_by   INTEGER REFERENCES staff(id),
    assigned_to  INTEGER REFERENCES staff(id),
    title        VARCHAR(200) NOT NULL,
    description  TEXT,
    priority     VARCHAR(20) DEFAULT 'normal',
    status       VARCHAR(30) DEFAULT 'pending',
    due_date     DATE,
    completed_at TIMESTAMP,
    task_type    VARCHAR(50) DEFAULT 'general',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_tasks_patient  ON tasks(patient_id);

-- ── Advanced Feature Tables ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS btg_access (
    id             SERIAL PRIMARY KEY,
    staff_id       INTEGER REFERENCES staff(id),
    patient_id     INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    justification  TEXT NOT NULL,
    granted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at     TIMESTAMP,
    revoked_at     TIMESTAMP,
    revoked_by     INTEGER REFERENCES staff(id),
    admin_notified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS document_signatures (
    id           SERIAL PRIMARY KEY,
    record_type  VARCHAR(50) NOT NULL,
    record_id    INTEGER NOT NULL,
    signed_by    INTEGER REFERENCES staff(id),
    content_hash VARCHAR(128) NOT NULL,
    signed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algorithm    VARCHAR(20) DEFAULT 'SHA-256'
);

CREATE TABLE IF NOT EXISTS inventory (
    id            SERIAL PRIMARY KEY,
    item_name     VARCHAR(200) NOT NULL,
    category      VARCHAR(100),
    quantity      INTEGER DEFAULT 0,
    unit          VARCHAR(50),
    reorder_level INTEGER DEFAULT 5,
    cpt_code      VARCHAR(20),
    unit_cost     NUMERIC(10,2),
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE referrals ADD COLUMN IF NOT EXISTS outcome VARCHAR(50) DEFAULT 'pending';
ALTER TABLE referrals ADD COLUMN IF NOT EXISTS outcome_notes TEXT;
ALTER TABLE referrals ADD COLUMN IF NOT EXISTS appointment_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE referrals ADD COLUMN IF NOT EXISTS report_received BOOLEAN DEFAULT FALSE;
ALTER TABLE referrals ADD COLUMN IF NOT EXISTS follow_up_due DATE;
ALTER TABLE patients  ADD COLUMN IF NOT EXISTS risk_score SMALLINT;
ALTER TABLE patients  ADD COLUMN IF NOT EXISTS risk_updated TIMESTAMP;
ALTER TABLE lab_tests ADD COLUMN IF NOT EXISTS auto_notified BOOLEAN DEFAULT FALSE;

-- Inventory seed data
INSERT INTO inventory (item_name, category, quantity, unit, reorder_level, cpt_code, unit_cost)
SELECT * FROM (VALUES
  ('Influenza Vaccine',    'Vaccines',    20, 'dose',  5,  '90686', 25.00),
  ('COVID-19 Vaccine',     'Vaccines',    10, 'dose',  3,  '91309', 35.00),
  ('Hepatitis B Vaccine',  'Vaccines',    15, 'dose',  5,  '90746', 28.00),
  ('Syringes 3mL',         'Supplies',   200, 'unit', 50,  NULL,     0.15),
  ('Alcohol Swabs',        'Supplies',   500, 'unit', 100, NULL,     0.05),
  ('Blood Glucose Strips', 'Diagnostics', 50, 'box',  10,  '82962',  8.00),
  ('Urine Dipsticks',      'Diagnostics', 30, 'box',   5,  '81001',  6.50),
  ('Gloves (M)',           'Supplies',   300, 'pair',  50, NULL,     0.08),
  ('Examination Couch Paper','Supplies', 10, 'roll',   2,  NULL,     4.50),
  ('PPE Masks',            'Supplies',   100, 'unit',  20, NULL,     0.25)
) AS v(item_name,category,quantity,unit,reorder_level,cpt_code,unit_cost)
WHERE NOT EXISTS (SELECT 1 FROM inventory LIMIT 1);

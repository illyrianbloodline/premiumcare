-- ============================================================
-- MedPlatform — Comprehensive Seed Data
-- Covers every table so you can test every screen
-- Run AFTER setup_database.sql:
--   psql -U medplatform_user -d medplatform -f seed_data.sql
-- ============================================================

-- Wipe existing sample data cleanly (safe — won't touch schema)
TRUNCATE TABLE
  appointment_reminders, receipts, invoice_items, invoices,
  referrals, recalls, reminders, vaccinations, waiting_room,
  patient_documents, lab_tests, prescriptions,
  scan_analyses, symptom_analyses, consultation_notes,
  visit_notes, messages, activity_log, appointments,
  patients, address_book
RESTART IDENTITY CASCADE;

-- Keep admin user, remove other sample staff, re-insert clean set
DELETE FROM staff WHERE email != 'admin@practice.local';


-- ── STAFF ────────────────────────────────────────────────────
-- Password for all staff: Staff123! (bcrypt)
INSERT INTO staff (name, email, password, role, specialty, phone, active) VALUES
('Dr. Elena Marchetti',   'elena.marchetti@practice.local',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'doctor',       'General Practice',  '0411 111 001', TRUE),
('Dr. James Okonkwo',     'james.okonkwo@practice.local',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'doctor',       'Cardiology',        '0411 111 002', TRUE),
('Dr. Sophie Nguyen',     'sophie.nguyen@practice.local',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'doctor',       'Endocrinology',     '0411 111 003', TRUE),
('Nurse Maria Santos',    'maria.santos@practice.local',     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'nurse',        'General',           '0411 111 004', TRUE),
('Nurse Tom Bradley',     'tom.bradley@practice.local',      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'nurse',        'General',           '0411 111 005', TRUE),
('Lisa Chen',             'lisa.chen@practice.local',        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'receptionist', NULL,                '0411 111 006', TRUE),
('Dr. Amara Diallo',      'amara.diallo@practice.local',     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KFvhCm', 'doctor',       'Respiratory',       '0411 111 007', FALSE);


-- ── PATIENTS (12 realistic patients) ─────────────────────────
INSERT INTO patients (
  first_name, last_name, dob, gender, blood_type, insurance_nr,
  address, phone, email, emergency_contact, family_doctor,
  medical_history, surgeries, family_history, drug_allergies, env_allergies,
  medications, supplements, past_medications,
  weight, height, blood_pressure, heart_rate, temperature,
  oxygen_sat, blood_glucose, cholesterol, notes, icd_codes, created_by
) VALUES
-- 1
('Sarah',    'Thompson',  '1982-04-12', 'Female', 'A+',  'INS-10021', '14 Maple St, Sydney NSW 2000',     '0412 345 678', 'sarah.t@email.com',  'John Thompson 0412 999 001', 'Dr. Elena Marchetti',
 'Hypertension, Type 2 Diabetes', 'Appendectomy 2010', 'Father: T2DM, Mother: Hypertension', 'Penicillin', 'Pollen',
 'Metformin 500mg BD, Amlodipine 5mg daily', 'Vitamin D 1000IU', 'Atenolol (discontinued 2020)',
 '72 kg','165 cm','138/88 mmHg','78 bpm','36.8°C','97%','7.2 mmol/L','5.4 mmol/L',
 'Regular 3-month review. Excellent compliance.', 'I10, E11', 2),
-- 2
('James',    'Kowalski',  '1957-09-03', 'Male',   'O-',  'INS-10022', '8 Oak Ave, Melbourne VIC 3000',     '0413 456 789', 'j.kowalski@email.com','Anna Kowalski 0413 999 002', 'Dr. James Okonkwo',
 'Type 2 Diabetes, Hyperlipidaemia, Ischaemic heart disease', 'CABG 2018', 'Brother: MI age 52',           'None',         'Dust mites',
 'Atorvastatin 40mg, Insulin glargine 20U nocte, Aspirin 100mg', 'CoQ10', 'Simvastatin (switched 2019)',
 '88 kg','178 cm','132/84 mmHg','72 bpm','36.6°C','96%','8.9 mmol/L','4.1 mmol/L',
 'High cardiac risk. Annual stress ECG.', 'E11, I25, E78', 3),
-- 3
('Maria',    'Fernandez', '1993-07-21', 'Female', 'B+',  'INS-10023', '22 Beach Rd, Brisbane QLD 4000',   '0414 567 890', 'maria.f@email.com',  'Rosa Fernandez 0414 999 003','Dr. Elena Marchetti',
 'Asthma, Anxiety', NULL, 'Mother: Asthma', 'Aspirin, Ibuprofen', 'Cat dander, Dust',
 'Salbutamol inhaler PRN, Sertraline 25mg daily', 'Magnesium', NULL,
 '58 kg','162 cm','118/74 mmHg','68 bpm','36.5°C','99%','5.1 mmol/L','4.8 mmol/L',
 'NSAID allergy — avoid all NSAIDs. Asthma well-controlled.', 'J45, F41', 2),
-- 4
('Robert',   'Chang',     '1969-11-30', 'Male',   'AB+', 'INS-10024', '5 Hill St, Perth WA 6000',         '0415 678 901', 'r.chang@email.com',  'Lucy Chang 0415 999 004',    'Dr. Sophie Nguyen',
 'Hypertension, Gout, Hypothyroidism', 'None', 'Father: Stroke', 'Sulfa drugs', 'None',
 'Lisinopril 10mg, Allopurinol 300mg, Thyroxine 75mcg', NULL, 'Colchicine (PRN, stopped)',
 '84 kg','175 cm','142/90 mmHg','80 bpm','36.7°C','98%','5.4 mmol/L','6.1 mmol/L',
 'Uric acid elevated last visit. Review diet.', 'I10, M10, E03', 4),
-- 5
('Emma',     'Wilson',    '1990-02-14', 'Female', 'A-',  'INS-10025', '30 Park Lane, Adelaide SA 5000',   '0416 789 012', 'emma.w@email.com',   'Peter Wilson 0416 999 005',  'Dr. Elena Marchetti',
 'Anxiety, Migraine, Iron deficiency anaemia', 'Laparoscopy 2019', 'None', 'Codeine', 'None',
 'Sertraline 50mg, Sumatriptan 50mg PRN, Ferrous sulphate 325mg', 'Iron, B12', 'Paroxetine (stopped 2021)',
 '62 kg','168 cm','112/70 mmHg','65 bpm','36.6°C','99%','4.9 mmol/L','4.3 mmol/L',
 'Migraine frequency improving. Monitor ferritin.', 'F41, G43, D50', 2),
-- 6
('Ahmed',    'Hassan',    '1975-06-08', 'Male',   'O+',  'INS-10026', '17 River St, Darwin NT 0800',      '0417 890 123', 'ahmed.h@email.com',  'Fatima Hassan 0417 999 006', 'Dr. Sophie Nguyen',
 'COPD, Hypertension, Type 2 Diabetes', 'None', 'Father: COPD, smoker', 'Codeine', 'Pollen',
 'Salbutamol inhaler, Tiotropium 18mcg, Amlodipine 10mg, Metformin 1g BD', 'Vitamin C', 'Theophylline (stopped 2018)',
 '79 kg','172 cm','148/92 mmHg','82 bpm','36.9°C','94%','9.2 mmol/L','5.9 mmol/L',
 'COPD stage 2. Refer pulmonology if FEV1 drops further. Stop smoking advice given.', 'J44, I10, E11', 4),
-- 7
('Linda',    'Morrison',  '1948-03-25', 'Female', 'B-',  'INS-10027', '1 Cliff Rd, Hobart TAS 7000',     '0418 901 234', 'linda.m@email.com',  'David Morrison 0418 999 007','Dr. James Okonkwo',
 'Osteoporosis, Hypothyroidism, Atrial Fibrillation, CKD stage 2', 'Hip replacement 2022',
 'Sister: Osteoporosis', 'None', 'None',
 'Thyroxine 100mcg, Warfarin 5mg, Alendronate 70mg weekly, Calcium+D3', 'Omega-3', 'Digoxin (stopped 2020)',
 '65 kg','158 cm','126/76 mmHg','74 bpm','36.4°C','97%','5.6 mmol/L','4.7 mmol/L',
 'INR target 2.0–3.0. Last INR 2.4. DEXA scan due in 12 months.', 'M81, E03, I48, N18', 3),
-- 8
('Daniel',   'Nguyen',    '2001-12-05', 'Male',   'A+',  'INS-10028', '9 College St, Sydney NSW 2010',    '0419 012 345', 'd.nguyen@email.com', 'Hoa Nguyen 0419 999 008',    'Dr. Elena Marchetti',
 'None', 'None', 'None', 'None', 'None',
 'None', 'Protein powder', NULL,
 '70 kg','180 cm','118/72 mmHg','66 bpm','36.5°C','99%','4.7 mmol/L','3.9 mmol/L',
 'Sports physical. Healthy young adult.', NULL, 2),
-- 9
('Patricia', 'O''Brien',  '1964-08-19', 'Female', 'O+',  'INS-10029', '44 Sunset Blvd, Sydney NSW 2020', '0420 123 456', 'pat.obrien@email.com','Sean O''Brien 0420 999 009', 'Dr. James Okonkwo',
 'Breast cancer (remission 2021), Hypertension', 'Mastectomy 2019, Reconstruction 2020',
 'Mother: Breast cancer', 'Sulfa, Tetracycline', 'None',
 'Tamoxifen 20mg, Amlodipine 5mg, Letrozole 2.5mg', 'Vitamin D, Calcium', 'Doxorubicin (chemo completed)',
 '68 kg','163 cm','134/82 mmHg','76 bpm','36.7°C','98%','5.3 mmol/L','5.1 mmol/L',
 '3-year post-mastectomy. Oncology review every 6 months. No evidence of recurrence.', 'Z85.3, I10', 3),
-- 10
('Marcus',   'Williams',  '1988-03-15', 'Male',   'B+',  'INS-10030', '7 Bay St, Melbourne VIC 3010',    '0421 234 567', 'marcus.w@email.com', 'Claire Williams 0421 999 010','Dr. Elena Marchetti',
 'Type 1 Diabetes, Coeliac disease', 'None', 'Father: T1DM',
 'Penicillin, Amoxicillin', 'Gluten (medical)',
 'Insulin aspart 8U with meals, Insulin glargine 24U nocte', 'B12, Iron', NULL,
 '75 kg','182 cm','120/78 mmHg','70 bpm','36.6°C','99%','6.8 mmol/L','4.2 mmol/L',
 'Excellent HbA1c control. Strict gluten-free diet. CGM in use.', 'E10, K90', 2),
-- 11
('Yuki',     'Tanaka',    '1979-11-02', 'Female', 'AB-', 'INS-10031', '3 Garden Rd, Brisbane QLD 4010',  '0422 345 678', 'yuki.t@email.com',   'Kenji Tanaka 0422 999 011',  'Dr. Sophie Nguyen',
 'Rheumatoid Arthritis, Depression', 'None', 'Mother: RA',
 'NSAIDs (GI intolerance)', 'None',
 'Methotrexate 15mg weekly, Folic acid 5mg weekly, Duloxetine 60mg', 'Fish oil', 'Naproxen (stopped — GI bleed 2022)',
 '55 kg','160 cm','116/72 mmHg','69 bpm','36.5°C','98%','5.0 mmol/L','4.5 mmol/L',
 'RA moderately controlled. Last DAS28 score 3.1. Rheumatology review due.', 'M05, F32', 4),
-- 12
('George',   'Papadopoulos','1952-05-17','Male',  'A+',  'INS-10032', '88 Main Rd, Adelaide SA 5010',    '0423 456 789', 'george.p@email.com', 'Helen Papadopoulos 0423 999 012','Dr. James Okonkwo',
 'CHF NYHA II, Hypertension, CKD stage 3, Gout', 'Pacemaker 2020',
 'Brother: CHF, Father: MI', 'ACE inhibitors (cough)', 'None',
 'Furosemide 40mg, Carvedilol 6.25mg BD, Spironolactone 25mg, Allopurinol 100mg', NULL, 'Lisinopril (switched due to cough)',
 '90 kg','170 cm','150/94 mmHg','88 bpm','36.8°C','95%','6.1 mmol/L','5.8 mmol/L',
 'CHF stable. Fluid restriction 1.5L/day. Renal function monitoring monthly.', 'I50, I10, N18, M10', 3);


-- ── APPOINTMENTS ─────────────────────────────────────────────
INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, duration_mins, appointment_type, status, notes, created_by) VALUES
-- Sarah Thompson (pid 1)
(1,  2, CURRENT_DATE,              '09:00', 30, 'Standard Consultation', 'scheduled',  'BP review and HbA1c results discussion', 1),
(1,  2, CURRENT_DATE - 30,         '09:30', 30, 'Follow-up',             'completed',  'Medication review. Increased Metformin to 1g BD.', 1),
(1,  2, CURRENT_DATE - 90,         '10:00', 45, 'Annual Review',         'completed',  'Annual health check. Referral to dietitian.', 1),
(1,  2, CURRENT_DATE + 30,         '09:00', 30, 'Follow-up',             'scheduled',  'HbA1c recheck and BP monitoring', 1),
-- James Kowalski (pid 2)
(2,  3, CURRENT_DATE,              '10:00', 45, 'Cardiac Review',        'scheduled',  'Annual cardiac review. ECG and lipid panel.', 1),
(2,  3, CURRENT_DATE - 45,         '11:00', 30, 'Standard Consultation', 'completed',  'Chest pain episode resolved. No new changes on ECG.', 1),
(2,  3, CURRENT_DATE - 120,        '09:00', 60, 'Procedure',             'completed',  'Stress ECG — normal.', 1),
-- Maria Fernandez (pid 3)
(3,  2, CURRENT_DATE,              '11:00', 30, 'New Patient',           'scheduled',  'New patient registration', 1),
(3,  2, CURRENT_DATE - 14,         '14:00', 30, 'Asthma Review',         'completed',  'Salbutamol use increased. Added ICS if needed.', 1),
-- Robert Chang (pid 4)
(4,  4, CURRENT_DATE,              '11:30', 30, 'Annual Review',         'scheduled',  'Annual blood work and gout review', 1),
(4,  4, CURRENT_DATE - 60,         '09:30', 30, 'Urgent',                'completed',  'Acute gout flare — right big toe. Colchicine prescribed.', 1),
-- Emma Wilson (pid 5)
(5,  2, CURRENT_DATE + 7,          '14:30', 15, 'Prescription Renewal',  'scheduled',  'Sertraline renewal', 1),
(5,  2, CURRENT_DATE - 7,          '16:00', 30, 'Follow-up',             'completed',  'Anxiety improving. Sleep better. Continue current management.', 1),
-- Ahmed Hassan (pid 6)
(6,  4, CURRENT_DATE,              '14:00', 60, 'Procedure',             'scheduled',  'Spirometry test. COPD management plan.', 1),
(6,  4, CURRENT_DATE - 21,         '10:00', 30, 'Standard Consultation', 'completed',  'Breathlessness worse. Chest X-ray ordered.', 1),
-- Linda Morrison (pid 7)
(7,  3, CURRENT_DATE + 3,          '09:00', 45, 'Follow-up',             'scheduled',  'INR check. Warfarin management.', 1),
(7,  3, CURRENT_DATE - 7,          '11:30', 30, 'Standard Consultation', 'completed',  'AF rate controlled. INR 2.4 — on target.', 1),
-- Daniel Nguyen (pid 8)
(8,  2, CURRENT_DATE + 14,         '10:00', 30, 'Standard Consultation', 'scheduled',  'Sports physical for university competition', 1),
-- Patricia O''Brien (pid 9)
(9,  3, CURRENT_DATE - 3,          '13:00', 45, 'Oncology Review',       'completed',  'No signs of recurrence. Continue Tamoxifen. Next mammogram 6 months.', 1),
(9,  3, CURRENT_DATE + 60,         '13:00', 45, 'Oncology Review',       'scheduled',  'Routine oncology follow-up', 1),
-- Marcus Williams (pid 10)
(10, 2, CURRENT_DATE - 10,         '09:30', 30, 'Diabetes Review',       'completed',  'HbA1c 6.8% — excellent. CGM data reviewed.', 1),
(10, 2, CURRENT_DATE + 45,         '09:30', 30, 'Diabetes Review',       'scheduled',  'Quarterly diabetes review', 1),
-- Yuki Tanaka (pid 11)
(11, 4, CURRENT_DATE - 5,          '15:00', 30, 'Rheumatology Review',   'completed',  'DAS28 3.1. Continue current DMARDs. No dose change.', 1),
(11, 4, CURRENT_DATE + 90,         '15:00', 30, 'Rheumatology Review',   'scheduled',  'Quarterly RA review', 1),
-- George Papadopoulos (pid 12)
(12, 3, CURRENT_DATE - 1,          '08:30', 45, 'Cardiac Review',        'completed',  'Pacemaker check normal. Oedema minimal. Maintain current regime.', 1),
(12, 3, CURRENT_DATE + 28,         '08:30', 45, 'Cardiac Review',        'scheduled',  'Monthly cardiac review and renal function check', 1),
-- A cancelled appointment to show that status
(5,  2, CURRENT_DATE - 20,         '10:00', 30, 'Follow-up',             'cancelled',  'Patient cancelled — travelling interstate', 1);


-- ── VISIT NOTES ───────────────────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by) VALUES
(1, 2, CURRENT_DATE - 30, 'Follow-up',  'completed',
 'Routine BP and diabetes review',
 'I10 Hypertension — controlled. E11 T2DM — HbA1c 7.4%',
 'Increased Metformin to 1g BD. Continue Amlodipine 5mg.',
 'Patient reports compliance with medications and dietary changes. BP 138/88 — slightly elevated. HbA1c 7.4% — above target of 7.0%. Weight stable at 72kg. No hypoglycaemic episodes. Feet checked — no neuropathy. Eyes reviewed by ophthalmologist last month — no retinopathy.',
 'Repeat HbA1c in 3 months. Dietary review recommended.', 1),
(1, 2, CURRENT_DATE - 90, 'Annual Review','completed',
 'Annual health check',
 'Preventive health — annual review',
 'Referral to dietitian. Continue current medications.',
 'Comprehensive annual review. All vaccinations up to date. Cervical screening due next year. Breast screening done 6 months ago — normal. Urine ACR 2.8 — within normal. eGFR 82. Lipid panel: Total cholesterol 5.4, LDL 3.1, HDL 1.4.',
 'Dietitian referral placed. Annual review in 12 months.', 1),
(2, 3, CURRENT_DATE - 45, 'Standard Consultation','completed',
 'Chest tightness episode last week',
 'I20 Stable angina — no change from baseline',
 'Rest and GTN spray if recurs. Repeat ECG normal.',
 'Patient reports 20-minute episode of chest tightness while walking uphill. Resolved with rest. No radiation. No diaphoresis. Vitals stable. ECG: normal sinus rhythm, no ST changes. Troponin negative. Likely stable angina. Medication adherent.',
 'Exercise stress test booked. Continue current cardiac medications.', 1),
(3, 2, CURRENT_DATE - 14,'Asthma Review','completed',
 'Increased use of Salbutamol this month',
 'J45 Asthma — mild persistent, partially controlled',
 'Added inhaled corticosteroid (Budesonide 200mcg BD) step-up therapy.',
 'Patient using Salbutamol 4-5x/week (up from 1-2x). Mainly triggered by cold air and exercise. Peak flow 88% predicted. Lungs clear on auscultation. FeNO not performed today. No ER visits. Reviewed inhaler technique — correct.',
 'Review in 4 weeks. Asthma action plan updated.', 1),
(6, 4, CURRENT_DATE - 21,'Standard Consultation','completed',
 'Increased breathlessness on exertion',
 'J44 COPD — moderate, FEV1 62% predicted',
 'Chest X-ray ordered. Optimise bronchodilator therapy.',
 'Patient reports SOBOE worsening over past 3 weeks. Now breathless on flat ground. No fever. No haemoptysis. Sputum yellow — possible infective exacerbation. O2 sat 94% on air. Chest: hyperinflated, bilateral wheeze, no creps. CXR ordered to exclude pneumonia.',
 'Review CXR results. If infective — start amoxicillin + prednisolone course.', 1),
(7, 3, CURRENT_DATE - 7, 'Standard Consultation','completed',
 'Routine AF and Warfarin management',
 'I48 AF — rate controlled. INR 2.4 — therapeutic range',
 'Maintain Warfarin 5mg. Next INR in 4 weeks.',
 'Patient stable. HR 74 irregular. BP 126/76. No signs of decompensation. INR 2.4 — within target 2.0–3.0. No bleeding symptoms. No new bruising. Pacemaker pocket site clean. Denies dizziness or palpitations.',
 'INR recheck 4 weeks. Renal function 3-monthly.', 1),
(9, 3, CURRENT_DATE - 3, 'Oncology Review','completed',
 'Routine oncology follow-up — 3 years post mastectomy',
 'Z85.3 Personal history of breast malignancy — in remission',
 'Continue Letrozole 2.5mg and Tamoxifen. Mammogram in 6 months.',
 'Patient well. No symptoms of recurrence. No bone pain. No lymphadenopathy. Wound site fully healed. Mood good, working part-time. Annual bloods: CA 15-3 normal. Liver function normal. Bone density stable on DEXA.',
 'Mammogram booked 6 months. Oncology clinic review 6 months.', 1),
(12, 3, CURRENT_DATE - 1, 'Cardiac Review','completed',
 'Monthly cardiac review — CHF management',
 'I50 CHF NYHA Class II — stable',
 'Continue current regime. Fluid restrict 1.5L/day. Daily weights.',
 'Weight 90kg (up 1kg from last month). Mild ankle oedema. No orthopnoea. Sleeping flat. BP 150/94 — slightly above target. HR 88 regular. Chest clear. Abdomen soft, no ascites. Pacemaker interrogation normal. eGFR 38 — stable CKD3.',
 'Increase Furosemide to 80mg if weight increases >2kg. Renal function again in 4 weeks.', 1);


-- ── PRESCRIPTIONS ─────────────────────────────────────────────
INSERT INTO prescriptions (patient_id, doctor_id, drug_name, dosage, frequency, route, start_date, end_date, repeats, instructions, status) VALUES
(1, 2, 'Metformin',         '1000mg',  'Twice daily',        'Oral', CURRENT_DATE - 180, NULL, 5, 'Take with food. Monitor for GI side effects.', 'active'),
(1, 2, 'Amlodipine',        '5mg',     'Once daily',         'Oral', CURRENT_DATE - 365, NULL, 5, 'Take in the morning.', 'active'),
(2, 3, 'Atorvastatin',      '40mg',    'Once daily at night','Oral', CURRENT_DATE - 365, NULL, 5, 'Take at bedtime. Avoid grapefruit juice.', 'active'),
(2, 3, 'Insulin glargine',  '20 units','Once daily nocte',   'SC',   CURRENT_DATE - 200, NULL, 5, 'Inject subcutaneously at 10pm. Rotate sites.', 'active'),
(2, 3, 'Aspirin',           '100mg',   'Once daily',         'Oral', CURRENT_DATE - 365, NULL, 5, 'Take after food.', 'active'),
(3, 2, 'Salbutamol inhaler','100mcg',  'PRN (as needed)',    'Inhaled', CURRENT_DATE - 90, NULL, 2, '2 puffs as needed for wheeze/shortness of breath.', 'active'),
(3, 2, 'Sertraline',        '25mg',    'Once daily',         'Oral', CURRENT_DATE - 60, NULL,  3, 'Take in the morning with food. Titrate as needed.', 'active'),
(5, 2, 'Sertraline',        '50mg',    'Once daily',         'Oral', CURRENT_DATE - 180, NULL, 5, 'Take in the morning.', 'active'),
(5, 2, 'Sumatriptan',       '50mg',    'PRN (for migraine)', 'Oral', CURRENT_DATE - 180, NULL, 2, 'Take at onset of migraine. Max 2 tablets/24hrs.', 'active'),
(6, 4, 'Tiotropium',        '18mcg',   'Once daily',         'Inhaled', CURRENT_DATE - 365, NULL, 5, 'One capsule via HandiHaler every morning.', 'active'),
(6, 4, 'Amlodipine',        '10mg',    'Once daily',         'Oral', CURRENT_DATE - 365, NULL, 5, 'Take in the morning.', 'active'),
(7, 3, 'Warfarin',          '5mg',     'Once daily',         'Oral', CURRENT_DATE - 730, NULL, 5, 'Take at 6pm daily. Regular INR monitoring required.', 'active'),
(7, 3, 'Thyroxine',         '100mcg',  'Once daily fasting', 'Oral', CURRENT_DATE - 730, NULL, 5, 'Take 30 mins before food. Do not take with calcium.', 'active'),
(7, 3, 'Alendronate',       '70mg',    'Once weekly',        'Oral', CURRENT_DATE - 365, NULL, 5, 'Take on empty stomach. Sit upright 30 mins after.', 'active'),
(9, 3, 'Letrozole',         '2.5mg',   'Once daily',         'Oral', CURRENT_DATE - 365, NULL, 5, 'Aromatase inhibitor. Monitor bone density annually.', 'active'),
(10, 2,'Insulin aspart',    '8 units', 'Three times daily',  'SC',   CURRENT_DATE - 730, NULL, 5, 'Inject 10 mins before each main meal.', 'active'),
(11, 4,'Methotrexate',      '15mg',    'Once weekly',        'Oral', CURRENT_DATE - 365, NULL, 5, 'Take on the same day each week. MUST take folic acid the following day.', 'active'),
(11, 4,'Duloxetine',        '60mg',    'Once daily',         'Oral', CURRENT_DATE - 180, NULL, 3, 'Take in the morning with food.', 'active'),
(12, 3,'Furosemide',        '40mg',    'Once daily',         'Oral', CURRENT_DATE - 365, NULL, 5, 'Take in the morning. Monitor fluid intake/output.', 'active'),
(12, 3,'Carvedilol',        '6.25mg',  'Twice daily',        'Oral', CURRENT_DATE - 365, NULL, 5, 'Take with food. Do not stop suddenly.', 'active'),
-- A completed/discontinued one
(4, 4, 'Colchicine',        '500mcg',  'Twice daily',        'Oral', CURRENT_DATE - 65, CURRENT_DATE - 51, 0, 'For acute gout. 5-day course.', 'completed');


-- ── LAB TESTS ─────────────────────────────────────────────────
INSERT INTO lab_tests (patient_id, doctor_id, test_name, test_type, ordered_date, result_date, result_value, reference_range, is_abnormal, status, notes) VALUES
-- Sarah
(1, 2, 'HbA1c',                'Blood', CURRENT_DATE - 30, CURRENT_DATE - 25, '7.4%',      '< 7.0%',           TRUE,  'resulted', 'Above target — increase Metformin'),
(1, 2, 'Lipid Panel',          'Blood', CURRENT_DATE - 30, CURRENT_DATE - 25, 'LDL 3.1',   'LDL < 2.6 mmol/L', TRUE,  'resulted', 'LDL mildly elevated'),
(1, 2, 'eGFR / Urine ACR',    'Blood', CURRENT_DATE - 90, CURRENT_DATE - 85, 'eGFR 82',   '> 60',             FALSE, 'resulted', 'Normal renal function'),
(1, 2, 'HbA1c',                'Blood', CURRENT_DATE,      NULL,               NULL,        '< 7.0%',           FALSE, 'ordered',  'Quarterly check'),
-- James
(2, 3, 'Troponin I',           'Blood', CURRENT_DATE - 45, CURRENT_DATE - 45, '< 0.01',    '< 0.04 µg/L',      FALSE, 'resulted', 'Normal — chest pain episode'),
(2, 3, 'Lipid Panel',          'Blood', CURRENT_DATE - 45, CURRENT_DATE - 42, 'LDL 2.2',   'LDL < 2.0 mmol/L', TRUE,  'resulted', 'Slightly elevated — atorvastatin dose adequate'),
(2, 3, 'HbA1c',                'Blood', CURRENT_DATE,      NULL,               NULL,        '< 7.5%',           FALSE, 'ordered',  'Annual diabetes review'),
(2, 3, 'BNP',                  'Blood', CURRENT_DATE - 45, CURRENT_DATE - 43, '182 pg/mL', '< 100 pg/mL',      TRUE,  'resulted', 'Mildly elevated — monitor'),
-- Ahmed
(6, 4, 'Spirometry FEV1',      'Pulm',  CURRENT_DATE - 21, CURRENT_DATE - 19, '62% predicted', '> 80%',        TRUE,  'resulted', 'COPD moderate confirmed'),
(6, 4, 'Sputum Culture',       'Micro', CURRENT_DATE - 21, CURRENT_DATE - 16, 'H.influenzae sensitive to amoxicillin', 'No growth', TRUE, 'resulted', 'Infective exacerbation confirmed'),
(6, 4, 'Chest X-Ray',          'Imaging',CURRENT_DATE - 21,CURRENT_DATE - 20, 'Hyperinflation consistent with COPD. No consolidation.', 'Normal', FALSE, 'resulted', ''),
-- Linda
(7, 3, 'INR',                  'Blood', CURRENT_DATE - 7,  CURRENT_DATE - 7,  '2.4',       '2.0 – 3.0',        FALSE, 'resulted', 'Therapeutic — maintain Warfarin 5mg'),
(7, 3, 'eGFR',                 'Blood', CURRENT_DATE - 7,  CURRENT_DATE - 6,  'eGFR 58',   '> 60',             TRUE,  'resulted', 'CKD stage 2 — monitor 3-monthly'),
(7, 3, 'INR',                  'Blood', CURRENT_DATE + 21, NULL,               NULL,        '2.0 – 3.0',        FALSE, 'ordered',  'Routine INR check'),
-- George
(12, 3,'BNP',                  'Blood', CURRENT_DATE - 1,  CURRENT_DATE - 1,  '420 pg/mL', '< 100 pg/mL',      TRUE,  'resulted', 'Elevated — CHF monitoring'),
(12, 3,'eGFR',                 'Blood', CURRENT_DATE - 1,  CURRENT_DATE - 1,  'eGFR 38',   '> 60',             TRUE,  'resulted', 'CKD3 — stable'),
(12, 3,'Electrolytes + Renal', 'Blood', CURRENT_DATE + 28, NULL,               NULL,        'Na 135-145, K 3.5-5.0', FALSE,'ordered', 'Monthly renal function'),
-- Patricia
(9, 3, 'CA 15-3 Tumour Marker','Blood', CURRENT_DATE - 3,  CURRENT_DATE - 2,  '18 U/mL',   '< 30 U/mL',        FALSE, 'resulted', 'Within normal — no recurrence markers'),
-- Ordered but not yet resulted
(5, 2, 'Iron Studies',         'Blood', CURRENT_DATE - 2,  NULL,               NULL,        NULL,               FALSE, 'ordered',  'Ferritin check — iron deficiency anaemia'),
(10,2, 'HbA1c',                'Blood', CURRENT_DATE - 10, CURRENT_DATE - 8,  '6.8%',      '< 7.5%',           FALSE, 'resulted', 'Excellent control'),
(11,4, 'LFTs',                 'Blood', CURRENT_DATE - 5,  CURRENT_DATE - 4,  'ALT 28, AST 22', 'ALT < 40, AST < 40', FALSE, 'resulted', 'Normal — Methotrexate monitoring');


-- ── INVOICES ──────────────────────────────────────────────────
INSERT INTO invoices (patient_id, doctor_id, invoice_date, due_date, items, total_amount, amount_paid, status, notes, created_by) VALUES
-- Paid invoices
(1,  2, CURRENT_DATE - 90, CURRENT_DATE - 60, 'Standard Consultation x1\nMedicare Item 23', 80.00,  80.00,  'paid',    'Annual review', 1),
(1,  2, CURRENT_DATE - 30, CURRENT_DATE,       'Standard Consultation x1\nBlood Test Referral', 85.00, 85.00, 'paid',  'Routine visit', 1),
(2,  3, CURRENT_DATE - 45, CURRENT_DATE - 15, 'Long Consultation x1\nECG x1\nPathology referral', 145.00, 145.00, 'paid', 'Cardiac review', 1),
(3,  2, CURRENT_DATE - 14, CURRENT_DATE + 16, 'Standard Consultation x1\nSpirometry x1', 110.00, 110.00, 'paid', 'Asthma review', 1),
(7,  3, CURRENT_DATE - 7,  CURRENT_DATE + 23, 'Standard Consultation x1\nINR test x1', 95.00,  95.00,  'paid',    'Warfarin review', 1),
(9,  3, CURRENT_DATE - 3,  CURRENT_DATE + 27, 'Long Consultation x1\nOncology Assessment x1\nPathology x1', 220.00, 220.00, 'paid', 'Oncology review', 1),
(10, 2, CURRENT_DATE - 10, CURRENT_DATE + 20, 'Standard Consultation x1\nHbA1c x1', 90.00,  90.00,  'paid',    'T1DM review', 1),
-- Partially paid
(6,  4, CURRENT_DATE - 21, CURRENT_DATE + 9,  'Long Consultation x1\nSpirometry x1\nChest X-Ray referral', 175.00, 100.00, 'partial', 'COPD review — payment plan', 1),
(12, 3, CURRENT_DATE - 1,  CURRENT_DATE + 29, 'Long Consultation x1\nECG x1\nPacemaker check x1\nPathology x1', 260.00, 130.00, 'partial', 'CHF monthly review', 1),
-- Unpaid
(4,  4, CURRENT_DATE - 5,  CURRENT_DATE + 25, 'Standard Consultation x1\nBlood Test x1', 95.00,  0.00,   'unpaid',  'Gout annual review', 1),
(5,  2, CURRENT_DATE - 2,  CURRENT_DATE + 28, 'Standard Consultation x1\nPathology referral x1', 85.00, 0.00, 'unpaid', 'Follow-up', 1),
(11, 4, CURRENT_DATE - 5,  CURRENT_DATE + 25, 'Long Consultation x1\nPathology (LFTs) x1', 130.00, 0.00, 'unpaid', 'Methotrexate monitoring', 1),
-- Overdue
(2,  3, CURRENT_DATE - 90, CURRENT_DATE - 30, 'Procedure — Stress ECG x1\nLong Consultation x1', 190.00, 0.00, 'unpaid', 'OVERDUE — second notice sent', 1),
(8,  2, CURRENT_DATE - 45, CURRENT_DATE - 15, 'Standard Consultation x1',                      75.00,  0.00, 'unpaid', 'OVERDUE', 1),
-- Historical paid ones for charts
(1,  2, CURRENT_DATE - 180, CURRENT_DATE - 150, 'Annual Review x1\nPathology x1\nImmunisation x1', 165.00, 165.00, 'paid', '', 1),
(1,  2, CURRENT_DATE - 270, CURRENT_DATE - 240, 'Standard Consultation x2', 160.00, 160.00, 'paid', '', 1),
(2,  3, CURRENT_DATE - 150, CURRENT_DATE - 120, 'Long Consultation x1\nECG x1', 145.00, 145.00, 'paid', '', 1),
(7,  3, CURRENT_DATE - 120, CURRENT_DATE - 90,  'Warfarin review x1\nINR x2\nPathology x1', 130.00, 130.00, 'paid', '', 1),
(6,  4, CURRENT_DATE - 120, CURRENT_DATE - 90,  'COPD review x1\nSpirometry x1', 155.00, 155.00, 'paid', '', 1);


-- ── RECEIPTS ──────────────────────────────────────────────────
INSERT INTO receipts (invoice_id, patient_id, amount, payment_type, receipt_date, notes, created_by)
SELECT id, patient_id, total_amount, 'Credit Card', invoice_date + 3, 'Full payment received', 1
FROM invoices WHERE status = 'paid';

INSERT INTO receipts (invoice_id, patient_id, amount, payment_type, receipt_date, notes, created_by)
SELECT id, patient_id, amount_paid, 'Cash', invoice_date + 14, 'Part payment — payment plan agreed', 1
FROM invoices WHERE status = 'partial';


-- ── VACCINATIONS ──────────────────────────────────────────────
INSERT INTO vaccinations (patient_id, doctor_id, vaccine_name, dose, date_given, batch_number, next_due_date, notes) VALUES
(1, 5, 'Influenza',          'Annual',   CURRENT_DATE - 180, 'INF2024A',  CURRENT_DATE + 185, 'Given in left deltoid. No adverse reaction.'),
(1, 5, 'COVID-19 (Pfizer)', '5th dose', CURRENT_DATE - 365, 'PF2024C1', CURRENT_DATE + 365, 'Booster — tolerated well'),
(2, 5, 'Influenza',          'Annual',   CURRENT_DATE - 180, 'INF2024A',  CURRENT_DATE + 185, 'High-dose flu vaccine given (cardiac patient)'),
(2, 5, 'Pneumococcal 23',   'Booster',  CURRENT_DATE - 730, 'PPN2022X',  NULL,               'Given at 65 years. No further dose needed.'),
(3, 5, 'Influenza',          'Annual',   CURRENT_DATE - 180, 'INF2024A',  CURRENT_DATE + 185, ''),
(3, 5, 'HPV (Gardasil 9)',  '1st dose', CURRENT_DATE - 365, 'GRD2023D',  CURRENT_DATE - 155, ''),
(3, 5, 'HPV (Gardasil 9)',  '2nd dose', CURRENT_DATE - 155, 'GRD2024A',  CURRENT_DATE + 55,  'Series ongoing'),
(6, 5, 'Influenza',          'Annual',   CURRENT_DATE - 120, 'INF2024B',  CURRENT_DATE + 245, 'High-risk COPD patient'),
(6, 5, 'Pneumococcal 23',   '1st dose', CURRENT_DATE - 365, 'PPN2023Y',  NULL,               'Indicated for COPD'),
(7, 5, 'Influenza',          'Annual',   CURRENT_DATE - 180, 'INF2024A',  CURRENT_DATE + 185, 'Elderly high-risk patient'),
(7, 5, 'Shingrix (Zoster)', '1st dose', CURRENT_DATE - 365, 'SHX2023A',  CURRENT_DATE - 180, ''),
(7, 5, 'Shingrix (Zoster)', '2nd dose', CURRENT_DATE - 180, 'SHX2024B',  NULL,               'Series complete'),
(8, 5, 'COVID-19 (Pfizer)', '4th dose', CURRENT_DATE - 200, 'PF2024A2',  CURRENT_DATE + 165, ''),
(8, 5, 'Influenza',          'Annual',   CURRENT_DATE - 180, 'INF2024A',  CURRENT_DATE + 185, ''),
(12,5, 'Influenza',          'Annual',   CURRENT_DATE - 90,  'INF2024C',  CURRENT_DATE + 275, 'CHF patient — high priority'),
(12,5, 'Pneumococcal 23',   '1st dose', CURRENT_DATE - 180, 'PPN2024X',  NULL,               'Indicated for CHF');


-- ── REFERRALS ─────────────────────────────────────────────────
INSERT INTO referrals (patient_id, referring_doctor, referred_to, specialty, reason, urgency, letter_content, date_created, status) VALUES
(1, 2, 'City Endocrinology Centre',          'Endocrinology', 'HbA1c above target despite optimised oral therapy. Consider insulin initiation.', 'routine',
 'Dear Dr,\n\nI am referring Ms Sarah Thompson, DOB 12/04/1982, for endocrinology review. Her HbA1c is 7.4% despite Metformin 1g BD and dietary changes. I would appreciate your assessment regarding further optimisation or insulin initiation.\n\nMedications: Metformin 1g BD, Amlodipine 5mg.\nAllergies: Penicillin.\n\nThank you.',
 CURRENT_DATE - 25, 'sent'),
(2, 3, 'St Vincent''s Cardiology',           'Cardiology',    'Annual cardiac review. History of CABG 2018. Stable angina. Request stress echo.', 'routine',
 'Dear Dr,\n\nPlease review Mr James Kowalski for annual cardiac assessment. He has a background of ischaemic heart disease and CABG 2018. Recent troponin normal. Request stress echocardiogram.\n\nMedications: Atorvastatin 40mg, Aspirin 100mg, Insulin glargine.',
 CURRENT_DATE - 40, 'completed'),
(3, 2, 'Allergy & Respiratory Clinic',       'Respiratory',   'Asthma partially controlled despite step-up therapy. Allergy assessment requested.', 'routine',
 'Dear Dr,\n\nI am referring Ms Maria Fernandez for allergy and respiratory assessment. Asthma has required step-up to ICS this month. Allergies to cats and dust. Please assess suitability for immunotherapy.',
 CURRENT_DATE - 10, 'draft'),
(6, 4, 'Metro Pulmonology Associates',       'Pulmonology',   'COPD moderate. FEV1 62%. Ongoing decline despite optimal medical management.', 'urgent',
 'Dear Dr,\n\nI am urgently referring Mr Ahmed Hassan for pulmonology review. FEV1 62% predicted — moderate COPD. Recent infective exacerbation. Please assess for pulmonary rehabilitation and optimisation of inhaler regime.',
 CURRENT_DATE - 18, 'sent'),
(7, 3, 'Melbourne Haematology',              'Haematology',   'Atrial fibrillation on Warfarin. Considering switch to DOAC — require haematology input.', 'routine',
 'Dear Dr,\n\nMrs Linda Morrison, 76F, is anticoagulated with Warfarin for AF. We are considering transition to a DOAC given monitoring burden. Please advise.',
 CURRENT_DATE - 5, 'draft'),
(9, 3, 'Royal Oncology Centre',              'Oncology',      'Routine breast cancer surveillance — 3 years post mastectomy.', 'routine',
 'Dear Dr,\n\nMs Patricia O''Brien is attending for her 3-year post-mastectomy review. No evidence of recurrence. Continuing Letrozole and Tamoxifen. Mammogram pending.',
 CURRENT_DATE - 2, 'sent'),
(12,3, 'Cardiology Heart Failure Clinic',    'Cardiology',    'CHF NYHA II — pacemaker patient. BNP 420. Annual heart failure clinic review.', 'urgent',
 'Dear Dr,\n\nMr George Papadopoulos has CHF NYHA II with a pacemaker implanted 2020. BNP mildly elevated at 420. eGFR 38. Please review in heart failure clinic.',
 CURRENT_DATE,      'sent');


-- ── RECALLS ───────────────────────────────────────────────────
INSERT INTO recalls (patient_id, doctor_id, result, notes, first_recall_date, first_action, second_recall_date, second_action, returned_date, status) VALUES
(1, 2, 'HbA1c above target — endocrinology referral required',
 'Awaiting endocrinology appointment confirmation',
 CURRENT_DATE + 7,  'phone', CURRENT_DATE + 21, 'sms', NULL, 'pending'),
(2, 3, 'Overdue stress ECG — rebook urgently',
 'Patient was called — left message. Try again.',
 CURRENT_DATE + 2,  'phone', CURRENT_DATE + 9,  'letter', NULL, 'pending'),
(6, 4, 'COPD review — spirometry and chest X-ray results',
 'CXR shows no consolidation. Review lung function results with patient.',
 CURRENT_DATE + 3,  'phone', NULL, NULL, NULL, 'pending'),
(7, 3, 'INR recheck due in 4 weeks',
 'Routine Warfarin monitoring recall',
 CURRENT_DATE + 28, 'sms',   NULL, NULL, NULL, 'pending'),
(9, 3, 'Mammogram booking — 6 months post oncology review',
 'Patient advised to book at Royal Women''s Imaging Centre.',
 CURRENT_DATE + 180,'sms',   CURRENT_DATE + 194,'phone', NULL, 'pending'),
(12,3, 'Monthly renal function and BNP recheck',
 'eGFR trending down — close monitoring required',
 CURRENT_DATE + 28, 'phone', NULL, NULL, NULL, 'pending'),
-- A returned one
(3, 2, 'Asthma action plan review — step-up therapy',
 'Patient returned. Asthma controlled on new regime.',
 CURRENT_DATE - 10, 'phone', NULL, NULL, CURRENT_DATE - 5, 'returned');


-- ── REMINDERS ─────────────────────────────────────────────────
INSERT INTO reminders (patient_id, doctor_id, due_date, reason, notes, contacted_date, contact_action, returned_date, status) VALUES
(1, 2, CURRENT_DATE + 14,   'Annual flu vaccination due',                    'Patient usually books in March',                  NULL, NULL, NULL, 'pending'),
(1, 2, CURRENT_DATE + 90,   'Dietitian review — 3 months post referral',     'Check if appointment kept',                       NULL, NULL, NULL, 'pending'),
(2, 3, CURRENT_DATE + 5,    'Overdue invoice — follow up payment',           'Second notice. INV-0013 overdue',                 NULL, NULL, NULL, 'pending'),
(5, 2, CURRENT_DATE - 5,    'Iron studies follow-up — ferritin result',      'Results due from lab',                            NULL, NULL, NULL, 'pending'),
(6, 4, CURRENT_DATE + 7,    'Smoking cessation referral',                    'Patient expressed willingness to quit this visit', NULL, NULL, NULL, 'pending'),
(7, 3, CURRENT_DATE - 2,    'Bone density DEXA scan due',                    'Last DEXA was 13 months ago — overdue',           NULL, NULL, NULL, 'pending'),
(8, 2, CURRENT_DATE + 21,   'University sports physical — results letter',   'Patient needs letter for university sports',      NULL, NULL, NULL, 'pending'),
(9, 3, CURRENT_DATE + 180,  'Mammogram result review',                       'Book appointment after mammogram',                NULL, NULL, NULL, 'pending'),
(12,3, CURRENT_DATE + 30,   'CHF weight diary review',                       'Patient to email weekly weights',                 NULL, NULL, NULL, 'pending'),
-- Completed reminders
(4, 4, CURRENT_DATE - 60,   'Uric acid result review',                       'Allopurinol dose adequate',                       CURRENT_DATE - 58, 'phone', CURRENT_DATE - 55, 'returned'),
(3, 2, CURRENT_DATE - 15,   'HPV vaccine 2nd dose due',                      'Series on track',                                 CURRENT_DATE - 14, 'sms',   CURRENT_DATE - 14, 'returned');


-- ── CONSULTATION NOTES ────────────────────────────────────────
INSERT INTO consultation_notes (patient_id, doctor_id, visit_date, subjective, objective, assessment, plan, notes) VALUES
(2, 3, CURRENT_DATE - 45,
 'Mr Kowalski presents with a 20-minute episode of chest tightness while walking uphill last week. Resolved with rest. No radiation to arm or jaw. No diaphoresis. No syncope. Reports good medication compliance.',
 'Vitals: BP 132/84, HR 72 regular, O2 sat 97%, Temp 36.6. CVS: normal heart sounds, no murmurs, no added sounds. Respiratory: clear. Abdomen: unremarkable. Peripheral pulses present. No ankle oedema. ECG: normal sinus rhythm, no ST changes. Troponin I < 0.01 µg/L.',
 'Stable angina — no acute ischaemia. Previous CABG 2018 with known 2-vessel disease. ECG and troponin normal. Likely exertion-related stable angina.',
 'Continue current cardiac medications. Nitrate spray prescribed PRN. Exercise stress test booked within 4 weeks. Avoid strenuous exercise pending review. Return immediately if chest pain at rest.',
 'Patient counselled on angina management. Written action plan provided.'),
(6, 4, CURRENT_DATE - 21,
 'Mr Hassan reports progressively worsening shortness of breath on exertion over the past 3 weeks. Now breathless on flat ground. Productive cough — yellow sputum for 10 days. Low-grade fever. No haemoptysis. No chest pain.',
 'Vitals: BP 148/92, HR 88, RR 22, Temp 37.8, O2 sat 94% on air. Chest: hyperinflated barrel chest, bilateral wheeze on expiration, coarse crackles at right base. No stridor. No cyanosis. Abdomen normal.',
 'COPD moderate (FEV1 62% predicted) with probable infective exacerbation. H.influenzae on sputum culture. Chest X-ray: no consolidation or pneumothorax.',
 'Amoxicillin 500mg TDS x 7 days. Prednisolone 40mg daily x 5 days. Increase Salbutamol frequency. Refer to pulmonology for ongoing management. Review in 1 week.',
 'Smoking cessation advice reiterated. Flu and pneumococcal vaccine up to date.'),
(12,3, CURRENT_DATE - 1,
 'Mr Papadopoulos attends for monthly CHF review. Weight 90kg this morning (89kg last month). Mild ankle oedema. Able to sleep flat. No paroxysmal nocturnal dyspnoea. No chest pain.',
 'Vitals: BP 150/94, HR 88 irregular, O2 sat 95%. JVP slightly elevated. Heart sounds: normal S1 S2, no murmurs. Chest: mild bibasal crackles. Abdomen: liver edge palpable 1cm. Bilateral pitting ankle oedema 1+. Pacemaker pocket: clean.',
 'CHF NYHA II — stable but slight fluid retention. Pacemaker functioning normally on interrogation. eGFR 38 — stable CKD3. BNP 420 — mildly elevated.',
 'Increase Furosemide if weight increases >2kg above target. Continue daily weighing. Fluid restrict 1.5L/day. Salt restriction reinforced. Renal function repeat 4 weeks. Cardiology clinic review next month.',
 'Patient and wife educated on warning signs of decompensation.'),
(1, 2, CURRENT_DATE - 30,
 'Ms Thompson attends for routine 3-monthly diabetes and hypertension review. Feels well. No hypoglycaemic episodes. Dietary compliance reasonable — occasional high-carb meals on weekends.',
 'Vitals: BP 138/88, HR 78, Weight 72kg. Fundoscopy deferred to ophthalmologist. Foot examination: intact sensation, no ulcers. HbA1c 7.4% (up from 7.1% last quarter).',
 'Type 2 diabetes — suboptimal control. Hypertension — borderline at target.',
 'Increase Metformin to 1g BD. Reinforce dietary counselling. Recheck HbA1c in 3 months. BP target < 130/80 — consider adding low-dose ACE inhibitor at next visit if not improved.',
 'Patient agreeable to medication increase. Dietitian referral discussed.');


-- ── PATIENT DOCUMENTS ─────────────────────────────────────────
INSERT INTO patient_documents (patient_id, uploaded_by, doc_type, title, filename, notes) VALUES
(1, 2, 'Lab Result',        'HbA1c Results - March 2024',           'sarah_hba1c_mar2024.pdf', 'HbA1c 7.4% - above target'),
(1, 2, 'Referral Letter',   'Endocrinology Referral Letter',        'sarah_endo_referral.pdf',  'Sent to City Endo Centre'),
(2, 3, 'Specialist Report', 'Cardiology Report - CABG 2018',        'james_cardio_report.pdf',  'Post-CABG discharge summary'),
(2, 3, 'Lab Result',        'Lipid Panel and Troponin Results',     'james_lipids_trop.pdf',    'Normal troponin, LDL mildly elevated'),
(3, 2, 'Consent Form',      'Signed Vaccination Consent - HPV',     'maria_hpv_consent.pdf',    ''),
(6, 4, 'Imaging',           'Chest X-Ray Report - Nov 2024',        'ahmed_cxr_nov24.pdf',      'Hyperinflation, no consolidation'),
(7, 3, 'Lab Result',        'INR Result and Warfarin Chart',        'linda_inr_chart.pdf',      'INR 2.4 - therapeutic'),
(7, 3, 'Specialist Report', 'Haematology Consult - AF Management',  'linda_haem_consult.pdf',   'Re: DOAC transition'),
(9, 3, 'Specialist Report', 'Oncology Discharge Summary 2021',      'patricia_onco_dc.pdf',     'Post-mastectomy discharge'),
(9, 3, 'Lab Result',        'CA 15-3 Tumour Marker Results',        'patricia_ca153.pdf',       'Normal - no recurrence markers'),
(12,3, 'Specialist Report', 'Pacemaker Interrogation Report 2024',  'george_pacemaker_2024.pdf','Normal function'),
(12,3, 'Lab Result',        'Renal Function and BNP Results',       'george_renal_bnp.pdf',     'eGFR 38, BNP 420');


-- ── ADDRESS BOOK ──────────────────────────────────────────────
INSERT INTO address_book (name, specialty, clinic, address, phone, fax, email, notes) VALUES
('Dr. Alexander Chen',       'Endocrinology',    'City Endocrinology Centre',        '100 Collins St, Melbourne VIC 3000', '03 9001 1001', '03 9001 1002', 'a.chen@cityendo.com.au',     'Referrals accepted Mon-Fri'),
('Dr. Rebecca Hall',         'Cardiology',       'St Vincent''s Heart Centre',       '41 Victoria Parade, Fitzroy VIC 3065','03 9231 2211', '03 9231 2212', 'rhall@stvincents.com.au',    'Urgent same-day slots available'),
('Dr. Michael Torres',       'Pulmonology',      'Metro Pulmonology Associates',     '320 Swanston St, Melbourne VIC 3000','03 9005 3300', '03 9005 3301', 'm.torres@metropulm.com.au',  'COPD specialist. Spirometry on-site'),
('Dr. Fiona Campbell',       'Oncology',         'Royal Oncology Centre',            '300 Grattan St, Carlton VIC 3053',   '03 9347 0000', '03 9347 0001', 'f.campbell@royalonco.com.au','Breast cancer specialist'),
('Dr. Nathan Park',          'Haematology',      'Melbourne Haematology',            '50 Lonsdale St, Melbourne VIC 3000', '03 9650 5500', '03 9650 5501', 'n.park@melbhaem.com.au',     'Warfarin/anticoagulation specialist'),
('Dr. Sarah O''Malley',      'Rheumatology',     'Arthritis & Rheumatology Clinic',  '210 High St, Kew VIC 3101',          '03 9855 7700', '03 9855 7701', 'somalley@arhclinic.com.au',  'RA and connective tissue disease'),
('City Medical Imaging',     'Radiology',        'City Medical Imaging',             '88 Elizabeth St, Melbourne VIC 3000','03 9600 9900', '03 9600 9901', 'bookings@citymedimage.com.au','Bulk bill X-ray, CT, MRI. Open 7 days'),
('PathWest Laboratories',    'Pathology',        'PathWest Laboratories',            '2 Hospital Ave, Nedlands WA 6009',   '08 9346 3000', '08 9346 3001', 'referrals@pathwest.com.au',  'Send-away bloods Monday & Thursday'),
('Green Valley Pharmacy',    'Pharmacy',         'Green Valley Pharmacy',            '12 Main St, Melbourne VIC 3000',     '03 9001 2200', NULL,           'gv.pharmacy@gmail.com',      'Compounding available. Fax prescriptions'),
('St John''s Hospital',      'Hospital',         'St John''s General Hospital',      '1 Hospital Dr, Melbourne VIC 3000',  '03 9999 0000', '03 9999 0001', 'admissions@stjohns.com.au',  'Emergency dept 24/7. Pre-admission clinic Tue/Thu');


-- ── MESSAGES / INBOX ─────────────────────────────────────────
INSERT INTO messages (sender_id, receiver_id, subject, body, is_read, created_at) VALUES
(1, 2, 'Abnormal Lab — James Kowalski',
 'BNP result back for James Kowalski: 420 pg/mL (ref < 100). Elevated but stable from last month. Please review at his next cardiac appointment. I have already noted this in the recall system.',
 FALSE, NOW() - INTERVAL '2 hours'),
(1, 3, 'Overdue Invoice — Patient #2',
 'INV-0013 for James Kowalski is now 30 days overdue (€190.00). Second notice has been sent by post. Please advise if we should escalate to collections or if there are any patient circumstances we should be aware of.',
 FALSE, NOW() - INTERVAL '5 hours'),
(3, 1, 'URGENT: Ahmed Hassan COPD Exacerbation',
 'Ahmed Hassan attended today with a significant COPD exacerbation. Sputum culture positive for H.influenzae. Started on Amoxicillin and Prednisolone. Referred urgently to Metro Pulmonology — please ensure referral letter is completed and faxed today. I have documented everything in his notes.',
 TRUE,  NOW() - INTERVAL '1 day'),
(1, 3, 'New Referral — Maria Fernandez',
 'Received referral letter from Dr O''Brien for Maria Fernandez, 31F, asthma. She is booked for a new patient consultation on Thursday at 11am. Please note ASPIRIN ALLERGY and NSAID sensitivity. Referral letter scanned to her documents.',
 FALSE, NOW() - INTERVAL '3 hours'),
(4, 1, 'Staff Meeting — This Friday 3pm',
 'Monthly staff meeting is this Friday at 3:00pm in the conference room.\n\nAgenda:\n1. QIP audit review\n2. Appointment system upgrade\n3. Flu vaccine clinic planning (April)\n4. Billing system update\n\nPlease bring your patient list statistics for the quarter.',
 TRUE,  NOW() - INTERVAL '2 days'),
(1, 3, 'Urgent: Emma Wilson Prescription',
 'Emma Wilson called requesting urgent Sertraline 50mg renewal — she runs out tomorrow. She has an appointment booked Friday at 2:30pm. If possible please have the script ready before she arrives or consider e-prescribing today.',
 FALSE, NOW() - INTERVAL '30 minutes'),
(3, 4, 'Patient Transfer — Yuki Tanaka',
 'Yuki Tanaka (RA patient) will be transferring her care to your list from next month as I am reducing my patient load. Her full notes are in the system. She is on Methotrexate 15mg weekly — LFTs to be monitored quarterly. DAS28 last 3.1. Please review and confirm you are able to accept.',
 FALSE, NOW() - INTERVAL '4 hours');


-- ── WAITING ROOM ──────────────────────────────────────────────
INSERT INTO waiting_room (patient_id, doctor_id, reason, status, checked_in_at) VALUES
(3,  2, 'New patient registration — Asthma review',  'waiting',    NOW() - INTERVAL '8 minutes'),
(4,  4, 'Annual review — Gout and hypertension',     'waiting',    NOW() - INTERVAL '22 minutes'),
(6,  4, 'Spirometry — COPD management',              'with_doctor',NOW() - INTERVAL '35 minutes');


-- ── ACTIVITY LOG ──────────────────────────────────────────────
INSERT INTO activity_log (staff_id, action, detail, created_at) VALUES
(1, 'Login',               'Administrator logged in',                                                NOW() - INTERVAL '1 hour'),
(2, 'Login',               'Dr. Elena Marchetti logged in',                                          NOW() - INTERVAL '55 minutes'),
(2, 'New visit note',      'Patient: Sarah Thompson — 2024-01-15',                                   NOW() - INTERVAL '50 minutes'),
(2, 'AI symptom analysis', 'Patient: Maria Fernandez',                                               NOW() - INTERVAL '45 minutes'),
(3, 'Login',               'Dr. James Okonkwo logged in',                                            NOW() - INTERVAL '44 minutes'),
(3, 'New invoice',         'Patient #2 — James Kowalski — INV-0013',                                 NOW() - INTERVAL '40 minutes'),
(4, 'Login',               'Dr. Sophie Nguyen logged in',                                            NOW() - INTERVAL '38 minutes'),
(4, 'Updated patient',     'Robert Chang — vitals updated',                                          NOW() - INTERVAL '35 minutes'),
(2, 'New referral',        'Maria Fernandez → Allergy & Respiratory Clinic',                         NOW() - INTERVAL '30 minutes'),
(1, 'Added staff member',  'Nurse Maria Santos',                                                     NOW() - INTERVAL '25 minutes'),
(3, 'AI scan analysis',    'X-Ray — James Kowalski',                                                 NOW() - INTERVAL '20 minutes'),
(2, 'Vaccination recorded','Influenza — Maria Fernandez',                                            NOW() - INTERVAL '15 minutes'),
(4, 'Lab test ordered',    'HbA1c — Ahmed Hassan',                                                   NOW() - INTERVAL '12 minutes'),
(1, 'Invoice paid',        'INV-0001 — Sarah Thompson — €80.00',                                     NOW() - INTERVAL '10 minutes'),
(2, 'New patient',         'Daniel Nguyen',                                                          NOW() - INTERVAL '8 minutes'),
(3, 'Updated staff member','Nurse Tom Bradley',                                                       NOW() - INTERVAL '5 minutes'),
(4, 'Patient checked in',  'Robert Chang — waiting room',                                            NOW() - INTERVAL '3 minutes'),
(2, 'Login',               'Dr. Elena Marchetti — second session',                                   NOW() - INTERVAL '1 minute');


-- ── SYMPTOM ANALYSES (AI) ─────────────────────────────────────
INSERT INTO symptom_analyses (patient_id, staff_id, symptoms, ai_result, created_at) VALUES
(3, 2,
 'Patient reports increased use of Salbutamol (4-5x/week). Mainly triggered by cold air and exercise. No nocturnal symptoms. Some chest tightness after exercise.',
 '## AI Clinical Analysis\n\n**Most Likely Diagnoses:**\n1. Mild persistent asthma, partially controlled (J45.1) — Probability: High\n2. Exercise-induced bronchospasm — Probability: Moderate\n\n**Differential Diagnoses:**\n- Vocal cord dysfunction\n- Cardiac dyspnoea (less likely given age)\n\n**Recommended Investigations:**\n- Spirometry with bronchodilator reversibility\n- FeNO (fractional exhaled nitric oxide) if available\n- Peak flow diary for 2 weeks\n\n**Red Flags:** None present. No nocturnal symptoms, no ER presentations.\n\n**Suggested Next Steps:**\n- Step up to low-dose ICS (Budesonide 200mcg BD)\n- Review inhaler technique\n- Provide written Asthma Action Plan\n- Review in 4-6 weeks\n\n*This is a decision-support tool. The treating physician must make all clinical decisions.*',
 NOW() - INTERVAL '45 minutes'),
(6, 4,
 'Worsening shortness of breath on exertion for 3 weeks. Yellow productive cough 10 days. Low grade fever. O2 sat 94%. Known COPD.',
 '## AI Clinical Analysis\n\n**Most Likely Diagnoses:**\n1. Acute exacerbation of COPD (J44.1) — Probability: Very High\n2. Community-acquired pneumonia — Probability: Moderate\n3. Cardiac decompensation — Probability: Low (exclude clinically)\n\n**Differential Diagnoses:**\n- Pulmonary embolism (consider if no response to antibiotics)\n- Pneumothorax\n\n**Recommended Investigations:**\n- Chest X-ray (urgent)\n- Sputum culture and sensitivity\n- FBC, CRP, U&E\n- ABG if O2 sat < 92%\n- BNP to exclude cardiac cause\n\n**Red Flags:**\n⚠ O2 saturation 94% — borderline. Monitor closely.\n⚠ If O2 drops below 88% — hospital admission required.\n\n**Suggested Next Steps:**\n- Antibiotics: Amoxicillin 500mg TDS x 7 days (or Doxycycline if penicillin-allergic)\n- Prednisolone 30-40mg daily x 5 days\n- Increase bronchodilator frequency\n- Consider hospital admission if no improvement in 48 hours\n\n*This is a decision-support tool. All clinical decisions must be made by the treating physician.*',
 NOW() - INTERVAL '20 minutes');


SELECT '✅ Seed data inserted successfully!' AS status;
SELECT 'Patients: ' || COUNT(*) AS summary FROM patients
UNION ALL SELECT 'Appointments: ' || COUNT(*) FROM appointments
UNION ALL SELECT 'Invoices: ' || COUNT(*) FROM invoices
UNION ALL SELECT 'Lab Tests: ' || COUNT(*) FROM lab_tests
UNION ALL SELECT 'Prescriptions: ' || COUNT(*) FROM prescriptions
UNION ALL SELECT 'Vaccinations: ' || COUNT(*) FROM vaccinations
UNION ALL SELECT 'Referrals: ' || COUNT(*) FROM referrals
UNION ALL SELECT 'Recalls: ' || COUNT(*) FROM recalls
UNION ALL SELECT 'Messages: ' || COUNT(*) FROM messages
UNION ALL SELECT 'Staff: ' || COUNT(*) FROM staff;

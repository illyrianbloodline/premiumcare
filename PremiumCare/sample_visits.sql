-- ============================================================
-- Sample Visit Notes — 10 visits per patient (first 5 patients)
-- Run: psql -U medplatform_user -d medplatform -f sample_visits.sql
-- ============================================================

-- First show your patients
SELECT id, first_name, last_name FROM patients ORDER BY id LIMIT 10;

-- Clear existing visit notes for clean sample
DELETE FROM visit_notes WHERE created_by = 1 AND visit_date >= CURRENT_DATE - 365;

-- ── PATIENT 1 — 10 visits ─────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
SELECT p.id, 1, v.vdate::DATE, v.vtype, 'completed', v.complaint, v.diagnosis, v.treatment, v.notes, v.followup, 1
FROM (SELECT id FROM patients ORDER BY id LIMIT 1) p
CROSS JOIN (VALUES
  ((CURRENT_DATE - 280)::TEXT, 'Konsultë e Re',       'E re — Hipertension',    'Amlodipine 5mg filloi',       'Presion 158/96. Pacienti ankohet për dhimbje koke. EKG normal. Filloi trajtim me Amlodipine 5mg. Këshillim për dietë dhe ushtrime.', '2 javë'),
  ((CURRENT_DATE - 245)::TEXT, 'Ndjekje',             'Hipertension i kontrolluar', 'Doza e njëjtë, monitorim', 'BP 142/88. Përmirësim i mirë. Pacienti toleron ilaçin. Rekomandohet reduktim i kripës.', '1 muaj'),
  ((CURRENT_DATE - 210)::TEXT, 'Kontroll Vjetor',     'Hipertension + Diabet tip 2', 'Metformin 500mg shtoi',   'BP 138/84. HbA1c 7.8% — i lartë. Glukoza agjërim 8.2 mmol/L. Shtoi Metformin 500mg dy herë në ditë. Referim te nutricionisti.', '6 javë'),
  ((CURRENT_DATE - 175)::TEXT, 'Ndjekje',             'Diabet — monitorim',      'Rregullim doze Metformin',    'HbA1c 7.2% — progres i mirë. Pesha -2kg. Pacienti zbaton dietën. Rrit Metformin në 1000mg.', '2 muaj'),
  ((CURRENT_DATE - 140)::TEXT, 'Urgjencë',            'Dhimbje gjoksi akute',    'Nitroglicerinë sublingual',   'Dhimbje gjoksi 6/10, rrezaton në krah të majtë. EKG: ST normal. Troponina negative. Dërgua në ER për vëzhgim. Kthye me diagnozë muskuloskeletale.', 'Kardiolog'),
  ((CURRENT_DATE - 105)::TEXT, 'Ndjekje Kardiologjike','Post-ER ndjekje',         'Aspirinë 100mg shtoi',       'Pas vizitës ER — kardiologo konfirmoi GERD si shkak. Shtoi Pantoprazol 40mg. BP 136/82. Ndjek me kardiolog çdo 3 muaj.', '3 muaj'),
  ((CURRENT_DATE - 70)::TEXT,  'Kontroll Rutinë',     'Hipertension + Diabet',   'Trajtim i pandryshuar',       'BP 132/80 — excellent. HbA1c 6.9% — brenda target. Pesha stabile. Pacienti i motivuar. Vazhdojnë ilaçet aktuale.', '3 muaj'),
  ((CURRENT_DATE - 42)::TEXT,  'Ndjekje',             'Kontroll laboratori',     'Statinë shtoi',               'LDL 4.1 mmol/L — i lartë. Trigliceridet 2.8. Filloi Atorvastatin 20mg. Këshillim dietik për reduktim yndyrash.', '6 javë'),
  ((CURRENT_DATE - 14)::TEXT,  'Recetë',              'Rinovim ilaçesh',         'Receta të rinovuara',         'Vizitë rutinë. BP 130/78. Pacienti ndihet mirë. Rinovoi të gjitha recetat. Lab të planifikuara për muajin tjetër.', '1 muaj'),
  ((CURRENT_DATE - 3)::TEXT,   'Ndjekje',             'Efekte anësore statina',  'Doza e ulur',                 'Ankesa për dhimbje muskulore legs pas Atorvastatin. CK e rritur lehtë. Ul dozën në 10mg. Kontrol CK pas 4 javësh.', '4 javë')
) AS v(vdate, vtype, diagnosis, treatment, notes, followup);

-- ── PATIENT 2 — 10 visits ─────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
SELECT p.id, 1, v.vdate::DATE, v.vtype, 'completed', v.complaint, v.diagnosis, v.treatment, v.notes, v.followup, 1
FROM (SELECT id FROM patients ORDER BY id LIMIT 1 OFFSET 1) p
CROSS JOIN (VALUES
  ((CURRENT_DATE - 320)::TEXT, 'Konsultë e Re',    'Astmë bronkiale',         'Salbutamol inhaler + ICS',    'Dispne me ushtrime, gulçim natën. Peak flow 72%. Diagnoza astmë e moderuar. Filloi Budesonide/Formoterol + Salbutamol PRN. Plan veprimi i shkruar.', '4 javë'),
  ((CURRENT_DATE - 285)::TEXT, 'Ndjekje',          'Astmë — kontroll i mirë', 'Trajtim i njëjtë',            'Simptomat të reduktuara. Peak flow 85%. Pacienti mëson teknikën e inhalatorit. Nuk ka zgjime natën. Vazhdojnë ilaçet.', '2 muaj'),
  ((CURRENT_DATE - 240)::TEXT, 'Urgjencë',         'Krizë astme akute',       'Nebulizim + kortikosteroide', 'Ekspozim ndaj alergjenit (mace). SpO2 88%. Nebulizim me Salbutamol 3x. Prednisolon 40mg PO. Pas trajtimit SpO2 97%. Shtoi antihistaminik.', '3 ditë'),
  ((CURRENT_DATE - 200)::TEXT, 'Ndjekje Post-Krizë','Astmë post-krizë',       'Shtoi Montelukast',           'SpO2 98% në ajër dhomë. Peak flow 90%. Shtoi Montelukast 10mg natën. Diskutoi evitim alergjeni. Shtëpia pa kafshë shtëpiake.', '6 javë'),
  ((CURRENT_DATE - 160)::TEXT, 'Kontroll Vjetor',  'Astmë e kontrolluar',     'Stepdown trajtim',            'Vit i mirë — vetëm 1 krizë. Peak flow 92%. Spirometria FEV1 88%. Ulja e ICS provues. Vazhdon Montelukast dhe Salbutamol PRN.', '3 muaj'),
  ((CURRENT_DATE - 120)::TEXT, 'Ndjekje',          'Astmë + rhinitis alergjik','Shtoi spray nazal',          'Bllokim nazal, kollë. Rhinitis alergjik e konfirmuar. Shtoi Mometasone spray nazal. Referim alergolog për testim.', '6 javë'),
  ((CURRENT_DATE - 85)::TEXT,  'Pas Testimit',     'Alergjia ndaj acarieneve','Imunoterapi diskutuar',       'Testim pozitiv: acariene, polene. Diskutua imunoterapi. Pacienti dëshiron ta konsiderojë. Referim alergologut specialist.', '3 muaj'),
  ((CURRENT_DATE - 55)::TEXT,  'Ndjekje',          'Astmë — mirë',            'Trajtim i njëjtë',            'Pa simptoma astme. Peak flow 94%. Rhiniti kontrolluar me spray. Vendosi të mos bëjë imunoterapi tani.', '3 muaj'),
  ((CURRENT_DATE - 22)::TEXT,  'Recetë',           'Rinovim inhalatorit',     'Receta të rinovuara',         'Vizitë e shpejtë për rinovim. SpO2 99%. Inhalatori teknika korrekte. Rinovoi Budesonide/Formoterol dhe Salbutamol.', '3 muaj'),
  ((CURRENT_DATE - 5)::TEXT,   'Ndjekje',          'Kollë post-virale',        'Simptomatike',               'Kollë pas grip-i 3 javë. Auskultuara — pa wheeze. SpO2 98%. Diagnoza kollë post-virale. Mel + lemon, hidratim. Nuk nevojitet antibiotik.', '2 javë')
) AS v(vdate, vtype, diagnosis, treatment, notes, followup);

-- ── PATIENT 3 — 10 visits ─────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
SELECT p.id, 1, v.vdate::DATE, v.vtype, 'completed', v.complaint, v.diagnosis, v.treatment, v.notes, v.followup, 1
FROM (SELECT id FROM patients ORDER BY id LIMIT 1 OFFSET 2) p
CROSS JOIN (VALUES
  ((CURRENT_DATE - 300)::TEXT, 'Konsultë e Re',    'Depresion',               'Sertraline 50mg filloi',      'Humor i ulët 3 muaj, anhedoni, gjumë i çrregulluar, apetit i zvogëluar. PHQ-9: 16 (i moderuar-rëndë). Filloi Sertraline 50mg. Referim psikolog.', '4 javë'),
  ((CURRENT_DATE - 265)::TEXT, 'Ndjekje',          'Depresion — fillim trajtim','Doza e njëjtë',             'PHQ-9: 12. Pacienti raporton përmirësim të lehtë të gjumit. Efekte anësore: nausea e lehtë që po kalon. Vazhdon 50mg.', '6 javë'),
  ((CURRENT_DATE - 225)::TEXT, 'Ndjekje',          'Depresion — progres',      'Rrit në 100mg',              'PHQ-9: 8 — progres i mirë. Nausea ka kaluar. Gjumi më i mirë, energji më e lartë. Rriti dozën në 100mg për efekt maksimal.', '8 javë'),
  ((CURRENT_DATE - 180)::TEXT, 'Ndjekje',          'Depresion — i mirë',       'Trajtim i njëjtë',           'PHQ-9: 4 — remision. Pacienti kthehet në punë. Psikologu raporton progres të mirë. Vazhdon terapinë kognitive-biheviorale.', '3 muaj'),
  ((CURRENT_DATE - 145)::TEXT, 'Urgjencë',         'Panik atak akute',         'Benzodiazepinë PRN',         'Panik ataku i parë — dhimbje gjoksi, gulçim, marramendje. EKG normal. Troponina negative. Diagnoza: çrregullim paniku. Shtoi Alprazolam 0.5mg PRN.', 'Psikiatër'),
  ((CURRENT_DATE - 110)::TEXT, 'Pas Psikiatrit',   'Depresion + çrr. paniku', 'Trajtim i rishikuar',         'Psikiatri konfirmoi: depresion major + çrregullim paniku. Rrit Sertraline 150mg. Alprazolam vetëm krizë. CBT intensiv.', '6 javë'),
  ((CURRENT_DATE - 75)::TEXT,  'Ndjekje',          'Mirë klinike',             'Trajtim i njëjtë',            'PHQ-9: 3. Pa panik atake 2 muaj. Pacienti aktiv, sportiv. Flet mirë me psikologun. Vazhdon plani aktual.', '3 muaj'),
  ((CURRENT_DATE - 40)::TEXT,  'Ndjekje',          'Kontroll rutinë',          'Plan reduktim gradual',       'PHQ-9: 2. Pacienti kërkon të ndalojë ilaçin. Diskutua plani i reduktimit gradual pas 12 muajsh trajtim. Fillojmë pas 3 muajsh.', '3 muaj'),
  ((CURRENT_DATE - 12)::TEXT,  'Recetë',           'Rinovim Sertraline',       'Recetë e rinovuar',          'Vizitë e shpejtë. Gjendja e mirë. PHQ-9: 2. Rinovoi Sertraline 150mg. Psikologu raporton funksionim të mirë.', '3 muaj'),
  ((CURRENT_DATE - 2)::TEXT,   'Ndjekje',          'Çrregullim gjumi',         'Melatonin shtoi',            'Pacienti ankohet për vështirësi të fjetur vonë. Higjiena e gjumit diskutuar. Shtoi Melatonin 2mg 30 min para gjumit.', '4 javë')
) AS v(vdate, vtype, diagnosis, treatment, notes, followup);

-- ── PATIENT 4 — 10 visits ─────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
SELECT p.id, 1, v.vdate::DATE, v.vtype, 'completed', v.complaint, v.diagnosis, v.treatment, v.notes, v.followup, 1
FROM (SELECT id FROM patients ORDER BY id LIMIT 1 OFFSET 3) p
CROSS JOIN (VALUES
  ((CURRENT_DATE - 350)::TEXT, 'Konsultë e Re',    'Diabet tip 2',             'Metformin 500mg',            'Glukoza agjërim 9.4 mmol/L. HbA1c 8.6%. BMI 31. Diagnoza diabet tip 2. Filloi Metformin 500mg. Referim diabetolog + nutricioniste.', '6 javë'),
  ((CURRENT_DATE - 300)::TEXT, 'Ndjekje',          'Diabet — fillim trajtim',  'Rrit Metformin 1000mg',      'HbA1c 8.1% — duke u përmirësuar. Pacienti ndjek dietën. Rrit Metformin në 1000mg dy herë. Pesha -1.5kg. Këshillim aktiviteti fizik.', '2 muaj'),
  ((CURRENT_DATE - 240)::TEXT, 'Kontroll 3-mujor', 'Diabet — progres',         'Shtoi Empagliflozin',        'HbA1c 7.4% — progres i mirë. BP 144/88 — i lartë. Shtoi Empagliflozin 10mg (benefit kardiorenal). Monitorim funksion renal.', '3 muaj'),
  ((CURRENT_DATE - 180)::TEXT, 'Kontroll 3-mujor', 'Diabet + Hipertension',    'Shtoi Perindopril',          'HbA1c 7.0% — excellent. BP 138/86. Shtoi Perindopril 5mg — renoprotektiv për diabetik. Kreatin normale. Referim retinolog.', '3 muaj'),
  ((CURRENT_DATE - 150)::TEXT, 'Pas Retinologut',  'Retinopati diabetike hershme','Kontroll i rreptë glikemik','Retinolog gjeti retinopati jo-proliferative hershme. Theksoi rëndësinë e kontrollit glikemik dhe BP. Target HbA1c < 6.5%.', '3 muaj'),
  ((CURRENT_DATE - 110)::TEXT, 'Kontroll 3-mujor', 'Diabet — nën target',      'Shtoi Semaglutide',          'HbA1c 6.9% — afër target. Pesha -3kg. Shtoi Semaglutide 0.25mg javore. Edukimi për injeksione. Nausea e mundshme javët e para.', '6 javë'),
  ((CURRENT_DATE - 75)::TEXT,  'Ndjekje',          'Tolerancë Semaglutide',    'Rrit dozën',                 'Nausea e lehtë javët 1-2, kaloi. Pesha -2kg shtesë. HbA1c pritet 6.5%. Rrit Semaglutide 0.5mg. BP 128/80 — excellent.', '3 muaj'),
  ((CURRENT_DATE - 40)::TEXT,  'Kontroll 3-mujor', 'Diabet — target arritur',  'Trajtim i njëjtë',           'HbA1c 6.4% — TARGET ARRITUR! Pesha -7kg total. BP 122/76. Kreatina normale. Retinolog: pa përparim retinopatie. Pacienti shumë i motivuar.', '3 muaj'),
  ((CURRENT_DATE - 10)::TEXT,  'Ndjekje',          'Hipoglicemi episodike',    'Rregullim i dozës',          'Pacienti raporton 2 episode hipoglicemie (3.2 mmol/L) natën. Ul Metformin në 500mg mbrëmje. Edukimi për hipoglicemi dhe menaxhim.', '4 javë'),
  ((CURRENT_DATE - 1)::TEXT,   'Recetë',           'Rinovim ilaçesh',          'Receta të rinovuara',        'Vizitë rutinë. Glukoza 5.8 mmol/L. Pa hipoglicemi pas rregullimit dozës. Rinovoi të gjitha recetat. Lab pas 3 muajsh.', '3 muaj')
) AS v(vdate, vtype, diagnosis, treatment, notes, followup);

-- ── PATIENT 5 — 10 visits ─────────────────────────────────
INSERT INTO visit_notes (patient_id, doctor_id, visit_date, visit_type, status, chief_complaint, diagnosis, treatment, clinical_notes, follow_up, created_by)
SELECT p.id, 1, v.vdate::DATE, v.vtype, 'completed', v.complaint, v.diagnosis, v.treatment, v.notes, v.followup, 1
FROM (SELECT id FROM patients ORDER BY id LIMIT 1 OFFSET 4) p
CROSS JOIN (VALUES
  ((CURRENT_DATE - 310)::TEXT, 'Konsultë e Re',    'Artrit reumatoid',         'Referim reumatolog',         'Dhimbje dhe ënjtje kyçesh duar dhe kyçe këmbësh 4 muaj. Ngurtësi matinale > 1 orë. Anti-CCP pozitive. RF pozitiv. ESR 68. Referim urgjent reumatolog.', 'Reumatolog urgjent'),
  ((CURRENT_DATE - 275)::TEXT, 'Pas Reumatologut', 'AR — fillim trajtim',      'Methotrexate + Folat',       'Reumatolog konfirmoi AR seropozitive. Filloi Methotrexate 15mg javore + Folic acid 5mg. Naproxen 500mg PRN. Edukimi për ilaçet.', '6 javë'),
  ((CURRENT_DATE - 235)::TEXT, 'Ndjekje',          'AR — monitorim MTX',       'Trajtim i njëjtë',           'LFT normale. CBC normale. Pacienti toleron MTX. Ulje e lehtë dhimbjeve 30%. Nausea e lehtë ditën e MTX — mori Folat.', '2 muaj'),
  ((CURRENT_DATE - 195)::TEXT, 'Ndjekje',          'AR — progres i ngadalshëm','Rrit MTX 20mg',              'Aktivitet i moderuar sëmundjeje — DAS28: 4.2. LFT normale. Rrit MTX 20mg. Konsiderohet adicionimi Hydroxychloroquine.', '2 muaj'),
  ((CURRENT_DATE - 155)::TEXT, 'Ndjekje',          'AR + Hydroxychloroquine',  'Shtoi HCQ 200mg',            'DAS28: 3.8 — përmirësim i lehtë. Shtoi Hydroxychloroquine 200mg dy herë. Testi i syve bazal — rekomandohet vjetor. LFT OK.', '3 muaj'),
  ((CURRENT_DATE - 115)::TEXT, 'Ndjekje',          'AR — remision e pjesshëm', 'Trajtim i njëjtë',           'DAS28: 2.6 — remision i ulët! Pacienti shumë i lumtur. Aktivitet fizik i rritur. LFT, CBC, kreatina — të gjitha normale. Vazhdon trajtimi.', '3 muaj'),
  ((CURRENT_DATE - 80)::TEXT,  'Urgjencë',         'Infeksion respirator akut','Antibiotik + pushim MTX',    'Pneumoni komunitare. Temp 38.9°C. RR 22. SpO2 94%. Pushoi MTX gjatë infeksionit. Amoxicillin 1g 3x. Hospitalizim nuk u nevojit.', '1 javë'),
  ((CURRENT_DATE - 65)::TEXT,  'Post-Pneumoni',    'Rikuperim — rinis MTX',    'MTX rifilloi',               'Rikuperim i plotë nga pneumonia. SpO2 99%. Rifilloi Methotrexate 20mg. LFT normale. DAS28: 3.1 — pak aktive pas infeksionit.', '6 javë'),
  ((CURRENT_DATE - 30)::TEXT,  'Ndjekje',          'AR — kontroll rutinë',     'Trajtim i njëjtë',           'DAS28: 2.4 — remision. Pacienti aktiv, punon. LFT, CBC OK. Sytë — ekzaminim normal nga okulist. Vazhdon plani.', '3 muaj'),
  ((CURRENT_DATE - 4)::TEXT,   'Ndjekje',          'Dhimbje kyçesh shtuar',    'Kortikosteroid i shkurtër',  'Rritje e përkohshme aktivitetit — ndryshim stinësh. DAS28: 3.4. Prednisolon 10mg 5 ditë si urë. Rishikim trajtimit me reumatolog.', '4 javë')
) AS v(vdate, vtype, diagnosis, treatment, notes, followup);

-- ── SUMMARY ────────────────────────────────────────────────
SELECT 'Visit notes added: ' || COUNT(*) AS result FROM visit_notes;
SELECT p.first_name || ' ' || p.last_name AS patient, COUNT(v.id) AS visits
FROM patients p
JOIN visit_notes v ON v.patient_id = p.id
GROUP BY p.id, p.first_name, p.last_name
ORDER BY p.id;

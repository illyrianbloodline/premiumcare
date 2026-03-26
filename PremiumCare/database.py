"""
MedPlatform – Database Layer
"""
import psycopg
from psycopg.extras import RealDictCursor
from config import DB_CONFIG
from datetime import date, datetime, timedelta

def get_conn():
    return psycopg.connect(**DB_CONFIG)

def setup():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id          SERIAL PRIMARY KEY,
        name        VARCHAR(150) NOT NULL,
        email       VARCHAR(150) UNIQUE NOT NULL,
        password    VARCHAR(255) NOT NULL,
        role        VARCHAR(50) DEFAULT 'doctor',
        specialty   VARCHAR(150),
        phone       VARCHAR(50),
        active      BOOLEAN DEFAULT TRUE,
        permissions TEXT DEFAULT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")
    # Migrate existing installs — add column if missing
    cur.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='staff' AND column_name='permissions'
        ) THEN
            ALTER TABLE staff ADD COLUMN permissions TEXT DEFAULT NULL;
        END IF;
    END $$;
    """)

    cur.execute("""
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
        created_by        INTEGER REFERENCES staff(id),
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS symptom_analyses (
        id           SERIAL PRIMARY KEY,
        patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        staff_id     INTEGER REFERENCES staff(id),
        symptoms     TEXT NOT NULL,
        ai_result    TEXT NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scan_analyses (
        id           SERIAL PRIMARY KEY,
        patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        staff_id     INTEGER REFERENCES staff(id),
        scan_type    VARCHAR(50),
        filename     VARCHAR(255),
        ai_result    TEXT,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id               SERIAL PRIMARY KEY,
        patient_id       INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id        INTEGER REFERENCES staff(id),
        appointment_date DATE NOT NULL,
        start_time       TIME NOT NULL,
        duration_mins    INTEGER DEFAULT 30,
        appointment_type VARCHAR(100),
        status           VARCHAR(30) DEFAULT 'scheduled',
        notes            TEXT,
        created_by       INTEGER REFERENCES staff(id),
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visit_notes (
        id              SERIAL PRIMARY KEY,
        appointment_id  INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
        patient_id      INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id       INTEGER REFERENCES staff(id),
        visit_date      DATE NOT NULL,
        visit_type      VARCHAR(100),
        status          VARCHAR(30) DEFAULT 'completed',
        chief_complaint TEXT,
        diagnosis       TEXT,
        treatment       TEXT,
        clinical_notes  TEXT,
        follow_up       TEXT,
        created_by      INTEGER REFERENCES staff(id),
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id         SERIAL PRIMARY KEY,
        staff_id   INTEGER REFERENCES staff(id),
        action     TEXT,
        detail     TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    # ── All clinical/billing tables (safe: IF NOT EXISTS) ────────────────────
    cur.execute("""
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
    );""")

    cur.execute("""
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
    );""")

    cur.execute("""
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
    );""")

    cur.execute("""
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
    );""")

    cur.execute("""
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
    );""")

    cur.execute("""
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
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id           SERIAL PRIMARY KEY,
        patient_id   INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id    INTEGER REFERENCES staff(id),
        invoice_date DATE NOT NULL,
        due_date     DATE,
        total_amount NUMERIC(10,2) DEFAULT 0,
        amount_paid  NUMERIC(10,2) DEFAULT 0,
        status       VARCHAR(30) DEFAULT 'unpaid',
        notes        TEXT,
        created_by   INTEGER REFERENCES staff(id),
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id          SERIAL PRIMARY KEY,
        invoice_id  INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
        item_code   VARCHAR(50),
        description TEXT,
        quantity    INTEGER DEFAULT 1,
        unit_price  NUMERIC(10,2) DEFAULT 0,
        gst         NUMERIC(10,2) DEFAULT 0,
        total       NUMERIC(10,2) DEFAULT 0
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_documents (
        id          SERIAL PRIMARY KEY,
        patient_id  INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        uploaded_by INTEGER REFERENCES staff(id),
        doc_type    VARCHAR(100),
        title       VARCHAR(255) NOT NULL,
        filename    VARCHAR(255) NOT NULL,
        notes       TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS waiting_room (
        id             SERIAL PRIMARY KEY,
        patient_id     INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id      INTEGER REFERENCES staff(id),
        checked_in_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
        reason         VARCHAR(200),
        status         VARCHAR(30) DEFAULT 'waiting',
        notes          TEXT
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS remember_tokens (
        id           SERIAL PRIMARY KEY,
        staff_id     INTEGER REFERENCES staff(id) ON DELETE CASCADE,
        selector     VARCHAR(32) UNIQUE NOT NULL,
        token_hash   VARCHAR(64) NOT NULL,
        expires_at   TIMESTAMP NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    # ── Migrations: add columns to existing installs ──────────────────────────
    migrations = [
        ("patients",  "archived",       "BOOLEAN DEFAULT FALSE"),
        ("staff",     "mfa_secret",     "TEXT"),
        ("staff",     "recovery_codes", "TEXT"),
        ("appointments", "title",       "VARCHAR(200)"),
        ("appointments", "appt_date",   "DATE"),
        ("appointments", "end_time",    "TIME"),
    ]
    for tbl, col, typedef in migrations:
        cur.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name='{tbl}' AND column_name='{col}')
                THEN ALTER TABLE {tbl} ADD COLUMN {col} {typedef}; END IF;
            END $$;
        """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_visit_notes_patient ON visit_notes(patient_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_visit_notes_date ON visit_notes(visit_date DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_appts_patient ON appointments(patient_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_appts_date ON appointments(appointment_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_remember_selector ON remember_tokens(selector);")
    # Migrate existing form titles to Albanian
    form_title_updates = [
        ('General Consent to Treatment',       'Pëlqim i Përgjithshëm për Trajtim'),
        ('Privacy & Information Notice',        'Njoftim mbi Privatësinë & Informacionin'),
        ('Telehealth Consent',                  'Pëlqim për Telehealth'),
        ('Photography / Clinical Images',       'Fotografim / Imazhe Klinike'),
        ('New Patient Intake Form',             'Formulari i Pranimit të Pacientit të Ri'),
        ('Medication Consent & Acknowledgement','Pëlqim & Konfirmim për Medikamentin'),
    ]
    for eng, alb in form_title_updates:
        cur.execute('UPDATE patient_forms SET form_title=%s WHERE form_title=%s', (alb, eng))

    cur.execute("SELECT COUNT(*) FROM staff")
    if cur.fetchone()[0] == 0:
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        pw = bcrypt.generate_password_hash("admin123").decode("utf-8")
        cur.execute(
            "INSERT INTO staff (name, email, password, role) VALUES (%s,%s,%s,%s)",
            ("Administrator", "admin@practice.local", pw, "admin")
        )

    conn.commit()
    cur.close()
    conn.close()

# ── Staff ──────────────────────────────────────────────────────────────────────

def get_staff_by_email(email):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM staff WHERE email=%s AND active=TRUE", (email,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def get_staff_by_id(sid):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM staff WHERE id=%s", (sid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def get_all_staff():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM staff ORDER BY name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def save_staff(data, sid=None):
    conn = get_conn()
    cur = conn.cursor()
    if sid:
        cur.execute("""
            UPDATE staff SET name=%s, email=%s, role=%s, specialty=%s,
                             phone=%s, active=%s, permissions=%s
            WHERE id=%s
        """, (data['name'], data['email'], data['role'], data.get('specialty'),
              data.get('phone'), data.get('active', True),
              data.get('permissions'), sid))
    else:
        cur.execute("""
            INSERT INTO staff (name, email, password, role, specialty, phone, permissions)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['name'], data['email'], data['password'],
              data['role'], data.get('specialty'), data.get('phone'),
              data.get('permissions')))
        sid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return sid

def delete_staff(sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE staff SET active=FALSE WHERE id=%s", (sid,))
    conn.commit(); cur.close(); conn.close()

# ── Patients ───────────────────────────────────────────────────────────────────

PATIENT_FIELDS = [
    "first_name","last_name","dob","gender","blood_type","insurance_nr",
    "address","phone","email","emergency_contact","family_doctor",
    "medical_history","surgeries","family_history","drug_allergies",
    "env_allergies","medications","supplements","past_medications",
    "weight","height","blood_pressure","heart_rate","temperature",
    "oxygen_sat","blood_glucose","cholesterol","notes","icd_codes","referrals",
    "insurance_company","insurance_type","insurance_expiry","insurance_notes"
]

def get_recent_patients(limit=8):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id,first_name,last_name,dob,family_doctor,icd_codes FROM patients ORDER BY id DESC LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_all_patients(search=""):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if search:
        like = f"%{search}%"
        cur.execute("""SELECT id,first_name,last_name,dob,gender,phone,
                              blood_type,drug_allergies,medical_history,
                              insurance_nr,created_at,risk_score
                       FROM patients
                       WHERE archived IS NOT TRUE
                         AND (first_name ILIKE %s OR last_name ILIKE %s
                              OR phone ILIKE %s OR insurance_nr ILIKE %s)
                       ORDER BY last_name,first_name""", (like, like, like, like))
    else:
        cur.execute("""SELECT id,first_name,last_name,dob,gender,phone,
                              blood_type,drug_allergies,medical_history,
                              insurance_nr,created_at,risk_score
                       FROM patients
                       WHERE archived IS NOT TRUE
                       ORDER BY last_name,first_name""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_patient(pid):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM patients WHERE id=%s", (pid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_patient(data, pid=None, staff_id=None):
    conn = get_conn()
    cur = conn.cursor()
    values = [data.get(f) or None for f in PATIENT_FIELDS]
    if pid:
        sets = ", ".join(f"{f}=%s" for f in PATIENT_FIELDS)
        sets += ", updated_at=CURRENT_TIMESTAMP"
        cur.execute(f"UPDATE patients SET {sets} WHERE id=%s", values + [pid])
    else:
        cols = ", ".join(PATIENT_FIELDS) + ", created_by"
        placeholders = ", ".join(["%s"] * len(PATIENT_FIELDS)) + ", %s"
        cur.execute(
            f"INSERT INTO patients ({cols}) VALUES ({placeholders}) RETURNING id",
            values + [staff_id]
        )
        pid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return pid

def delete_patient(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM patients WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()

# ── AI records ────────────────────────────────────────────────────────────────

def save_symptom_analysis(patient_id, staff_id, symptoms, result):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO symptom_analyses (patient_id,staff_id,symptoms,ai_result) VALUES (%s,%s,%s,%s) RETURNING id",
        (patient_id, staff_id, symptoms, result)
    )
    rid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return rid

def get_symptom_analyses(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""SELECT sa.*, s.name as doctor_name FROM symptom_analyses sa
                   LEFT JOIN staff s ON sa.staff_id=s.id
                   WHERE sa.patient_id=%s ORDER BY sa.created_at DESC""", (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def save_scan_analysis(patient_id, staff_id, scan_type, filename, result):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scan_analyses (patient_id,staff_id,scan_type,filename,ai_result) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (patient_id, staff_id, scan_type, filename, result)
    )
    rid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return rid

def get_scan_analyses(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""SELECT sa.*, s.name as doctor_name FROM scan_analyses sa
                   LEFT JOIN staff s ON sa.staff_id=s.id
                   WHERE sa.patient_id=%s ORDER BY sa.created_at DESC""", (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_ai_usage_stats():
    """Return total AI query counts for dashboard."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM symptom_analyses")
    symptoms = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM scan_analyses")
    scans = cur.fetchone()['total']
    cur.close(); conn.close()
    return {'symptoms': symptoms, 'scans': scans, 'total': symptoms + scans}

# ── Visit Notes ───────────────────────────────────────────────────────────────

def get_visit_notes_for_patient(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT vn.*, s.name AS doctor_name, a.start_time, a.duration_mins
        FROM visit_notes vn
        LEFT JOIN staff s ON vn.doctor_id = s.id
        LEFT JOIN appointments a ON vn.appointment_id = a.id
        WHERE vn.patient_id = %s
        ORDER BY vn.visit_date DESC, vn.created_at DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_visit_note(note_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT vn.*, s.name AS doctor_name FROM visit_notes vn
        LEFT JOIN staff s ON vn.doctor_id = s.id WHERE vn.id = %s
    """, (note_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_visit_note(data, note_id=None, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    if note_id:
        cur.execute("""
            UPDATE visit_notes
            SET doctor_id=%s, visit_date=%s, visit_type=%s, status=%s,
                chief_complaint=%s, diagnosis=%s, treatment=%s,
                clinical_notes=%s, follow_up=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
        """, (data.get('doctor_id'), data['visit_date'], data.get('visit_type'),
              data.get('status','completed'), data.get('chief_complaint'),
              data.get('diagnosis'), data.get('treatment'),
              data.get('clinical_notes'), data.get('follow_up'), note_id))
    else:
        cur.execute("""
            INSERT INTO visit_notes
                (patient_id, appointment_id, doctor_id, visit_date, visit_type,
                 status, chief_complaint, diagnosis, treatment, clinical_notes,
                 follow_up, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['patient_id'], data.get('appointment_id'), data.get('doctor_id'),
              data['visit_date'], data.get('visit_type'), data.get('status','completed'),
              data.get('chief_complaint'), data.get('diagnosis'), data.get('treatment'),
              data.get('clinical_notes'), data.get('follow_up'), created_by))
        note_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return note_id

def delete_visit_note(note_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM visit_notes WHERE id=%s", (note_id,))
    conn.commit(); cur.close(); conn.close()


def get_campaign_patients(filters: dict) -> list:
    """
    Return patients matching campaign filter criteria.
    Filters: age_min, age_max, gender, last_visit_months,
             no_visit_months, diagnosis_contains, icd_contains,
             has_phone_only
    """
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=RealDictCursor)

    conditions = ["p.id IS NOT NULL"]
    params     = []

    # Age range
    if filters.get('age_min'):
        conditions.append("DATE_PART('year', AGE(p.dob)) >= %s")
        params.append(int(filters['age_min']))
    if filters.get('age_max'):
        conditions.append("DATE_PART('year', AGE(p.dob)) <= %s")
        params.append(int(filters['age_max']))

    # Gender
    if filters.get('gender') and filters['gender'] != 'all':
        conditions.append("LOWER(p.gender) = LOWER(%s)")
        params.append(filters['gender'])

    # Has phone number
    if filters.get('has_phone_only'):
        conditions.append("p.phone IS NOT NULL AND p.phone != ''")

    # Diagnosis contains
    if filters.get('diagnosis_contains'):
        conditions.append("LOWER(p.medical_history) LIKE LOWER(%s)")
        params.append(f"%{filters['diagnosis_contains']}%")

    # ICD code contains
    if filters.get('icd_contains'):
        conditions.append("LOWER(p.icd_codes) LIKE LOWER(%s)")
        params.append(f"%{filters['icd_contains']}%")

    # Last visit more than N months ago (or never visited)
    if filters.get('no_visit_months'):
        months = int(filters['no_visit_months'])
        conditions.append("""
            (
                NOT EXISTS (
                    SELECT 1 FROM visit_notes vn
                    WHERE vn.patient_id = p.id
                    AND vn.visit_date >= CURRENT_DATE - INTERVAL '%s months'
                )
                AND NOT EXISTS (
                    SELECT 1 FROM appointments a
                    WHERE a.patient_id = p.id
                    AND a.appointment_date >= CURRENT_DATE - INTERVAL '%s months'
                    AND a.status = 'completed'
                )
            )
        """)
        params.extend([months, months])

    where = " AND ".join(conditions)

    cur.execute(f"""
        SELECT
            p.id,
            p.first_name,
            p.last_name,
            p.phone,
            p.dob,
            p.gender,
            p.medical_history,
            p.icd_codes,
            DATE_PART('year', AGE(p.dob))::int AS age,
            (
                SELECT MAX(vn.visit_date)
                FROM visit_notes vn
                WHERE vn.patient_id = p.id
            ) AS last_visit,
            (
                SELECT MAX(a.appointment_date)
                FROM appointments a
                WHERE a.patient_id = p.id AND a.status = 'completed'
            ) AS last_appt
        FROM patients p
        WHERE {where}
        ORDER BY p.last_name, p.first_name
        LIMIT 500
    """, params)

    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── Appointments ──────────────────────────────────────────────────────────────

def get_appointments_for_patient(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*, s.name AS doctor_name
        FROM appointments a
        LEFT JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.start_time DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_appointments_for_day(date_str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name, s.name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        LEFT JOIN staff s ON a.doctor_id = s.id
        WHERE a.appointment_date = %s ORDER BY a.start_time
    """, (date_str,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_appointments_for_week(start_date, end_date):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name, s.name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        LEFT JOIN staff s ON a.doctor_id = s.id
        WHERE a.appointment_date BETWEEN %s AND %s
        ORDER BY a.appointment_date, a.start_time
    """, (start_date, end_date))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_appointment(appt_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name, s.name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        LEFT JOIN staff s ON a.doctor_id = s.id
        WHERE a.id = %s
    """, (appt_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_appointment(data, appt_id=None, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    if appt_id:
        cur.execute("""
            UPDATE appointments SET patient_id=%s, doctor_id=%s,
                appointment_date=%s, start_time=%s, duration_mins=%s,
                appointment_type=%s, status=%s, notes=%s WHERE id=%s
        """, (data['patient_id'], data['doctor_id'],
              data.get('appointment_date'),
              data['start_time'],
              data.get('duration_mins', 30),
              data.get('appointment_type'), data.get('status','scheduled'),
              data.get('notes'), appt_id))
    else:
        cur.execute("""
            INSERT INTO appointments
                (patient_id, doctor_id, appointment_date, start_time,
                 duration_mins, appointment_type, status, notes, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['patient_id'], data['doctor_id'],
              data.get('appointment_date'),
              data['start_time'],
              data.get('duration_mins', 30),
              data.get('appointment_type'), data.get('status','scheduled'),
              data.get('notes'), created_by))
        appt_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return appt_id

def delete_appointment(appt_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM appointments WHERE id=%s", (appt_id,))
    conn.commit(); cur.close(); conn.close()

def update_appointment_status(appt_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status=%s WHERE id=%s", (status, appt_id))
    conn.commit(); cur.close(); conn.close()


# ── Team Chat ──────────────────────────────────────────────────────────────────

def setup_team_chat():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_group BOOLEAN DEFAULT FALSE;
    ALTER TABLE messages ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES messages(id) ON DELETE CASCADE;
    CREATE INDEX IF NOT EXISTS idx_messages_group ON messages(is_group, created_at DESC);
    """)
    conn.commit(); cur.close(); conn.close()

def get_team_chat(limit=100):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT m.*, s.name AS sender_name, s.role AS sender_role
        FROM messages m
        LEFT JOIN staff s ON m.sender_id = s.id
        WHERE m.is_group = TRUE AND m.parent_id IS NULL
        ORDER BY m.created_at ASC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def send_team_message(sender_id, body, subject=''):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, subject, body, is_group, is_read)
        VALUES (%s, NULL, %s, %s, TRUE, TRUE) RETURNING id
    """, (sender_id, subject or 'Team Chat', body))
    mid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return mid

# ── Activity log ──────────────────────────────────────────────────────────────

def log_activity(staff_id, action, detail=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activity_log (staff_id,action,detail) VALUES (%s,%s,%s)",
        (staff_id, action, detail)
    )
    conn.commit(); cur.close(); conn.close()

def get_activity_log(limit=50):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""SELECT al.*, s.name as staff_name FROM activity_log al
                   LEFT JOIN staff s ON al.staff_id=s.id
                   ORDER BY al.created_at DESC LIMIT %s""", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── Billing / Invoices ────────────────────────────────────────────────────────

def get_invoices(patient_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if patient_id:
        cur.execute("""
            SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
                   s.name AS doctor_name
            FROM invoices i
            LEFT JOIN patients p ON i.patient_id=p.id
            LEFT JOIN staff s ON i.doctor_id=s.id
            WHERE i.patient_id=%s ORDER BY i.invoice_date DESC
        """, (patient_id,))
    else:
        cur.execute("""
            SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
                   s.name AS doctor_name
            FROM invoices i
            LEFT JOIN patients p ON i.patient_id=p.id
            LEFT JOIN staff s ON i.doctor_id=s.id
            ORDER BY i.invoice_date DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_invoice(inv_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.id=%s
    """, (inv_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_invoice(data, inv_id=None, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    if inv_id:
        cur.execute("""
            UPDATE invoices SET patient_id=%s, doctor_id=%s, invoice_date=%s,
                due_date=%s, items=%s, total_amount=%s, amount_paid=%s,
                status=%s, notes=%s WHERE id=%s
        """, (data['patient_id'], data.get('doctor_id'), data['invoice_date'],
              data.get('due_date'), data.get('items'), data.get('total_amount',0),
              data.get('amount_paid',0), data.get('status','unpaid'),
              data.get('notes'), inv_id))
    else:
        cur.execute("""
            INSERT INTO invoices (patient_id, doctor_id, invoice_date, due_date,
                items, total_amount, amount_paid, status, notes, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['patient_id'], data.get('doctor_id'), data['invoice_date'],
              data.get('due_date'), data.get('items'), data.get('total_amount',0),
              data.get('amount_paid',0), data.get('status','unpaid'),
              data.get('notes'), created_by))
        inv_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return inv_id

def delete_invoice(inv_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM invoices WHERE id=%s", (inv_id,))
    conn.commit(); cur.close(); conn.close()

def pay_invoice(inv_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT total_amount FROM invoices WHERE id=%s", (inv_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE invoices SET status='paid', amount_paid=%s WHERE id=%s",
                    (row['total_amount'], inv_id))
    conn.commit(); cur.close(); conn.close()

# ── Lab Tests ─────────────────────────────────────────────────────────────────

def get_lab_tests(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT l.*, s.name AS doctor_name FROM lab_tests l
        LEFT JOIN staff s ON l.doctor_id=s.id
        WHERE l.patient_id=%s ORDER BY l.ordered_date DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def save_lab_test(data, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lab_tests (patient_id, doctor_id, test_name, test_type,
            ordered_date, status, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (data['patient_id'], data.get('doctor_id'), data['test_name'],
          data.get('test_type'), data.get('ordered_date'), data.get('status','ordered'),
          data.get('notes')))
    lid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return lid

def update_lab_result(lab_id, result_date, result_value, reference_range, is_abnormal):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE lab_tests SET result_date=%s, result_value=%s,
            reference_range=%s, is_abnormal=%s, status='resulted'
        WHERE id=%s
    """, (result_date, result_value, reference_range, is_abnormal, lab_id))
    conn.commit(); cur.close(); conn.close()

def delete_lab_test(lab_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM lab_tests WHERE id=%s", (lab_id,))
    conn.commit(); cur.close(); conn.close()

# ── Patient Documents ─────────────────────────────────────────────────────────

def get_patient_documents(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT d.*, s.name AS uploaded_by_name FROM patient_documents d
        LEFT JOIN staff s ON d.uploaded_by=s.id
        WHERE d.patient_id=%s ORDER BY d.created_at DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def save_patient_document(data, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patient_documents (patient_id, uploaded_by, doc_type, title, filename, notes)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
    """, (data['patient_id'], created_by, data.get('doc_type'), data['title'],
          data['filename'], data.get('notes')))
    did = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return did

def delete_patient_document(doc_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM patient_documents WHERE id=%s", (doc_id,))
    conn.commit(); cur.close(); conn.close()

# ── Address Book ──────────────────────────────────────────────────────────────

def get_address_book():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM address_book ORDER BY name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_address_book_entry(entry_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM address_book WHERE id=%s", (entry_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_address_book_entry(data, entry_id=None):
    conn = get_conn()
    cur = conn.cursor()
    if entry_id:
        cur.execute("""
            UPDATE address_book SET name=%s, specialty=%s, phone=%s,
                fax=%s, email=%s, address=%s, notes=%s WHERE id=%s
        """, (data['name'], data.get('specialty'), data.get('phone'),
              data.get('fax'), data.get('email'), data.get('address'),
              data.get('notes'), entry_id))
    else:
        cur.execute("""
            INSERT INTO address_book (name, specialty, phone, fax, email, address, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['name'], data.get('specialty'), data.get('phone'),
              data.get('fax'), data.get('email'), data.get('address'), data.get('notes')))
        entry_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return entry_id

def delete_address_book_entry(entry_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM address_book WHERE id=%s", (entry_id,))
    conn.commit(); cur.close(); conn.close()

# ── Inbox / Messages ──────────────────────────────────────────────────────────

def get_messages(receiver_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT m.*, s.name AS sender_name FROM messages m
        LEFT JOIN staff s ON m.sender_id=s.id
        WHERE m.receiver_id=%s ORDER BY m.created_at DESC
    """, (receiver_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def send_message(sender_id, receiver_id, subject, body):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, subject, body)
        VALUES (%s,%s,%s,%s) RETURNING id
    """, (sender_id, receiver_id, subject, body))
    mid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return mid

def mark_message_read(msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE messages SET is_read=TRUE WHERE id=%s", (msg_id,))
    conn.commit(); cur.close(); conn.close()

def delete_message(msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE id=%s", (msg_id,))
    conn.commit(); cur.close(); conn.close()

def get_unread_count(staff_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=%s AND is_read=FALSE", (staff_id,))
    count = cur.fetchone()[0]
    cur.close(); conn.close()
    return count

# ── Consultation Notes ────────────────────────────────────────────────────────

def get_consultation_notes(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT cn.*, s.name AS doctor_name FROM consultation_notes cn
        LEFT JOIN staff s ON cn.doctor_id=s.id
        WHERE cn.patient_id=%s ORDER BY cn.visit_date DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_consultation_note(note_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT cn.*, s.name AS doctor_name FROM consultation_notes cn
        LEFT JOIN staff s ON cn.doctor_id=s.id
        WHERE cn.id=%s
    """, (note_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_consultation_note(data, note_id=None):
    conn = get_conn()
    cur = conn.cursor()
    if note_id:
        cur.execute("""
            UPDATE consultation_notes SET doctor_id=%s, visit_date=%s,
                subjective=%s, objective=%s, assessment=%s, plan=%s, notes=%s
            WHERE id=%s
        """, (data.get('doctor_id'), data['visit_date'], data.get('subjective'),
              data.get('objective'), data.get('assessment'), data.get('plan'),
              data.get('notes'), note_id))
    else:
        cur.execute("""
            INSERT INTO consultation_notes (patient_id, doctor_id, visit_date,
                subjective, objective, assessment, plan, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data['patient_id'], data.get('doctor_id'), data['visit_date'],
              data.get('subjective'), data.get('objective'), data.get('assessment'),
              data.get('plan'), data.get('notes')))
        note_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return note_id

def delete_consultation_note(note_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM consultation_notes WHERE id=%s", (note_id,))
    conn.commit(); cur.close(); conn.close()

# ── Appointment reminders (next 7 days) ──────────────────────────────────────

def get_upcoming_appointments(days=7):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*,
               p.first_name||' '||p.last_name AS patient_name,
               p.phone, p.email,
               s.name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id=p.id
        LEFT JOIN staff s ON a.doctor_id=s.id
        WHERE a.appointment_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
          AND a.status='scheduled'
        ORDER BY a.appointment_date, a.start_time
    """ % days)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── Prescriptions ─────────────────────────────────────────────────────────────

def get_prescriptions(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT pr.*, s.name AS doctor_name, s.specialty,
               p.first_name||' '||p.last_name AS patient_name,
               p.dob, p.address
        FROM prescriptions pr
        LEFT JOIN staff s ON pr.doctor_id=s.id
        LEFT JOIN patients p ON pr.patient_id=p.id
        WHERE pr.patient_id=%s ORDER BY pr.created_at DESC
    """, (patient_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def get_prescription(rx_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT pr.*, s.name AS doctor_name, s.specialty,
               p.first_name||' '||p.last_name AS patient_name,
               p.dob, p.address, p.phone
        FROM prescriptions pr
        LEFT JOIN staff s ON pr.doctor_id=s.id
        LEFT JOIN patients p ON pr.patient_id=p.id
        WHERE pr.id=%s
    """, (rx_id,))
    row = cur.fetchone(); cur.close(); conn.close(); return row

def save_prescription(data, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO prescriptions
            (patient_id, doctor_id, drug_name, dosage, frequency, route,
             start_date, end_date, repeats, instructions, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (data['patient_id'], data.get('doctor_id'), data['drug_name'],
          data.get('dosage'), data.get('frequency'), data.get('route','Oral'),
          data.get('start_date'), data.get('end_date') or None,
          int(data.get('repeats',0) or 0), data.get('instructions'),
          data.get('status','active')))
    rx_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close(); return rx_id

def delete_prescription(rx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM prescriptions WHERE id=%s", (rx_id,))
    conn.commit(); cur.close(); conn.close()

# ── Recalls ───────────────────────────────────────────────────────────────────

def get_recalls(patient_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if patient_id:
        cur.execute("""
            SELECT r.*, s.name AS doctor_name,
                   p.first_name||' '||p.last_name AS patient_name
            FROM recalls r
            LEFT JOIN staff s ON r.doctor_id=s.id
            LEFT JOIN patients p ON r.patient_id=p.id
            WHERE r.patient_id=%s ORDER BY r.created_at DESC
        """, (patient_id,))
    else:
        cur.execute("""
            SELECT r.*, s.name AS doctor_name,
                   p.first_name||' '||p.last_name AS patient_name
            FROM recalls r
            LEFT JOIN staff s ON r.doctor_id=s.id
            LEFT JOIN patients p ON r.patient_id=p.id
            ORDER BY r.created_at DESC
        """)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def save_recall(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO recalls (patient_id, doctor_id, result, notes, status)
        VALUES (%s,%s,%s,%s,'pending') RETURNING id
    """, (data['patient_id'], data.get('doctor_id'), data['result'], data.get('notes')))
    rid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close(); return rid

def update_recall(recall_id, data):
    conn = get_conn()
    cur = conn.cursor()
    # determine status from dates
    status = 'pending'
    if data.get('returned_date'): status = 'returned'
    elif data.get('third_recall_date'): status = 'third'
    elif data.get('second_recall_date'): status = 'second'
    elif data.get('first_recall_date'): status = 'first'
    cur.execute("""
        UPDATE recalls SET first_recall_date=%s, first_action=%s,
            second_recall_date=%s, second_action=%s,
            third_recall_date=%s, third_action=%s,
            returned_date=%s, status=%s WHERE id=%s
    """, (data.get('first_recall_date') or None, data.get('first_action') or None,
          data.get('second_recall_date') or None, data.get('second_action') or None,
          data.get('third_recall_date') or None, data.get('third_action') or None,
          data.get('returned_date') or None, status, recall_id))
    conn.commit(); cur.close(); conn.close()

def delete_recall(recall_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM recalls WHERE id=%s", (recall_id,))
    conn.commit(); cur.close(); conn.close()

# ── Referrals ─────────────────────────────────────────────────────────────────

def get_referrals(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT r.*, s.name AS doctor_name, s.specialty AS doctor_specialty,
               p.first_name||' '||p.last_name AS patient_name,
               p.dob, p.gender, p.phone, p.email
        FROM referrals r
        LEFT JOIN staff s ON r.referring_doctor=s.id
        LEFT JOIN patients p ON r.patient_id=p.id
        WHERE r.patient_id=%s ORDER BY r.created_at DESC
    """, (patient_id,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def get_referral(ref_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT r.*, s.name AS doctor_name, s.specialty AS doctor_specialty,
               p.first_name||' '||p.last_name AS patient_name,
               p.dob, p.gender, p.phone, p.email
        FROM referrals r
        LEFT JOIN staff s ON r.referring_doctor=s.id
        LEFT JOIN patients p ON r.patient_id=p.id
        WHERE r.id=%s
    """, (ref_id,))
    row = cur.fetchone(); cur.close(); conn.close(); return row

def save_referral(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO referrals
            (patient_id, referring_doctor, referred_to, specialty, reason,
             urgency, letter_content, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (data['patient_id'], data.get('doctor_id'), data['referred_to'],
          data.get('specialty'), data['reason'], data.get('urgency','routine'),
          data.get('letter_content'), data.get('status','draft')))
    rid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close(); return rid

def delete_referral(ref_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM referrals WHERE id=%s", (ref_id,))
    conn.commit(); cur.close(); conn.close()

# ── Reminders ─────────────────────────────────────────────────────────────────

def get_reminders(patient_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if patient_id:
        cur.execute("""
            SELECT r.*, s.name AS doctor_name,
                   p.first_name||' '||p.last_name AS patient_name
            FROM reminders r
            LEFT JOIN staff s ON r.doctor_id=s.id
            LEFT JOIN patients p ON r.patient_id=p.id
            WHERE r.patient_id=%s ORDER BY r.due_date
        """, (patient_id,))
    else:
        cur.execute("""
            SELECT r.*, s.name AS doctor_name,
                   p.first_name||' '||p.last_name AS patient_name
            FROM reminders r
            LEFT JOIN staff s ON r.doctor_id=s.id
            LEFT JOIN patients p ON r.patient_id=p.id
            ORDER BY r.due_date
        """)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def save_reminder(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reminders (patient_id, doctor_id, due_date, reason, notes, status)
        VALUES (%s,%s,%s,%s,%s,'pending') RETURNING id
    """, (data['patient_id'], data.get('doctor_id'), data['due_date'],
          data['reason'], data.get('notes')))
    rid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close(); return rid

def update_reminder(reminder_id, data):
    conn = get_conn()
    cur = conn.cursor()
    status = 'returned' if data.get('returned_date') else ('contacted' if data.get('contacted_date') else 'pending')
    cur.execute("""
        UPDATE reminders SET contacted_date=%s, contact_action=%s,
            returned_date=%s, status=%s WHERE id=%s
    """, (data.get('contacted_date') or None, data.get('contact_action') or None,
          data.get('returned_date') or None, status, reminder_id))
    conn.commit(); cur.close(); conn.close()

def delete_reminder(reminder_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id=%s", (reminder_id,))
    conn.commit(); cur.close(); conn.close()

# ── Patient archive / merge ───────────────────────────────────────────────────

def get_archived_patients():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id,first_name,last_name,dob,phone FROM patients
        WHERE archived=TRUE ORDER BY last_name,first_name
    """)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def archive_patient(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE patients SET archived=TRUE WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()

def unarchive_patient(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE patients SET archived=FALSE WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()

def get_duplicate_patients():
    """Find patients with same first+last name and same DOB."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT first_name, last_name, dob,
               COUNT(*) AS cnt,
               array_agg(id ORDER BY id) AS ids
        FROM patients WHERE archived=FALSE
        GROUP BY first_name, last_name, dob
        HAVING COUNT(*) > 1
        ORDER BY last_name, first_name
    """)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def merge_patients(keep_id, merge_id):
    """Re-point all records from merge_id to keep_id, then archive merge_id."""
    conn = get_conn()
    cur = conn.cursor()
    for table in ['appointments','visit_notes','symptom_analyses','scan_analyses',
                  'prescriptions','lab_tests','invoices','patient_documents',
                  'referrals','recalls','reminders','consultation_notes']:
        cur.execute(f"UPDATE {table} SET patient_id=%s WHERE patient_id=%s",
                    (keep_id, merge_id))
    cur.execute("UPDATE patients SET archived=TRUE WHERE id=%s", (merge_id,))
    conn.commit(); cur.close(); conn.close()

def report_earnings_charges(start, end, doctor_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name,
               (i.total_amount - i.amount_paid) AS outstanding
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.invoice_date BETWEEN %s AND %s
    """
    params = [start, end]
    if doctor_id:
        q += " AND i.doctor_id=%s"
        params.append(doctor_id)
    q += " ORDER BY s.name, i.invoice_date"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def report_earnings_payments(start, end, doctor_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.invoice_date BETWEEN %s AND %s
          AND i.amount_paid > 0
    """
    params = [start, end]
    if doctor_id:
        q += " AND i.doctor_id=%s"
        params.append(doctor_id)
    q += " ORDER BY i.invoice_date"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def report_overdue():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               p.phone, p.id AS patient_id,
               s.name AS doctor_name,
               (i.total_amount - i.amount_paid) AS outstanding,
               (CURRENT_DATE - i.invoice_date) AS days_overdue
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.status != 'paid'
          AND i.invoice_date <= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY days_overdue DESC
    """)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def report_booking(start, end, doctor_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """
        SELECT a.*, p.first_name||' '||p.last_name AS patient_name,
               p.phone, s.name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id=p.id
        LEFT JOIN staff s ON a.doctor_id=s.id
        WHERE a.appointment_date BETWEEN %s AND %s
    """
    params = [start, end]
    if doctor_id:
        q += " AND a.doctor_id=%s"
        params.append(doctor_id)
    q += " ORDER BY a.appointment_date, a.start_time"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def report_daily_banking(report_date):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.invoice_date=%s AND i.amount_paid > 0
        ORDER BY i.id
    """, (report_date,))
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

def report_transactions(start, end, doctor_id=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """
        SELECT i.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM invoices i
        LEFT JOIN patients p ON i.patient_id=p.id
        LEFT JOIN staff s ON i.doctor_id=s.id
        WHERE i.invoice_date BETWEEN %s AND %s
    """
    params = [start, end]
    if doctor_id:
        q += " AND i.doctor_id=%s"
        params.append(doctor_id)
    q += " ORDER BY i.invoice_date"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close(); return rows

# ── Vaccinations ──────────────────────────────────────────────────────────────

def get_vaccinations(patient_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT v.*, s.name AS doctor_name FROM vaccinations v
        LEFT JOIN staff s ON v.doctor_id=s.id
        WHERE v.patient_id=%s ORDER BY v.date_given DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def save_vaccination(data, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vaccinations
            (patient_id, doctor_id, vaccine_name, dose, date_given,
             batch_number, next_due_date, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (data['patient_id'], created_by,
          data['vaccine_name'], data.get('dose'),
          data['date_given'], data.get('batch_number') or None,
          data.get('next_due_date') or None, data.get('notes') or None))
    vid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return vid

def delete_vaccination(vac_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM vaccinations WHERE id=%s", (vac_id,))
    conn.commit(); cur.close(); conn.close()

# ── Waiting Room ──────────────────────────────────────────────────────────────

def get_waiting_room():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT wr.*,
               p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM waiting_room wr
        LEFT JOIN patients p ON wr.patient_id=p.id
        LEFT JOIN staff s ON wr.doctor_id=s.id
        WHERE wr.status IN ('waiting','with_doctor')
        ORDER BY wr.checked_in_at
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def checkin_patient(patient_id, doctor_id, reason):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO waiting_room (patient_id, doctor_id, reason, status)
        VALUES (%s,%s,%s,'waiting') RETURNING id
    """, (patient_id, doctor_id or None, reason or None))
    wid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return wid

def update_waiting_status(waiting_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE waiting_room SET status=%s WHERE id=%s", (status, waiting_id))
    conn.commit(); cur.close(); conn.close()

def remove_from_waiting(waiting_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE waiting_room SET status='done' WHERE id=%s", (waiting_id,))
    conn.commit(); cur.close(); conn.close()

# ── Dashboard analytics ───────────────────────────────────────────────────────

def get_monthly_revenue(months=6):
    """Return last N months of billed vs collected totals."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', invoice_date), 'Mon') AS month_label,
            DATE_TRUNC('month', invoice_date) AS month_date,
            COALESCE(SUM(total_amount), 0)  AS billed,
            COALESCE(SUM(amount_paid), 0)   AS collected
        FROM invoices
        WHERE invoice_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '%s months'
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY month_date
    """ % months)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_staff_role_distribution():
    """Count active staff by role."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT role, COUNT(*) AS count
        FROM staff WHERE active=TRUE
        GROUP BY role ORDER BY count DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── MFA & Security ────────────────────────────────────────────────────────────

def save_mfa_secret(staff_id, secret):
    """Store or clear a TOTP secret for a staff member."""
    conn = get_conn(); cur = conn.cursor()
    # Add column if it doesn't exist yet (safe migration)
    cur.execute("""
        ALTER TABLE staff ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(64);
    """)
    cur.execute("UPDATE staff SET mfa_secret=%s WHERE id=%s", (secret, staff_id))
    conn.commit(); cur.close(); conn.close()

def update_staff_password(staff_id, hashed_password):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE staff SET password=%s WHERE id=%s", (hashed_password, staff_id))
    conn.commit(); cur.close(); conn.close()


# ── Tasks ─────────────────────────────────────────────────────────────────────

def setup_tasks():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
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
    """)
    conn.commit(); cur.close(); conn.close()

def get_tasks(assigned_to=None, patient_id=None, status=None):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """SELECT t.*, p.first_name||' '||p.last_name AS patient_name,
                  s1.name AS created_by_name, s2.name AS assigned_to_name
           FROM tasks t
           LEFT JOIN patients p  ON t.patient_id   = p.id
           LEFT JOIN staff    s1 ON t.created_by   = s1.id
           LEFT JOIN staff    s2 ON t.assigned_to  = s2.id
           WHERE 1=1"""
    params = []
    if assigned_to: q += " AND t.assigned_to=%s"; params.append(assigned_to)
    if patient_id:  q += " AND t.patient_id=%s";  params.append(patient_id)
    if status:      q += " AND t.status=%s";       params.append(status)
    q += " ORDER BY CASE t.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 ELSE 3 END, t.created_at DESC"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def save_task(data, task_id=None):
    conn = get_conn(); cur = conn.cursor()
    if task_id:
        cur.execute("""UPDATE tasks SET title=%s, description=%s, priority=%s,
                       status=%s, due_date=%s, assigned_to=%s, task_type=%s,
                       completed_at=CASE WHEN %s='completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
                       WHERE id=%s""",
                   (data['title'], data.get('description'), data.get('priority','normal'),
                    data.get('status','pending'), data.get('due_date') or None,
                    data.get('assigned_to') or None, data.get('task_type','general'),
                    data.get('status','pending'), task_id))
    else:
        cur.execute("""INSERT INTO tasks (patient_id, created_by, assigned_to, title,
                       description, priority, status, due_date, task_type)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                   (data.get('patient_id'), data.get('created_by'),
                    data.get('assigned_to') or None, data['title'],
                    data.get('description'), data.get('priority','normal'),
                    data.get('status','pending'), data.get('due_date') or None,
                    data.get('task_type','general')))
        task_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return task_id

def delete_task(task_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit(); cur.close(); conn.close()

def get_task(task_id):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    row = cur.fetchone(); cur.close(); conn.close()
    return row

def get_pending_task_counts(staff_id):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) AS cnt FROM tasks WHERE assigned_to=%s AND status='pending'", (staff_id,))
    row = cur.fetchone(); cur.close(); conn.close()
    return row['cnt'] if row else 0

# ── Audit Report ──────────────────────────────────────────────────────────────

def get_audit_report(days=30, staff_id=None):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    q = """SELECT al.*, s.name AS staff_name, s.role AS staff_role
           FROM activity_log al
           LEFT JOIN staff s ON al.staff_id = s.id
           WHERE al.created_at >= NOW() - INTERVAL '%s days'"""
    params = [days]
    if staff_id: q += " AND al.staff_id=%s"; params.append(staff_id)
    q += " ORDER BY al.created_at DESC"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def get_audit_summary(days=30):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT s.name, s.role, COUNT(*) AS total_actions,
               SUM(CASE WHEN al.action LIKE 'PHI%%' THEN 1 ELSE 0 END) AS phi_accesses,
               SUM(CASE WHEN al.action LIKE 'SECURITY%%' THEN 1 ELSE 0 END) AS security_events,
               MAX(al.created_at) AS last_action
        FROM activity_log al
        LEFT JOIN staff s ON al.staff_id = s.id
        WHERE al.created_at >= NOW() - INTERVAL %s
          AND al.staff_id IS NOT NULL
        GROUP BY s.id, s.name, s.role
        ORDER BY total_actions DESC
    """, (f'{days} days',))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def get_vitals_history(patient_id, limit=10):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT visit_date, clinical_notes, created_at
        FROM visit_notes WHERE patient_id=%s
        ORDER BY visit_date DESC LIMIT %s
    """, (patient_id, limit))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def get_room_status():
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT wr.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS doctor_name
        FROM waiting_room wr
        LEFT JOIN patients p ON wr.patient_id=p.id
        LEFT JOIN staff    s ON wr.doctor_id=s.id
        WHERE wr.status IN ('waiting','with_doctor')
        ORDER BY wr.checked_in_at
    """)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

# ── Break-the-Glass emergency access ──────────────────────────────────────────

def setup_advanced():
    """Create advanced-feature tables (safe to run multiple times)."""
    conn = get_conn(); cur = conn.cursor()

    # Break-the-Glass log
    cur.execute("""
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
    CREATE INDEX IF NOT EXISTS idx_btg_staff   ON btg_access(staff_id);
    CREATE INDEX IF NOT EXISTS idx_btg_patient ON btg_access(patient_id);
    """)

    # Document signatures
    cur.execute("""
    CREATE TABLE IF NOT EXISTS document_signatures (
        id           SERIAL PRIMARY KEY,
        record_type  VARCHAR(50) NOT NULL,  -- 'visit_note', 'referral', etc.
        record_id    INTEGER NOT NULL,
        signed_by    INTEGER REFERENCES staff(id),
        content_hash VARCHAR(128) NOT NULL,  -- SHA-256 hex
        signed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        algorithm    VARCHAR(20) DEFAULT 'SHA-256'
    );
    CREATE INDEX IF NOT EXISTS idx_sig_record ON document_signatures(record_type, record_id);
    """)

    # Inventory
    cur.execute("""
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
    """)

    # Add columns to existing tables if missing
    for col_sql in [
        "ALTER TABLE referrals ADD COLUMN IF NOT EXISTS outcome VARCHAR(50) DEFAULT 'pending'",
        "ALTER TABLE referrals ADD COLUMN IF NOT EXISTS outcome_notes TEXT",
        "ALTER TABLE referrals ADD COLUMN IF NOT EXISTS appointment_confirmed BOOLEAN DEFAULT FALSE",
        "ALTER TABLE referrals ADD COLUMN IF NOT EXISTS report_received BOOLEAN DEFAULT FALSE",
        "ALTER TABLE referrals ADD COLUMN IF NOT EXISTS follow_up_due DATE",
        "ALTER TABLE patients  ADD COLUMN IF NOT EXISTS risk_score SMALLINT",
        "ALTER TABLE patients  ADD COLUMN IF NOT EXISTS risk_updated TIMESTAMP",
        "ALTER TABLE lab_tests ADD COLUMN IF NOT EXISTS auto_notified BOOLEAN DEFAULT FALSE",
    ]:
        cur.execute(col_sql)

    conn.commit(); cur.close(); conn.close()


# ── Break-the-Glass ────────────────────────────────────────────────────────────

def btg_request(staff_id, patient_id, justification, duration_minutes=60):
    conn = get_conn(); cur = conn.cursor()
    from datetime import datetime, timedelta
    expires = datetime.now() + timedelta(minutes=duration_minutes)
    cur.execute("""
        INSERT INTO btg_access (staff_id, patient_id, justification, expires_at)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (staff_id, patient_id, justification, expires))
    btg_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return btg_id

def btg_check(staff_id, patient_id):
    """Return active BTG grant if exists, else None."""
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM btg_access
        WHERE staff_id=%s AND patient_id=%s
          AND expires_at > NOW() AND revoked_at IS NULL
        ORDER BY granted_at DESC LIMIT 1
    """, (staff_id, patient_id))
    row = cur.fetchone(); cur.close(); conn.close()
    return row

def btg_get_unnotified():
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT b.*, s.name AS staff_name, s.role AS staff_role,
               p.first_name||' '||p.last_name AS patient_name
        FROM btg_access b
        LEFT JOIN staff    s ON b.staff_id   = s.id
        LEFT JOIN patients p ON b.patient_id = p.id
        WHERE b.admin_notified = FALSE
    """)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def btg_mark_notified(btg_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE btg_access SET admin_notified=TRUE WHERE id=%s", (btg_id,))
    conn.commit(); cur.close(); conn.close()

def btg_get_log(limit=50):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT b.*, s.name AS staff_name, p.first_name||' '||p.last_name AS patient_name
        FROM btg_access b
        LEFT JOIN staff    s ON b.staff_id   = s.id
        LEFT JOIN patients p ON b.patient_id = p.id
        ORDER BY b.granted_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows


# ── Cryptographic document signing ────────────────────────────────────────────

def sign_document(record_type, record_id, content, signed_by):
    import hashlib
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    conn = get_conn(); cur = conn.cursor()
    # Remove any previous sig for this record
    cur.execute("DELETE FROM document_signatures WHERE record_type=%s AND record_id=%s",
                (record_type, record_id))
    cur.execute("""
        INSERT INTO document_signatures (record_type, record_id, signed_by, content_hash)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (record_type, record_id, signed_by, content_hash))
    sig_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return content_hash, sig_id

def verify_document(record_type, record_id, content):
    import hashlib
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT ds.*, s.name AS signed_by_name
        FROM document_signatures ds
        LEFT JOIN staff s ON ds.signed_by = s.id
        WHERE ds.record_type=%s AND ds.record_id=%s
        ORDER BY ds.signed_at DESC LIMIT 1
    """, (record_type, record_id))
    sig = cur.fetchone(); cur.close(); conn.close()
    if not sig:
        return None, False
    current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    intact = (current_hash == sig['content_hash'])
    return sig, intact


# ── Referral close-the-loop ────────────────────────────────────────────────────

def get_open_referrals():
    """Referrals sent but outcome not yet confirmed."""
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT r.*, p.first_name||' '||p.last_name AS patient_name,
               s.name AS referring_doctor_name
        FROM referrals r
        LEFT JOIN patients p ON r.patient_id     = p.id
        LEFT JOIN staff    s ON r.referring_doctor= s.id
        WHERE r.status = 'sent'
          AND r.outcome IN ('pending', NULL)
        ORDER BY r.date_created
    """)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def update_referral_outcome(ref_id, outcome, notes, appt_confirmed, report_received):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        UPDATE referrals SET outcome=%s, outcome_notes=%s,
               appointment_confirmed=%s, report_received=%s,
               status=CASE WHEN %s='completed' THEN 'completed' ELSE status END
        WHERE id=%s
    """, (outcome, notes, appt_confirmed, report_received, outcome, ref_id))
    conn.commit(); cur.close(); conn.close()


# ── Risk score ────────────────────────────────────────────────────────────────

def save_risk_score(patient_id, score):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        UPDATE patients SET risk_score=%s, risk_updated=CURRENT_TIMESTAMP
        WHERE id=%s
    """, (score, patient_id))
    conn.commit(); cur.close(); conn.close()


# ── Gap-in-care alerts ────────────────────────────────────────────────────────

def get_gap_in_care_data(patient_id):
    """Return minimal data needed for gap-in-care screening."""
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT p.dob, p.gender, p.medical_history, p.icd_codes,
               p.blood_pressure, p.blood_glucose, p.cholesterol,
               p.last_name, p.first_name, p.risk_score,
               (SELECT MAX(v.visit_date) FROM visit_notes v WHERE v.patient_id=p.id) AS last_visit,
               (SELECT MAX(vac.date_given) FROM vaccinations vac
                WHERE vac.patient_id=p.id AND vac.vaccine_name ILIKE '%%flu%%') AS last_flu_shot,
               (SELECT COUNT(*)::int FROM lab_tests lt WHERE lt.patient_id=p.id
                AND lt.is_abnormal=TRUE AND lt.status='resulted') AS abnormal_labs
        FROM patients p WHERE p.id=%s
    """, (patient_id,))
    row = cur.fetchone(); cur.close(); conn.close()
    return row


# ── Wait-time predictor ────────────────────────────────────────────────────────

def get_wait_time_stats():
    """Average wait time based on today's check-ins."""
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            COUNT(*) AS total_today,
            AVG(EXTRACT(EPOCH FROM (NOW() - checked_in_at))/60)::INT AS avg_wait_mins,
            MIN(EXTRACT(EPOCH FROM (NOW() - checked_in_at))/60)::INT AS min_wait_mins,
            MAX(EXTRACT(EPOCH FROM (NOW() - checked_in_at))/60)::INT AS max_wait_mins
        FROM waiting_room
        WHERE DATE(checked_in_at) = CURRENT_DATE
          AND status IN ('waiting','with_doctor')
    """)
    row = cur.fetchone(); cur.close(); conn.close()
    return row


# ── Inventory ─────────────────────────────────────────────────────────────────

def get_inventory():
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM inventory ORDER BY category, item_name")
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def save_inventory_item(data, item_id=None):
    conn = get_conn(); cur = conn.cursor()
    if item_id:
        cur.execute("""UPDATE inventory SET item_name=%s, category=%s, quantity=%s,
                       unit=%s, reorder_level=%s, cpt_code=%s, unit_cost=%s,
                       updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                   (data['item_name'], data.get('category'), data.get('quantity',0),
                    data.get('unit'), data.get('reorder_level',5),
                    data.get('cpt_code') or None, data.get('unit_cost') or None, item_id))
    else:
        cur.execute("""INSERT INTO inventory (item_name, category, quantity, unit,
                       reorder_level, cpt_code, unit_cost)
                       VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                   (data['item_name'], data.get('category'), data.get('quantity',0),
                    data.get('unit'), data.get('reorder_level',5),
                    data.get('cpt_code') or None, data.get('unit_cost') or None))
        item_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return item_id

def decrement_inventory(item_id, qty=1):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE inventory SET quantity=GREATEST(0, quantity-%s),
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""", (qty, item_id))
    conn.commit(); cur.close(); conn.close()

# ── Patient Forms ─────────────────────────────────────────────────────────────

FORM_TEMPLATES = {
    'consent_general':    {'title': 'Pëlqim i Përgjithshëm për Trajtim',      'content': 'I consent to examination and treatment by the medical staff of this practice. I understand that no guarantee has been made as to the results of treatment.'},
    'consent_privacy':    {'title': 'Njoftim mbi Privatësinë & Informacionin',       'content': 'I acknowledge receipt of the Practice Privacy Notice and consent to my information being used for the purposes described.'},
    'consent_telehealth': {'title': 'Pëlqim për Telehealth',                 'content': 'I consent to receiving medical consultations via telehealth video conferencing. I understand telehealth may not be appropriate for all conditions.'},
    'consent_photo':      {'title': 'Fotografim / Imazhe Klinike',      'content': 'I consent to clinical photographs being taken for my medical record. Images will be stored securely and used only for my clinical care.'},
    'intake_new_patient': {'title': 'Formulari i Pranimit të Pacientit të Ri',            'content': 'Please confirm your personal details, insurance, emergency contact, current medications, allergies, and past medical history are correct.'},
    'consent_medication': {'title': 'Pëlqim & Konfirmim për Medikamentin','content': 'I acknowledge I have been informed of the medication prescribed including its purpose, dosage, side effects, and when to seek urgent help.'},
}

def _setup_patient_forms(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_forms (
        id              SERIAL PRIMARY KEY,
        patient_id      INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        form_type       VARCHAR(100) NOT NULL,
        form_title      VARCHAR(255) NOT NULL,
        form_content    TEXT,
        status          VARCHAR(30) DEFAULT 'pending',
        signed_at       TIMESTAMP,
        signed_by_name  VARCHAR(150),
        signature_data  TEXT,
        ip_address      VARCHAR(50),
        created_by      INTEGER REFERENCES staff(id),
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_patient_forms ON patient_forms(patient_id);")
    cur.execute("""
        DO $$ BEGIN
            BEGIN ALTER TABLE patients ADD COLUMN insurance_company VARCHAR(150); EXCEPTION WHEN duplicate_column THEN NULL; END;
            BEGIN ALTER TABLE patients ADD COLUMN insurance_type VARCHAR(100); EXCEPTION WHEN duplicate_column THEN NULL; END;
            BEGIN ALTER TABLE patients ADD COLUMN insurance_expiry DATE; EXCEPTION WHEN duplicate_column THEN NULL; END;
            BEGIN ALTER TABLE patients ADD COLUMN insurance_notes TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END;
        END $$;
    """)
    conn.commit()
    cur.close()

def get_patient_forms(patient_id):
    conn = get_conn()
    _setup_patient_forms(conn)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT pf.*, s.name AS created_by_name
        FROM patient_forms pf
        LEFT JOIN staff s ON pf.created_by = s.id
        WHERE pf.patient_id = %s
        ORDER BY pf.created_at DESC
    """, (patient_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_patient_form(form_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT pf.*, s.name AS created_by_name, p.first_name, p.last_name
        FROM patient_forms pf
        LEFT JOIN staff s ON pf.created_by = s.id
        LEFT JOIN patients p ON pf.patient_id = p.id
        WHERE pf.id = %s
    """, (form_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def save_patient_form(data, created_by=None):
    conn = get_conn()
    _setup_patient_forms(conn)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patient_forms
            (patient_id, form_type, form_title, form_content, status, created_by)
        VALUES (%s, %s, %s, %s, 'pending', %s) RETURNING id
    """, (data['patient_id'], data['form_type'], data['form_title'],
          data.get('form_content', ''), created_by))
    fid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return fid

def sign_patient_form(form_id, signed_by_name, signature_data, ip_address):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE patient_forms
        SET status='signed', signed_at=CURRENT_TIMESTAMP,
            signed_by_name=%s, signature_data=%s, ip_address=%s
        WHERE id=%s
    """, (signed_by_name, signature_data, ip_address, form_id))
    conn.commit(); cur.close(); conn.close()

def delete_patient_form(form_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM patient_forms WHERE id=%s", (form_id,))
    conn.commit(); cur.close(); conn.close()


def get_all_forms(status=None, limit=200):
    """Get all patient forms across all patients for the global forms page."""
    conn = get_conn()
    _setup_patient_forms(conn)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if status:
        cur.execute("""
            SELECT pf.*, p.first_name, p.last_name, p.dob, s.name AS created_by_name
            FROM patient_forms pf
            LEFT JOIN patients p ON pf.patient_id = p.id
            LEFT JOIN staff s ON pf.created_by = s.id
            WHERE pf.status = %s
            ORDER BY pf.created_at DESC LIMIT %s
        """, (status, limit))
    else:
        cur.execute("""
            SELECT pf.*, p.first_name, p.last_name, p.dob, s.name AS created_by_name
            FROM patient_forms pf
            LEFT JOIN patients p ON pf.patient_id = p.id
            LEFT JOIN staff s ON pf.created_by = s.id
            ORDER BY pf.created_at DESC LIMIT %s
        """, (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── Practice Settings ─────────────────────────────────────────────────────────

def setup_settings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS practice_settings (
        key   VARCHAR(100) PRIMARY KEY,
        value TEXT
    );
    """)
    # Insert defaults if not present
    defaults = [
        ('practice_name',   'Medical Practice'),
        ('logo_filename',   ''),
        ('primary_color',   '#2d6fd4'),
        ('accent_color',    '#1a3570'),
        ('sidebar_color',   '#0c1a2e'),
        ('font_family',     'system-ui'),
    ]
    for k, v in defaults:
        cur.execute(
            "INSERT INTO practice_settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO NOTHING",
            (k, v)
        )
    conn.commit(); cur.close(); conn.close()

def get_settings():
    """Return all practice settings as a dict."""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT key, value FROM practice_settings")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {r['key']: r['value'] for r in rows}
    except:
        return {}

def save_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO practice_settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
        (key, value)
    )
    conn.commit(); cur.close(); conn.close()

def save_settings(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    for k, v in data.items():
        cur.execute(
            "INSERT INTO practice_settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
            (k, v)
        )
    conn.commit(); cur.close(); conn.close()

# ── Medicine Catalog ──────────────────────────────────────────────────────────

def setup_medicine_catalog():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine_catalog (
        id              SERIAL PRIMARY KEY,
        name            VARCHAR(200) NOT NULL,
        generic_name    VARCHAR(200),
        brand_name      VARCHAR(200),
        drug_class      VARCHAR(100),
        country_origin  VARCHAR(100),
        manufacturer    VARCHAR(200),
        dosage_forms    VARCHAR(200),
        strengths       VARCHAR(200),
        in_stock        BOOLEAN DEFAULT TRUE,
        stock_qty       INTEGER DEFAULT 0,
        unit_price      NUMERIC(10,2),
        requires_rx     BOOLEAN DEFAULT TRUE,
        notes           TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Insert common medicines if table is empty
    cur.execute("SELECT COUNT(*) FROM medicine_catalog")
    if cur.fetchone()[0] == 0:
        sample = [
            ('Amoxicillin','Amoxicillin','Amoxil','Antibiotic','Germany','Pfizer','Capsule, Suspension','250mg, 500mg',True,120,4.50,True),
            ('Ibuprofen','Ibuprofen','Nurofen','NSAID','UK','Reckitt','Tablet, Gel','200mg, 400mg, 600mg',True,200,2.80,False),
            ('Paracetamol','Paracetamol','Panadol','Analgesic','Switzerland','GSK','Tablet, Syrup','500mg, 1000mg',True,350,1.50,False),
            ('Metformin','Metformin HCl','Glucophage','Antidiabetic','France','Merck','Tablet','500mg, 850mg, 1000mg',True,80,5.20,True),
            ('Amlodipine','Amlodipine besylate','Norvasc','CCB','USA','Pfizer','Tablet','5mg, 10mg',True,60,6.80,True),
            ('Atorvastatin','Atorvastatin calcium','Lipitor','Statin','USA','Pfizer','Tablet','10mg, 20mg, 40mg',True,75,8.50,True),
            ('Omeprazole','Omeprazole','Losec','PPI','Sweden','AstraZeneca','Capsule','20mg, 40mg',True,90,7.20,True),
            ('Lisinopril','Lisinopril','Zestril','ACE Inhibitor','Germany','AstraZeneca','Tablet','5mg, 10mg, 20mg',True,55,4.90,True),
            ('Salbutamol','Salbutamol sulfate','Ventolin','Bronchodilator','UK','GSK','Inhaler, Syrup','100mcg/dose',True,40,12.00,True),
            ('Warfarin','Warfarin sodium','Coumadin','Anticoagulant','USA','BMS','Tablet','1mg, 2mg, 5mg',True,30,6.30,True),
            ('Sertraline','Sertraline HCl','Zoloft','SSRI','USA','Pfizer','Tablet','50mg, 100mg',True,45,9.80,True),
            ('Prednisolone','Prednisolone','Prelone','Corticosteroid','France','Sanofi','Tablet, Syrup','5mg, 25mg',True,60,5.50,True),
            ('Cetirizine','Cetirizine HCl','Zyrtec','Antihistamine','Belgium','UCB','Tablet, Syrup','10mg',True,110,3.20,False),
            ('Azithromycin','Azithromycin','Zithromax','Antibiotic','USA','Pfizer','Tablet, Suspension','250mg, 500mg',True,35,11.50,True),
            ('Metoprolol','Metoprolol tartrate','Lopressor','Beta-blocker','Switzerland','Novartis','Tablet','25mg, 50mg, 100mg',True,70,5.70,True),
        ]
        for row in sample:
            cur.execute("""
                INSERT INTO medicine_catalog
                    (name,generic_name,brand_name,drug_class,country_origin,manufacturer,
                     dosage_forms,strengths,in_stock,stock_qty,unit_price,requires_rx)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, row)
    conn.commit(); cur.close(); conn.close()

def search_medicine_catalog(q='', in_stock_only=False, country='', drug_class=''):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    where = ["1=1"]
    params = []
    if q:
        where.append("(name ILIKE %s OR generic_name ILIKE %s OR brand_name ILIKE %s OR drug_class ILIKE %s)")
        like = f"%{q}%"
        params += [like, like, like, like]
    if in_stock_only:
        where.append("in_stock = TRUE AND stock_qty > 0")
    if country:
        where.append("country_origin ILIKE %s")
        params.append(f"%{country}%")
    if drug_class:
        where.append("drug_class ILIKE %s")
        params.append(f"%{drug_class}%")
    cur.execute(f"""
        SELECT * FROM medicine_catalog
        WHERE {' AND '.join(where)}
        ORDER BY name LIMIT 50
    """, params)
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def get_medicine_catalog_filters():
    """Return distinct countries and drug classes for filter dropdowns."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT country_origin FROM medicine_catalog WHERE country_origin IS NOT NULL ORDER BY 1")
    countries = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT drug_class FROM medicine_catalog WHERE drug_class IS NOT NULL ORDER BY 1")
    classes = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return countries, classes

def save_patient_medicines(patient_id, staff_id, medicines):
    """Save selected medicines as prescriptions for a patient."""
    conn = get_conn()
    cur = conn.cursor()
    ids = []
    for m in medicines:
        cur.execute("""
            INSERT INTO prescriptions
                (patient_id, doctor_id, drug_name, dosage, frequency, route,
                 start_date, instructions, status)
            VALUES (%s,%s,%s,%s,%s,%s,CURRENT_DATE,%s,'active') RETURNING id
        """, (
            patient_id, staff_id,
            m.get('name',''), m.get('dosage',''),
            m.get('frequency','Once daily'), m.get('route','Oral'),
            m.get('notes','')
        ))
        ids.append(cur.fetchone()[0])
    conn.commit(); cur.close(); conn.close()
    return ids

def setup_canary_accounts():
    """
    Create honeypot staff accounts.
    If anyone logs into these, it means credentials were leaked.
    These accounts are INACTIVE and will never work for real login,
    but their use is logged as a security alert.
    """
    conn = get_conn()
    cur  = conn.cursor()
    canaries = [
        ('backup.admin@practice.local',  'Backup Admin'),
        ('admin.backup@practice.local',  'Admin Backup'),
        ('sysadmin@practice.local',      'System Admin'),
    ]
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt()
    for email, name in canaries:
        import secrets
        fake_pw = bcrypt.generate_password_hash(secrets.token_hex(32)).decode()
        cur.execute("""
            INSERT INTO staff (name, email, password, role, active)
            SELECT %s, %s, %s, 'doctor', FALSE
            WHERE NOT EXISTS (SELECT 1 FROM staff WHERE email = %s)
        """, (name, email, fake_pw, email))
    conn.commit(); cur.close(); conn.close()

# ── GDPR / Right to be Forgotten ─────────────────────────────────────────────

def anonymize_staff(staff_id: int, performed_by: int) -> bool:
    """
    GDPR / Health Privacy — "Right to be Forgotten" for staff accounts.

    Does NOT delete the row — the staff id must remain for audit trail
    integrity (medical records they signed reference this id).

    Instead:
      - Scrubs name, email, phone, mfa_secret, recovery_codes
      - Sets active = FALSE
      - Logs the anonymization in activity_log
      - Keeps id, role, created_at for referential integrity

    Returns True on success.
    """
    conn = get_conn()
    cur  = conn.cursor()
    import secrets as _sec
    ghost_email = f"anonymized_{_sec.token_hex(8)}@deleted.local"
    ghost_name  = f"[Deleted User #{staff_id}]"
    try:
        cur.execute("""
            UPDATE staff SET
                name           = %s,
                email          = %s,
                password       = 'ANONYMIZED',
                phone          = NULL,
                specialty      = NULL,
                mfa_secret     = NULL,
                recovery_codes = NULL,
                active         = FALSE,
                permissions    = NULL
            WHERE id = %s
        """, (ghost_name, ghost_email, staff_id))
        # Also remove remember tokens
        cur.execute("DELETE FROM remember_tokens WHERE staff_id=%s", (staff_id,))
        log_activity(performed_by, "GDPR_STAFF_ANONYMIZED",
                     f"Staff #{staff_id} anonymized per right-to-be-forgotten request")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()


def anonymize_patient(patient_id: int, performed_by: int) -> bool:
    """
    GDPR anonymization for patient records.
    Scrubs PII but keeps clinical data linked to an anonymous record
    (required by medical retention laws in most jurisdictions).
    """
    conn = get_conn()
    cur  = conn.cursor()
    import secrets as _sec
    try:
        cur.execute("""
            UPDATE patients SET
                first_name        = '[Anonimizuar]',
                last_name         = %s,
                dob               = NULL,
                phone             = NULL,
                email             = NULL,
                address           = NULL,
                emergency_contact = NULL,
                insurance_nr      = NULL,
                notes             = NULL
            WHERE id = %s
        """, (f'#{patient_id}', patient_id))
        log_activity(performed_by, "GDPR_PATIENT_ANONYMIZED",
                     f"Patient #{patient_id} PII scrubbed per GDPR request")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()

# ── Audit compatibility aliases ───────────────────────────────────────────────
def setup_extended():       return setup()
def setup_primaryclinic():  return setup()
def report_earnings_by_charges(start, end, doctor_id=None):
    return report_earnings_charges(start, end, doctor_id)
def report_earnings_by_payments(start, end, doctor_id=None):
    return report_earnings_payments(start, end, doctor_id)
def report_overdue_accounts():
    return report_overdue()

# ── Smart Today Alerts ─────────────────────────────────────────────────────────

def get_smart_today_alerts():
    """
    Returns a list of actionable alerts for today's dashboard.
    Each alert: {type, priority, title, detail, patient_id, patient_name, action_url, action_label}
    priority: 'high' | 'medium' | 'low'
    """
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    alerts = []

    try:
        # 1. Patients with appointments today who have no visit note yet
        cur.execute("""
            SELECT a.id AS appt_id, a.patient_id, a.start_time,
                   p.first_name||' '||p.last_name AS patient_name,
                   a.appointment_type
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.appt_date = CURRENT_DATE
              AND a.status = 'scheduled'
              AND NOT EXISTS (
                  SELECT 1 FROM visit_notes vn
                  WHERE vn.appointment_id = a.id
              )
            ORDER BY a.start_time
            LIMIT 10
        """)
        for row in cur.fetchall():
            alerts.append({
                'type':         'visit_missing',
                'priority':     'high',
                'icon':         'bi-clipboard-pulse',
                'color':        '#dc2626',
                'title':        f"Shënim mungon — {row['patient_name']}",
                'detail':       f"Takim sot ora {str(row['start_time'])[:5]} · {row['appointment_type'] or ''}",
                'patient_id':   row['patient_id'],
                'patient_name': row['patient_name'],
                'action_url':   f"/patients/{row['patient_id']}/visits/from-appointment/{row['appt_id']}",
                'action_label': '+ Shënim me 1 klik',
            })

        # 2. Overdue recalls (first_recall_date passed, not returned)
        cur.execute("""
            SELECT r.id, r.patient_id, r.result, r.first_recall_date,
                   p.first_name||' '||p.last_name AS patient_name
            FROM recalls r
            JOIN patients p ON r.patient_id = p.id
            WHERE r.status = 'pending'
              AND r.first_recall_date <= CURRENT_DATE
            ORDER BY r.first_recall_date
            LIMIT 8
        """)
        for row in cur.fetchall():
            days_overdue = (date.today() - row['first_recall_date']).days if row['first_recall_date'] else 0
            alerts.append({
                'type':         'recall_overdue',
                'priority':     'high' if days_overdue > 7 else 'medium',
                'icon':         'bi-arrow-repeat',
                'color':        '#d97706',
                'title':        f"Rikujtes i vonuar — {row['patient_name']}",
                'detail':       f"{row['result'] or 'Kontroll'} · {days_overdue} ditë vonë",
                'patient_id':   row['patient_id'],
                'patient_name': row['patient_name'],
                'action_url':   f"/patients/{row['patient_id']}#tab-recalls",
                'action_label': 'Shiko',
            })

        # 3. Abnormal lab results not yet reviewed (result_date today or yesterday)
        cur.execute("""
            SELECT l.id, l.patient_id, l.test_name, l.result_value,
                   p.first_name||' '||p.last_name AS patient_name
            FROM lab_tests l
            JOIN patients p ON l.patient_id = p.id
            WHERE l.is_abnormal = TRUE
              AND l.result_date >= CURRENT_DATE - INTERVAL '2 days'
              AND l.status = 'resulted'
            ORDER BY l.result_date DESC
            LIMIT 6
        """)
        for row in cur.fetchall():
            alerts.append({
                'type':         'abnormal_lab',
                'priority':     'high',
                'icon':         'bi-exclamation-triangle-fill',
                'color':        '#dc2626',
                'title':        f"Rezultat jonormal — {row['patient_name']}",
                'detail':       f"{row['test_name']}: {row['result_value'] or ''}",
                'patient_id':   row['patient_id'],
                'patient_name': row['patient_name'],
                'action_url':   f"/patients/{row['patient_id']}#tab-labs",
                'action_label': 'Shiko',
            })

        # 4. Prescriptions expiring in next 3 days
        cur.execute("""
            SELECT pr.id, pr.patient_id, pr.drug_name, pr.end_date,
                   p.first_name||' '||p.last_name AS patient_name
            FROM prescriptions pr
            JOIN patients p ON pr.patient_id = p.id
            WHERE pr.status = 'active'
              AND pr.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
            ORDER BY pr.end_date
            LIMIT 6
        """)
        for row in cur.fetchall():
            days_left = (row['end_date'] - date.today()).days if row['end_date'] else 0
            alerts.append({
                'type':         'rx_expiring',
                'priority':     'medium',
                'icon':         'bi-capsule',
                'color':        '#7c3aed',
                'title':        f"Recetë skadon — {row['patient_name']}",
                'detail':       f"{row['drug_name']} · skadon në {days_left} ditë",
                'patient_id':   row['patient_id'],
                'patient_name': row['patient_name'],
                'action_url':   f"/patients/{row['patient_id']}#tab-prescriptions",
                'action_label': 'Përsërit',
            })

        # 5. Reminders due today
        cur.execute("""
            SELECT r.id, r.patient_id, r.reason,
                   p.first_name||' '||p.last_name AS patient_name
            FROM reminders r
            JOIN patients p ON r.patient_id = p.id
            WHERE r.status = 'pending'
              AND r.due_date <= CURRENT_DATE
            ORDER BY r.due_date
            LIMIT 6
        """)
        for row in cur.fetchall():
            alerts.append({
                'type':         'reminder_due',
                'priority':     'medium',
                'icon':         'bi-bell-fill',
                'color':        '#059669',
                'title':        f"Kujtesë — {row['patient_name']}",
                'detail':       row['reason'] or 'Kontroll i planifikuar',
                'patient_id':   row['patient_id'],
                'patient_name': row['patient_name'],
                'action_url':   f"/patients/{row['patient_id']}#tab-reminders",
                'action_label': 'Shiko',
            })

    except Exception as e:
        pass
    finally:
        cur.close()
        conn.close()

    # Sort: high priority first
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    alerts.sort(key=lambda x: priority_order.get(x['priority'], 2))
    return alerts[:20]  # cap at 20


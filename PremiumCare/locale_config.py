"""
locale_config.py — Regional Localization for Kosovo, Albania, North Macedonia
==============================================================================

Drop this file into C:\\Projects\\medplatform\\
Then in config.py add:  COUNTRY = "XK"  # or "AL" or "MK"

Covers:
  - National ID number formats & validation
  - Phone number formats
  - Currency & number formatting
  - Insurance card formats
  - Postal code formats
  - Address structure
  - Date/time formats
  - Healthcare system identifiers
  - Emergency numbers
"""

import re
from datetime import date


# ══════════════════════════════════════════════════════════════════════════════
#  COUNTRY PROFILES
# ══════════════════════════════════════════════════════════════════════════════

COUNTRIES = {

    # ── KOSOVO ────────────────────────────────────────────────────────────────
    "XK": {
        "name":             "Kosovë / Kosovo",
        "name_sq":          "Kosovë",
        "name_en":          "Kosovo",
        "flag":             "🇽🇰",
        "currency":         "EUR",
        "currency_symbol":  "€",
        "currency_name":    "Euro",
        "currency_decimals": 2,

        # Phone
        "phone_code":       "+383",
        "phone_format":     "+383 4X XXX XXX",
        "phone_regex":      r"^(\+383|00383|0)?[4-9]\d{7,8}$",
        "phone_placeholder": "044 123 456",
        "mobile_prefixes":  ["43", "44", "45", "46", "49"],
        "landline_prefixes": ["28", "29", "38", "39"],

        # National ID — Kosovo Personal Number (Numri Personal)
        # Format: 10 digits, starts with birth year digits
        # Example: 1234567890
        "id_name":          "Numri Personal",
        "id_name_en":       "Personal Number",
        "id_format":        "XXXXXXXXXX (10 shifra)",
        "id_regex":         r"^\d{10}$",
        "id_placeholder":   "1234567890",
        "id_length":        10,
        "id_validate":      lambda v: bool(re.match(r"^\d{10}$", v.strip())),

        # Insurance
        "insurance_name":   "Numri i Sigurimit Shëndetësor",
        "insurance_format": "XX-XXXXXXX",
        "insurance_regex":  r"^[A-Z]{2}-\d{7}$",
        "insurance_placeholder": "KS-1234567",
        "insurance_issuer": "Fondi i Sigurimit të Detyrueshëm Shëndetësor (FSDSK)",

        # Address
        "postal_digits":    5,
        "postal_regex":     r"^\d{5}$",
        "postal_placeholder": "10000",
        "postal_name":      "Kodi Postar",
        "cities": [
            "Prishtinë", "Prizren", "Ferizaj", "Pejë", "Gjakovë",
            "Mitrovicë", "Gjilan", "Vushtrri", "Suharekë", "Rahovec",
            "Lipjan", "Malishevë", "Kaçanik", "Skenderaj", "Klinë",
            "Istog", "Deçan", "Dragash", "Podujevë", "Obiliq"
        ],
        "address_format":   "{street}, {city}, {postal}",

        # Date / Time
        "date_format":      "DD/MM/YYYY",
        "date_format_py":   "%d/%m/%Y",
        "datetime_format":  "DD/MM/YYYY HH:MM",
        "datetime_format_py": "%d/%m/%Y %H:%M",
        "first_day_week":   1,  # Monday

        # Number formatting
        "decimal_separator":   ",",
        "thousands_separator": ".",
        "number_example":      "1.234,56",

        # Healthcare
        "healthcare_system":   "FSDSK — Fondi i Sigurimit të Detyrueshëm Shëndetësor",
        "doctor_title":        "Dr.",
        "specialist_referral": "Letër Referimi",
        "prescription_title":  "Recetë Mjekësore",
        "icd_version":         "ICD-10",

        # Emergency
        "emergency_general":   "112",
        "emergency_police":    "192",
        "emergency_fire":      "193",
        "emergency_ambulance": "194",

        # Tax / Business
        "tax_id_name":      "Numri Fiskal",
        "tax_id_format":    "XXXXXXXXXX",
        "tax_id_regex":     r"^\d{9}$",

        # Languages
        "primary_language": "sq",
        "secondary_languages": ["sr", "en"],
    },

    # ── ALBANIA ───────────────────────────────────────────────────────────────
    "AL": {
        "name":             "Shqipëri / Albania",
        "name_sq":          "Shqipëri",
        "name_en":          "Albania",
        "flag":             "🇦🇱",
        "currency":         "ALL",
        "currency_symbol":  "L",
        "currency_name":    "Lek Shqiptar",
        "currency_decimals": 0,  # Lek doesn't use decimals in practice

        # Phone
        "phone_code":       "+355",
        "phone_format":     "+355 6X XXX XXXX",
        "phone_regex":      r"^(\+355|00355|0)?[6-9]\d{8}$",
        "phone_placeholder": "069 123 4567",
        "mobile_prefixes":  ["67", "68", "69"],
        "landline_prefixes": ["42", "52", "54", "56", "58"],

        # National ID — NIPT (Numri i Identifikimit për Personin e Tatueshëm)
        # Personal ID: Letter + 9 digits + Letter (e.g., A12345678B)
        # Or new format: 10 alphanumeric chars
        "id_name":          "Numri i Identitetit",
        "id_name_en":       "National ID Number",
        "id_format":        "L-XXXXXXXXX-L (shkronjë + 9 shifra + shkronjë)",
        "id_regex":         r"^[A-Z]\d{8}[A-Z]$",
        "id_placeholder":   "A12345678B",
        "id_length":        10,
        "id_validate":      lambda v: bool(re.match(r"^[A-Z]\d{8}[A-Z]$", v.strip().upper())),

        # Insurance
        "insurance_name":   "Numri i Sigurimit Shoqëror",
        "insurance_format": "XXX-XXX-XXX-X",
        "insurance_regex":  r"^\d{3}-\d{3}-\d{3}-\d$",
        "insurance_placeholder": "123-456-789-0",
        "insurance_issuer": "Instituti i Sigurimeve Shoqërore (ISSH)",

        # Address
        "postal_digits":    4,
        "postal_regex":     r"^\d{4}$",
        "postal_placeholder": "1001",
        "postal_name":      "Kodi Postar",
        "cities": [
            "Tiranë", "Durrës", "Vlorë", "Shkodër", "Elbasan",
            "Fier", "Korçë", "Berat", "Lushnjë", "Kavajë",
            "Gjirokastër", "Sarandë", "Lezhë", "Kukës", "Pogradec",
            "Patos", "Laç", "Burrel", "Peshkopi", "Librazhd"
        ],
        "address_format":   "{street}, {postal} {city}",

        # Date / Time
        "date_format":      "DD.MM.YYYY",
        "date_format_py":   "%d.%m.%Y",
        "datetime_format":  "DD.MM.YYYY HH:MM",
        "datetime_format_py": "%d.%m.%Y %H:%M",
        "first_day_week":   1,  # Monday

        # Number formatting
        "decimal_separator":   ",",
        "thousands_separator": " ",
        "number_example":      "1 234,56",

        # Healthcare
        "healthcare_system":   "ISKSH — Instituti i Sigurimeve të Kujdesit Shëndetësor",
        "doctor_title":        "Dr.",
        "specialist_referral": "Fletëdërgesa",
        "prescription_title":  "Recetë Mjekësore",
        "icd_version":         "ICD-10",

        # Emergency
        "emergency_general":   "112",
        "emergency_police":    "129",
        "emergency_fire":      "128",
        "emergency_ambulance": "127",

        # Tax / Business
        "tax_id_name":      "NIPT",
        "tax_id_format":    "L-XXXXXXXX-X",
        "tax_id_regex":     r"^[A-Z]\d{8}[A-Z]$",

        # Languages
        "primary_language": "sq",
        "secondary_languages": ["en"],
    },

    # ── NORTH MACEDONIA ───────────────────────────────────────────────────────
    "MK": {
        "name":             "Maqedoni e Veriut / North Macedonia",
        "name_sq":          "Maqedoni e Veriut",
        "name_en":          "North Macedonia",
        "flag":             "🇲🇰",
        "currency":         "MKD",
        "currency_symbol":  "ден",
        "currency_name":    "Denar Maqedonas",
        "currency_decimals": 2,

        # Phone
        "phone_code":       "+389",
        "phone_format":     "+389 7X XXX XXX",
        "phone_regex":      r"^(\+389|00389|0)?[2-9]\d{7,8}$",
        "phone_placeholder": "070 123 456",
        "mobile_prefixes":  ["70", "71", "72", "75", "76", "77", "78"],
        "landline_prefixes": ["2", "31", "32", "33", "34"],

        # National ID — EMBG (Единствен матичен број на граѓанинот)
        # 13 digits: DDMMYYYRRSSSK (birth date + region + sequence + check)
        # Example: 2807993450058
        "id_name":          "Numri Amë (EMBG)",
        "id_name_en":       "Unique Identification Number (EMBG)",
        "id_format":        "DDMMYYYRRSSSK (13 shifra)",
        "id_regex":         r"^\d{13}$",
        "id_placeholder":   "2807993450058",
        "id_length":        13,
        "id_validate":      lambda v: bool(re.match(r"^\d{13}$", v.strip())) and _validate_embg(v.strip()),

        # Insurance
        "insurance_name":   "Numri i Sigurimit Shëndetësor",
        "insurance_format": "XXXXXXXXXX (10 shifra)",
        "insurance_regex":  r"^\d{10}$",
        "insurance_placeholder": "1234567890",
        "insurance_issuer": "Fondi i Sigurimit Shëndetësor (FSH / ФЗОМ)",

        # Address
        "postal_digits":    4,
        "postal_regex":     r"^\d{4}$",
        "postal_placeholder": "1000",
        "postal_name":      "Kodi Postar",
        "cities": [
            "Shkup", "Tetovë", "Gostivar", "Kumanovë", "Manastir",
            "Ohër", "Strumicë", "Veles", "Shtip", "Koçan",
            "Kavadar", "Dibër", "Kičevo", "Strugar", "Radovish",
            "Negotino", "Gjevgjeli", "Sveti Nikole", "Makedonski Brod", "Demir Hisar"
        ],
        "address_format":   "{street}, {postal} {city}",

        # Date / Time
        "date_format":      "DD.MM.YYYY",
        "date_format_py":   "%d.%m.%Y",
        "datetime_format":  "DD.MM.YYYY HH:MM",
        "datetime_format_py": "%d.%m.%Y %H:%M",
        "first_day_week":   1,  # Monday

        # Number formatting
        "decimal_separator":   ",",
        "thousands_separator": ".",
        "number_example":      "1.234,56",

        # Healthcare
        "healthcare_system":   "FZOM — Фонд за здравствено осигурување на Македонија",
        "doctor_title":        "Dr.",
        "specialist_referral": "Uputnica / Fletëdërgesa",
        "prescription_title":  "Recetë / Рецепт",
        "icd_version":         "ICD-10",

        # Emergency
        "emergency_general":   "112",
        "emergency_police":    "192",
        "emergency_fire":      "193",
        "emergency_ambulance": "194",

        # Tax / Business
        "tax_id_name":      "EDB (Едinstven Danocen Broj)",
        "tax_id_format":    "XXXXXXXXXX (13 shifra)",
        "tax_id_regex":     r"^\d{13}$",

        # Languages
        "primary_language": "sq",
        "secondary_languages": ["mk", "en"],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _validate_embg(embg: str) -> bool:
    """
    Validate EMBG (North Macedonia / ex-Yugoslav personal ID).
    13 digits: DDMMYYYRRSSSK
    - DD  = day of birth (01-31)
    - MM  = month of birth (01-12)
    - YYY = last 3 digits of birth year
    - RR  = region code
    - SSS = sequence number
    - K   = check digit (mod 11)
    """
    if not re.match(r"^\d{13}$", embg):
        return False
    try:
        dd  = int(embg[0:2])
        mm  = int(embg[2:4])
        if not (1 <= dd <= 31 and 1 <= mm <= 12):
            return False
        # Check digit validation (mod 11)
        weights = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total   = sum(int(embg[i]) * weights[i] for i in range(12))
        check   = 11 - (total % 11)
        if check in (10, 11):
            check = 0
        return check == int(embg[12])
    except Exception:
        return False


def _validate_albanian_id(nid: str) -> bool:
    """Validate Albanian NID: letter + 8 digits + letter"""
    return bool(re.match(r"^[A-Z]\d{8}[A-Z]$", nid.upper().strip()))


def _validate_kosovo_id(nid: str) -> bool:
    """Validate Kosovo Personal Number: 10 digits"""
    return bool(re.match(r"^\d{10}$", nid.strip()))


# ══════════════════════════════════════════════════════════════════════════════
#  LOCALE CLASS — use this in your app
# ══════════════════════════════════════════════════════════════════════════════

class Locale:
    """
    Helper class. Instantiate once in app.py:
        from locale_config import Locale
        from config import COUNTRY
        locale = Locale(COUNTRY)
    """

    def __init__(self, country_code: str = "XK"):
        code = country_code.upper()
        if code not in COUNTRIES:
            raise ValueError(f"Unknown country: {code}. Use XK, AL, or MK.")
        self.code   = code
        self.config = COUNTRIES[code]

    def __getattr__(self, key):
        try:
            return self.config[key]
        except KeyError:
            raise AttributeError(f"No locale config for '{key}'")

    # ── Currency ──────────────────────────────────────────────────────────────

    def format_currency(self, amount: float) -> str:
        """Format a money amount for display: €1.234,56 / 1 234 L / 1.234 ден"""
        decimals = self.config["currency_decimals"]
        symbol   = self.config["currency_symbol"]
        sep_t    = self.config["thousands_separator"]
        sep_d    = self.config["decimal_separator"]

        if decimals > 0:
            integer_part = int(amount)
            decimal_part = round((amount - integer_part) * (10 ** decimals))
            formatted_int = f"{integer_part:,}".replace(",", sep_t)
            result = f"{formatted_int}{sep_d}{decimal_part:0{decimals}d}"
        else:
            formatted_int = f"{int(round(amount)):,}".replace(",", sep_t)
            result = formatted_int

        # Currency symbol position
        if self.code == "XK":
            return f"€{result}"
        elif self.code == "AL":
            return f"{result} L"
        else:
            return f"{result} {symbol}"

    # ── Phone ─────────────────────────────────────────────────────────────────

    def validate_phone(self, phone: str) -> bool:
        return bool(re.match(self.config["phone_regex"], phone.strip()))

    def format_phone(self, phone: str) -> str:
        """Clean and format a local phone number"""
        digits = re.sub(r"\D", "", phone)
        code   = re.sub(r"\D", "", self.config["phone_code"])
        if digits.startswith(code):
            digits = digits[len(code):]
        if digits.startswith("0"):
            digits = digits[1:]
        # Format as local: 044 123 456
        if len(digits) == 8:
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        elif len(digits) == 9:
            return f"{digits[:2]} {digits[2:5]} {digits[5:]}"
        return phone  # return original if can't format

    # ── National ID ───────────────────────────────────────────────────────────

    def validate_id(self, nid: str) -> tuple:
        """Returns (is_valid: bool, message: str)"""
        nid = nid.strip().upper()
        is_valid = self.config["id_validate"](nid)
        if is_valid:
            # Extract birth info from EMBG
            if self.code == "MK" and len(nid) == 13:
                try:
                    day   = nid[0:2]
                    month = nid[2:4]
                    year  = "1" + nid[4:7] if int(nid[4:7]) > 800 else "2" + nid[4:7]
                    return True, f"Valid · Born {day}/{month}/{year}"
                except Exception:
                    pass
            return True, "Valid"
        return False, f"Invalid format. Expected: {self.config['id_format']}"

    # ── Postal Code ───────────────────────────────────────────────────────────

    def validate_postal(self, code: str) -> bool:
        return bool(re.match(self.config["postal_regex"], code.strip()))

    # ── Date formatting ───────────────────────────────────────────────────────

    def format_date(self, d) -> str:
        """Format a date object using country format"""
        if d is None:
            return "—"
        if hasattr(d, "strftime"):
            return d.strftime(self.config["date_format_py"])
        return str(d)

    def format_datetime(self, dt) -> str:
        if dt is None:
            return "—"
        if hasattr(dt, "strftime"):
            return dt.strftime(self.config["datetime_format_py"])
        return str(dt)

    # ── Age from DOB ─────────────────────────────────────────────────────────

    def age_from_dob(self, dob) -> str:
        if dob is None:
            return "—"
        today = date.today()
        years = (today - dob).days // 365
        return f"{years} vjeç"

    # ── Jinja2 template helpers ───────────────────────────────────────────────

    def template_context(self) -> dict:
        """
        Call this in your Flask before_request or inject into templates.
        Usage in app.py:
            @app.context_processor
            def inject_locale():
                return {'locale': locale.template_context()}

        Then in templates:
            {{ locale.currency_symbol }}
            {{ locale.phone_placeholder }}
            {{ locale.id_name }}
        """
        return {
            "country_code":          self.code,
            "country_name":          self.config["name_sq"],
            "flag":                  self.config["flag"],
            "currency_symbol":       self.config["currency_symbol"],
            "currency_name":         self.config["currency_name"],
            "phone_code":            self.config["phone_code"],
            "phone_placeholder":     self.config["phone_placeholder"],
            "id_name":               self.config["id_name"],
            "id_placeholder":        self.config["id_placeholder"],
            "id_format":             self.config["id_format"],
            "insurance_name":        self.config["insurance_name"],
            "insurance_placeholder": self.config["insurance_placeholder"],
            "postal_name":           self.config["postal_name"],
            "postal_placeholder":    self.config["postal_placeholder"],
            "cities":                self.config["cities"],
            "date_format":           self.config["date_format"],
            "emergency_ambulance":   self.config["emergency_ambulance"],
            "emergency_general":     self.config["emergency_general"],
            "healthcare_system":     self.config["healthcare_system"],
            "prescription_title":    self.config["prescription_title"],
            "specialist_referral":   self.config["specialist_referral"],
        }


# ══════════════════════════════════════════════════════════════════════════════
#  HOW TO WIRE INTO YOUR APP
# ══════════════════════════════════════════════════════════════════════════════
"""
1. Add to config.py:
       COUNTRY = "XK"   # Kosovo / XK | Albania / AL | North Macedonia / MK

2. Add to app.py (near the top, after imports):
       from locale_config import Locale
       from config import COUNTRY
       locale = Locale(COUNTRY)

       @app.context_processor
       def inject_locale():
           return {'locale': locale.template_context()}

3. Use in templates (patient_form.html, etc.):

       <!-- Phone field -->
       <input type="tel" name="phone" placeholder="{{ locale.phone_placeholder }}"
              pattern="{{ locale.phone_regex }}">
       <small>Format: {{ locale.phone_code }} {{ locale.phone_placeholder }}</small>

       <!-- National ID field -->
       <label>{{ locale.id_name }}</label>
       <input type="text" name="insurance_nr"
              placeholder="{{ locale.id_placeholder }}"
              maxlength="{{ locale.id_length }}">
       <small>Format: {{ locale.id_format }}</small>

       <!-- Currency amounts -->
       <span>{{ locale.currency_symbol }}{{ amount }}</span>

       <!-- City dropdown -->
       <select name="city">
         {% for city in locale.cities %}
         <option>{{ city }}</option>
         {% endfor %}
       </select>

4. Validate in Python routes (app.py):
       phone = request.form.get('phone','')
       if phone and not locale.validate_phone(phone):
           flash(f'Format gabim: {locale.phone_format}', 'danger')

       nid = request.form.get('insurance_nr','')
       valid, msg = locale.validate_id(nid)
       if nid and not valid:
           flash(msg, 'danger')
"""


# ══════════════════════════════════════════════════════════════════════════════
#  QUICK REFERENCE — ID FORMATS BY COUNTRY
# ══════════════════════════════════════════════════════════════════════════════
"""
╔══════════════╦══════════════════════╦════════════════════════╦══════════════════╗
║ Country      ║ National ID          ║ Phone                  ║ Currency         ║
╠══════════════╬══════════════════════╬════════════════════════╬══════════════════╣
║ Kosovo (XK)  ║ 1234567890           ║ +383 044 123 456       ║ € (EUR)          ║
║              ║ 10 digits            ║                        ║                  ║
╠══════════════╬══════════════════════╬════════════════════════╬══════════════════╣
║ Albania (AL) ║ A12345678B           ║ +355 069 123 4567      ║ L (ALL / Lek)    ║
║              ║ letter+8digits+      ║                        ║                  ║
║              ║ letter               ║                        ║                  ║
╠══════════════╬══════════════════════╬════════════════════════╬══════════════════╣
║ N.Macedonia  ║ 2807993450058        ║ +389 070 123 456       ║ ден (MKD/Denar)  ║
║ (MK)         ║ 13 digits (EMBG)     ║                        ║                  ║
║              ║ encodes DOB+region   ║                        ║                  ║
╠══════════════╬══════════════════════╬════════════════════════╬══════════════════╣
║ Postal codes ║ Kosovo: 5 digits     ║ Albania: 4 digits      ║ Macedonia: 4     ║
║              ║ (10000 Prishtinë)    ║ (1001 Tiranë)          ║ (1000 Shkup)     ║
╠══════════════╬══════════════════════╬════════════════════════╬══════════════════╣
║ Emergency    ║ Ambulance: 194       ║ Police: 192            ║ General: 112     ║
║ (all 3)      ║                      ║ Fire: 193              ║                  ║
╚══════════════╩══════════════════════╩════════════════════════╩══════════════════╝

Date format: DD/MM/YYYY (Kosovo) | DD.MM.YYYY (Albania, Macedonia)
Decimal:     1.234,56 (Kosovo, Macedonia) | 1 234,56 (Albania)
ICD version: ICD-10 (all three countries)
"""

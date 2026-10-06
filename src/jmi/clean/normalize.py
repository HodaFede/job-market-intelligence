"""Fonctions de normalisation, toutes pures et testées unitairement (tests/test_normalize.py)."""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from jmi.config import resource

UNKNOWN = "Non précisé"


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def norm(text: str | None) -> str:
    """Minuscules, sans accents, espaces insécables remplacés, espaces compactés."""
    if not text:
        return ""
    text = str(text).replace(" ", " ").replace("\xa0", " ").replace("’", "'")
    return re.sub(r"\s+", " ", strip_accents(text).lower()).strip()


# ---------------------------------------------------------------------------
# Salaire
# ---------------------------------------------------------------------------
@dataclass
class Salary:
    annual_min: float | None = None
    annual_max: float | None = None
    daily_rate: float | None = None  # TJM freelance, analysé à part
    period: str | None = None        # year / month / hour / day

    @property
    def annual_mid(self) -> float | None:
        vals = [v for v in (self.annual_min, self.annual_max) if v is not None]
        return sum(vals) / len(vals) if vals else None


_PERIOD_PATTERNS = [
    ("day", r"par jour|/ ?jour|/ ?j\b|\btjm\b|journalier|daily|per day"),
    ("hour", r"horaire|/ ?h\b|de l'heure|par heure|hourly|per hour"),
    ("month", r"mensuel|par mois|/ ?mois|monthly|per month"),
    ("year", r"annuel|/ ?an\b|par an\b|brut/an|\bk ?€|\d ?k\b|yearly|per year|annual"),
]
_UNIT_ALIASES = {"year": "year", "annual": "year", "yearly": "year", "month": "month", "monthly": "month",
                 "hour": "hour", "hourly": "hour", "day": "day", "daily": "day", "week": "week"}
_NUMBER = re.compile(r"(?<![\d.,])(\d{1,3}(?:[ .]\d{3})+|\d+(?:[.,]\d+)?)(?![\d.,])\s*(k\b)?", re.I)


def _to_annual(value: float, period: str, hours_per_year: int) -> float:
    return {"year": value, "month": value * 12, "hour": value * hours_per_year, "week": value * 52}[period]


def _detect_period(text: str) -> str | None:
    for period, pattern in _PERIOD_PATTERNS:
        if re.search(pattern, text):
            return period
    return None


def parse_salary(text: str | None = None, min_raw: float | None = None, max_raw: float | None = None,
                 unit_raw: str | None = None, hours_per_year: int = 1607) -> Salary:
    """Convertit un salaire brut (texte libre ou champs structurés) en salaire annuel brut.

    Exemples gérés : "Annuel de 42000.0 Euros à 48000.0 Euros sur 12.0 mois", "45K€ - 55K€",
    "Entre 40 000 et 50 000 € brut/an", "Mensuel de 3500 Euros", "550 € par jour" (TJM).
    """
    # 1) Champs structurés (Adzuna, JSON-LD)
    if min_raw is not None or max_raw is not None:
        period = _UNIT_ALIASES.get(norm(unit_raw), None) if unit_raw else None
        values = [float(v) for v in (min_raw, max_raw) if v is not None]
        if period is None:
            period = _guess_period(max(values))
        lo, hi = min(values), max(values)
        if period == "day":
            return Salary(daily_rate=(lo + hi) / 2, period="day")
        return Salary(_to_annual(lo, period, hours_per_year), _to_annual(hi, period, hours_per_year), period=period)

    # 2) Texte libre
    t = norm(text)
    if not t:
        return Salary()
    t = re.sub(r"sur \d+(?:[.,]\d+)? ?mois", " ", t)          # "sur 12.0 mois" n'est pas un montant
    t = re.sub(r"\d+(?:[.,]\d+)? ?(?:h|heures?) ?(?:/|par) ?semaine", " ", t)
    period = _detect_period(t)

    values: list[float] = []
    has_k = []
    for num, k in _NUMBER.findall(t):
        clean = num.replace(" ", "")
        clean = clean.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", clean) else clean.replace(",", ".")
        values.append(float(clean))
        has_k.append(bool(k))
    if not values:
        return Salary()
    if any(has_k) or (period == "year" and max(values) < 1000):
        values = [v * 1000 if v < 1000 else v for v in values]
    if period is None:
        period = _guess_period(max(values))
    lo, hi = min(values), max(values)
    if period == "day":
        return Salary(daily_rate=(lo + hi) / 2, period="day")
    return Salary(_to_annual(lo, period, hours_per_year), _to_annual(hi, period, hours_per_year), period=period)


def _guess_period(value: float) -> str:
    if value >= 15000:
        return "year"
    if value >= 1000:
        return "month"
    if value >= 150:
        return "day"
    return "hour"


# ---------------------------------------------------------------------------
# Expérience, séniorité, rôle
# ---------------------------------------------------------------------------
def parse_experience_years(text: str | None) -> float | None:
    t = norm(text)
    if not t:
        return None
    if re.search(r"debutant|jeune diplome|sans experience|graduate|entry level", t):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:an\(s\)|ans?\b|years?)", t)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+)\s*mois", t)
    if m:
        return round(int(m.group(1)) / 12, 1)
    return None


SENIORITY_ORDER = ["Stage / Alternance", "Junior", "Confirmé", "Senior", UNKNOWN]


def seniority_level(title: str | None, experience_years: float | None = None, contract: str | None = None,
                    description: str | None = None) -> str:
    t = norm(title)
    if re.search(r"\bstage\b|stagiaire|intern(ship)?\b|alternan|apprenti", t) or contract in ("Stage", "Alternance"):
        return "Stage / Alternance"
    if re.search(r"\bsenior\b|\bsr\b|\blead\b|principal|\bexpert\b|head of|\bstaff\b|tech lead", t):
        return "Senior"
    if re.search(r"\bjunior\b|\bjr\b|debutant|jeune diplome|graduate", t):
        return "Junior"
    if re.search(r"confirme|experimente|medior|intermediate", t):
        return "Confirmé"
    years = experience_years
    if years is None and description:
        years = parse_experience_years(description)
    if years is None:
        return UNKNOWN
    if years <= 2:
        return "Junior"
    if years <= 5:
        return "Confirmé"
    return "Senior"


ROLE_RULES: list[tuple[str, str]] = [
    ("AI / LLM Engineer", r"\bllm\b|ia generative|genai|generative ai|\bai engineer\b|\bia engineer\b|ingenieur ia\b|developpeur ia\b|ingenieur nlp|prompt engineer"
                          r"|(?:ingenieur|engineer|developpeur)[^|]{0,40}(?:intelligence artificielle|\bia\b|\bai\b)"),
    ("Machine Learning Engineer", r"machine learning engineer|\bml engineer|mlops|ml ops|ingenieur machine learning|ingenieur ml\b"),
    ("Data Scientist", r"data scien|statisticien|scientifique des donnees|machine learning|\bml\b|deep learning"),
    ("Data Engineer", r"data engineer|ingenieur (?:de )?donnees|ingenieur data|big data|data architect|architecte (?:data|donnees)|developpeur (?:big )?data|\betl\b"
                      r"|data[^|]{0,25}\bengineer\b"),
    ("Analytics Engineer / BI", r"analytics engineer|bi engineer|developpeur bi|ingenieur decisionnel|consultant (?:bi|decisionnel)|developpeur decisionnel"),
    ("Recherche / R&D IA", r"chercheu|research|\bphd\b|\bthese\b|doctora|\br&d\b|\br et d\b"),
    ("Consultant Data & IA", r"consultant"),
    ("Data Manager / Gouvernance", r"data steward|data manager|gouvernance|data quality|qualite des donnees|data owner|data governance"),
    ("Chef de projet / Lead Data & IA", r"(?:chef de projet|project manager|responsable|head of|directeur|director|lead|manager|product owner|chief|charge de mission)"
                                         r"[^|]{0,60}(?:\bdata\b|donnees|intelligence artificielle|\bia\b|\bai\b)"),
    ("Data Analyst", r"analyst|analyste|business intelligence|\bbi\b|decisionnel|reporting|data visuali[sz]"),
]


def role_family(title: str | None) -> str:
    t = norm(title)
    for role, pattern in ROLE_RULES:
        if re.search(pattern, t):
            return role
    return "Autre métier data"


# Une offre est retenue si son intitulé évoque la donnée ou l'IA ; les postes d'enseignement
# et de vente ne sont pas des métiers data même quand ils citent l'IA. Le brut reste intact.
_SCOPE_KEYWORDS = (r"\bdata\b|donnee|intelligence artificielle|\bia\b|\bai\b|\ba\.i\b|\bml\b|machine learning|deep learning|"
                   r"\bnlp\b|\bllm\b|\bbi\b|business intelligence|analytics|decisionnel|statisticien|mlops|big data|datascientist")
_SCOPE_EXCLUDED = r"professeur|enseignant|formateur|teacher|commercial|business developer|account executive|\bsales\b|recruteur|recrutement"


def is_data_ai_title(title: str | None) -> bool:
    t = norm(title)
    if not t or re.search(_SCOPE_EXCLUDED, t):
        return False
    return bool(re.search(_SCOPE_KEYWORDS, t))


# ---------------------------------------------------------------------------
# Télétravail, contrat, secteur
# ---------------------------------------------------------------------------
def remote_policy(*texts: str | None) -> str:
    t = norm(" ".join(x for x in texts if x))
    if not t:
        return UNKNOWN
    if re.search(r"full ?remote|100 ?% (?:en )?(?:teletravail|remote)|teletravail (?:total|complet|integral)|"
                 r"remote first|entierement a distance|telecommute", t):
        return "Full remote"
    if re.search(r"pas de teletravail|sans teletravail|aucun teletravail|100 ?% (?:sur site|presentiel)|"
                 r"teletravail non (?:possible|autorise)|no remote|on[- ]site only", t):
        return "Sur site"
    if re.search(r"teletravail|hybride|hybrid|remote|travail a distance", t):
        return "Hybride"
    return UNKNOWN


def contract_type(raw: str | None, title: str | None = None) -> str:
    t = norm(raw)
    ti = norm(title)
    if re.search(r"alternan|apprenti|contrat pro", t) or re.search(r"alternan|apprenti", ti):
        return "Alternance"
    if re.search(r"\bstage\b|intern", t) or re.search(r"\bstage\b|stagiaire|intern(ship)?\b", ti):
        return "Stage"
    if re.search(r"freelance|independant|portage|contractor|\blib\b|liberal|\bmission\b", t):
        return "Freelance"
    if re.search(r"interim|\bmis\b|travail temporaire|temporary|\bsai\b|saisonnier", t):
        return "Intérim / temporaire"
    if re.search(r"\bcdd\b|duree determinee|\bcontract\b", t):
        return "CDD"
    if re.search(r"\bcdi\b|duree indeterminee|permanent|full_time|full time", t):
        return "CDI"
    return UNKNOWN


SECTOR_RULES: list[tuple[str, str]] = [
    ("Recrutement / Intérim", r"interim|recrutement|travail temporaire|agence d'emploi|recruitment|staffing"),
    ("Banque / Assurance / Finance", r"banque|bancaire|assurance|financ|credit|mutuelle|accounting|bourse|fintech"),
    ("Énergie / Utilities", r"energie|electricite|\bgaz\b|petrol|nucleaire|energy|eau et assainissement"),
    ("Santé / Pharma", r"pharma|sante|hospital|hopital|medical|medtech|healthcare|biotech"),
    ("Industrie / Aéronautique", r"industrie|manufactur|aeronaut|automobile|chimi|fabrication|btp|construction|metallurg|engineering"),
    ("Retail / E-commerce", r"commerce|retail|grande distribution|e-commerce|grande consommation|luxe|\bmode\b|sales jobs"),
    ("Télécoms / Médias", r"telecom|media|edition de journaux|audiovisuel|publicite|marketing"),
    ("Transport / Logistique", r"transport|logisti|ferroviaire|aerien|maritime"),
    ("Secteur public / Éducation", r"administration|public|collectivite|enseignement|education|universit|recherche"),
    ("Tech / Éditeur de logiciels", r"edition de logiciel|saas|software|startup|scale-up|internet|plateforme|jeux video"),
    ("Conseil / ESN", r"conseil|consult|\besn\b|ssii|informatique|programmation|it jobs|systemes et logiciels|traitement de donnees|hebergement"),
]


def sector_category(sector_raw: str | None, company: str | None = None) -> str:
    for text in (sector_raw, company):
        t = norm(text)
        if not t:
            continue
        for label, pattern in SECTOR_RULES:
            if re.search(pattern, t):
                return label
    return "Autre / Non précisé"


# ---------------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------------
@dataclass
class Location:
    city: str = UNKNOWN
    department_code: str | None = None
    region: str = UNKNOWN
    latitude: float | None = None
    longitude: float | None = None


REGION_DEPTS = {
    "Île-de-France": "75 77 78 91 92 93 94 95",
    "Auvergne-Rhône-Alpes": "01 03 07 15 26 38 42 43 63 69 73 74",
    "Bourgogne-Franche-Comté": "21 25 39 58 70 71 89 90",
    "Bretagne": "22 29 35 56",
    "Centre-Val de Loire": "18 28 36 37 41 45",
    "Corse": "2A 2B",
    "Grand Est": "08 10 51 52 54 55 57 67 68 88",
    "Hauts-de-France": "02 59 60 62 80",
    "Normandie": "14 27 50 61 76",
    "Nouvelle-Aquitaine": "16 17 19 23 24 33 40 47 64 79 86 87",
    "Occitanie": "09 11 12 30 31 32 34 46 48 65 66 81 82",
    "Pays de la Loire": "44 49 53 72 85",
    "Provence-Alpes-Côte d'Azur": "04 05 06 13 83 84",
    "Outre-mer": "971 972 973 974 976",
}
DEPT_TO_REGION = {d: region for region, depts in REGION_DEPTS.items() for d in depts.split()}

# Noms de départements (forme normalisée) → code. Adzuna écrit « Ville, Département ».
DEPT_NAMES = {
    "ain": "01", "aisne": "02", "allier": "03", "alpes de haute provence": "04", "hautes alpes": "05",
    "alpes maritimes": "06", "ardeche": "07", "ardennes": "08", "ariege": "09", "aube": "10", "aude": "11",
    "aveyron": "12", "bouches du rhone": "13", "calvados": "14", "cantal": "15", "charente": "16",
    "charente maritime": "17", "cher": "18", "correze": "19", "cote d or": "21", "cotes d armor": "22",
    "creuse": "23", "dordogne": "24", "doubs": "25", "drome": "26", "eure": "27", "eure et loir": "28",
    "finistere": "29", "corse du sud": "2A", "haute corse": "2B", "gard": "30", "haute garonne": "31",
    "gers": "32", "gironde": "33", "herault": "34", "ille et vilaine": "35", "indre": "36",
    "indre et loire": "37", "isere": "38", "jura": "39", "landes": "40", "loir et cher": "41", "loire": "42",
    "haute loire": "43", "loire atlantique": "44", "loiret": "45", "lot": "46", "lot et garonne": "47",
    "lozere": "48", "maine et loire": "49", "manche": "50", "marne": "51", "haute marne": "52",
    "mayenne": "53", "meurthe et moselle": "54", "meuse": "55", "morbihan": "56", "moselle": "57",
    "nievre": "58", "nord": "59", "oise": "60", "orne": "61", "pas de calais": "62", "puy de dome": "63",
    "pyrenees atlantiques": "64", "hautes pyrenees": "65", "pyrenees orientales": "66", "bas rhin": "67",
    "haut rhin": "68", "rhone": "69", "haute saone": "70", "saone et loire": "71", "sarthe": "72",
    "savoie": "73", "haute savoie": "74", "paris": "75", "seine maritime": "76", "seine et marne": "77",
    "yvelines": "78", "deux sevres": "79", "somme": "80", "tarn": "81", "tarn et garonne": "82", "var": "83",
    "vaucluse": "84", "vendee": "85", "vienne": "86", "haute vienne": "87", "vosges": "88", "yonne": "89",
    "territoire de belfort": "90", "essonne": "91", "hauts de seine": "92", "seine saint denis": "93",
    "val de marne": "94", "val d oise": "95", "guadeloupe": "971", "martinique": "972", "guyane": "973",
    "la reunion": "974", "mayotte": "976",
}
REGION_KEYS = {}


def _admin_key(name: str) -> str:
    return norm(name).replace("-", " ").replace("'", " ").strip()


def region_from_admin_name(name: str | None) -> tuple[str | None, str | None]:
    """Reconnaît un nom de département ou de région → (code département ou None, région)."""
    if not name:
        return None, None
    key = _admin_key(name)
    if key in DEPT_NAMES:
        code = DEPT_NAMES[key]
        return code, DEPT_TO_REGION.get(code)
    for region in REGION_DEPTS:
        if _admin_key(region) == key:
            return None, region
    return None, None


def _city_key(name: str) -> str:
    return norm(name).replace("-", " ").replace("'", " ").replace("saint ", "st ")


@lru_cache(maxsize=1)
def _city_table(path: str | None = None) -> tuple[dict[str, dict], dict[str, str]]:
    table_path = Path(path) if path else resource("config/cities_fr.csv")
    by_key: dict[str, dict] = {}
    dept_region: dict[str, str] = {}
    with open(table_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_key[_city_key(row["city"])] = row
            dept_region.setdefault(row["dept_code"], row["region"])
    return by_key, dept_region


def normalize_location(raw: str | None, latitude: float | None = None, longitude: float | None = None) -> Location:
    by_key, dept_region = _city_table()
    if not raw or norm(raw) in ("france", "france entiere", "teletravail", "remote"):
        return Location(latitude=None, longitude=None)
    text = str(raw).strip()
    dept = None
    m = re.match(r"^\s*(\d{2,3}|2[AB])\s*-\s*(.+)$", text)
    if m:
        dept, text = m.group(1), m.group(2)
    parts = [p.strip() for p in text.split(",") if p.strip()]
    admin_region = None
    # Format Adzuna : « Ville, Département » ou « Département » / « Région » seul.
    for part in parts[1:] + (parts[:1] if len(parts) == 1 else []):
        code, reg = region_from_admin_name(part)
        if reg:
            dept = dept or code
            admin_region = reg
            break
    if not admin_region and parts:
        # Région en tête de chaîne (« Ile-de-France, France ») : seuls les noms de région sont acceptés ici,
        # pour ne pas confondre une commune et un département homonymes (Vienne, Nord…).
        code, reg = region_from_admin_name(parts[0])
        if reg and code is None:
            admin_region = reg
    if len(parts) == 1 and admin_region and not by_key.get(_city_key(parts[0])):
        # Le lieu n'est qu'un département ou une région : pas de ville précise.
        return Location(UNKNOWN, dept, admin_region, latitude, longitude)
    text = parts[0] if parts else ""
    if admin_region and not by_key.get(_city_key(text)) and region_from_admin_name(text)[1]:
        # Le premier élément est lui-même une région ou un département (« Ile-de-France, … »).
        return Location(UNKNOWN, dept, admin_region, latitude, longitude)
    if re.match(r"^\d{1,2}\s*(?:e|er|eme|ème)?[\s-]*(?:arrondissement|$)", norm(text)):
        # « 1er-Arrondissement, Lyon » → la commune est l'élément suivant (ni département ni région).
        text = next((q for q in parts[1:] if by_key.get(_city_key(q)) or not region_from_admin_name(q)[1]), text)
    text = re.sub(r"\s+\d{1,2}\s*(?:e|er|eme|ème)?\s*canton.*$", "", text, flags=re.I)  # « Reims 1er Canton »
    # Secteurs Adzuna (« Lille-Nord », « Aix-en-Provence Sud-Ouest ») → commune.
    text = re.sub(r"[\s-]+(?:nord|sud|est|ouest)(?:[\s-]+(?:nord|sud|est|ouest))*$", "", text, flags=re.I)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\b(cedex|arrondissement)\b.*$", "", text, flags=re.I)
    text = re.sub(r"\s+\d{1,2}\s*(?:e|er|eme|ème)?\s*$", "", text.strip(), flags=re.I)
    key = _city_key(text)
    row = by_key.get(key)
    if row:
        return Location(row["city"], row["dept_code"], row["region"], float(row["latitude"]), float(row["longitude"]))
    city = text.strip().title() or UNKNOWN
    region = admin_region or (DEPT_TO_REGION.get(dept, dept_region.get(dept, UNKNOWN)) if dept else UNKNOWN)
    return Location(city, dept, region, latitude, longitude)

import pytest

from jmi.clean import normalize as N


@pytest.mark.parametrize("text, expected_min, expected_max", [
    ("Annuel de 42000.0 Euros à 48000.0 Euros sur 12.0 mois", 42000, 48000),
    ("45K€ - 55K€", 45000, 55000),
    ("Entre 40 000 et 50 000 € brut/an", 40000, 50000),
    ("Mensuel de 3500 Euros sur 12 mois", 42000, 42000),
    ("Salaire : 45-55k€ selon profil", 45000, 55000),
    ("42 000 € à 48 000 € par an", 42000, 48000),
    ("3 200 € brut mensuel", 38400, 38400),
    ("Horaire de 15.00 Euros sur 12 mois", 15 * 1607, 15 * 1607),
    ("40k", 40000, 40000),
])
def test_parse_salary_text(text, expected_min, expected_max):
    s = N.parse_salary(text)
    assert s.annual_min == pytest.approx(expected_min)
    assert s.annual_max == pytest.approx(expected_max)


def test_parse_salary_daily_rate_is_kept_apart():
    s = N.parse_salary("550 € par jour")
    assert s.daily_rate == 550
    assert s.annual_mid is None


def test_parse_salary_structured_fields():
    s = N.parse_salary(min_raw=3000, max_raw=3500, unit_raw="MONTH")
    assert (s.annual_min, s.annual_max) == (36000, 42000)
    assert N.parse_salary(min_raw=60000, max_raw=70000, unit_raw="year").annual_mid == 65000


@pytest.mark.parametrize("text", [None, "", "A négocier", "Selon profil"])
def test_parse_salary_missing(text):
    assert N.parse_salary(text).annual_mid is None


@pytest.mark.parametrize("raw, city, region", [
    ("75 - PARIS 08", "Paris", "Île-de-France"),
    ("Paris 9e Arrondissement", "Paris", "Île-de-France"),
    ("69 - LYON 03", "Lyon", "Auvergne-Rhône-Alpes"),
    ("Nantes, Pays de la Loire", "Nantes", "Pays de la Loire"),
    ("92 - COURBEVOIE", "Courbevoie", "Île-de-France"),
    ("La Défense", "La Défense", "Île-de-France"),
    ("79 - Niort", "Niort", "Nouvelle-Aquitaine"),     # hors référentiel : région via le département
])
def test_normalize_location(raw, city, region):
    loc = N.normalize_location(raw)
    assert (loc.city, loc.region) == (city, region)


def test_location_unknown_and_coordinates():
    assert N.normalize_location("France").city == N.UNKNOWN
    paris = N.normalize_location("Paris")
    assert paris.latitude == pytest.approx(48.8566)


@pytest.mark.parametrize("title, years, contract, expected", [
    ("Stage - Data Analyst", None, None, "Stage / Alternance"),
    ("Data Scientist", None, "Alternance", "Stage / Alternance"),
    ("Senior Data Engineer", None, None, "Senior"),
    ("Lead Data Scientist", 2, None, "Senior"),        # le titre prime sur l'expérience
    ("Data Analyst Junior", None, None, "Junior"),
    ("Data Analyst", 1, None, "Junior"),
    ("Data Analyst", 4, None, "Confirmé"),
    ("Data Analyst", 8, None, "Senior"),
    ("Data Analyst", None, None, N.UNKNOWN),
    ("Data Manager", None, None, N.UNKNOWN),           # « manager » est un métier, pas une séniorité
])
def test_seniority(title, years, contract, expected):
    assert N.seniority_level(title, years, contract) == expected


@pytest.mark.parametrize("text, years", [
    ("2 An(s)", 2), ("3 ans d'expérience minimum", 3), ("Débutant accepté", 0), ("18 mois", 1.5), (None, None),
])
def test_experience_years(text, years):
    assert N.parse_experience_years(text) == years


@pytest.mark.parametrize("title, role", [
    ("Data Analyst H/F", "Data Analyst"),
    ("Analyste de données", "Data Analyst"),
    ("Data Scientist NLP", "Data Scientist"),
    ("Ingénieur de données", "Data Engineer"),
    ("Machine Learning Engineer", "Machine Learning Engineer"),
    ("MLOps Engineer", "Machine Learning Engineer"),
    ("Ingénieur IA générative", "AI / LLM Engineer"),
    ("Analytics Engineer", "Analytics Engineer / BI"),
    ("Consultant BI", "Analytics Engineer / BI"),
    ("Consultant Data & IA", "Consultant Data & IA"),
    ("Data Steward", "Data Manager / Gouvernance"),
    ("Data Quality Analyst", "Data Manager / Gouvernance"),
    ("Chef de projet", "Autre métier data"),
    ("Ingénieur intelligence artificielle F/H (CDI)", "AI / LLM Engineer"),
    ("Lead Tech IA F/H", "Chef de projet / Lead Data & IA"),
    ("Chef de projet intelligence artificielle / data H/F", "Chef de projet / Lead Data & IA"),
    ("Head of Data & IA Engineering - H/F", "Chef de projet / Lead Data & IA"),
    ("Data Analytics Backend Engineer Go / ClickHouse", "Data Engineer"),
    ("Chercheur appliqué intelligence artificielle", "Recherche / R&D IA"),
])
def test_role_family(title, role):
    assert N.role_family(title) == role


@pytest.mark.parametrize("text, policy", [
    ("Télétravail possible 2 jours par semaine.", "Hybride"),
    ("Mode de travail hybride", "Hybride"),
    ("Poste en full remote", "Full remote"),
    ("100% télétravail", "Full remote"),
    ("Poste basé sur site, pas de télétravail.", "Sur site"),
    ("Rien à signaler", N.UNKNOWN),
])
def test_remote_policy(text, policy):
    assert N.remote_policy(text) == policy


@pytest.mark.parametrize("raw, title, expected", [
    ("Contrat à durée indéterminée", "Data Analyst", "CDI"),
    ("CDD", "Data Analyst", "CDD"),
    ("Contrat à durée déterminée - 24 Mois", "Alternance - Data Scientist", "Alternance"),
    ("permanent full_time", "Data Engineer", "CDI"),
    ("Freelance", "Data Engineer", "Freelance"),
    ("MIS", "Data Analyst", "Intérim / temporaire"),
    (None, "Stagiaire Data", "Stage"),
])
def test_contract_type(raw, title, expected):
    assert N.contract_type(raw, title) == expected


@pytest.mark.parametrize("raw, company, expected", [
    ("Conseil en systèmes et logiciels informatiques", None, "Conseil / ESN"),
    ("Production et distribution d'électricité", None, "Énergie / Utilities"),
    ("Industrie pharmaceutique", None, "Santé / Pharma"),
    ("Activités des banques", None, "Banque / Assurance / Finance"),
    (None, "Banque Alpha", "Banque / Assurance / Finance"),
    (None, None, "Autre / Non précisé"),
])
def test_sector(raw, company, expected):
    assert N.sector_category(raw, company) == expected


@pytest.mark.parametrize("raw,city,region", [
    ("Lyon, Rhône", "Lyon", "Auvergne-Rhône-Alpes"),
    ("Nantes, Loire-Atlantique", "Nantes", "Pays de la Loire"),
    ("Île-de-France", "Non précisé", "Île-de-France"),
    ("Hauts-de-Seine", "Non précisé", "Île-de-France"),
    ("Ville Inconnue, Haute-Garonne", "Ville Inconnue", "Occitanie"),
])
def test_location_adzuna_format_ville_departement(raw, city, region):
    loc = N.normalize_location(raw)
    assert (loc.city, loc.region) == (city, region)


@pytest.mark.parametrize("title,ok", [
    ("Data Analyst H/F", True),
    ("Ingénieur intelligence artificielle", True),
    ("Consultant BI", True),
    ("Professeur d'intelligence artificielle - IA", False),
    ("Commercial indépendant BtoB - formation & intelligence artificielle", False),
    ("Contrôleur de gestion H/F", False),
    ("Responsable régional des relations hospitalières", False),
])
def test_is_data_ai_title(title, ok):
    assert N.is_data_ai_title(title) is ok


@pytest.mark.parametrize("raw,city,region", [
    ("1er-Arrondissement, Lyon, Rhône, Auvergne-Rhône-Alpes", "Lyon", "Auvergne-Rhône-Alpes"),
    ("1er Arrondissement, Paris", "Paris", "Île-de-France"),
    ("Reims 1er Canton, Reims, Marne, Grand-Est", "Reims", "Grand Est"),
])
def test_location_arrondissements_et_cantons(raw, city, region):
    loc = N.normalize_location(raw)
    assert (loc.city, loc.region) == (city, region)


@pytest.mark.parametrize("raw,city,region", [
    ("Ile-de-France, France", "Non précisé", "Île-de-France"),
    ("Lyon, France", "Lyon", "Auvergne-Rhône-Alpes"),
])
def test_location_region_en_tete(raw, city, region):
    loc = N.normalize_location(raw)
    assert (loc.city, loc.region) == (city, region)

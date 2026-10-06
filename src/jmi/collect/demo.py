"""Jeu de données de DÉMONSTRATION (synthétique, reproductible).

Il sert uniquement à faire tourner le pipeline et à construire le dashboard Tableau
avant d'avoir des identifiants API. Chaque offre porte `source="demo"` et `is_demo=True` ;
dès que des données réelles existent dans data/raw/, le nettoyage les utilise à la place
(mode `auto`), sans jamais les mélanger par défaut.

Les offres reproduisent volontairement le désordre des vraies sources (formats de
salaire, de lieu et d'expérience hétérogènes, doublons) pour exercer le nettoyage.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from jmi.collect.base import RawOffer

ROLES = {
    # rôle: (poids, titres possibles, salaire médian junior/confirmé/senior en k€, compétences {nom affiché: proba})
    "Data Analyst": (
        30, ["Data Analyst", "Analyste de données", "Data Analyst Marketing", "Business Data Analyst", "Analyste BI"],
        (37, 45, 55),
        {"SQL": .85, "Python": .6, "Excel": .55, "Tableau": .3, "Power BI": .5, "Looker Studio": .1,
         "statistiques": .35, "reporting et KPI": .6, "communication": .55, "anglais": .35, "dbt": .08,
         "BigQuery": .12, "Snowflake": .1, "pandas": .25, "VBA": .12, "Git": .15, "R": .12, "A/B testing": .1,
         "Agile": .2, "esprit d'analyse": .45, "autonomie": .4},
    ),
    "Data Scientist": (
        20, ["Data Scientist", "Data Scientist Junior", "Data Scientist NLP", "Data Scientist - Machine Learning",
             "Statisticien Data Scientist"],
        (42, 52, 65),
        {"Python": .95, "SQL": .7, "machine learning": .85, "scikit-learn": .45, "pandas": .5, "statistiques": .6,
         "deep learning": .35, "TensorFlow": .2, "PyTorch": .3, "NLP": .3, "R": .2, "Spark": .2, "AWS": .2,
         "Azure": .15, "GCP": .12, "Git": .4, "Docker": .2, "MLflow": .12, "LLM": .25, "IA générative": .2,
         "séries temporelles": .2, "communication": .45, "anglais": .5, "Tableau": .12, "Power BI": .1},
    ),
    "Data Engineer": (
        18, ["Data Engineer", "Ingénieur Data", "Data Engineer Cloud", "Big Data Engineer", "Ingénieur de données"],
        (44, 54, 67),
        {"Python": .85, "SQL": .85, "Spark": .55, "Airflow": .45, "dbt": .3, "Kafka": .3, "AWS": .4, "Azure": .35,
         "GCP": .25, "Snowflake": .25, "Databricks": .3, "Docker": .45, "Kubernetes": .25, "Git": .6, "CI/CD": .4,
         "Scala": .15, "Java": .12, "ETL": .5, "PostgreSQL": .3, "Terraform": .1, "Linux": .3, "Agile": .3,
         "anglais": .45, "modélisation de données": .3},
    ),
    "Analytics Engineer / BI": (
        10, ["Analytics Engineer", "Consultant BI", "Développeur BI", "BI Engineer", "Ingénieur décisionnel"],
        (40, 49, 60),
        {"SQL": .95, "dbt": .45, "Tableau": .35, "Power BI": .5, "Looker": .2, "Qlik": .12, "Snowflake": .3,
         "BigQuery": .25, "Python": .4, "modélisation de données": .55, "ETL": .4, "Talend": .12, "Git": .35,
         "data warehouse": .35, "reporting et KPI": .5, "communication": .35, "relation client": .25},
    ),
    "Machine Learning Engineer": (
        8, ["Machine Learning Engineer", "MLOps Engineer", "Ingénieur Machine Learning", "ML Engineer"],
        (46, 57, 72),
        {"Python": .95, "machine learning": .8, "Docker": .6, "Kubernetes": .45, "MLflow": .35, "AWS": .4,
         "GCP": .3, "Azure": .3, "PyTorch": .45, "TensorFlow": .3, "CI/CD": .5, "Git": .7, "API REST": .45,
         "Spark": .2, "Linux": .35, "LLM": .3, "deep learning": .4, "anglais": .55},
    ),
    "AI / LLM Engineer": (
        6, ["AI Engineer", "Ingénieur IA générative", "LLM Engineer", "Développeur IA", "Ingénieur NLP / LLM"],
        (47, 60, 78),
        {"Python": .95, "LLM": .9, "IA générative": .7, "RAG": .55, "LangChain": .45, "Hugging Face": .35,
         "NLP": .5, "PyTorch": .35, "API REST": .5, "Docker": .45, "Azure": .35, "AWS": .3, "GCP": .25,
         "Git": .6, "deep learning": .35, "anglais": .5, "Agile": .2},
    ),
    "Consultant Data & IA": (
        6, ["Consultant Data & IA", "Consultant Data", "Consultant Data Analyst", "Consultant IA", "Consultant Junior Data"],
        (39, 49, 64),
        {"SQL": .7, "Python": .6, "Power BI": .4, "Tableau": .3, "relation client": .7, "communication": .75,
         "gestion de projet": .5, "Agile": .35, "anglais": .55, "machine learning": .3, "IA générative": .3,
         "data gouvernance": .2, "Azure": .2, "AWS": .15, "Excel": .3, "esprit d'analyse": .4},
    ),
    "Data Manager / Gouvernance": (
        2, ["Data Steward", "Data Manager", "Chargé de gouvernance des données", "Data Quality Analyst"],
        (40, 50, 63),
        {"data gouvernance": .85, "qualité des données": .6, "RGPD": .55, "SQL": .6, "Excel": .4,
         "gestion de projet": .45, "communication": .55, "Collibra": .15, "Power BI": .25, "Tableau": .15},
    ),
}

CITIES = [  # (libellé brut tel qu'une source pourrait l'écrire, poids)
    ("75 - PARIS 08", 14), ("Paris", 10), ("Paris 9e Arrondissement", 6), ("75 - Paris 15e", 4),
    ("92 - Puteaux", 3), ("La Défense", 4), ("92 - COURBEVOIE", 3), ("Boulogne-Billancourt", 3),
    ("Issy-les-Moulineaux, Île-de-France", 2), ("Levallois-Perret", 2), ("Saint-Denis", 2), ("Massy", 1),
    ("Lyon 3e Arrondissement", 5), ("69 - LYON", 4), ("Villeurbanne", 1), ("Toulouse", 5), ("31 - TOULOUSE", 2),
    ("Nantes, Pays de la Loire", 4), ("Bordeaux", 4), ("Lille", 4), ("59 - LILLE", 1), ("Marseille", 2),
    ("Aix-en-Provence", 2), ("Sophia Antipolis", 2), ("Nice", 1), ("Montpellier", 3), ("Rennes", 3),
    ("Strasbourg", 2), ("Grenoble", 2), ("Rouen", 1), ("Tours", 1), ("Dijon", 1), ("Clermont-Ferrand", 1),
    ("Niort", 1), ("France", 2),
]

SECTORS = {
    # secteur brut: (poids, préfixes d'entreprises fictives)
    "Conseil en systèmes et logiciels informatiques": (24, ["ESN", "Cabinet Conseil", "DataConsult"]),
    "Activités des banques et assurances": (14, ["Banque", "Assurances", "Mutuelle"]),
    "Édition de logiciels / SaaS": (12, ["SaaS", "Startup", "Scale-up"]),
    "Commerce de détail et e-commerce": (9, ["Retail", "E-commerce", "Distribution"]),
    "Production et distribution d'électricité et de gaz": (7, ["Énergie", "Réseau Électrique"]),
    "Industrie pharmaceutique et santé": (7, ["Pharma", "Santé", "MedTech"]),
    "Industrie manufacturière et aéronautique": (8, ["Industrie", "Aéro", "Automobile"]),
    "Télécommunications et médias": (6, ["Télécom", "Média"]),
    "Transports et logistique": (5, ["Logistique", "Transport"]),
    "Administration publique": (5, ["Collectivité", "Établissement Public"]),
    "Agence de recrutement / intérim": (3, ["Cabinet de recrutement"]),
}

GREEK = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Kappa", "Lambda", "Sigma", "Omega", "Nova", "Orion"]

SENIORITY = [("Stage / Alternance", 12), ("Junior", 30), ("Confirmé", 36), ("Senior", 22)]

REMOTE_TEXTS = [
    ("Télétravail possible 2 jours par semaine.", 34), ("Mode de travail hybride (3 jours sur site).", 14),
    ("Poste en full remote, déplacements ponctuels.", 7), ("Télétravail partiel selon la politique interne.", 10),
    ("Poste basé sur site, pas de télétravail.", 9), ("", 26),
]

CONTRACTS = [("CDI", 66), ("CDD", 8), ("Stage", 7), ("Alternance", 6), ("Freelance", 9), ("Intérim", 4)]


def _weighted(rng: random.Random, items):
    values, weights = zip(*items)
    return rng.choices(values, weights=weights, k=1)[0]


def _salary_text(rng: random.Random, low: int, high: int) -> tuple[str | None, float | None, float | None, str | None]:
    """Renvoie (texte, min, max, unité) sous un des formats rencontrés sur les vraies sources."""
    fmt = rng.randint(0, 6)
    if fmt == 0:
        return f"Annuel de {low * 1000:.1f} Euros à {high * 1000:.1f} Euros sur 12.0 mois", None, None, None
    if fmt == 1:
        return f"{low}K€ - {high}K€", None, None, None
    if fmt == 2:
        return f"Entre {low:,} 000 et {high:,} 000 € brut/an".replace(",", " "), None, None, None
    if fmt == 3:
        monthly = round(low * 1000 / 12, -1)
        return f"Mensuel de {monthly:.0f} Euros sur 12 mois", None, None, None
    if fmt == 4:
        return None, float(low * 1000), float(high * 1000), "YEAR"
    if fmt == 5:
        return f"{low} 000 € à {high} 000 € par an", None, None, None
    return f"Salaire : {low}-{high}k€ selon profil", None, None, None


def generate_demo_offers(n: int = 1200, seed: int = 42, end: date | None = None) -> list[RawOffer]:
    rng = random.Random(seed)
    end = end or date(2026, 9, 30)
    roles = [(name, spec[0]) for name, spec in ROLES.items()]
    offers: list[RawOffer] = []

    for i in range(n):
        role = _weighted(rng, roles)
        _, titles, sal_med, skills = ROLES[role]
        seniority = _weighted(rng, SENIORITY)
        contract = _weighted(rng, CONTRACTS)
        if seniority == "Stage / Alternance":
            contract = rng.choice(["Stage", "Alternance"])
        elif contract in ("Stage", "Alternance"):
            contract = "CDI"

        title = rng.choice(titles)
        if seniority == "Junior" and rng.random() < .5:
            title += " Junior" if "Junior" not in title else ""
        elif seniority == "Senior" and rng.random() < .6:
            title = rng.choice(["Senior ", "Lead ", ""]) + title
        elif seniority == "Stage / Alternance":
            title = rng.choice(["Stage - ", "Alternance - ", "Stagiaire "]) + title

        sector = _weighted(rng, [(s, v[0]) for s, v in SECTORS.items()])
        company = f"{rng.choice(SECTORS[sector][1])} {rng.choice(GREEK)}"
        location = _weighted(rng, CITIES)
        remote_txt = _weighted(rng, REMOTE_TEXTS)

        years = {"Stage / Alternance": 0, "Junior": rng.randint(0, 2), "Confirmé": rng.randint(3, 5),
                 "Senior": rng.randint(6, 10)}[seniority]
        exp_fmt = rng.randint(0, 3)
        experience = [f"{years} An(s)", f"{years} ans d'expérience minimum", "Débutant accepté" if years == 0 else
                      f"Expérience de {years} ans souhaitée", None][exp_fmt if years else rng.choice([2, 3])]

        picked = [s for s, p in skills.items() if rng.random() < p]
        if len(picked) < 3:
            picked += rng.sample(list(skills), k=3)
        picked = list(dict.fromkeys(picked))

        desc = [
            f"{company} ({sector.lower()}) recrute un(e) {title}.",
            rng.choice([
                "Vous construirez des tableaux de bord pour les équipes métier et automatiserez le reporting.",
                "Vous participerez à la conception de modèles et à leur mise en production.",
                "Vous accompagnerez nos clients dans leurs projets de transformation data.",
                "Vous fiabiliserez les pipelines de données et la qualité des indicateurs.",
            ]),
            "Compétences recherchées : " + ", ".join(picked) + ".",
            remote_txt,
        ]
        if experience and rng.random() < .5:
            desc.append(f"Profil : {experience}.")

        salary_raw = sal_min = sal_max = unit = None
        if contract == "Freelance":
            if rng.random() < .6:
                salary_raw = f"{rng.randint(40, 75) * 10} € par jour"
        elif seniority != "Stage / Alternance" and rng.random() < .52:
            base = {"Junior": sal_med[0], "Confirmé": sal_med[1], "Senior": sal_med[2]}[seniority]
            if "Paris" in location or location.startswith(("75", "92")) or location in ("La Défense",):
                base *= 1.08
            mid = rng.lognormvariate(0, .1) * base
            low, high = int(mid * .93), int(mid * 1.08) + 1
            salary_raw, sal_min, sal_max, unit = _salary_text(rng, low, high)
        elif seniority == "Stage / Alternance" and rng.random() < .4:
            salary_raw = f"Mensuel de {rng.randint(110, 160) * 10} Euros sur 12 mois"

        published = end - timedelta(days=int(rng.triangular(0, 180, 20)))
        offers.append(RawOffer(
            source="demo", source_id=f"DEMO-{i:05d}", title=title, description=" ".join(d for d in desc if d),
            company=company, location_raw=location, published_at=published.isoformat(),
            contract_raw=contract, salary_raw=salary_raw, salary_min_raw=sal_min, salary_max_raw=sal_max,
            salary_unit_raw=unit, experience_raw=experience, sector_raw=sector,
            search_keyword=role.lower(), is_demo=True,
        ))

    # ~3 % de republications : même offre captée par deux mots-clés (testé par la déduplication)
    for original in rng.sample(offers, k=max(1, n // 33)):
        dup = RawOffer(**{**original.to_dict(), "source_id": original.source_id + "-R", "search_keyword": "data"})
        offers.append(dup)
    return offers

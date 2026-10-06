# Job Market Intelligence — Data & IA en France

[![tests](https://github.com/HodaFede/job-market-intelligence/actions/workflows/tests.yml/badge.svg)](https://github.com/HodaFede/job-market-intelligence/actions/workflows/tests.yml)

Que demandent vraiment les recruteurs Data et IA ? Ce projet collecte des offres d'emploi, les nettoie, en extrait les compétences par NLP, les modélise en SQL et les restitue dans un dashboard **Tableau Public**, avec un rapport d'analyse et des recommandations.

**Dashboard Tableau Public** : _lien à ajouter après publication_ · **Rapport** : [`reports/insights.md`](reports/insights.md)

> Les exports actuellement versionnés proviennent du **jeu de démonstration synthétique** (colonne `est_demo = 1`), qui sert à faire tourner le pipeline sans clé d'API. Dès qu'une collecte réelle est lancée, le pipeline l'utilise à la place, sans jamais mélanger les deux par défaut.

<!-- Après publication : ajouter une capture du dashboard
![Dashboard](docs/img/dashboard_overview.png)
-->

## Ce que montre le projet

| Compétence | Où la voir |
|---|---|
| Web scraping & API | `src/jmi/collect/` : API France Travail (OAuth2, pagination), API Adzuna, scraper JSON-LD schema.org qui respecte robots.txt |
| Nettoyage (pandas) | `src/jmi/clean/` : salaires multi-formats → annuel brut, villes → région + coordonnées, séniorité, métier, télétravail, déduplication multi-sources |
| NLP | `src/jmi/nlp/skills.py` : extraction de 75 compétences par regex (faux positifs du français gérés), TF-IDF par métier |
| SQL | `sql/` : modèle relationnel SQLite, 14 vues analytiques (CTE, fonctions de fenêtrage, médianes et quartiles, co-occurrences et lift) |
| Dataviz | `exports/tableau/` + [guide Tableau Public](docs/tableau_guide.md) : 4 dashboards et une story |
| Exploration (EDA) | [`notebooks/01_exploration_qualite.ipynb`](notebooks/01_exploration_qualite.ipynb) : contrôle qualité, distributions, heatmaps |
| Analyse métier | [`reports/insights.md`](reports/insights.md), [`docs/business_analysis.md`](docs/business_analysis.md) |
| Qualité & automatisation | 100+ tests pytest lancés par GitHub Actions à chaque push, collecte automatique deux fois par semaine |

## Pipeline

```
Collecte (APIs + scraping)  →  data/raw/*.jsonl
      ↓
Nettoyage & normalisation   →  data/processed/offers_clean.csv
      ↓
NLP compétences + TF-IDF    →  data/processed/offer_skills.csv
      ↓
SQLite + vues SQL           →  data/warehouse/jobs.db
      ↓
Exports CSV                 →  exports/tableau/*.csv  →  Tableau Public
      ↓
Rapport d'analyse           →  reports/insights.md
```

Détails : [docs/architecture.md](docs/architecture.md).

## Démarrage rapide (Mac)

Prérequis : Python 3.10+ (`python3 --version`), Git, et [Tableau Public](https://public.tableau.com) pour la visualisation.

```bash
git clone https://github.com/HodaFede/job-market-intelligence.git
cd job-market-intelligence
make install                 # crée .venv et installe les dépendances
source .venv/bin/activate

# Option A — tout de suite, avec le jeu de démonstration
python -m jmi demo
python -m jmi run

# Option B — données réelles (identifiants gratuits, voir docs/data_collection.md)
cp .env.example .env         # renseigner France Travail et/ou Adzuna
python -m jmi collect
python -m jmi run

pytest                       # tests

make install-dev             # Jupyter + matplotlib pour le notebook
make notebook                # réexécute notebooks/01_exploration_qualite.ipynb
```

Sans `make` : `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -e .`

Ensuite, ouvre `exports/tableau/offres.csv` dans Tableau Public en suivant le [guide pas à pas](docs/tableau_guide.md).

## Automatisation

- `.github/workflows/tests.yml` : tests à chaque push et pull request (Python 3.10 et 3.12).
- `.github/workflows/weekly_collect.yml` : collecte réelle le lundi et le jeudi, pipeline, puis commit des exports Tableau et du rapport. À activer en ajoutant les clés d'API dans les secrets du dépôt (voir [docs/data_collection.md](docs/data_collection.md)).

## Indicateurs

Nombre d'offres, salaire médian et moyen, part des offres avec salaire, répartition par ville, région et secteur, compétences et technologies par métier, séniorité, télétravail, contrats, tendance mensuelle, prime salariale associée aux compétences, associations de compétences. Définitions et formules : [docs/kpis.md](docs/kpis.md).

## Exports pour Tableau

| Fichier | Contenu |
|---|---|
| `offres.csv` | une ligne par offre (métier, séniorité, ville, coordonnées, salaire, télétravail, contrat, date) |
| `offres_competences.csv` | compétences détectées par offre, à relier sur `id_offre` |
| `kpi_globaux.csv` | KPIs d'en-tête |
| `salaires_metier_seniorite.csv` | médiane, quartiles et fiabilité par métier × séniorité |
| `competences_par_metier.csv` | % des offres qui citent chaque compétence, par métier |
| `prime_salariale_competences.csv` | salaire médian avec / sans chaque compétence |
| `paires_competences.csv` | co-occurrences et lift |
| `villes.csv`, `secteurs.csv` | synthèses géographique et sectorielle |
| `tendance_mensuelle.csv`, `teletravail_metier.csv`, `seniorite_metier.csv`, `contrats.csv` | répartitions |
| `termes_tfidf.csv` | vocabulaire caractéristique de chaque métier |

Colonnes détaillées : [docs/data_dictionary.md](docs/data_dictionary.md).

## Structure

```
.github/         workflows GitHub Actions (tests, collecte automatique)
config/          paramètres, référentiel de compétences, référentiel de villes, URLs à scraper
data/            brut, nettoyé, base SQLite (non versionné)
docs/            architecture, collecte, KPIs, NLP, guide Tableau, analyse métier
exports/tableau/ CSV pour Tableau Public
notebooks/       exploration et contrôle qualité
reports/         rapport d'insights généré
sql/             schéma + vues analytiques
src/jmi/         code Python (collect, clean, nlp, warehouse, export, analysis)
tableau/         classeur Tableau (.twbx)
tests/           tests pytest + fixtures
```

## Choix et limites

- NLP volontairement explicable (dictionnaire + regex + TF-IDF) : chaque chiffre peut être retracé jusqu'à la règle qui l'a produit.
- Les salaires ne portent que sur les offres qui les affichent ; stages, alternances et TJM freelance sont traités à part.
- Une offre publiée n'est pas une embauche ; la séniorité et le télétravail sont déduits du texte.
- Collecte respectueuse : API officielles en priorité, robots.txt et délais pour le scraping, aucune donnée personnelle, descriptions non republiées.

## Documentation

- [Architecture](docs/architecture.md)
- [Collecte des données](docs/data_collection.md)
- [Dictionnaire des données](docs/data_dictionary.md)
- [Indicateurs](docs/kpis.md)
- [NLP compétences](docs/nlp_skills.md)
- [Guide Tableau Public](docs/tableau_guide.md)
- [Analyse métier](docs/business_analysis.md)

## Auteure

**Hoda Fede Ndinge** — Data Analyst, Mastère Data & IA (IPSSI Paris). GitHub : [HodaFede](https://github.com/HodaFede)

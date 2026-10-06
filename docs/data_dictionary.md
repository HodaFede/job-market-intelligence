# Dictionnaire des données

## `exports/tableau/offres.csv` — une ligne par offre

| Colonne | Type | Description | Valeurs / exemple |
|---|---|---|---|
| id_offre | texte | identifiant unique `source:id_source` | `france_travail:198XKQP` |
| source | texte | origine | france_travail, adzuna, jsonld_scraper, demo |
| est_demo | 0/1 | 1 = ligne synthétique du jeu de démonstration | |
| intitule | texte | intitulé tel que publié | « Data Analyst H/F » |
| metier | texte | famille de métier déduite de l'intitulé | Data Analyst, Data Scientist, Data Engineer, Analytics Engineer / BI, Machine Learning Engineer, AI / LLM Engineer, Consultant Data & IA, Data Manager / Gouvernance, Autre métier data |
| seniorite | texte | niveau déduit de l'intitulé, sinon des années d'expérience (≤ 2 Junior, 3–5 Confirmé, ≥ 6 Senior) | Stage / Alternance, Junior, Confirmé, Senior, Non précisé |
| annees_experience | nombre | années demandées si mentionnées | 2 |
| type_contrat | texte | | CDI, CDD, Stage, Alternance, Freelance, Intérim / temporaire, Non précisé |
| entreprise | texte | | |
| secteur | texte | secteur regroupé (11 catégories) | Conseil / ESN, Banque / Assurance / Finance… |
| ville | texte | ville normalisée (arrondissements fusionnés) | Paris |
| departement | texte | code département | 92 |
| region | texte | région administrative | Île-de-France |
| pays | texte | constante pour le rôle géographique Tableau | France |
| latitude, longitude | décimal | coordonnées de la ville (référentiel ou source) | |
| teletravail | texte | politique déduite du texte | Hybride, Full remote, Sur site, Non précisé |
| teletravail_possible | 0/1 | 1 si Hybride ou Full remote | |
| salaire_min, salaire_max | décimal | fourchette annuelle brute en € | |
| salaire_annuel | décimal | milieu de fourchette, vide si non affiché / stage / aberrant | 50000 |
| salaire_affiche | 0/1 | 1 si salaire_annuel est renseigné | |
| tjm | décimal | taux journalier (freelance) | 550 |
| est_cdi | 0/1 | | |
| date_publication | date ISO | | 2026-09-12 |
| mois_publication | date ISO | premier jour du mois | 2026-09-01 |
| nb_competences | entier | nombre de compétences détectées | 8 |
| url | texte | lien vers l'offre d'origine | |

## `offres_competences.csv` — une ligne par compétence détectée dans une offre

| Colonne | Description |
|---|---|
| id_offre | clé vers `offres.csv` |
| competence | libellé canonique (`config/skills_dictionary.yaml`) |
| categorie_competence | Langages, Bases de données, BI & Dataviz, Data engineering, Cloud, MLOps & DevOps, ML & IA, IA générative, Méthodes & gouvernance, Soft skills |
| type_competence | Technologie / Compétence / méthode |

## Fichiers agrégés

| Fichier | Colonnes |
|---|---|
| `kpi_globaux.csv` | nb_offres, nb_entreprises, nb_villes, salaire_moyen, salaire_median, pct_offres_avec_salaire, pct_teletravail, pct_cdi, pct_offres_junior, nb_competences_moyen, date_min, date_max, jeu_de_donnees |
| `salaires_metier_seniorite.csv` | metier, seniorite, nb_offres_avec_salaire, salaire_moyen, salaire_median, salaire_q1, salaire_q3, salaire_min, salaire_max, fiabilite |
| `villes.csv` | ville, region, pays, latitude, longitude, nb_offres, part_offres_pct, salaire_median, nb_offres_avec_salaire, pct_teletravail |
| `secteurs.csv` | secteur, nb_offres, part_offres_pct, salaire_median, pct_teletravail, pct_cdi |
| `competences_par_metier.csv` | metier (dont « Tous métiers »), competence, categorie_competence, type_competence, nb_offres, nb_offres_metier, part_offres_pct, rang |
| `prime_salariale_competences.csv` | competence, categorie_competence, nb_offres_avec, nb_offres_sans, salaire_median_avec, salaire_median_sans, prime_eur, prime_pct |
| `paires_competences.csv` | competence_a, competence_b, nb_offres_communes, pct_offres_a_avec_b, lift |
| `tendance_mensuelle.csv` | mois, metier, nb_offres, salaire_moyen, nb_offres_teletravail |
| `teletravail_metier.csv` | metier, teletravail, nb_offres, part_offres_pct |
| `seniorite_metier.csv` | metier, seniorite, ordre_seniorite, nb_offres, part_offres_pct |
| `contrats.csv` | type_contrat, metier, nb_offres, tjm_moyen |
| `termes_tfidf.csv` | metier, terme, score_tfidf, rang |

## Fichiers intermédiaires (non versionnés)

- `data/raw/<source>/<source>_AAAAMMJJ_HHMMSS.jsonl` : offres brutes au format `RawOffer` (`src/jmi/collect/base.py`).
- `data/processed/offers_clean.csv` : table propre complète, description incluse.
- `data/processed/offer_skills.csv` : compétences détectées.
- `data/warehouse/jobs.db` : base SQLite (tables `offers`, `skills`, `offer_skills`, `top_terms`, `pipeline_runs` + vues `v_*`).

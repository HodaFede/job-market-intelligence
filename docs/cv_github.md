# Valoriser le projet (CV, GitHub, entretien)

Les chiffres entre crochets sont à remplacer par ceux de **ta collecte réelle** (`reports/insights.md`, `exports/tableau/kpi_globaux.csv`). Ne reprends pas ceux du jeu de démonstration.

## Sur le CV

**Job Market Intelligence — Analyse du marché de l'emploi Data & IA en France** · Python, SQL, NLP, Tableau Public · [lien GitHub] · [lien Tableau Public]

Version courte (3 lignes) :

- Pipeline Python de bout en bout : collecte de [X] offres (API France Travail, Adzuna, web scraping JSON-LD), nettoyage et déduplication avec pandas, modélisation SQLite.
- Extraction de compétences par NLP (regex sur un référentiel de 75 compétences, TF-IDF par métier) et analyses SQL : médianes salariales, co-occurrences et lift entre compétences.
- Dashboard Tableau Public (4 vues + story) et recommandations pour candidats, recruteurs et organismes de formation ; 100+ tests pytest.

Version « consultant » (orientée valeur) :

- Construit un outil de veille du marché Data/IA qui identifie les compétences, salaires et conditions de travail par métier, à partir de [X] offres réelles.
- Transformé du texte libre en indicateurs fiables : normalisation de formats de salaire hétérogènes (annuel, mensuel, horaire, « 45K€ », TJM), géocodage des villes, classification des métiers et de la séniorité.
- Restitué les résultats dans un dashboard Tableau Public et un rapport d'insights avec recommandations argumentées.

Compétences à lister : Python (pandas, requests, BeautifulSoup, scikit-learn), SQL (SQLite, fonctions de fenêtrage, CTE), web scraping, NLP (regex, TF-IDF), Tableau Public, Git/GitHub, tests (pytest).

## Sur GitHub

- **Nom du dépôt** : `job-market-intelligence`.
- **Description** (champ About) : « Pipeline Python/SQL/NLP qui analyse les offres d'emploi Data & IA en France — dashboard Tableau Public ».
- **Topics** : `data-analysis`, `web-scraping`, `nlp`, `sql`, `tableau`, `pandas`, `python`, `job-market`, `france`.
- **Épingle** le dépôt sur ton profil, avec une capture du dashboard dans le README (`docs/img/`).
- **Historique Git lisible** : des commits par étape (`feat(collect): API France Travail`, `feat(nlp): extraction compétences`, `docs: guide Tableau`…) montrent ta démarche mieux qu'un seul gros commit.
- Ajoute le lien du dashboard Tableau Public en haut du README et dans le champ *Website* du dépôt.
- Mets à jour les exports après une vraie collecte, puis commit : le dépôt montre alors des chiffres réels.

## Sur Tableau Public

- Titre clair, description avec lien GitHub, dashboard d'accueil = la Story.
- Mets le classeur en avant (*Featured*) sur ton profil.

## Pitch d'entretien (2 minutes)

1. **Le problème** : en cherchant un poste, je voulais objectiver ce que demandent les recruteurs Data/IA au lieu de me fier à quelques annonces.
2. **La démarche** : trois sources réelles, un format commun, un nettoyage centralisé et testé, du NLP explicable plutôt qu'une boîte noire, des agrégats en SQL, une restitution Tableau.
3. **Une difficulté** : « tableau de bord » détecté comme l'outil Tableau, « R&D » comme le langage R ; j'ai traité ces faux positifs avec des expressions régulières et des tests dédiés.
4. **Un résultat** : [ton insight le plus marquant, par ex. « Python et SQL sont demandés dans X % des offres ; Spark et Airflow vont ensemble avec un lift de Y »].
5. **Ce que je ferais ensuite** : collecte hebdomadaire automatisée, prime salariale à métier et séniorité égaux.

## Questions probables et éléments de réponse

- *Pourquoi la médiane ?* Distribution asymétrique, la moyenne est tirée par quelques offres senior.
- *Comment évites-tu les doublons ?* Identifiant source, puis clé intitulé + entreprise + ville normalisés ; je garde la publication la plus ancienne.
- *Ton NLP est-il fiable ?* Référentiel explicite, cas limites testés, TF-IDF pour repérer les oublis, contrôle manuel sur un échantillon.
- *Pourquoi Tableau Public ?* Gratuit sur Mac, partage en ligne immédiat pour les recruteurs ; les concepts (modèle, mesures, filtres, storytelling) se transposent à d'autres outils de BI.
- *Limites ?* Offres ≠ embauches, salaires affichés seulement, séniorité déduite du texte.

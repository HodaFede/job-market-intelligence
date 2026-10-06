# Collecte des données

Trois sources réelles, complémentaires, plus un jeu de démonstration pour démarrer.

| Source | Type | Accès | Points forts | Limites |
|---|---|---|---|---|
| France Travail — Offres d'emploi v2 | API officielle | gratuit, inscription | volume, couverture nationale, secteur d'activité, expérience, salaire souvent renseigné | descriptions parfois courtes, peu de startups |
| Adzuna | API agrégateur | gratuit (quota) | agrège de nombreux job boards, salaires structurés | description tronquée à 500 caractères (compétences sous-détectées), salaires parfois estimés (exclus) |
| Pages carrières (JSON-LD) | web scraping | liste d'URL à fournir | description complète, données publiées par l'employeur | à alimenter manuellement, dépend des sites |
| Démo | synthétique | `python -m jmi demo` | pipeline et dashboard utilisables tout de suite | ne décrit pas le marché réel |

## Obtenir les identifiants (une fois)

**France Travail**

1. Crée un compte sur [francetravail.io](https://francetravail.io) (espace développeur).
2. Crée une application, puis abonne-la à l'API **« Offres d'emploi v2 »**.
3. Copie l'identifiant client et la clé secrète dans `.env` (`FRANCE_TRAVAIL_CLIENT_ID`, `FRANCE_TRAVAIL_CLIENT_SECRET`).

**Adzuna**

1. Inscris-toi sur [developer.adzuna.com](https://developer.adzuna.com).
2. Récupère `app_id` et `app_key`, et renseigne `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` dans `.env`.

```bash
cp .env.example .env
open -e .env        # édite le fichier sur Mac
```

Une source sans identifiants est simplement ignorée, avec un message dans la console.

## Lancer la collecte

```bash
python -m jmi collect                       # toutes les sources configurées
python -m jmi collect --source france_travail
python -m jmi run                           # nettoyage → exports Tableau
```

Les mots-clés et volumes se règlent dans `config/settings.yaml` (`keywords`, `collect.*`). Chaque exécution crée un nouveau fichier dans `data/raw/<source>/` ; relancer la collecte chaque semaine construit un historique, et la déduplication évite de compter deux fois une offre toujours en ligne.

## Collecte automatique (GitHub Actions)

Le workflow `.github/workflows/weekly_collect.yml` relance la collecte le lundi et le jeudi à 6h UTC, exécute le pipeline sur les données réelles uniquement, puis commite `exports/tableau/` et `reports/insights.md`. Le dépôt montre ainsi des chiffres à jour sans intervention.

Pour l'activer :

1. Sur GitHub : **Settings › Secrets and variables › Actions › New repository secret**, et crée `FRANCE_TRAVAIL_CLIENT_ID`, `FRANCE_TRAVAIL_CLIENT_SECRET`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`.
2. Onglet **Actions › weekly-collect › Run workflow** pour un premier lancement manuel, et vérifie le résultat.

Les fichiers bruts restent hors du dépôt : ils sont conservés d'une exécution à l'autre dans le cache GitHub Actions. Ce cache est purgé après 7 jours sans accès ; avec deux passages par semaine il reste vivant, mais l'historique de référence reste celui de ton Mac. Si l'API refuse les requêtes venant des serveurs GitHub, garde la collecte en local.

## Le scraper JSON-LD

La plupart des pages d'offres embarquent un bloc `<script type="application/ld+json">` de type [schema.org/JobPosting](https://schema.org/JobPosting) destiné à Google Jobs. Le scraper (`src/jmi/collect/jsonld_scraper.py`) :

1. lit les URL de `config/scrape_urls.txt` ;
2. vérifie `robots.txt` pour chaque domaine et saute les pages interdites ;
3. attend 2 secondes entre deux requêtes (`collect.jsonld.delay_seconds`) ;
4. extrait titre, description (HTML nettoyé), entreprise, lieu, salaire structuré, type de contrat, télétravail (`jobLocationType = TELECOMMUTE`).

C'est plus robuste qu'un parsing de HTML visuel, qui casse à chaque refonte du site.

## Cadre légal et éthique

- Privilégier les API officielles ; ne scraper que des pages publiques, en respectant `robots.txt` et les conditions d'utilisation de chaque site. Les job boards qui interdisent l'extraction automatisée dans leurs CGU ne doivent pas être ajoutés à `scrape_urls.txt`.
- Volume raisonnable et délais entre requêtes.
- Aucune donnée personnelle de candidat n'est collectée. Les noms de recruteurs éventuellement présents dans les descriptions ne sont pas exploités, et les descriptions ne sont pas republiées : seuls des agrégats et des champs structurés sont exportés vers Tableau Public.
- `data/raw` et `data/processed` ne sont pas versionnés sur GitHub.

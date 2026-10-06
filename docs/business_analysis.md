# Analyse métier

Le projet répond à une question simple, posée par trois publics différents : **que demande réellement le marché de l'emploi Data / IA en France ?**

## Questions par public

| Public | Questions | Où trouver la réponse |
|---|---|---|
| Candidat junior | Quelles compétences apprendre en priorité ? Quels métiers recrutent des juniors ? Quel salaire viser ? | D3 Compétences, D2 Salaires, `seniorite_metier.csv` |
| Recruteur / manager | Mon offre est-elle dans le marché (salaire, télétravail) ? Quelles compétences sont rares ? | D2, D4, `prime_salariale_competences.csv` |
| Organisme de formation / école | Quelles briques ajouter aux parcours ? Quelles stacks vont ensemble ? | D3, `paires_competences.csv`, `termes_tfidf.csv` |

## Grille de lecture

1. **Volume** : où se concentre la demande (métiers, villes, secteurs) et comment elle évolue mois par mois.
2. **Exigences** : le socle commun (présent quel que soit le métier), puis ce qui différencie chaque métier.
3. **Valeur** : salaires médians par métier et séniorité, en regardant la fiabilité de chaque médiane.
4. **Conditions** : contrat, télétravail, part d'offres accessibles aux juniors.
5. **Signaux faibles** : termes TF-IDF émergents et associations à fort lift (IA générative, MLOps, gouvernance).

## Rapport généré

`reports/insights.md` est recalculé à chaque `python -m jmi run`. Il contient les chiffres clés, le classement des compétences, les stacks par métier, les associations fortes, la géographie et une série de recommandations construites à partir des données (pas de chiffres écrits à la main). Il signale en tête s'il s'appuie sur le jeu de démonstration.

## Recommandations : comment elles sont construites

Chaque recommandation du rapport s'appuie sur un indicateur précis, ce qui permet de la défendre en entretien :

| Recommandation | Indicateur |
|---|---|
| Prioriser le socle technique | top 3 des technologies, tous métiers (`competences_par_metier`, Tous métiers) |
| Choix de l'outil de BI | part des offres qui citent chaque outil de BI |
| Métiers à cibler en junior | part Junior + Stage/Alternance par métier (`seniorite_metier`) |
| Soft skills à mettre en avant | top soft skills (`competences_par_metier`, catégorie Soft skills) |
| Afficher un salaire (recruteurs) | `pct_offres_avec_salaire` |
| Recruter en régions avec télétravail | médiane Île-de-France vs régions, % télétravail hors IDF |
| Cloud et IA générative dans les formations | part des offres qui citent AWS/Azure/GCP ou LLM/RAG, par métier |

## Limites à énoncer

- Les offres publiées ne sont pas les embauches : certaines restent en ligne longtemps, d'autres sont pourvues sans annonce.
- Les salaires ne concernent que les offres qui les affichent, ce qui peut sur-représenter certains secteurs (public, ESN).
- La séniorité et le télétravail sont déduits du texte : une partie reste « Non précisé ».
- La prime salariale par compétence est une corrélation descriptive, pas un effet causal.
- Le jeu de démonstration illustre la méthode ; aucune conclusion sur le marché ne doit en être tirée.

## Pour aller plus loin

- Comparer les salaires à métier et séniorité égaux (prime « nette » d'une compétence) ou par régression.
- Suivre l'évolution sur plusieurs mois de collecte (part de l'IA générative dans les offres de Data Scientist, par exemple).
- Ajouter un score « adéquation profil / offre » à partir de ses propres compétences.

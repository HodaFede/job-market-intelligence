# Indicateurs (KPIs)

Chaque indicateur a une définition unique, calculée une fois en SQL (vues `sql/views/`) et reproduite à l'identique dans Tableau. Les tests (`tests/test_pipeline.py`) vérifient que les deux calculs donnent le même résultat.

## Indicateurs d'en-tête

| Indicateur | Définition | SQL (vue) | Tableau |
|---|---|---|---|
| Nombre d'offres | offres uniques après déduplication (intitulé + entreprise + ville) | `COUNT(*)` — `v_kpi_globaux` | `COUNTD([Id Offre])` |
| Salaire médian | médiane du salaire annuel brut, offres qui affichent un salaire, hors stage/alternance et hors TJM | fenêtre `ROW_NUMBER` / `COUNT` | `MEDIAN([Salaire Annuel])` |
| Salaire moyen | moyenne sur le même périmètre (sensible aux valeurs extrêmes, à lire avec la médiane) | `AVG(salary_mid)` | `AVG([Salaire Annuel])` |
| % offres avec salaire | part des offres dont le salaire est exploitable | `AVG(has_salary)` | `AVG([Salaire Affiche])` |
| % télétravail | part des offres « Hybride » ou « Full remote » (sur toutes les offres, y compris non précisé) | `v_kpi_globaux` | `AVG([Teletravail Possible])` |
| % CDI | part des CDI | `v_kpi_globaux` | `AVG([Est Cdi])` |
| % offres junior | part Junior + Stage/Alternance | `v_kpi_globaux` | voir guide Tableau |
| Nb compétences moyen | nombre moyen de compétences détectées par offre | `AVG(skills_count)` | `AVG([Nb Competences])` |

Pourquoi la médiane plutôt que la moyenne : quelques offres senior très bien payées tirent la moyenne vers le haut ; la médiane décrit mieux « l'offre typique ». Les deux sont affichées.

## Indicateurs par axe

| Axe | Indicateurs | Vue / export |
|---|---|---|
| Villes | nb offres, part des offres, salaire médian, % télétravail, coordonnées | `villes.csv` |
| Secteurs | nb offres, part, salaire médian, % télétravail, % CDI | `secteurs.csv` |
| Métier × séniorité | nb offres avec salaire, moyenne, médiane, Q1, Q3, min, max, fiabilité | `salaires_metier_seniorite.csv` |
| Compétences | nb offres qui citent la compétence, % des offres du métier, rang | `competences_par_metier.csv` |
| Technologies | même vue filtrée sur `type_competence = Technologie` | `competences_par_metier.csv` |
| Prime compétence | médiane avec vs sans la compétence, écart en € et % (≥ 20 offres avec salaire) | `prime_salariale_competences.csv` |
| Associations | nb offres communes, % de A qui citent B, lift | `paires_competences.csv` |
| Séniorité | répartition par métier | `seniorite_metier.csv` |
| Télétravail | répartition Hybride / Full remote / Sur site / Non précisé par métier | `teletravail_metier.csv` |
| Contrats | répartition par type, TJM moyen des freelances | `contrats.csv` |
| Tendance | offres publiées par mois et par métier | `tendance_mensuelle.csv` |

## Règles de calcul à connaître

- **Salaire annuel** : milieu de la fourchette (min + max) / 2. Mensuel × 12, horaire × 1 607 h, valeurs hors [18 000 ; 200 000] € écartées.
- **TJM** (taux journalier freelance) : jamais converti en salaire annuel, analysé à part.
- **Quartiles SQL** : méthode du rang le plus proche ; ils peuvent différer légèrement des quartiles interpolés de Tableau ou pandas sur les petits groupes.
- **Fiabilité** : « Faible » sous 10 offres avec salaire, « Moyenne » de 10 à 29, « Bonne » à partir de 30. Une médiane « Faible » ne devrait pas porter une conclusion.
- **Lift** d'une paire A–B : `n(A et B) × N / (n(A) × n(B))`. Un lift de 3 signifie que les deux compétences apparaissent ensemble trois fois plus souvent que si elles étaient indépendantes.
- **Prime salariale** : écart descriptif. Il mélange l'effet de la compétence et celui du métier ou de la séniorité (Deep Learning est surtout demandé à des profils mieux payés). Pour aller plus loin : comparer à métier et séniorité égaux, ou une régression.

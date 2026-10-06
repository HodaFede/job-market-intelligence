# Guide Tableau Public (Mac)

Ce guide part des fichiers produits par `python -m jmi run` dans `exports/tableau/` et va jusqu'au classeur publié sur ton profil Tableau Public. Compte environ trois à quatre heures pour tout construire la première fois.

Les libellés de menus sont donnés en français (interface Tableau en français), avec l'anglais entre parenthèses quand ça aide à retrouver une option.

---

## 0. Installation

1. Crée un compte gratuit sur [public.tableau.com](https://public.tableau.com).
2. Depuis le site, télécharge **Tableau Public** (l'application de bureau), ouvre le `.dmg` et glisse l'application dans *Applications*.
3. Pour passer l'interface en français : menu **Help › Choose Language › Français**, puis redémarre.

À savoir avant de commencer :

- Tableau Public lit des fichiers (texte, Excel, JSON…) mais pas une base SQLite : c'est pour ça que le pipeline exporte des CSV.
- Un classeur Tableau Public est **public** une fois enregistré sur ton profil. Les exports ne contiennent ni description d'offre ni donnée personnelle.
- Tableau renomme automatiquement les colonnes : `salaire_annuel` devient **Salaire Annuel**, `id_offre` devient **Id Offre**. Ce guide utilise ces noms affichés.

---

## 1. Les fichiers à connecter

| Fichier | Grain (1 ligne =) | Sert à |
|---|---|---|
| `offres.csv` | une offre | source principale : volumes, salaires, villes, télétravail, filtres |
| `offres_competences.csv` | un couple offre × compétence | relié à `offres.csv`, compte les offres par compétence en gardant tous les filtres |
| `kpi_globaux.csv` | une ligne | bandeau de KPI (contrôle de cohérence, date de collecte, jeu réel ou démo) |
| `competences_par_metier.csv` | métier × compétence | % d'offres qui citent chaque compétence (déjà calculé) |
| `salaires_metier_seniorite.csv` | métier × séniorité | médiane, quartiles, fiabilité de l'échantillon |
| `prime_salariale_competences.csv` | une compétence | écart de salaire médian avec / sans la compétence |
| `paires_competences.csv` | paire de compétences | co-occurrences et lift |
| `villes.csv` | une ville | carte (latitude / longitude incluses) |
| `secteurs.csv` | un secteur | volumes, salaire médian, télétravail par secteur |
| `tendance_mensuelle.csv` | mois × métier | évolution des publications |
| `teletravail_metier.csv` | métier × politique | répartition du télétravail |
| `seniorite_metier.csv` | métier × séniorité | répartition des niveaux demandés |
| `contrats.csv` | contrat × métier | types de contrat, TJM moyen freelance |
| `termes_tfidf.csv` | métier × terme | nuage de mots / vocabulaire caractéristique |

La logique : `offres` + `offres_competences` forment un petit modèle relationnel interactif ; les autres fichiers sont des agrégats calculés en SQL, utilisés tels quels pour les visuels qui demandent des pourcentages ou des médianes par groupe (plus fiables que de les recalculer dans Tableau).

---

## 2. Connexion aux CSV

### 2.1 Source principale : offres + compétences

1. Ouvre Tableau Public. Dans le volet **Se connecter**, section **Vers un fichier**, clique **Fichier texte**.
2. Sélectionne `exports/tableau/offres.csv`. La page **Source de données** s'ouvre.
3. Dans la liste **Fichiers** à gauche, glisse `offres_competences.csv` sur le canevas, à côté de `offres.csv`. Un trait (une « relation ») apparaît.
4. Clique sur le trait et vérifie la condition : **Id Offre = Id Offre**. Tableau la détecte normalement tout seul.
5. Renomme la source (clic droit sur son nom en haut) : **Offres Data IA**.

### 2.2 Vérifier les types de champs

Toujours sur la page Source de données, clique sur l'icône au-dessus de chaque colonne si le type est faux :

| Champ | Type attendu | Rôle géographique |
|---|---|---|
| Date Publication, Mois Publication | Date | – |
| Departement | Chaîne (sinon « 06 » devient 6) | – |
| Ville | Chaîne | Ville |
| Region | Chaîne | État/Province |
| Pays | Chaîne | Pays/Région |
| Latitude, Longitude | Nombre décimal | Latitude, Longitude |
| Salaire Annuel, Salaire Min, Salaire Max, Tjm | Nombre décimal | – |
| Est Demo, Salaire Affiche, Teletravail Possible, Est Cdi | Nombre entier (0/1) | – |

Si une région n'est pas reconnue sur la carte, utilise Latitude/Longitude à la place : elles sont fournies pour toutes les villes du référentiel.

### 2.3 Sources secondaires

Pour chaque fichier agrégé dont tu as besoin : menu **Données › Nouvelle source de données › Fichier texte**, puis sélectionne le CSV. Garde les noms par défaut, ils suffisent.

Pour qu'un filtre **Metier** posé sur la source principale agisse aussi sur `competences_par_metier`, `salaires_metier_seniorite`, etc. : Tableau relie automatiquement les champs qui portent le même nom (fusion de données). Sur le filtre, choisis **Appliquer aux feuilles de calcul › Toutes celles utilisant les sources de données associées** (*All Using Related Data Sources*).

### 2.4 Après une nouvelle collecte

Relance `python -m jmi run`. Les CSV sont réécrits sous le même nom : dans Tableau, **Données › Actualiser** (ou rouvre le classeur), puis republie sous le même nom pour écraser la version en ligne.

---

## 3. Champs calculés

Menu **Analyse › Créer un champ calculé**. Crée-les dans la source **Offres Data IA**.

| Nom | Formule | Format |
|---|---|---|
| Nb offres | `COUNTD([Id Offre])` | nombre, 0 décimale |
| Salaire médian | `MEDIAN([Salaire Annuel])` | devise €, 0 décimale |
| Salaire moyen | `AVG([Salaire Annuel])` | devise €, 0 décimale |
| % salaire affiché | `AVG([Salaire Affiche])` | pourcentage, 0 décimale |
| % télétravail | `AVG([Teletravail Possible])` | pourcentage |
| % CDI | `AVG([Est Cdi])` | pourcentage |
| % junior | `AVG(IF [Seniorite] = "Junior" OR [Seniorite] = "Stage / Alternance" THEN 1 ELSE 0 END)` | pourcentage |
| Nb offres citant | `COUNTD([Id Offre (Offres Competences)])` | nombre |
| Ordre séniorité | `CASE [Seniorite] WHEN "Stage / Alternance" THEN 1 WHEN "Junior" THEN 2 WHEN "Confirmé" THEN 3 WHEN "Senior" THEN 4 ELSE 5 END` | – |
| Libellé jeu de données | `IF MAX([Est Demo]) = 1 THEN "⚠ Données de démonstration (synthétiques)" ELSE "Données réelles — France Travail / Adzuna / sites carrières" END` | – |

Note : `Nb offres citant` utilise le champ Id Offre de la table `offres_competences` (Tableau ajoute le suffixe entre parenthèses pour le distinguer).

Pour trier la séniorité dans le bon ordre : clic droit sur **Seniorite › Trier › Champ › Ordre séniorité**.

---

## 4. Les feuilles à créer

Chaque feuille = un visuel. Nomme-les clairement (double-clic sur l'onglet), tu les retrouveras plus vite dans les dashboards.

### Vue d'ensemble

**F01 – KPI** (source Offres Data IA)
Glisse `Nb offres`, `Salaire médian`, `% salaire affiché`, `% télétravail`, `% CDI`, `% junior` sur **Texte** dans la fiche Repères ; une seule feuille par KPI donne plus de liberté de mise en page (6 petites feuilles F01a…F01f). Police 28 pt pour le chiffre, 10 pt pour le libellé.

**F02 – Offres par métier**
Lignes : `Metier` ; Colonnes : `Nb offres`. Tri décroissant. Étiquettes activées. Couleur unique.

**F03 – Tendance mensuelle**
Colonnes : `Mois Publication` (clic droit › **Mois** continu) ; Lignes : `Nb offres` ; Couleur : `Metier`. Type de repère : Ligne.

**F04 – Carte des offres**
Double-clic sur `Longitude` puis `Latitude` (ou utilise `villes.csv`). Détail : `Ville` ; Taille : `Nb offres` ; Couleur : `Salaire médian` (palette séquentielle). Info-bulle : ville, nb offres, salaire médian, % télétravail. Menu **Carte › Arrière-plans** : *Clair*.

### Salaires

**F05 – Salaire médian métier × séniorité** (source `salaires_metier_seniorite`)
Lignes : `Metier` ; Colonnes : `Seniorite` (trié par ordre) ; Couleur et Texte : `Salaire Median`. Type : Carré (heatmap). Ajoute `Fiabilite` dans l'info-bulle et filtre `Nb Offres Avec Salaire` ≥ 5 pour ne pas afficher de médiane sur 2 offres.

**F06 – Distribution des salaires**
Dans le volet Données, clic droit sur `Salaire Annuel › Créer › Classes`, taille 5 000. Colonnes : `Salaire Annuel (classes)` ; Lignes : `Nb offres`. Ajoute une ligne de référence (onglet **Analyse › Ligne de référence**) sur la médiane.

**F07 – Fourchette par métier (boîte à moustaches)**
Colonnes : `Salaire Annuel` (désagrégé : **Analyse › décocher Agréger les mesures**) ; Lignes : `Metier` ; Type : Cercle ; puis **Analyse › Boîte à moustaches**. Montre la dispersion, pas seulement la moyenne.

**F08 – Prime salariale par compétence** (source `prime_salariale_competences`)
Lignes : `Competence` ; Colonnes : `Prime Eur`. Tri décroissant. Couleur : `Prime Eur` palette divergente centrée sur 0. Titre explicite : « Écart de salaire médian, offres citant / ne citant pas la compétence (corrélation) ».

### Compétences et technologies

**F09 – Top compétences** (source `competences_par_metier`)
Filtre `Metier` = Tous métiers par défaut (afficher le filtre, liste à valeur unique). Filtre `Type Competence`. Lignes : `Competence` ; Colonnes : `Part Offres Pct`. Filtre `Rang` ≤ 15. Étiquettes « 72 % ».

**F10 – Heatmap compétences × métiers** (source `competences_par_metier`)
Exclure « Tous métiers ». Colonnes : `Metier` ; Lignes : `Competence` ; Couleur + Texte : `Part Offres Pct`. Filtre `Categorie Competence` affiché. C'est le visuel le plus parlant pour un recruteur.

**F11 – Compétences par catégorie** (source Offres Data IA)
Lignes : `Categorie Competence`, `Competence` ; Colonnes : `Nb offres citant`. Ce visuel réagit à tous les filtres de la source principale (ville, séniorité, télétravail…).

**F12 – Associations de compétences** (source `paires_competences`)
Tableau croisé : Lignes `Competence A`, `Competence B` ; Texte : `Nb Offres Communes`, `Lift`. Filtre `Nb Offres Communes` ≥ 15, tri par `Lift` décroissant, top 20.

**F13 – Vocabulaire caractéristique** (source `termes_tfidf`)
Type de repère : Texte. Texte : `Terme` ; Taille : `Score Tfidf` ; Filtre `Metier` (valeur unique). Donne un nuage de mots par métier.

### Géographie, secteurs, conditions

**F14 – Régions**
Lignes : `Region` ; Colonnes : `Nb offres` ; Couleur : `% télétravail`.

**F15 – Secteurs** (source `secteurs`)
Lignes : `Secteur` ; Colonnes : `Nb Offres` et `Salaire Median` (axe double, ou deux colonnes côte à côte).

**F16 – Télétravail par métier**
Lignes : `Metier` ; Colonnes : `Nb offres` ; Couleur : `Teletravail`. Clic droit sur l'axe › **Calcul de table rapide › Pourcentage du total**, calculé le long de `Teletravail` → barres empilées à 100 %.

**F17 – Séniorité demandée par métier**
Même principe que F16 avec `Seniorite` en couleur (ordre séniorité).

**F18 – Contrats**
Lignes : `Type Contrat` ; Colonnes : `Nb offres`. Info-bulle : TJM moyen (depuis `contrats.csv`) pour Freelance.

---

## 5. Filtres

À afficher sur les dashboards (clic droit sur le champ dans Filtres › **Afficher le filtre**), puis **Appliquer aux feuilles de calcul › Toutes celles utilisant cette source de données** (ou sources associées) :

| Filtre | Type d'affichage conseillé |
|---|---|
| Metier | liste déroulante à valeurs multiples |
| Seniorite | cases à cocher |
| Region | liste déroulante |
| Type Contrat | cases à cocher |
| Teletravail | cases à cocher |
| Secteur | liste déroulante |
| Date Publication | curseur de plage de dates |
| Categorie Competence | liste (dashboard Compétences) |

En plus, une **action de filtre** rend le dashboard interactif : **Tableau de bord › Actions › Ajouter une action › Filtre**, source F02 (Offres par métier), cible toutes les feuilles, exécution « Sélectionner ». Un clic sur un métier filtre tout le reste.

---

## 6. Les quatre dashboards

Taille conseillée : **Fixe, 1200 × 850** (Tableau de bord › Taille). Utilise des conteneurs horizontaux / verticaux pour aligner proprement. Un titre par dashboard, une ligne de sous-titre qui donne la source et la période, le libellé jeu de données (champ calculé) en haut à droite.

**D1 — Vue d'ensemble du marché**
KPI (F01a–f) en bandeau, F02 à gauche, F03 en haut à droite, F04 en bas à droite. Filtres Metier, Seniorite, Region, Date en colonne à droite.
Question à laquelle il répond : *combien d'offres, où, pour quels métiers, et comment ça évolue ?*

**D2 — Salaires**
F05 (heatmap) en grand, F07 (boîtes), F06 (distribution), F08 (prime compétence). Filtres Metier, Seniorite, Region.
Question : *combien paie chaque métier selon l'expérience, et quelles compétences vont avec les salaires élevés ?*

**D3 — Compétences et technologies**
F09 (top 15) à gauche, F10 (heatmap) au centre, F12 (associations) et F13 (nuage de mots) à droite. Filtres Metier, Type, Categorie.
Question : *quelle stack apprendre pour quel métier ?*

**D4 — Géographie, secteurs et conditions de travail**
F04 ou F14, F15, F16, F17, F18.
Question : *qui recrute, où, en quel contrat et avec quel télétravail ?*

Règles de lisibilité : 2 à 3 couleurs maximum (une couleur d'accent pour le message clé, du gris pour le reste) ; des titres qui énoncent le constat (« Python et SQL : le socle de 7 offres sur 10 ») plutôt que le contenu (« Compétences par offre ») ; info-bulles courtes ; pas de graphique 3D ni de camembert à plus de 4 parts.

---

## 7. Storytelling (Histoire)

**Histoire › Nouvelle histoire** (*Story*). Chaque point d'histoire affiche un dashboard ou une feuille avec une légende rédigée. Proposition en 6 points :

1. **Le marché** — D1 filtré sur tous les métiers : « X offres Data/IA analysées entre <date min> et <date max> ; l'Île-de-France en concentre Y %. »
2. **Les métiers qui recrutent** — F02 + F03 : quel métier domine, lequel progresse.
3. **Le socle commun** — F09 sur Tous métiers : Python et SQL partout, puis ce qui différencie.
4. **Une stack par métier** — F10 : ce qui distingue Data Analyst, Data Scientist, Data Engineer, AI Engineer.
5. **Ce que vaut chaque profil** — D2 : médianes par séniorité, compétences associées aux salaires élevés (en rappelant que c'est une corrélation).
6. **Recommandations** — une feuille Texte (ou une image) reprenant les recommandations de `reports/insights.md` : quoi apprendre, quels métiers cibler en junior, où chercher.

Les chiffres des légendes se trouvent dans `reports/insights.md`, régénéré à chaque `python -m jmi run`.

---

## 8. Publier

1. **Fichier › Enregistrer sur Tableau Public sous…** (*Save to Tableau Public As*), connecte-toi, nomme le classeur « Job Market Intelligence — Data & IA France ».
2. Le navigateur ouvre la page du classeur. Clique sur l'icône d'édition des détails : ajoute une description (2–3 lignes + lien vers le dépôt GitHub), des mots-clés (data, emploi, NLP, Python), et choisis le dashboard affiché en premier (la Story ou D1).
3. Dans les paramètres du classeur, autorise le téléchargement si tu veux que les recruteurs puissent l'ouvrir.
4. Prends une capture de chaque dashboard (⌘ + Maj + 4) et range-les dans `docs/img/` : elles illustrent le README.
5. Copie l'URL publique dans le README (section « Dashboard ») et sur ton CV.

Selon la version de l'application, tu peux aussi garder une copie locale du classeur (`.twbx`) ; sinon, télécharge-la depuis ton profil et range-la dans `tableau/`.

---

## 9. Check-list avant publication

- [ ] Le libellé « données de démonstration » est visible si `Est Demo` = 1 (et disparaît avec des données réelles).
- [ ] Les KPI du dashboard correspondent à `kpi_globaux.csv` (même nombre d'offres, même salaire médian).
- [ ] Les médianes sur moins de 5 offres sont masquées ou signalées (colonne `Fiabilite`).
- [ ] Les filtres s'appliquent à toutes les feuilles concernées.
- [ ] Chaque dashboard a un titre-constat, une source et une période.
- [ ] Les info-bulles ne montrent pas de champs techniques (Id Offre, Est Demo…).

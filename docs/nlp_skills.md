# Analyse des compétences par NLP

L'objectif est de transformer le texte libre des offres en données comptables : quelles compétences sont demandées, pour quel métier, avec quelles autres compétences. Le choix est volontairement simple et explicable, parce qu'un recruteur ou un manager doit pouvoir comprendre comment un chiffre a été obtenu.

## 1. Extraction par dictionnaire et expressions régulières

Code : `src/jmi/nlp/skills.py` — Référentiel : `config/skills_dictionary.yaml` (environ 75 compétences, 11 catégories).

Pour chaque offre, on concatène intitulé et description, puis :

1. **Normalisation** : minuscules, suppression des accents, apostrophes typographiques unifiées. « Séries temporelles » et « series temporelles » sont équivalents.
2. **Recherche de chaque compétence** avec ses variantes (`power ?bi`, `scikit[- ]learn`, `postgres(?:ql)?`…).
3. **Bornes de mot adaptées** : `(?<![\w+#])…(?![\w+#])` au lieu de `\b`, pour que `CI/CD`, `C#` ou `scikit-learn` soient bien détectés et que `Java` ne matche pas dans `JavaScript`.
4. **Faux positifs du français** traités explicitement :
   - « tableau de bord », « tableaux », « tableau croisé » ne comptent pas comme l'outil Tableau (mais alimentent la compétence *KPI & reporting*) ;
   - « R&D » ne compte pas comme le langage R, qui est cherché en respectant la casse.
5. Résultat : une table longue `offer_skills (offer_id, skill)` — une ligne par compétence détectée — chargée en SQL et exportée pour Tableau.

Chaque compétence porte une **catégorie** (Langages, Cloud, ML & IA, IA générative, Soft skills…) et un **type** : *tech* (outil, langage, plateforme) ou *skill* (méthode, savoir-être). C'est ce qui permet de séparer « technologies » et « compétences » dans les dashboards.

Pourquoi pas un modèle de NER ou un LLM : sur un vocabulaire technique fermé, le dictionnaire est plus précis, reproductible, rapide et sans coût. Sa limite (il ne trouve que ce qu'on lui a listé) est compensée par l'étape suivante.

## 2. TF-IDF par famille de métier

Fonction : `top_terms_by_group()` — Export : `termes_tfidf.csv`.

- Uni- et bi-grammes, calculés **à l'intérieur d'une même portion de phrase** : une virgule ou un point coupe la séquence, ce qui évite les faux bigrammes du type « spark kafka » quand l'offre liste « Spark, Kafka ».
- Mots vides français, anglais et vocabulaire générique de recrutement retirés (« poste », « profil », « rejoindre »…).
- `max_df = 0.6` : un terme présent dans plus de 60 % des offres ne distingue rien.
- Score = TF-IDF moyen sur les offres du métier ; un unigramme est retiré s'il est déjà porté par un bigramme presque aussi fort (« hugging » / « hugging face »).

Usage : repérer les termes caractéristiques d'un métier **et** les outils absents du dictionnaire. Sur le jeu de démonstration, *Collibra* remonte dans le top des Data Managers alors qu'il n'est pas dans le référentiel : c'est le signal pour les y ajouter.

## 3. Co-occurrences

Vue SQL `v_paires_competences` : auto-jointure de `offer_skills` sur `offer_id`, avec le **lift** pour corriger l'effet taille (Python et SQL apparaissent ensemble souvent simplement parce qu'ils sont partout). Les paires à lift élevé dessinent des « stacks » cohérentes : LangChain + RAG, Spark + Airflow, dbt + Snowflake.

## 4. Qualité et maintenance

- Les cas limites sont couverts par `tests/test_skills.py` (tableau de bord, R&D, CI/CD, Java/JavaScript, accents).
- Pour ajouter une compétence : une ligne dans le YAML, puis `python -m jmi run`. Aucun code à toucher.
- Pour contrôler la précision sur des données réelles : tirer 50 offres au hasard dans `data/processed/offers_clean.csv`, annoter à la main, comparer avec `offer_skills.csv`. Viser une précision > 90 % avant de publier des chiffres.

## Pistes d'amélioration

- Lemmatisation avec spaCy (`fr_core_news_sm`) pour les compétences rédigées en phrases.
- Embeddings (sentence-transformers) pour regrouper les intitulés de poste proches.
- Distinguer compétence « exigée » et « appréciée » à partir du contexte (« un plus », « idéalement »).

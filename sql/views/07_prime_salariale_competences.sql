-- « Prime » associée à une compétence : salaire médian des offres qui la citent vs celles qui ne la citent pas.
-- Corrélation descriptive, pas un effet causal (le métier et la séniorité jouent aussi).
DROP VIEW IF EXISTS v_prime_salariale_competences;
CREATE VIEW v_prime_salariale_competences AS
WITH salaried AS (
    SELECT offer_id, salary_mid FROM offers WHERE salary_mid IS NOT NULL
),
grid AS (
    SELECT s.skill, sa.salary_mid,
           CASE WHEN os.offer_id IS NULL THEN 0 ELSE 1 END AS has_skill
    FROM skills s
    CROSS JOIN salaried sa
    LEFT JOIN offer_skills os ON os.skill = s.skill AND os.offer_id = sa.offer_id
),
ranked AS (
    SELECT skill, has_skill, salary_mid,
           ROW_NUMBER() OVER (PARTITION BY skill, has_skill ORDER BY salary_mid) AS rn,
           COUNT(*)     OVER (PARTITION BY skill, has_skill)                     AS cnt
    FROM grid
),
med AS (
    SELECT skill, has_skill, AVG(salary_mid) AS median, MAX(cnt) AS n
    FROM ranked WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    GROUP BY skill, has_skill
)
SELECT
    w.skill                                         AS competence,
    s.category                                      AS categorie_competence,
    w.n                                             AS nb_offres_avec,
    wo.n                                            AS nb_offres_sans,
    ROUND(w.median, 0)                              AS salaire_median_avec,
    ROUND(wo.median, 0)                             AS salaire_median_sans,
    ROUND(w.median - wo.median, 0)                  AS prime_eur,
    ROUND(100.0 * (w.median - wo.median) / wo.median, 1) AS prime_pct,
    CASE WHEN w.n >= 20 THEN 'Moyenne' ELSE 'Faible (10 à 19 offres)' END AS fiabilite
FROM med w
JOIN med wo ON wo.skill = w.skill AND wo.has_skill = 0
JOIN skills s ON s.skill = w.skill
WHERE w.has_skill = 1 AND w.n >= 10;

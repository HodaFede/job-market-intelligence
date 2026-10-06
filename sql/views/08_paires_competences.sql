-- Co-occurrence de compétences (auto-jointure) et lift : > 1 = associées plus souvent que par hasard.
DROP VIEW IF EXISTS v_paires_competences;
CREATE VIEW v_paires_competences AS
WITH n_total AS (SELECT COUNT(*) AS n FROM offers),
freq AS (SELECT skill, COUNT(*) AS n FROM offer_skills GROUP BY skill),
pairs AS (
    SELECT a.skill AS skill_a, b.skill AS skill_b, COUNT(*) AS n_ab
    FROM offer_skills a
    JOIN offer_skills b ON a.offer_id = b.offer_id AND a.skill < b.skill
    GROUP BY a.skill, b.skill
    HAVING COUNT(*) >= 5
)
SELECT
    p.skill_a                                                AS competence_a,
    p.skill_b                                                AS competence_b,
    p.n_ab                                                   AS nb_offres_communes,
    ROUND(100.0 * p.n_ab / fa.n, 1)                          AS pct_offres_a_avec_b,
    ROUND(1.0 * p.n_ab * (SELECT n FROM n_total) / (fa.n * fb.n), 2) AS lift
FROM pairs p
JOIN freq fa ON fa.skill = p.skill_a
JOIN freq fb ON fb.skill = p.skill_b;

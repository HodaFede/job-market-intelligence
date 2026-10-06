-- Part des offres de chaque métier qui citent une compétence (+ une ligne « Tous métiers »).
DROP VIEW IF EXISTS v_competences_par_metier;
CREATE VIEW v_competences_par_metier AS
WITH totals AS (
    SELECT role_family, COUNT(*) AS n FROM offers GROUP BY role_family
    UNION ALL
    SELECT 'Tous métiers', COUNT(*) FROM offers
),
counts AS (
    SELECT o.role_family, os.skill, COUNT(*) AS n
    FROM offer_skills os JOIN offers o ON o.offer_id = os.offer_id
    GROUP BY o.role_family, os.skill
    UNION ALL
    SELECT 'Tous métiers', skill, COUNT(*) FROM offer_skills GROUP BY skill
)
SELECT
    c.role_family                                    AS metier,
    c.skill                                          AS competence,
    s.category                                       AS categorie_competence,
    CASE s.skill_type WHEN 'tech' THEN 'Technologie' ELSE 'Compétence / méthode' END AS type_competence,
    c.n                                              AS nb_offres,
    t.n                                              AS nb_offres_metier,
    ROUND(100.0 * c.n / t.n, 1)                      AS part_offres_pct,
    RANK() OVER (PARTITION BY c.role_family ORDER BY c.n DESC) AS rang
FROM counts c
JOIN totals t ON t.role_family = c.role_family
JOIN skills s ON s.skill = c.skill;

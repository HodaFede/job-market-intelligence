-- Synthèse géographique (coordonnées incluses pour la carte Tableau).
DROP VIEW IF EXISTS v_villes;
CREATE VIEW v_villes AS
WITH ranked AS (
    SELECT city, salary_mid,
           ROW_NUMBER() OVER (PARTITION BY city ORDER BY salary_mid) AS rn,
           COUNT(*)     OVER (PARTITION BY city)                     AS cnt
    FROM offers WHERE salary_mid IS NOT NULL
),
med AS (
    SELECT city, AVG(salary_mid) AS salaire_median, MAX(cnt) AS nb_salaires
    FROM ranked WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2) GROUP BY city
)
SELECT
    o.city                                                   AS ville,
    o.region                                                 AS region,
    'France'                                                 AS pays,
    AVG(o.latitude)                                          AS latitude,
    AVG(o.longitude)                                         AS longitude,
    COUNT(*)                                                 AS nb_offres,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM offers), 2) AS part_offres_pct,
    ROUND(m.salaire_median, 0)                               AS salaire_median,
    COALESCE(m.nb_salaires, 0)                               AS nb_offres_avec_salaire,
    ROUND(100.0 * AVG(CASE WHEN o.remote_policy IN ('Hybride', 'Full remote') THEN 1 ELSE 0 END), 1) AS pct_teletravail
FROM offers o
LEFT JOIN med m ON m.city = o.city
GROUP BY o.city, o.region;

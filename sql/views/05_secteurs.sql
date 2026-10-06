DROP VIEW IF EXISTS v_secteurs;
CREATE VIEW v_secteurs AS
WITH ranked AS (
    SELECT sector, salary_mid,
           ROW_NUMBER() OVER (PARTITION BY sector ORDER BY salary_mid) AS rn,
           COUNT(*)     OVER (PARTITION BY sector)                     AS cnt
    FROM offers WHERE salary_mid IS NOT NULL
),
med AS (
    SELECT sector, AVG(salary_mid) AS salaire_median
    FROM ranked WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2) GROUP BY sector
)
SELECT
    o.sector                                                     AS secteur,
    COUNT(*)                                                     AS nb_offres,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM offers), 2)   AS part_offres_pct,
    ROUND(m.salaire_median, 0)                                   AS salaire_median,
    ROUND(100.0 * AVG(CASE WHEN o.remote_policy IN ('Hybride', 'Full remote') THEN 1 ELSE 0 END), 1) AS pct_teletravail,
    ROUND(100.0 * AVG(CASE WHEN o.contract_type = 'CDI' THEN 1 ELSE 0 END), 1) AS pct_cdi
FROM offers o
LEFT JOIN med m ON m.sector = o.sector
GROUP BY o.sector;

-- Une ligne : les KPIs d'en-tête du dashboard.
DROP VIEW IF EXISTS v_kpi_globaux;
CREATE VIEW v_kpi_globaux AS
WITH sal AS (
    SELECT salary_mid,
           ROW_NUMBER() OVER (ORDER BY salary_mid) AS rn,
           COUNT(*)     OVER ()                    AS cnt
    FROM offers WHERE salary_mid IS NOT NULL
),
median AS (
    SELECT AVG(salary_mid) AS salaire_median
    FROM sal WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
)
SELECT
    COUNT(*)                                                          AS nb_offres,
    COUNT(DISTINCT company)                                           AS nb_entreprises,
    COUNT(DISTINCT CASE WHEN city <> 'Non précisé' THEN city END)     AS nb_villes,
    ROUND(AVG(salary_mid), 0)                                         AS salaire_moyen,
    ROUND((SELECT salaire_median FROM median), 0)                     AS salaire_median,
    ROUND(100.0 * AVG(has_salary), 1)                                 AS pct_offres_avec_salaire,
    ROUND(100.0 * AVG(CASE WHEN remote_policy IN ('Hybride', 'Full remote') THEN 1 ELSE 0 END), 1) AS pct_teletravail,
    ROUND(100.0 * AVG(CASE WHEN contract_type = 'CDI' THEN 1 ELSE 0 END), 1)   AS pct_cdi,
    ROUND(100.0 * AVG(CASE WHEN seniority IN ('Junior', 'Stage / Alternance') THEN 1 ELSE 0 END), 1) AS pct_offres_junior,
    ROUND(AVG(skills_count), 1)                                       AS nb_competences_moyen,
    MIN(published_date)                                               AS date_min,
    MAX(published_date)                                               AS date_max,
    CASE WHEN MAX(is_demo) = 1 THEN 'Démonstration (synthétique)' ELSE 'Réel' END AS jeu_de_donnees
FROM offers;

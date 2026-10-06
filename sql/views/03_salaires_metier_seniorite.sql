-- Salaires annuels bruts par métier × séniorité : moyenne, médiane, quartiles (méthode du rang le plus proche).
DROP VIEW IF EXISTS v_salaires_metier_seniorite;
CREATE VIEW v_salaires_metier_seniorite AS
WITH ranked AS (
    SELECT role_family, seniority, salary_mid,
           ROW_NUMBER() OVER (PARTITION BY role_family, seniority ORDER BY salary_mid) AS rn,
           COUNT(*)     OVER (PARTITION BY role_family, seniority)                     AS cnt
    FROM offers
    WHERE salary_mid IS NOT NULL
)
SELECT
    role_family                                                              AS metier,
    seniority                                                                AS seniorite,
    MAX(cnt)                                                                 AS nb_offres_avec_salaire,
    ROUND(AVG(salary_mid), 0)                                                AS salaire_moyen,
    ROUND(AVG(CASE WHEN rn IN ((cnt + 1) / 2, (cnt + 2) / 2) THEN salary_mid END), 0) AS salaire_median,
    MAX(CASE WHEN rn = CAST(0.25 * (cnt - 1) + 0.5 AS INTEGER) + 1 THEN salary_mid END)    AS salaire_q1,
    MAX(CASE WHEN rn = CAST(0.75 * (cnt - 1) + 0.5 AS INTEGER) + 1 THEN salary_mid END)    AS salaire_q3,
    MIN(salary_mid)                                                          AS salaire_min,
    MAX(salary_mid)                                                          AS salaire_max,
    CASE WHEN MAX(cnt) >= 30 THEN 'Bonne' WHEN MAX(cnt) >= 10 THEN 'Moyenne' ELSE 'Faible (< 10 offres)' END AS fiabilite
FROM ranked
GROUP BY role_family, seniority;

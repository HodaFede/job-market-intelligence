DROP VIEW IF EXISTS v_tendance_mensuelle;
CREATE VIEW v_tendance_mensuelle AS
SELECT
    published_month                     AS mois,
    role_family                         AS metier,
    COUNT(*)                            AS nb_offres,
    ROUND(AVG(salary_mid), 0)           AS salaire_moyen,
    SUM(CASE WHEN remote_policy IN ('Hybride', 'Full remote') THEN 1 ELSE 0 END) AS nb_offres_teletravail
FROM offers
WHERE published_month IS NOT NULL
GROUP BY published_month, role_family;

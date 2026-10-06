DROP VIEW IF EXISTS v_teletravail_metier;
CREATE VIEW v_teletravail_metier AS
SELECT
    role_family                                                              AS metier,
    remote_policy                                                            AS teletravail,
    COUNT(*)                                                                 AS nb_offres,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY role_family), 1) AS part_offres_pct
FROM offers
GROUP BY role_family, remote_policy;

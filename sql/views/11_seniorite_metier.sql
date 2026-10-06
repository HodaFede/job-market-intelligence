DROP VIEW IF EXISTS v_seniorite_metier;
CREATE VIEW v_seniorite_metier AS
SELECT
    role_family                                                              AS metier,
    seniority                                                                AS seniorite,
    CASE seniority WHEN 'Stage / Alternance' THEN 1 WHEN 'Junior' THEN 2 WHEN 'Confirmé' THEN 3
                   WHEN 'Senior' THEN 4 ELSE 5 END                           AS ordre_seniorite,
    COUNT(*)                                                                 AS nb_offres,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY role_family), 1) AS part_offres_pct
FROM offers
GROUP BY role_family, seniority;

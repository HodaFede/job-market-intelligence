DROP VIEW IF EXISTS v_contrats;
CREATE VIEW v_contrats AS
SELECT
    contract_type                                               AS type_contrat,
    role_family                                                 AS metier,
    COUNT(*)                                                    AS nb_offres,
    ROUND(AVG(daily_rate), 0)                                   AS tjm_moyen
FROM offers
GROUP BY contract_type, role_family;

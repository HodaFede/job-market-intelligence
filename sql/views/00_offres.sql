-- Table principale pour Tableau : une ligne par offre (sans la description, trop volumineuse).
DROP VIEW IF EXISTS v_offres;
CREATE VIEW v_offres AS
SELECT
    offer_id                                   AS id_offre,
    source                                     AS source,
    is_demo                                    AS est_demo,
    title                                      AS intitule,
    role_family                                AS metier,
    seniority                                  AS seniorite,
    experience_years                           AS annees_experience,
    contract_type                              AS type_contrat,
    company                                    AS entreprise,
    sector                                     AS secteur,
    city                                       AS ville,
    department_code                            AS departement,
    region                                     AS region,
    'France'                                   AS pays,
    latitude                                   AS latitude,
    longitude                                  AS longitude,
    remote_policy                              AS teletravail,
    CASE WHEN remote_policy IN ('Hybride', 'Full remote') THEN 1 ELSE 0 END AS teletravail_possible,
    salary_min                                 AS salaire_min,
    salary_max                                 AS salaire_max,
    salary_mid                                 AS salaire_annuel,
    has_salary                                 AS salaire_affiche,
    daily_rate                                 AS tjm,
    CASE WHEN contract_type = 'CDI' THEN 1 ELSE 0 END AS est_cdi,
    published_date                             AS date_publication,
    published_month                            AS mois_publication,
    skills_count                               AS nb_competences,
    url                                        AS url
FROM offers;

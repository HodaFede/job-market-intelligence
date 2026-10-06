-- Table d'association offre ↔ compétence (format long). Relier à offres.csv sur id_offre.
DROP VIEW IF EXISTS v_offres_competences;
CREATE VIEW v_offres_competences AS
SELECT
    os.offer_id    AS id_offre,
    os.skill       AS competence,
    s.category     AS categorie_competence,
    CASE s.skill_type WHEN 'tech' THEN 'Technologie' ELSE 'Compétence / méthode' END AS type_competence
FROM offer_skills os
JOIN skills s ON s.skill = os.skill;

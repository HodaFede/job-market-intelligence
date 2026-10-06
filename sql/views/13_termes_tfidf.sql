-- Termes caractéristiques (TF-IDF) par métier : veille sur le vocabulaire hors dictionnaire.
DROP VIEW IF EXISTS v_termes_tfidf;
CREATE VIEW v_termes_tfidf AS
SELECT role_family AS metier, term AS terme, tfidf_score AS score_tfidf, rank AS rang
FROM top_terms;

-- Modèle relationnel SQLite (data/warehouse/jobs.db)
--
--   offers (1) ──< offer_skills >── (1) skills
--
-- offers       : une ligne par offre nettoyée et dédupliquée (table de faits)
-- skills       : référentiel des compétences (dimension)
-- offer_skills : table d'association offre ↔ compétence détectée par le NLP
-- top_terms    : termes TF-IDF caractéristiques par famille de métier
-- pipeline_runs: traçabilité des exécutions (jeu réel / démo, volumes)

PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS v_offres;
DROP TABLE IF EXISTS offer_skills;
DROP TABLE IF EXISTS top_terms;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS offers;

CREATE TABLE offers (
    offer_id          TEXT PRIMARY KEY,
    source            TEXT NOT NULL,
    source_id         TEXT NOT NULL,
    is_demo           INTEGER NOT NULL DEFAULT 0 CHECK (is_demo IN (0, 1)),
    title             TEXT NOT NULL,
    role_family       TEXT NOT NULL,
    seniority         TEXT NOT NULL,
    experience_years  REAL,
    contract_type     TEXT NOT NULL,
    company           TEXT,
    sector            TEXT NOT NULL,
    city              TEXT NOT NULL,
    department_code   TEXT,
    region            TEXT NOT NULL,
    latitude          REAL,
    longitude         REAL,
    remote_policy     TEXT NOT NULL,
    salary_min        REAL,
    salary_max        REAL,
    salary_mid        REAL,
    has_salary        INTEGER NOT NULL CHECK (has_salary IN (0, 1)),
    daily_rate        REAL,
    published_date    TEXT,          -- ISO AAAA-MM-JJ
    published_month   TEXT,          -- AAAA-MM-01
    url               TEXT,
    search_keyword    TEXT,
    description       TEXT,
    skills_count      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE skills (
    skill       TEXT PRIMARY KEY,
    category    TEXT NOT NULL,
    skill_type  TEXT NOT NULL CHECK (skill_type IN ('tech', 'skill'))
);

CREATE TABLE offer_skills (
    offer_id  TEXT NOT NULL REFERENCES offers(offer_id),
    skill     TEXT NOT NULL REFERENCES skills(skill),
    PRIMARY KEY (offer_id, skill)
);

CREATE TABLE top_terms (
    role_family  TEXT NOT NULL,
    term         TEXT NOT NULL,
    tfidf_score  REAL NOT NULL,
    rank         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_at         TEXT NOT NULL,
    dataset_label  TEXT NOT NULL,
    n_raw          INTEGER NOT NULL,
    n_offers       INTEGER NOT NULL,
    n_offer_skills INTEGER NOT NULL
);

CREATE INDEX idx_offers_role      ON offers(role_family);
CREATE INDEX idx_offers_city      ON offers(city);
CREATE INDEX idx_offers_month     ON offers(published_month);
CREATE INDEX idx_offer_skills_sk  ON offer_skills(skill);

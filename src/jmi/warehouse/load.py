"""Chargement SQLite : schéma, tables, vues analytiques (sql/views/*.sql)."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

OFFER_COLUMNS = [
    "offer_id", "source", "source_id", "is_demo", "title", "role_family", "seniority", "experience_years",
    "contract_type", "company", "sector", "city", "department_code", "region", "latitude", "longitude",
    "remote_policy", "salary_min", "salary_max", "salary_mid", "has_salary", "daily_rate", "published_date",
    "published_month", "url", "search_keyword", "description", "skills_count",
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _drop_views(con: sqlite3.Connection) -> None:
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'view'").fetchall():
        con.execute(f'DROP VIEW IF EXISTS "{name}"')


def view_files(views_dir: Path) -> list[Path]:
    return sorted(views_dir.glob("*.sql"))


def load_warehouse(db_path: Path, schema_sql: Path, views_dir: Path, offers: pd.DataFrame,
                   offer_skills: pd.DataFrame, skills_catalog: pd.DataFrame, top_terms: pd.DataFrame,
                   dataset_label: str, n_raw: int) -> None:
    con = connect(db_path)
    try:
        _drop_views(con)
        con.executescript(schema_sql.read_text(encoding="utf-8"))

        counts = offer_skills.groupby("offer_id").size() if not offer_skills.empty else pd.Series(dtype=int)
        df = offers.copy()
        df["skills_count"] = df["offer_id"].map(counts).fillna(0).astype(int)
        for col in ("published_date", "published_month"):
            df[col] = df[col].map(lambda d: d.isoformat() if hasattr(d, "isoformat") else d)
        df = df.astype(object).where(pd.notna(df), None)

        placeholders = ", ".join("?" for _ in OFFER_COLUMNS)
        con.executemany(f"INSERT INTO offers ({', '.join(OFFER_COLUMNS)}) VALUES ({placeholders})",
                        df[OFFER_COLUMNS].itertuples(index=False, name=None))
        con.executemany("INSERT INTO skills (skill, category, skill_type) VALUES (?, ?, ?)",
                        skills_catalog[["skill", "category", "skill_type"]].itertuples(index=False, name=None))
        con.executemany("INSERT INTO offer_skills (offer_id, skill) VALUES (?, ?)",
                        offer_skills[["offer_id", "skill"]].drop_duplicates().itertuples(index=False, name=None))
        if not top_terms.empty:
            con.executemany("INSERT INTO top_terms (role_family, term, tfidf_score, rank) VALUES (?, ?, ?, ?)",
                            top_terms[["role_family", "term", "tfidf_score", "rank"]]
                            .itertuples(index=False, name=None))
        con.execute("INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?)",
                    (datetime.now().isoformat(timespec="seconds"), dataset_label, n_raw, len(df), len(offer_skills)))

        for path in view_files(views_dir):
            con.executescript(path.read_text(encoding="utf-8"))
        con.commit()
        log.info("Entrepôt SQLite prêt : %s (%s offres, %s liens compétences, %s vues)",
                 db_path, len(df), len(offer_skills), len(view_files(views_dir)))
    finally:
        con.close()

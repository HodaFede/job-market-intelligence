"""Exports CSV pour Tableau Public (une vue SQL = un fichier CSV).

Tableau Public ne se connecte pas à SQLite : on lui fournit des fichiers texte UTF-8,
séparateur virgule, dates ISO, point décimal — lus sans configuration sur Mac.
"""
from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

import pandas as pd

from jmi.warehouse.load import view_files

log = logging.getLogger(__name__)


def export_name(view_file: Path) -> str:
    """`06_competences_par_metier.sql` → `competences_par_metier`."""
    return re.sub(r"^\d+_", "", view_file.stem)


def export_views(db_path: Path, views_dir: Path, out_dir: Path) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, int] = {}
    con = sqlite3.connect(db_path)
    try:
        for vf in view_files(views_dir):
            name = export_name(vf)
            df = pd.read_sql_query(f"SELECT * FROM v_{name}", con)
            df.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8")
            written[name] = len(df)
    finally:
        con.close()
    log.info("Exports Tableau écrits dans %s : %s", out_dir, ", ".join(f"{k} ({v})" for k, v in written.items()))
    return written

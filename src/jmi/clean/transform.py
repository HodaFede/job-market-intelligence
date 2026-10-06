"""Transformation des offres brutes (JSONL multi-sources) en une table propre et dédupliquée."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import pandas as pd

from jmi.clean import normalize as N

log = logging.getLogger(__name__)

CLEAN_COLUMNS = [
    "offer_id", "source", "source_id", "is_demo", "title", "role_family", "seniority", "experience_years",
    "contract_type", "company", "sector", "city", "department_code", "region", "latitude", "longitude",
    "remote_policy", "salary_min", "salary_max", "salary_mid", "has_salary", "daily_rate",
    "published_date", "published_month", "url", "search_keyword", "description",
]


def select_records(records: list[dict[str, Any]], mode: str = "auto") -> tuple[list[dict[str, Any]], str]:
    """Choisit données réelles / démo. Ne remplace jamais du réel par du synthétique.

    auto : réel s'il existe, sinon démo — real : réel seulement — all : les deux.
    Renvoie (enregistrements, libellé du jeu utilisé).
    """
    real = [r for r in records if not r.get("is_demo")]
    demo = [r for r in records if r.get("is_demo")]
    if mode == "real":
        return real, "réel"
    if mode == "all":
        return real + demo, "réel + démo" if real and demo else ("réel" if real else "démo")
    if real:
        if demo:
            log.info("Données réelles trouvées : le jeu de démonstration (%s offres) est ignoré.", len(demo))
        return real, "réel"
    log.warning("Aucune donnée réelle : utilisation du jeu de DÉMONSTRATION (is_demo = 1).")
    return demo, "démo"


def _dedup_key(title: str, company: str | None, city: str) -> str:
    base = "|".join([N.norm(title), N.norm(company), N.norm(city)])
    return hashlib.md5(base.encode()).hexdigest()


def clean_records(records: list[dict[str, Any]], salary_bounds: tuple[float, float] = (18000, 200000),
                  hours_per_year: int = 1607) -> pd.DataFrame:
    rows = []
    out_of_scope = 0
    for r in records:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        if not N.is_data_ai_title(title):
            out_of_scope += 1
            continue
        description = r.get("description") or ""
        contract = N.contract_type(r.get("contract_raw"), title)
        years = N.parse_experience_years(r.get("experience_raw"))
        loc = N.normalize_location(r.get("location_raw"), r.get("latitude"), r.get("longitude"))
        sal = N.parse_salary(r.get("salary_raw"), r.get("salary_min_raw"), r.get("salary_max_raw"),
                             r.get("salary_unit_raw"), hours_per_year)
        seniority = N.seniority_level(title, years, contract, description)
        sal_min, sal_max, sal_mid = sal.annual_min, sal.annual_max, sal.annual_mid
        if sal_mid is not None and not (salary_bounds[0] <= sal_mid <= salary_bounds[1]):
            sal_min = sal_max = sal_mid = None  # valeur aberrante ou mal parsée
        if seniority == "Stage / Alternance":
            sal_min = sal_max = sal_mid = None  # gratification / salaire d'apprenti : non comparable
        published = pd.to_datetime(r.get("published_at"), errors="coerce", utc=True)
        published_date = published.date() if pd.notna(published) else None

        rows.append({
            "offer_id": f"{r['source']}:{r['source_id']}",
            "source": r["source"],
            "source_id": str(r["source_id"]),
            "is_demo": int(bool(r.get("is_demo"))),
            "title": title,
            "role_family": N.role_family(title),
            "seniority": seniority,
            "experience_years": years,
            "contract_type": contract,
            "company": (r.get("company") or "").strip() or N.UNKNOWN,
            "sector": N.sector_category(r.get("sector_raw"), r.get("company")),
            "city": loc.city,
            "department_code": loc.department_code,
            "region": loc.region,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "remote_policy": N.remote_policy(r.get("remote_raw"), description),
            "salary_min": round(sal_min) if sal_min else None,
            "salary_max": round(sal_max) if sal_max else None,
            "salary_mid": round(sal_mid) if sal_mid else None,
            "has_salary": int(sal_mid is not None),
            "daily_rate": sal.daily_rate,
            "published_date": published_date,
            "published_month": published_date.replace(day=1) if published_date else None,
            "url": r.get("url"),
            "search_keyword": r.get("search_keyword"),
            "description": description,
            "_dedup": _dedup_key(title, r.get("company"), loc.city),
        })

    if out_of_scope:
        log.info("Hors périmètre data/IA (intitulé sans terme data/IA, enseignement, vente) : %s offres écartées", out_of_scope)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=CLEAN_COLUMNS)
    before = len(df)
    # Les fichiers bruts sont lus du plus ancien au plus récent : on inverse pour que, à date égale,
    # la ligne de la collecte la plus récente (champs les plus complets) l'emporte.
    df = (df.iloc[::-1].sort_values("published_date", na_position="last", kind="stable")
            .drop_duplicates(subset="offer_id")
            .drop_duplicates(subset="_dedup", keep="first"))
    log.info("Déduplication : %s → %s offres", before, len(df))
    return df[CLEAN_COLUMNS].reset_index(drop=True)

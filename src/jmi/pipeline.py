"""Pipeline de bout en bout : brut → propre → NLP → SQLite → CSV Tableau → rapport."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from jmi.analysis.report import build_report
from jmi.clean.transform import clean_records, select_records
from jmi.collect.base import load_raw_records
from jmi.config import Settings, resource
from jmi.export.tableau import export_views
from jmi.nlp.skills import SkillExtractor, top_terms_by_group
from jmi.warehouse.load import load_warehouse

log = logging.getLogger(__name__)


@dataclass
class RunSummary:
    dataset_label: str
    n_raw: int
    n_offers: int
    n_offer_skills: int
    exports: dict[str, int]


def run_pipeline(settings: Settings) -> RunSummary:
    clean_cfg = settings.section("clean")
    nlp_cfg = settings.section("nlp")

    records = load_raw_records(settings.path("raw"))
    if not records:
        raise SystemExit("data/raw est vide : lance `python -m jmi collect` ou `python -m jmi demo` d'abord.")
    selected, label = select_records(records, clean_cfg.get("data_mode", "auto"))

    offers = clean_records(selected,
                           salary_bounds=(clean_cfg.get("salary_min_plausible", 18000),
                                          clean_cfg.get("salary_max_plausible", 200000)),
                           hours_per_year=clean_cfg.get("hours_per_year", 1607))
    processed = settings.path("processed")
    processed.mkdir(parents=True, exist_ok=True)
    offers.to_csv(processed / "offers_clean.csv", index=False, encoding="utf-8")

    extractor = SkillExtractor(resource(nlp_cfg.get("skills_dictionary", "config/skills_dictionary.yaml"), settings))
    offer_skills = extractor.offer_skills(offers)
    offer_skills.to_csv(processed / "offer_skills.csv", index=False, encoding="utf-8")
    top_terms = top_terms_by_group(offers, top_n=nlp_cfg.get("top_terms_per_role", 25))

    db = settings.path("warehouse")
    views_dir = resource(settings.raw["paths"]["sql_views"], settings)
    load_warehouse(db, resource(settings.raw["paths"]["sql_schema"], settings), views_dir,
                   offers, offer_skills, extractor.catalog(), top_terms, label, len(selected))
    exports = export_views(db, views_dir, settings.path("exports"))
    build_report(settings.path("exports"), settings.path("reports") / "insights.md")

    summary = RunSummary(label, len(selected), len(offers), len(offer_skills), exports)
    log.info("Pipeline terminé — jeu : %s | %s offres brutes → %s offres | %s compétences détectées",
             label, summary.n_raw, summary.n_offers, summary.n_offer_skills)
    return summary

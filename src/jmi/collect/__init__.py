"""Orchestration de la collecte : chaque source écrit un fichier JSONL horodaté dans data/raw/<source>/."""
from __future__ import annotations

import logging
from pathlib import Path

from jmi.collect.adzuna import AdzunaCollector
from jmi.collect.base import HttpClient, save_jsonl
from jmi.collect.demo import generate_demo_offers
from jmi.collect.france_travail import FranceTravailCollector
from jmi.collect.jsonld_scraper import JsonLdScraper, read_urls
from jmi.config import Settings

log = logging.getLogger(__name__)


def _client(settings: Settings, delay: float = 0.5) -> HttpClient:
    http = settings.section("collect").get("http", {})
    return HttpClient(user_agent=http.get("user_agent", "JobMarketIntelligence/1.0"),
                      timeout=http.get("timeout_seconds", 20), max_retries=http.get("max_retries", 3), delay=delay)


def run_collection(settings: Settings, sources: list[str] | None = None) -> dict[str, Path | None]:
    cfg = settings.section("collect")
    raw_dir = settings.path("raw")
    keywords = settings.keywords
    wanted = set(sources or ["france_travail", "adzuna", "jsonld"])
    written: dict[str, Path | None] = {}

    if "france_travail" in wanted and cfg.get("france_travail", {}).get("enabled", True):
        ft = FranceTravailCollector(_client(settings, delay=0.3))
        offers = ft.collect(keywords, cfg["france_travail"].get("max_results_per_keyword", 450))
        written["france_travail"] = save_jsonl(offers, raw_dir, "france_travail")

    if "adzuna" in wanted and cfg.get("adzuna", {}).get("enabled", True):
        az_cfg = cfg.get("adzuna", {})
        az = AdzunaCollector(_client(settings, delay=1.0), country=az_cfg.get("country", "fr"))
        offers = az.collect(keywords, az_cfg.get("results_per_page", 50), az_cfg.get("max_pages_per_keyword", 5))
        written["adzuna"] = save_jsonl(offers, raw_dir, "adzuna")

    if "jsonld" in wanted and cfg.get("jsonld", {}).get("enabled", True):
        js_cfg = cfg.get("jsonld", {})
        urls = read_urls(settings.root / js_cfg.get("urls_file", "config/scrape_urls.txt"))
        if urls:
            scraper = JsonLdScraper(_client(settings, delay=js_cfg.get("delay_seconds", 2.0)))
            written["jsonld_scraper"] = save_jsonl(scraper.scrape(urls), raw_dir, "jsonld_scraper")
        else:
            log.info("Scraper JSON-LD : aucune URL dans %s", js_cfg.get("urls_file"))

    if not any(written.values()):
        log.warning("Aucune donnée réelle collectée. Renseigne .env (voir .env.example) "
                    "ou lance `python -m jmi demo` pour le jeu de démonstration.")
    return written


def write_demo(settings: Settings, n: int = 1200, seed: int = 42) -> Path | None:
    demo_dir = settings.path("raw") / "demo"
    for old in demo_dir.glob("*.jsonl"):  # le jeu démo est régénéré, jamais cumulé
        old.unlink()
    return save_jsonl(generate_demo_offers(n=n, seed=seed), settings.path("raw"), "demo")

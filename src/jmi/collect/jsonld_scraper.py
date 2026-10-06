"""Web scraping des pages d'offres via les données structurées schema.org/JobPosting.

La plupart des sites carrières et des ATS publient un bloc JSON-LD `JobPosting` pour
être indexés par Google Jobs. Le lire est plus robuste que de parser le HTML visuel
(qui change souvent) et ne cible que l'information que l'éditeur rend publique.

Règles de politesse : robots.txt vérifié par domaine, délai entre requêtes, User-Agent explicite.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Iterator

from bs4 import BeautifulSoup

from jmi.collect.base import HttpClient, RawOffer

log = logging.getLogger(__name__)


def _iter_jsonld_objects(data: Any) -> Iterator[dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_objects(item)
    elif isinstance(data, dict):
        yield data
        if "@graph" in data:
            yield from _iter_jsonld_objects(data["@graph"])


def _is_job_posting(obj: dict[str, Any]) -> bool:
    t = obj.get("@type")
    return t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t)


def _html_to_text(html: str | None) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def extract_job_postings(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    postings = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or tag.get_text() or "")
        except json.JSONDecodeError:
            continue
        postings.extend(obj for obj in _iter_jsonld_objects(data) if _is_job_posting(obj))
    return postings


def parse_posting(posting: dict[str, Any], url: str) -> RawOffer:
    org = _first(posting.get("hiringOrganization")) or {}
    location = _first(posting.get("jobLocation")) or {}
    address = location.get("address") or {} if isinstance(location, dict) else {}
    if isinstance(address, str):
        location_raw = address
    else:
        location_raw = ", ".join(filter(None, [address.get("addressLocality"), address.get("addressRegion")])) or None
    geo = location.get("geo") or {} if isinstance(location, dict) else {}

    salary = posting.get("baseSalary") or {}
    value = salary.get("value") if isinstance(salary, dict) else None
    sal_min = sal_max = unit = None
    if isinstance(value, dict):
        sal_min = value.get("minValue") or value.get("value")
        sal_max = value.get("maxValue") or value.get("value")
        unit = value.get("unitText")
    elif isinstance(value, (int, float, str)):
        sal_min = sal_max = value
        unit = salary.get("unitText") if isinstance(salary, dict) else None

    remote = "TELECOMMUTE" if posting.get("jobLocationType") == "TELECOMMUTE" else None
    experience = posting.get("experienceRequirements")
    if isinstance(experience, dict):
        months = experience.get("monthsOfExperience")
        experience = f"{int(months) // 12} ans" if months else None

    employment = posting.get("employmentType")
    if isinstance(employment, list):
        employment = ", ".join(employment)

    source_id = posting.get("identifier")
    if isinstance(source_id, dict):
        source_id = source_id.get("value")
    source_id = str(source_id or hashlib.md5(url.encode()).hexdigest()[:16])

    return RawOffer(
        source="jsonld_scraper",
        source_id=source_id,
        title=posting.get("title") or "",
        description=_html_to_text(posting.get("description")),
        company=org.get("name") if isinstance(org, dict) else str(org),
        location_raw=location_raw,
        published_at=posting.get("datePosted"),
        contract_raw=employment,
        salary_min_raw=float(sal_min) if sal_min not in (None, "") else None,
        salary_max_raw=float(sal_max) if sal_max not in (None, "") else None,
        salary_unit_raw=unit,
        experience_raw=experience if isinstance(experience, str) else None,
        sector_raw=posting.get("industry") if isinstance(posting.get("industry"), str) else None,
        remote_raw=remote,
        url=url,
        latitude=geo.get("latitude"),
        longitude=geo.get("longitude"),
    )


def read_urls(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]


class JsonLdScraper:
    name = "jsonld_scraper"

    def __init__(self, client: HttpClient):
        self.client = client

    def scrape(self, urls: list[str]) -> list[RawOffer]:
        offers: list[RawOffer] = []
        for url in urls:
            if not self.client.allowed_by_robots(url):
                log.info("robots.txt interdit %s — ignorée", url)
                continue
            try:
                resp = self.client.get(url)
                resp.raise_for_status()
            except Exception as exc:  # une page en erreur ne doit pas bloquer la collecte
                log.warning("Page ignorée %s : %s", url, exc)
                continue
            postings = extract_job_postings(resp.text)
            if not postings:
                log.info("Aucun JobPosting JSON-LD sur %s", url)
            offers.extend(parse_posting(p, url) for p in postings)
        return offers

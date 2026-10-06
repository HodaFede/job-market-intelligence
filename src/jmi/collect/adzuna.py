"""Collecteur API Adzuna (https://developer.adzuna.com) — agrégateur d'offres multi-sites."""
from __future__ import annotations

import logging
import os
from typing import Any

from jmi.collect.base import HttpClient, RawOffer

log = logging.getLogger(__name__)

SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"


def _location_text(location: dict[str, Any]) -> str | None:
    """« Ville, Département, Région » : le nom affiché complété par la hiérarchie `area` d'Adzuna."""
    raw = [location.get("display_name") or ""] + list(reversed((location.get("area") or [])[1:]))
    seen: list[str] = []
    for chunk in raw:
        for part in str(chunk).split(","):
            part = part.strip()
            if part and part.lower() not in (x.lower() for x in seen):
                seen.append(part)
    return ", ".join(seen) or None


def parse_offer(item: dict[str, Any], keyword: str | None = None) -> RawOffer:
    location = item.get("location") or {}
    company = item.get("company") or {}
    category = item.get("category") or {}
    # Adzuna estime parfois le salaire (salary_is_predicted = "1") : on ne garde que l'affiché.
    predicted = str(item.get("salary_is_predicted", "0")) == "1"
    return RawOffer(
        source="adzuna",
        source_id=str(item.get("id")),
        title=item.get("title") or "",
        description=item.get("description") or "",
        company=company.get("display_name"),
        location_raw=_location_text(location),
        published_at=item.get("created"),
        contract_raw=" ".join(filter(None, [item.get("contract_type"), item.get("contract_time")])) or None,
        salary_min_raw=None if predicted else item.get("salary_min"),
        salary_max_raw=None if predicted else item.get("salary_max"),
        salary_unit_raw=None if predicted else "year",
        sector_raw=category.get("label"),
        url=item.get("redirect_url"),
        latitude=item.get("latitude"),
        longitude=item.get("longitude"),
        search_keyword=keyword,
    )


class AdzunaCollector:
    name = "adzuna"

    def __init__(self, client: HttpClient, app_id: str | None = None, app_key: str | None = None,
                 country: str = "fr"):
        self.client = client
        self.app_id = app_id or os.environ.get("ADZUNA_APP_ID")
        self.app_key = app_key or os.environ.get("ADZUNA_APP_KEY")
        self.country = country

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    def collect(self, keywords: list[str], results_per_page: int = 50, max_pages: int = 5) -> list[RawOffer]:
        if not self.configured:
            log.warning("Adzuna : identifiants absents (.env) — source ignorée.")
            return []
        offers: list[RawOffer] = []
        for kw in keywords:
            count = 0
            for page in range(1, max_pages + 1):
                resp = self.client.get(
                    SEARCH_URL.format(country=self.country, page=page),
                    params={"app_id": self.app_id, "app_key": self.app_key, "what": kw,
                            "results_per_page": results_per_page, "content-type": "application/json"},
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                offers.extend(parse_offer(item, kw) for item in results)
                count += len(results)
                if len(results) < results_per_page:
                    break
            log.info("Adzuna « %s » : %s offres", kw, count)
        return offers

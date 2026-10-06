"""Collecteur API France Travail — Offres d'emploi v2 (https://francetravail.io).

Authentification OAuth2 "client credentials". L'API renvoie au plus 150 offres par appel
(paramètre `range=debut-fin`) et répond 206 tant qu'il reste des résultats.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Iterator

from jmi.collect.base import HttpClient, RawOffer

log = logging.getLogger(__name__)

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SCOPE = "api_offresdemploiv2 o2dsoffre"
PAGE_SIZE = 150


def parse_offer(item: dict[str, Any], keyword: str | None = None) -> RawOffer:
    lieu = item.get("lieuTravail") or {}
    salaire = item.get("salaire") or {}
    entreprise = item.get("entreprise") or {}
    origine = item.get("origineOffre") or {}
    competences = [c.get("libelle", "") for c in item.get("competences") or []]
    description = item.get("description") or ""
    if competences:  # les compétences structurées enrichissent le texte analysé par le NLP
        description += "\nCompétences : " + ", ".join(competences)
    return RawOffer(
        source="france_travail",
        source_id=str(item.get("id")),
        title=item.get("intitule") or "",
        description=description,
        company=entreprise.get("nom"),
        location_raw=lieu.get("libelle"),
        published_at=item.get("dateCreation"),
        contract_raw=item.get("typeContratLibelle") or item.get("typeContrat"),
        salary_raw=salaire.get("libelle") or salaire.get("commentaire"),
        experience_raw=item.get("experienceLibelle"),
        sector_raw=item.get("secteurActiviteLibelle"),
        remote_raw=None,  # pas de champ dédié : déduit du texte au nettoyage
        url=origine.get("urlOrigine"),
        latitude=lieu.get("latitude"),
        longitude=lieu.get("longitude"),
        search_keyword=keyword,
    )


class FranceTravailCollector:
    name = "france_travail"

    def __init__(self, client: HttpClient, client_id: str | None = None, client_secret: str | None = None):
        self.client = client
        self.client_id = client_id or os.environ.get("FRANCE_TRAVAIL_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET")
        self._token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_token(self) -> str:
        resp = self.client.post(
            TOKEN_URL,
            params={"realm": "/partenaire"},
            data={"grant_type": "client_credentials", "client_id": self.client_id,
                  "client_secret": self.client_secret, "scope": SCOPE},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def search(self, keyword: str, max_results: int = 450) -> Iterator[RawOffer]:
        if self._token is None:
            self._token = self._get_token()
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        start = 0
        while start < max_results:
            end = min(start + PAGE_SIZE, max_results) - 1
            resp = self.client.get(SEARCH_URL, headers=headers,
                                   params={"motsCles": keyword, "range": f"{start}-{end}"})
            if resp.status_code == 204:
                break
            resp.raise_for_status()
            results = resp.json().get("resultats", [])
            for item in results:
                yield parse_offer(item, keyword)
            if resp.status_code == 200 or len(results) < (end - start + 1):
                break  # 200 = dernière page
            start = end + 1

    def collect(self, keywords: list[str], max_results: int = 450) -> list[RawOffer]:
        if not self.configured:
            log.warning("France Travail : identifiants absents (.env) — source ignorée.")
            return []
        offers: list[RawOffer] = []
        for kw in keywords:
            batch = list(self.search(kw, max_results))
            log.info("France Travail « %s » : %s offres", kw, len(batch))
            offers.extend(batch)
        return offers

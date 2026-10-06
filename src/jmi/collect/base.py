"""Briques communes aux collecteurs : schéma brut, client HTTP poli, stockage JSONL."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib import robotparser
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)


@dataclass
class RawOffer:
    """Format commun à toutes les sources, avant nettoyage.

    On conserve les champs texte bruts (salaire, lieu, expérience...) : le parsing est
    fait une seule fois, dans `jmi.clean`, pour toutes les sources.
    """

    source: str
    source_id: str
    title: str
    description: str = ""
    company: str | None = None
    location_raw: str | None = None
    published_at: str | None = None
    contract_raw: str | None = None
    salary_raw: str | None = None
    salary_min_raw: float | None = None
    salary_max_raw: float | None = None
    salary_unit_raw: str | None = None
    experience_raw: str | None = None
    sector_raw: str | None = None
    remote_raw: str | None = None
    url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    search_keyword: str | None = None
    is_demo: bool = False
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HttpClient:
    """Session requests avec User-Agent explicite, retries exponentiels et respect de robots.txt."""

    def __init__(self, user_agent: str, timeout: float = 20, max_retries: int = 3, delay: float = 0.0,
                 session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Language": "fr-FR,fr;q=0.9"})
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._last_call = 0.0

    def _throttle(self) -> None:
        wait = self.delay - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                resp = self.session.get(f"{base}/robots.txt", timeout=self.timeout)
                if resp.status_code >= 400:
                    rp = None  # pas de robots.txt : tout est autorisé
                else:
                    rp.parse(resp.text.splitlines())
            except requests.RequestException:
                rp = None
            self._robots[base] = rp
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(self.user_agent, url)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.request(method, url, **kwargs)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                backoff = 2 ** attempt
                log.warning("Requête échouée (%s/%s) %s : %s — nouvel essai dans %ss",
                            attempt, self.max_retries, url, exc, backoff)
                if attempt < self.max_retries:
                    time.sleep(backoff)
        raise RuntimeError(f"Échec après {self.max_retries} tentatives : {url}") from last_exc

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)


def save_jsonl(offers: Iterable[RawOffer], raw_dir: Path, source: str) -> Path | None:
    offers = list(offers)
    if not offers:
        return None
    out_dir = raw_dir / source
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"{source}_{stamp}.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for offer in offers:
            fh.write(json.dumps(offer.to_dict(), ensure_ascii=False) + "\n")
    log.info("%s offres enregistrées dans %s", len(offers), out)
    return out


def load_raw_records(raw_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*/*.jsonl")):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    rec["_raw_file"] = path.name
                    records.append(rec)
    return records

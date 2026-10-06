from pathlib import Path

from jmi.collect import adzuna, france_travail, jsonld_scraper
from jmi.collect.base import RawOffer, load_raw_records, save_jsonl
from jmi.collect.demo import generate_demo_offers


def test_france_travail_parse(fixture_json):
    item = fixture_json("france_travail_search.json")["resultats"][0]
    offer = france_travail.parse_offer(item, "data analyst")
    assert offer.source == "france_travail" and offer.source_id == "198XKQP"
    assert offer.location_raw == "92 - PUTEAUX"
    assert offer.salary_raw.startswith("Annuel de 40000")
    assert "Power BI" in offer.description  # compétences structurées ajoutées au texte
    assert offer.is_demo is False


def test_france_travail_pagination_and_auth(fixture_json, fake_client, fake_response):
    payload = fixture_json("france_travail_search.json")
    client = fake_client([
        fake_response(200, {"access_token": "tok"}),
        fake_response(200, payload),           # 200 = dernière page
    ])
    ft = france_travail.FranceTravailCollector(client, "id", "secret")
    offers = ft.collect(["data analyst"], max_results=300)
    assert len(offers) == 2
    method, url, kwargs = client.calls[1]
    assert kwargs["headers"]["Authorization"] == "Bearer tok"
    assert kwargs["params"]["range"] == "0-149"


def test_france_travail_without_credentials_is_skipped(fake_client, monkeypatch):
    monkeypatch.delenv("FRANCE_TRAVAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("FRANCE_TRAVAIL_CLIENT_SECRET", raising=False)
    client = fake_client([])
    assert france_travail.FranceTravailCollector(client).collect(["data"]) == []
    assert client.calls == []


def test_adzuna_parse_ignores_predicted_salary(fixture_json):
    real, predicted = fixture_json("adzuna_search.json")["results"]
    a = adzuna.parse_offer(real)
    assert (a.salary_min_raw, a.salary_max_raw, a.salary_unit_raw) == (60000, 70000, "year")
    assert a.company == "Exemple Tech"
    b = adzuna.parse_offer(predicted)
    assert b.salary_min_raw is None and b.salary_max_raw is None


def test_jsonld_extracts_job_posting_from_graph(fixture_text):
    postings = jsonld_scraper.extract_job_postings(fixture_text("jobposting_page.html"))
    assert len(postings) == 1  # Organization ignoré, JSON cassé toléré
    offer = jsonld_scraper.parse_posting(postings[0], "https://exemple.fr/offre/42")
    assert offer.title == "Consultant Data & IA Junior"
    assert offer.source_id == "REF-2026-042"
    assert offer.location_raw == "Nantes, Pays de la Loire"
    assert (offer.salary_min_raw, offer.salary_max_raw, offer.salary_unit_raw) == (38000, 42000, "YEAR")
    assert "<strong>" not in offer.description and "Python" in offer.description


def test_scraper_respects_robots(fake_client, fake_response, fixture_text):
    blocked = fake_client([], allowed=False)
    assert jsonld_scraper.JsonLdScraper(blocked).scrape(["https://exemple.fr/offre/1"]) == []
    assert blocked.calls == []
    ok = fake_client([fake_response(200, text=fixture_text("jobposting_page.html"))])
    assert len(jsonld_scraper.JsonLdScraper(ok).scrape(["https://exemple.fr/offre/1"])) == 1


def test_read_urls_ignores_comments(tmp_path: Path):
    f = tmp_path / "urls.txt"
    f.write_text("# commentaire\n\nhttps://a.fr/1\n  https://b.fr/2  \n", encoding="utf-8")
    assert jsonld_scraper.read_urls(f) == ["https://a.fr/1", "https://b.fr/2"]


def test_jsonl_roundtrip(tmp_path: Path):
    offers = [RawOffer(source="test", source_id=str(i), title=f"Data Analyst {i}") for i in range(3)]
    save_jsonl(offers, tmp_path, "test")
    records = load_raw_records(tmp_path)
    assert [r["source_id"] for r in records] == ["0", "1", "2"]


def test_demo_is_flagged_and_reproducible():
    a = generate_demo_offers(n=50, seed=1)
    b = generate_demo_offers(n=50, seed=1)
    assert [o.to_dict()["title"] for o in a] == [o.to_dict()["title"] for o in b]
    assert all(o.is_demo and o.source == "demo" for o in a)

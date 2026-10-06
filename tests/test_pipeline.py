"""Test de bout en bout : démo → nettoyage → NLP → SQLite → CSV Tableau → rapport, dans un dossier temporaire."""
import sqlite3

import pandas as pd
import pytest

from jmi.collect import write_demo
from jmi.collect.base import RawOffer, save_jsonl
from jmi.config import load_settings
from jmi.pipeline import run_pipeline

EXPECTED_EXPORTS = {
    "offres", "offres_competences", "kpi_globaux", "salaires_metier_seniorite", "villes", "secteurs",
    "competences_par_metier", "prime_salariale_competences", "paires_competences", "tendance_mensuelle",
    "teletravail_metier", "seniorite_metier", "contrats", "termes_tfidf",
}


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    root = tmp_path_factory.mktemp("jmi")
    settings = load_settings(root=root)
    write_demo(settings, n=400, seed=7)
    summary = run_pipeline(settings)
    return settings, summary


def test_all_exports_written(run):
    settings, summary = run
    exports = settings.path("exports")
    assert set(summary.exports) == EXPECTED_EXPORTS
    for name in EXPECTED_EXPORTS:
        assert (exports / f"{name}.csv").exists()


def test_offres_csv_is_tableau_friendly(run):
    settings, _ = run
    df = pd.read_csv(settings.path("exports") / "offres.csv")
    assert df["id_offre"].is_unique
    assert {"metier", "seniorite", "ville", "latitude", "longitude", "salaire_annuel", "teletravail",
            "date_publication", "est_demo"} <= set(df.columns)
    assert "description" not in df.columns
    assert df["est_demo"].eq(1).all()
    pd.to_datetime(df["date_publication"], format="%Y-%m-%d")  # dates ISO lisibles par Tableau


def test_bridge_table_references_existing_offers(run):
    settings, _ = run
    offers = pd.read_csv(settings.path("exports") / "offres.csv")
    links = pd.read_csv(settings.path("exports") / "offres_competences.csv")
    assert links["id_offre"].isin(offers["id_offre"]).all()
    assert not links.duplicated(["id_offre", "competence"]).any()


def test_kpis_match_offers(run):
    settings, _ = run
    offers = pd.read_csv(settings.path("exports") / "offres.csv")
    kpi = pd.read_csv(settings.path("exports") / "kpi_globaux.csv").iloc[0]
    assert kpi["nb_offres"] == len(offers)
    assert kpi["salaire_median"] == pytest.approx(offers["salaire_annuel"].median(), abs=1)
    assert kpi["salaire_moyen"] == pytest.approx(offers["salaire_annuel"].mean(), abs=1)
    assert kpi["jeu_de_donnees"].startswith("Démonstration")
    assert kpi["pct_offres_avec_competence"] == pytest.approx(100 * (offers["nb_competences"] > 0).mean(), abs=0.1)


def test_sql_median_by_group_matches_pandas(run):
    settings, _ = run
    offers = pd.read_csv(settings.path("exports") / "offres.csv")
    sal = pd.read_csv(settings.path("exports") / "salaires_metier_seniorite.csv")
    expected = offers.dropna(subset=["salaire_annuel"]).groupby(["metier", "seniorite"])["salaire_annuel"].median()
    for row in sal.itertuples():
        assert row.salaire_median == pytest.approx(expected[(row.metier, row.seniorite)], abs=1)
        assert row.salaire_q1 <= row.salaire_median <= row.salaire_q3


def test_skill_shares_are_consistent(run):
    settings, _ = run
    s = pd.read_csv(settings.path("exports") / "competences_par_metier.csv")
    assert s["part_offres_pct"].between(0, 100).all()
    assert "Tous métiers" in set(s["metier"])


def test_pair_lift_is_symmetric_and_unique(run):
    settings, _ = run
    p = pd.read_csv(settings.path("exports") / "paires_competences.csv")
    assert (p["competence_a"] < p["competence_b"]).all()
    assert (p["nb_offres_communes"] >= 5).all()


def test_report_and_run_log(run):
    settings, summary = run
    report = (settings.path("reports") / "insights.md").read_text(encoding="utf-8")
    assert "démonstration" in report.lower()
    con = sqlite3.connect(settings.path("warehouse"))
    label, n = con.execute("SELECT dataset_label, n_offers FROM pipeline_runs").fetchone()
    con.close()
    assert label == "démo" and n == summary.n_offers


def test_real_data_takes_precedence_over_demo(tmp_path):
    settings = load_settings(root=tmp_path)
    write_demo(settings, n=100, seed=1)
    real = [RawOffer(source="france_travail", source_id=str(i), title="Data Analyst",
                     description="SQL, Python", company=f"Entreprise {i}", location_raw="Lyon",
                     published_at="2026-09-01") for i in range(30)]
    save_jsonl(real, settings.path("raw"), "france_travail")
    summary = run_pipeline(settings)
    offers = pd.read_csv(settings.path("exports") / "offres.csv")
    assert summary.dataset_label == "réel"
    assert set(offers["source"]) == {"france_travail"} and offers["est_demo"].eq(0).all()


def test_prime_salariale_has_reliability_flag(run):
    settings, _ = run
    premium = pd.read_csv(settings.path("exports") / "prime_salariale_competences.csv")
    assert "fiabilite" in premium.columns
    assert (premium["nb_offres_avec"] >= 10).all()
    assert premium["fiabilite"].isin(["Moyenne", "Faible (10 à 19 offres)"]).all()

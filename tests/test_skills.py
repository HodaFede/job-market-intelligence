import pandas as pd
import pytest

from jmi.nlp.skills import SkillExtractor, top_terms_by_group


@pytest.fixture(scope="module")
def extractor():
    from pathlib import Path
    return SkillExtractor(Path(__file__).resolve().parents[1] / "config" / "skills_dictionary.yaml")


def test_tableau_de_bord_is_not_the_tableau_tool(extractor):
    assert "Tableau" not in extractor.extract("Création de tableaux de bord sous Excel")
    assert "Tableau" not in extractor.extract("Un tableau croisé dynamique")
    found = extractor.extract("Vous construirez des tableaux de bord avec Tableau.")
    assert "Tableau" in found and "KPI & reporting" in found


def test_r_language_vs_r_and_d(extractor):
    assert "R" in extractor.extract("Maîtrise de R/Python")
    assert "R" not in extractor.extract("Expérience en R&D chimie")
    assert "R" not in extractor.extract("rigueur et recherche")


def test_technical_names_with_symbols(extractor):
    found = extractor.extract("CI/CD, scikit-learn, Power BI et PostgreSQL")
    assert {"CI/CD", "Scikit-learn", "Power BI", "PostgreSQL"} <= set(found)


def test_java_vs_javascript(extractor):
    assert extractor.extract("JavaScript uniquement") == ["JavaScript"]


def test_accents_are_ignored(extractor):
    assert "Séries temporelles" in extractor.extract("Modèles de series temporelles")
    assert "IA générative" in extractor.extract("projets d'IA generative")


def test_offer_skills_long_format(extractor):
    offers = pd.DataFrame([
        {"offer_id": "a", "title": "Data Analyst", "description": "SQL et Tableau"},
        {"offer_id": "b", "title": "Data Engineer", "description": "Spark, Airflow"},
        {"offer_id": "c", "title": "Assistant", "description": ""},
    ])
    links = extractor.offer_skills(offers)
    assert set(links.columns) == {"offer_id", "skill", "category", "skill_type"}
    assert set(links.loc[links.offer_id == "a", "skill"]) == {"SQL", "Tableau"}
    assert "c" not in set(links.offer_id)
    assert not links.duplicated(["offer_id", "skill"]).any()


def test_catalog_names_are_unique(extractor):
    cat = extractor.catalog()
    assert cat["skill"].is_unique
    assert set(cat["skill_type"]) <= {"tech", "skill"}


def test_tfidf_bigrams_do_not_cross_list_separators():
    offers = pd.DataFrame({
        "role_family": ["A"] * 4 + ["B"] * 4,
        "description": ["Spark, Kafka, Terraform"] * 4 + ["Excel, reporting financier"] * 4,
    })
    terms = top_terms_by_group(offers, min_df=2)
    assert "terraform" in set(terms.loc[terms.role_family == "A", "term"])
    assert "spark kafka" not in set(terms["term"])
    assert "reporting financier" in set(terms["term"])

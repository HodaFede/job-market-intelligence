"""Garde-fous sur le dépôt : visualisation 100 % Tableau Public, documentation alignée sur les exports."""
import re
from pathlib import Path

from jmi.export.tableau import export_name

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".sql", ".yaml", ".yml", ".toml", ".txt", ".cfg", ".ini"}
# Fichiers où l'outil peut apparaître légitimement : c'est une compétence demandée dans les offres.
SKILL_CONTEXT = {"config/skills_dictionary.yaml", "src/jmi/collect/demo.py", "src/jmi/analysis/report.py",
                 "tests/test_skills.py", "tests/test_collectors.py", "tests/test_project.py", "tests/fixtures/france_travail_search.json"}


def _project_files():
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT).as_posix()
        if any(part in rel.split("/") for part in (".venv", ".git", "data", "exports", "reports", "__pycache__")):
            continue
        if path.is_file():
            yield rel, path


def test_no_other_bi_tool_used_for_visualisation():
    assert not list(ROOT.rglob("*.pbix")) and not list(ROOT.rglob("*.pbit"))
    offenders = []
    for rel, path in _project_files():
        if path.suffix in TEXT_SUFFIXES and rel not in SKILL_CONTEXT:
            if re.search(r"power\s?bi", path.read_text(encoding="utf-8", errors="ignore"), re.I):
                offenders.append(rel)
    assert offenders == [], f"Référence à un autre outil de BI : {offenders}"


def test_every_export_is_documented():
    views = sorted((ROOT / "sql" / "views").glob("*.sql"))
    guide = (ROOT / "docs" / "tableau_guide.md").read_text(encoding="utf-8")
    dictionary = (ROOT / "docs" / "data_dictionary.md").read_text(encoding="utf-8")
    for v in views:
        name = f"{export_name(v)}.csv"
        assert name in guide, f"{name} absent du guide Tableau"
        assert name in dictionary, f"{name} absent du dictionnaire de données"


def test_view_names_match_files():
    for v in (ROOT / "sql" / "views").glob("*.sql"):
        assert f"CREATE VIEW v_{export_name(v)} " in v.read_text(encoding="utf-8")


def test_readme_points_to_tableau_public_and_docs():
    readme = re.sub(r"<!--.*?-->", "", (ROOT / "README.md").read_text(encoding="utf-8"), flags=re.S)
    assert "Tableau Public" in readme
    for link in re.findall(r"\]\(((?:docs|reports)/[^)#]+)\)", readme):
        if link.startswith("reports/"):
            continue  # généré par le pipeline
        assert (ROOT / link).exists(), f"Lien cassé dans le README : {link}"


def test_secrets_are_not_versioned():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore.splitlines()
    assert "data/raw/**" in gitignore

from jmi.clean.transform import CLEAN_COLUMNS, clean_records, select_records


def _rec(**kw):
    base = {"source": "test", "source_id": "1", "title": "Data Analyst", "description": "SQL", "company": "ACME",
            "location_raw": "Paris", "published_at": "2026-09-01", "is_demo": False}
    base.update(kw)
    return base


def test_real_data_is_never_replaced_by_demo():
    records = [_rec(source_id="r1"), _rec(source="demo", source_id="d1", is_demo=True)]
    selected, label = select_records(records, "auto")
    assert label == "réel" and [r["source_id"] for r in selected] == ["r1"]


def test_demo_used_only_when_no_real_data():
    selected, label = select_records([_rec(source="demo", is_demo=True)], "auto")
    assert label == "démo" and len(selected) == 1
    assert select_records([_rec(source="demo", is_demo=True)], "real")[0] == []


def test_clean_output_schema_and_values():
    df = clean_records([_rec(salary_raw="45K€ - 55K€", contract_raw="CDI",
                             description="SQL, Tableau. Télétravail 2 jours par semaine.")])
    assert list(df.columns) == CLEAN_COLUMNS
    row = df.iloc[0]
    assert row.offer_id == "test:1"
    assert row.salary_mid == 50000 and row.has_salary == 1
    assert row.remote_policy == "Hybride" and row.city == "Paris" and row.contract_type == "CDI"
    assert str(row.published_month) == "2026-09-01"


def test_dedup_same_offer_from_two_sources():
    df = clean_records([
        _rec(source="france_travail", source_id="A", title="Data Analyst H/F", company="ACME"),
        _rec(source="adzuna", source_id="B", title="data analyst h/f", company="Acme", published_at="2026-09-03"),
        _rec(source="adzuna", source_id="C", title="Data Engineer", company="ACME"),
    ])
    assert len(df) == 2
    assert "france_travail:A" in set(df.offer_id)  # on garde la publication la plus ancienne


def test_internship_and_outlier_salaries_are_excluded():
    df = clean_records([
        _rec(source_id="s", title="Stage Data Analyst", salary_raw="Mensuel de 1500 Euros"),
        _rec(source_id="o", title="Data Analyst", salary_raw="5 000 000 € par an"),
    ])
    assert df["salary_mid"].isna().all() and (df["has_salary"] == 0).all()


def test_rows_without_title_are_dropped():
    assert clean_records([_rec(title="")]).empty

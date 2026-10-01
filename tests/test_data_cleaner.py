"""Tests for DataCleaner."""

import pandas as pd
import pytest

from modules.data_cleaner import DataCleaner


@pytest.fixture
def cleaner():
    return DataCleaner()


def make_df(cleaner, rows):
    return cleaner.to_dataframe(rows)


def test_whitespace_is_collapsed_and_trimmed(cleaner):
    df = make_df(cleaner, [{"Company Name": "  Acme   Bio \n", "Phone": " +34  600 ", "Email": "A@B.COM ", "City": " Madrid ", "Website": "HTTP://X.COM/ "}])
    out = cleaner.clean(df).iloc[0]
    assert out["Company Name"] == "Acme Bio"
    assert out["Phone"] == "+34 600"
    assert out["Email"] == "a@b.com"
    assert out["Website"] == "http://x.com"


def test_duplicates_removed_by_email_then_name(cleaner):
    df = make_df(cleaner, [
        {"Company Name": "A", "Email": "x@a.com"},
        {"Company Name": "A (copy)", "Email": "X@a.com"},
        {"Company Name": "No Mail", "Email": ""},
        {"Company Name": "no mail", "Email": ""},
    ])
    assert len(cleaner.clean(df)) == 2


def test_rows_without_company_name_are_dropped(cleaner):
    df = make_df(cleaner, [{"Company Name": "  ", "Email": "x@a.com"}, {"Company Name": "Ok", "Email": "y@a.com"}])
    assert cleaner.clean(df)["Company Name"].tolist() == ["Ok"]


@pytest.mark.parametrize("raw,expected", [
    ("Barcelona - 08028", "Barcelona"),
    ("08006 Barcelona", "Barcelona"),
    ("San Mateo de Gállego - C.P 50840", "San Mateo de Gállego"),
    ("Madrid", "Madrid"),
    ("", ""),
])
def test_clean_city(raw, expected):
    assert DataCleaner.clean_city(raw) == expected


def test_public_sample_only_complete_rows_with_generic_mailboxes(cleaner):
    df = make_df(cleaner, [
        {"Company Name": "Generic", "Phone": "1", "Email": "info@a.com", "City": "M", "Website": "w"},
        {"Company Name": "Personal", "Phone": "1", "Email": "jane.doe@b.com", "City": "M", "Website": "w"},
        {"Company Name": "Incomplete", "Phone": "", "Email": "info@c.com", "City": "M", "Website": "w"},
    ])
    sample = cleaner.public_sample(df, size=10)
    assert sample["Company Name"].tolist() == ["Generic"]


def test_export_writes_utf8_csv_without_index(cleaner, tmp_path):
    df = make_df(cleaner, [{"Company Name": "Biotecnología S.L.", "Email": "a@b.com"}])
    path = cleaner.export(cleaner.clean(df), str(tmp_path / "out.csv"))
    back = pd.read_csv(path, dtype=str).fillna("")
    assert list(back.columns) == ["Company Name", "Phone", "Email", "City", "Website"]
    assert back.loc[0, "Company Name"] == "Biotecnología S.L."


@pytest.mark.parametrize("raw,expected", [
    ("+34 948346480", "+34 948 346 480"),
    ("+34 93 403 45 53", "+34 934 034 553"),
    ("0034 913 43 99 86", "+34 913 439 986"),
    ("+49 89 4520 1180", "+49 89 4520 1180"),
    ("", ""),
])
def test_normalize_phone(raw, expected):
    assert DataCleaner.normalize_phone(raw) == expected

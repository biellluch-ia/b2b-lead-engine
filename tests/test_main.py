"""End-to-end test of the CLI in offline demo mode."""

import pandas as pd

import main


def test_demo_run_produces_clean_csv(tmp_path):
    out = tmp_path / "leads.csv"
    assert main.main(["--output", str(out)]) == 0
    df = pd.read_csv(out)
    assert len(df) == 5  # 6 raw records, 1 duplicate removed
    assert not df["Company Name"].duplicated().any()


def test_unknown_profile_returns_error(tmp_path):
    assert main.main(["--profile", "does_not_exist", "--output", str(tmp_path / "x.csv")]) == 1

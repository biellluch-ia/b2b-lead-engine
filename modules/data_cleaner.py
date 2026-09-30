"""Pandas-based cleaning and export of scraped lead data."""

from __future__ import annotations

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


class DataCleaner:
    """Normalises, de-duplicates and exports lead records."""

    def __init__(self, columns: list[str] | None = None) -> None:
        self.columns = columns or config.OUTPUT_COLUMNS

    def to_dataframe(self, records: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(records, columns=self.columns)

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip whitespace, normalise emails/URLs, drop empties and duplicates."""
        df = df.copy().fillna("")
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        df["Email"] = df["Email"].str.lower()
        df["Website"] = df["Website"].str.lower().str.rstrip("/")
        df = df[df["Company Name"] != ""]

        before = len(df)
        dedupe_key = df["Email"].where(df["Email"] != "", df["Company Name"].str.lower())
        df = df.loc[~dedupe_key.duplicated()].reset_index(drop=True)
        logger.info("Removed %d duplicate rows", before - len(df))
        return df

    def export(self, df: pd.DataFrame, path: str = config.OUTPUT_FILE) -> str:
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info("Exported %d rows to %s", len(df), path)
        return path

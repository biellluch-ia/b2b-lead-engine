"""Pandas-based cleaning and export of scraped lead data."""

from __future__ import annotations

import logging
import re

import pandas as pd

import config

logger = logging.getLogger(__name__)

# Role mailboxes (not tied to a named individual) - safe for public samples.
GENERIC_LOCAL_PARTS = {
    "info", "contact", "contacto", "hello", "hola", "admin", "office", "oficina",
    "sales", "ventas", "comercial", "secretaria", "secretariageneral", "marketing",
    "business", "bd", "mail", "general", "comunicacion", "press", "prensa", "sales",
}
POSTCODE_PREFIX_RE = re.compile(r"^\s*(?:C\.?\s?P\.?\s*)?\d{4,5}\s*[-,]?\s*", re.IGNORECASE)
POSTCODE_SUFFIX_RE = re.compile(r"\s*[-,(]?\s*(?:C\.?\s?P\.?\s*)?\d{4,5}\)?\s*$", re.IGNORECASE)


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
        df["City"] = df["City"].map(self.clean_city)
        df["Phone"] = df["Phone"].map(self.normalize_phone)
        df["Email"] = df["Email"].str.lower()
        df["Website"] = df["Website"].str.lower().str.rstrip("/")
        df = df[df["Company Name"] != ""]

        before = len(df)
        dedupe_key = df["Email"].where(df["Email"] != "", df["Company Name"].str.lower())
        df = df.loc[~dedupe_key.duplicated()].reset_index(drop=True)
        logger.info("Removed %d duplicate rows", before - len(df))
        return df

    @staticmethod
    def normalize_phone(value: str) -> str:
        """Format Spanish numbers as '+34 XXX XXX XXX'; leave others untouched."""
        digits = re.sub(r"\D", "", value)
        if digits.startswith("0034"):
            digits = digits[2:]
        if digits.startswith("34") and len(digits) == 11:
            digits = digits[2:]
            return f"+34 {digits[0:3]} {digits[3:6]} {digits[6:9]}"
        return value

    @staticmethod
    def clean_city(value: str) -> str:
        """Drop postcodes glued to city names (e.g. 'Barcelona - 08028', '08006 Barcelona')."""
        value = POSTCODE_PREFIX_RE.sub("", value)
        return POSTCODE_SUFFIX_RE.sub("", value).strip(" -,")

    @staticmethod
    def is_generic_email(email: str) -> bool:
        return email.split("@")[0].lower() in GENERIC_LOCAL_PARTS

    def public_sample(self, df: pd.DataFrame, size: int = 15, seed: int = 7) -> pd.DataFrame:
        """Complete rows with role mailboxes only (no named individuals)."""
        complete = df[(df != "").all(axis=1)]
        generic = complete[complete["Email"].map(self.is_generic_email)]
        return generic.sample(n=min(size, len(generic)), random_state=seed).reset_index(drop=True)

    def export(self, df: pd.DataFrame, path: str = config.OUTPUT_FILE) -> str:
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info("Exported %d rows to %s", len(df), path)
        return path

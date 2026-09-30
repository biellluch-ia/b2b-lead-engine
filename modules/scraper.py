"""HTTP fetching and HTML parsing for B2B directory pages."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

import config

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


class B2BDirectoryScraper:
    """Fetches directory pages and extracts structured company records."""

    def __init__(
        self,
        headers: Optional[dict] = None,
        timeout: float = config.REQUEST_TIMEOUT,
        delay: float = config.REQUEST_DELAY,
        selectors: Optional[dict] = None,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(headers or config.HEADERS)
        self.timeout = timeout
        self.delay = delay
        self.selectors = selectors or config.SELECTORS

    # ------------------------------------------------------------------ HTTP
    def fetch(self, url: str) -> Optional[str]:
        """Return the page HTML, or None if every attempt failed."""
        for attempt in range(1, config.MAX_RETRIES + 2):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                logger.info("Fetched %s (HTTP %s)", url, response.status_code)
                return response.text
            except requests.RequestException as exc:
                logger.warning("Attempt %d failed for %s: %s", attempt, url, exc)
                time.sleep(self.delay)
        logger.error("Giving up on %s", url)
        return None

    # --------------------------------------------------------------- Parsing
    def parse(self, html: str) -> list[dict]:
        """Extract one record per listing card found in the HTML."""
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(self.selectors["card"])
        records = [self._parse_card(card) for card in cards]
        return [r for r in records if r["Company Name"]]

    def _parse_card(self, card: Tag) -> dict:
        return {
            "Company Name": self._text(card, "company_name"),
            "Phone": self._extract_phone(card),
            "Email": self._extract_email(card),
            "City": self._text(card, "city"),
            "Website": self._extract_website(card),
        }

    def _text(self, card: Tag, key: str) -> str:
        node = card.select_one(self.selectors[key])
        return node.get_text(" ", strip=True) if node else ""

    def _extract_email(self, card: Tag) -> str:
        link = card.select_one("a[href^='mailto:']")
        if link:
            return link["href"].replace("mailto:", "").split("?")[0].strip()
        match = EMAIL_RE.search(self._text(card, "email") or card.get_text(" "))
        return match.group(0) if match else ""

    def _extract_phone(self, card: Tag) -> str:
        link = card.select_one("a[href^='tel:']")
        if link:
            return link["href"].replace("tel:", "").strip()
        match = PHONE_RE.search(self._text(card, "phone"))
        return match.group(0).strip() if match else ""

    def _extract_website(self, card: Tag) -> str:
        link = card.select_one(self.selectors["website"])
        return link["href"].strip() if link and link.has_attr("href") else ""

    # ------------------------------------------------------------- Pipeline
    def scrape(self, urls: list[str]) -> list[dict]:
        """Fetch and parse each URL, pausing between requests."""
        records: list[dict] = []
        for index, url in enumerate(urls):
            if index:
                time.sleep(self.delay)
            html = self.fetch(url)
            if html is None:
                continue
            page_records = self.parse(html)
            logger.info("Extracted %d records from %s", len(page_records), url)
            records.extend(page_records)
        return records

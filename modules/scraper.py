"""HTTP fetching and HTML parsing for B2B directory pages."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib import robotparser
from urllib.parse import urljoin, urlparse

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
        max_pages: int = config.MAX_PAGES,
        respect_robots: bool = config.RESPECT_ROBOTS,
        max_detail_pages: Optional[int] = None,
        default_country_code: str = "",
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(headers or config.HEADERS)
        self.timeout = timeout
        self.delay = delay
        self.selectors = selectors or config.SELECTORS
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.max_detail_pages = max_detail_pages
        self.default_country_code = default_country_code
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._requests_made = 0
        self._robots: dict[str, Optional[robotparser.RobotFileParser]] = {}

    # ---------------------------------------------------------------- robots
    def is_allowed(self, url: str) -> bool:
        """Check robots.txt for the URL's host (allowed if none is published)."""
        if not self.respect_robots:
            return True
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser = robotparser.RobotFileParser()
            try:
                resp = self.session.get(f"{origin}/robots.txt", timeout=self.timeout)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                    self._robots[origin] = parser
                else:
                    self._robots[origin] = None
            except requests.RequestException:
                logger.warning("Could not read robots.txt for %s; skipping URL", origin)
                return False
        parser = self._robots[origin]
        return True if parser is None else parser.can_fetch(self.session.headers["User-Agent"], url)

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
    def parse(self, html: str, base_url: str = "") -> list[dict]:
        """Extract one record per listing card found in the HTML."""
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(self.selectors["card"])
        records = [self._parse_card(card) for card in cards]
        for record in records:
            if base_url and record["Website"]:
                record["Website"] = urljoin(base_url, record["Website"])
        return [r for r in records if r["Company Name"]]

    def next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Return the absolute URL of the next results page, if any."""
        selector = self.selectors.get("next_page")
        if not selector:
            return None
        link = BeautifulSoup(html, "html.parser").select_one(selector)
        if link and link.has_attr("href"):
            return urljoin(current_url, link["href"])
        return None

    def _parse_card(self, card: Tag) -> dict:
        return {
            "Company Name": self._text(card, "company_name"),
            "Phone": self._extract_phone(card),
            "Email": self._extract_email(card),
            "City": self._text(card, "city"),
            "Website": self._extract_website(card),
        }

    def _text(self, card: Tag, key: str) -> str:
        selector = self.selectors.get(key)
        node = card.select_one(selector) if selector else None
        return node.get_text(" ", strip=True) if node else ""

    def _extract_email(self, card: Tag) -> str:
        if self.selectors.get("email"):  # explicit selector: no generic fallback
            match = EMAIL_RE.search(self._text(card, "email"))
            return match.group(0) if match else ""
        link = card.select_one("a[href^='mailto:']")
        if link:
            return link["href"].replace("mailto:", "").split("?")[0].strip()
        match = EMAIL_RE.search(card.get_text(" "))
        return match.group(0) if match else ""

    def _extract_phone(self, card: Tag) -> str:
        if self.selectors.get("phone"):  # explicit selector: no generic fallback
            match = PHONE_RE.search(self._text(card, "phone"))
            return self._with_country_code(match.group(0).strip()) if match else ""
        link = card.select_one("a[href^='tel:']")
        return link["href"].replace("tel:", "").strip() if link else ""

    def _with_country_code(self, phone: str) -> str:
        if self.default_country_code and not phone.startswith(("+", "00")):
            return f"{self.default_country_code} {phone}"
        return phone

    def _extract_website(self, card: Tag) -> str:
        selector = self.selectors.get("website")
        link = card.select_one(selector) if selector else None
        return link["href"].strip() if link and link.has_attr("href") else ""

    # ------------------------------------------------------------- Pipeline
    def scrape(self, urls: list[str]) -> list[dict]:
        """Crawl each start URL (following pagination), pausing between requests.

        If the profile defines a ``detail_link`` selector, listing pages only
        provide links and the records are extracted from each detail page.
        """
        records: list[dict] = []
        detail_urls: list[str] = []
        detail_mode = bool(self.selectors.get("detail_link"))
        for start in urls:
            url: Optional[str] = start
            pages = 0
            while url and pages < self.max_pages:
                html = self._polite_fetch(url)
                if html is None:
                    break
                pages += 1
                if detail_mode:
                    found = self.detail_links(html, url)
                    logger.info("Page %d: %d detail links from %s", pages, len(found), url)
                    detail_urls.extend(u for u in found if u not in detail_urls)
                else:
                    page_records = self.parse(html, base_url=url)
                    logger.info("Page %d: %d records from %s", pages, len(page_records), url)
                    records.extend(page_records)
                url = self.next_page_url(html, url)

        if detail_mode:
            if self.max_detail_pages:
                detail_urls = detail_urls[: self.max_detail_pages]
            total = len(detail_urls)
            failed: list[str] = []
            for index, detail_url in enumerate(detail_urls, 1):
                html = self._polite_fetch(detail_url)
                if html is None:
                    failed.append(detail_url)
                    continue
                page_records = self.parse(html, base_url=detail_url)
                records.extend(page_records[:1])
                if index % 25 == 0 or index == total:
                    logger.info("Detail pages: %d/%d processed, %d records", index, total, len(records))
            if failed:
                logger.info("Retrying %d failed pages after a pause", len(failed))
                time.sleep(30)
                for detail_url in failed:
                    html = self._polite_fetch(detail_url)
                    if html is None:
                        logger.error("Still failing, skipped: %s", detail_url)
                        continue
                    records.extend(self.parse(html, base_url=detail_url)[:1])
        return records

    def detail_links(self, html: str, current_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for node in soup.select(self.selectors["detail_link"]):
            if node.has_attr("href"):
                links.append(urljoin(current_url, node["href"]))
        return list(dict.fromkeys(links))

    def _cache_path(self, url: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{hashlib.sha1(url.encode()).hexdigest()}.html"

    def _polite_fetch(self, url: str) -> Optional[str]:
        """Disk cache + robots.txt check + throttling + fetch."""
        path = self._cache_path(url)
        if path and path.is_file():
            return path.read_text(encoding="utf-8")
        html = self._network_fetch(url)
        if html is not None and path:
            path.write_text(html, encoding="utf-8")
        return html

    def _network_fetch(self, url: str) -> Optional[str]:
        if not self.is_allowed(url):
            logger.warning("Blocked by robots.txt: %s", url)
            return None
        if self._requests_made:
            time.sleep(self.delay)
        self._requests_made += 1
        return self.fetch(url)

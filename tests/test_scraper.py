"""Offline tests for B2BDirectoryScraper (no network access)."""

import pytest

import config
from main import DEMO_HTML
from modules.scraper import B2BDirectoryScraper


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def scraper():
    return B2BDirectoryScraper(delay=0, respect_robots=False)


def test_parse_demo_page_extracts_all_fields(scraper):
    records = scraper.parse(DEMO_HTML)
    assert len(records) == 6  # duplicates are removed later by DataCleaner
    first = records[0]
    assert first["Company Name"] == "NeuroGenix Therapeutics"
    assert first["Phone"] == "+34 932 145 870"
    assert first["Email"] == "info@neurogenix.example"
    assert first["City"] == "Barcelona"
    assert first["Website"] == "https://www.neurogenix.example"


def test_cards_without_company_name_are_dropped(scraper):
    html = '<div class="company-card"><span class="city">Madrid</span></div>'
    assert scraper.parse(html) == []


def test_relative_website_becomes_absolute(scraper):
    html = '<div class="company-card"><h2 class="company-name">X</h2><a class="website" href="/co/x">w</a></div>'
    records = scraper.parse(html, base_url="https://dir.example.com/list")
    assert records[0]["Website"] == "https://dir.example.com/co/x"


def test_explicit_email_selector_disables_generic_fallback():
    """A footer mailto must not leak into a record whose own email is empty."""
    selectors = {**config.SELECTORS, "email": ".email-field"}
    scraper = B2BDirectoryScraper(selectors=selectors, respect_robots=False)
    html = (
        '<div class="company-card"><h2 class="company-name">AbbVie</h2>'
        '<a href="mailto:footer@directory.org">footer</a></div>'
    )
    assert scraper.parse(html)[0]["Email"] == ""


def test_default_country_code_is_prefixed_only_when_missing():
    scraper = B2BDirectoryScraper(default_country_code="+34", respect_robots=False)
    assert scraper._with_country_code("948346480") == "+34 948346480"
    assert scraper._with_country_code("+49 89 4520") == "+49 89 4520"


def test_next_page_and_detail_links(scraper):
    scraper.selectors = {**scraper.selectors, "detail_link": "a.item", "next_page": "a.next"}
    html = '<a class="item" href="/c/1">1</a><a class="item" href="/c/1">dup</a><a class="item" href="/c/2">2</a><a class="next" href="?p=2">n</a>'
    base = "https://dir.example.com/list"
    assert scraper.detail_links(html, base) == [
        "https://dir.example.com/c/1",
        "https://dir.example.com/c/2",
    ]
    assert scraper.next_page_url(html, base) == "https://dir.example.com/list?p=2"
    assert scraper.next_page_url("<p>none</p>", base) is None


def test_fetch_returns_html_on_success(scraper, monkeypatch):
    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse("<html>ok</html>"))
    assert scraper.fetch("https://x.example") == "<html>ok</html>"


def test_fetch_returns_none_after_retries(scraper, monkeypatch):
    import requests

    calls = []

    def boom(*args, **kwargs):
        calls.append(1)
        raise requests.ConnectionError("down")

    monkeypatch.setattr(scraper.session, "get", boom)
    monkeypatch.setattr("modules.scraper.time.sleep", lambda s: None)
    assert scraper.fetch("https://x.example") is None
    assert len(calls) == config.MAX_RETRIES + 1


def test_robots_txt_blocks_disallowed_paths(monkeypatch):
    scraper = B2BDirectoryScraper(delay=0, respect_robots=True)
    robots = "User-agent: *\nDisallow: /private/\n"
    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse(robots))
    assert scraper.is_allowed("https://dir.example.com/public/list")
    assert not scraper.is_allowed("https://dir.example.com/private/list")


def test_missing_robots_txt_allows_everything(monkeypatch):
    scraper = B2BDirectoryScraper(delay=0, respect_robots=True)
    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse("nf", 404))
    assert scraper.is_allowed("https://dir.example.com/anything")


def test_disk_cache_avoids_second_network_request(tmp_path, monkeypatch):
    scraper = B2BDirectoryScraper(delay=0, respect_robots=False, cache_dir=tmp_path)
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return FakeResponse("<html>page</html>")

    monkeypatch.setattr(scraper.session, "get", fake_get)
    assert scraper._polite_fetch("https://x.example/a") == "<html>page</html>"
    assert scraper._polite_fetch("https://x.example/a") == "<html>page</html>"
    assert len(calls) == 1


def test_scrape_follows_pagination_up_to_max_pages(monkeypatch):
    pages = {
        "https://d.example/1": '<div class="company-card"><h2 class="company-name">A</h2></div><a rel="next" href="/2">n</a>',
        "https://d.example/2": '<div class="company-card"><h2 class="company-name">B</h2></div><a rel="next" href="/3">n</a>',
        "https://d.example/3": '<div class="company-card"><h2 class="company-name">C</h2></div>',
    }
    scraper = B2BDirectoryScraper(delay=0, respect_robots=False, max_pages=2)
    monkeypatch.setattr(scraper, "fetch", lambda url: pages[url])
    monkeypatch.setattr("modules.scraper.time.sleep", lambda s: None)
    names = [r["Company Name"] for r in scraper.scrape(["https://d.example/1"])]
    assert names == ["A", "B"]

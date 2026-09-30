"""Central configuration for the B2B Lead Generation engine."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# HTTP behaviour -------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "B2BLeadGenBot/1.0 (+https://github.com/biellluch-ia/b2b-lead-engine; "
        "contact: biellluch8@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 10  # seconds
REQUEST_DELAY = 1.5   # seconds between requests (polite crawling)
MAX_RETRIES = 2

# Output ---------------------------------------------------------------------
OUTPUT_FILE = "b2b_leads_dataset.csv"
OUTPUT_COLUMNS = ["Company Name", "Phone", "Email", "City", "Website"]

# Targets --------------------------------------------------------------------
# Live extraction is driven by JSON profiles in PROFILES_DIR (see
# profiles/template.json). Run: python main.py --profile <name>
# Without a profile or --url, main.py runs against a bundled offline demo page.
PROFILES_DIR = BASE_DIR / "profiles"
TARGET_URLS: list[str] = []
MAX_PAGES = 5
CACHE_DIR = BASE_DIR / ".cache"  # downloaded pages; makes long runs resumable
RESPECT_ROBOTS = True

# CSS selectors describing one directory listing. Adapt per target site.
SELECTORS = {
    "card": "div.company-card",
    "company_name": ".company-name",
    "phone": ".phone",
    "email": None,  # None = fall back to mailto: links
    "city": ".city",
    "website": "a.website",
    "next_page": "a[rel='next']",
}


def load_profile(name: str) -> dict:
    """Load a scraping profile (start URLs + selectors) from PROFILES_DIR."""
    import json

    path = PROFILES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Profile not found: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)

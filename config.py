"""Central configuration for the B2B Lead Generation engine."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# HTTP behaviour -------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "B2BLeadGenBot/1.0 (+https://github.com/your-user/b2b-lead-gen-engine; "
        "contact: leads@example.com)"
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
# Add real directory listing URLs here to run live extraction.
# When empty, main.py runs against a bundled offline demo page.
TARGET_URLS: list[str] = []

# CSS selectors describing one directory listing. Adapt per target site.
SELECTORS = {
    "card": "div.company-card",
    "company_name": ".company-name",
    "phone": ".phone",
    "email": ".email",
    "city": ".city",
    "website": "a.website",
}

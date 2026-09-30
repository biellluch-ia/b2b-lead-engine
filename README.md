# B2B Lead Generation & Directory Scraper Engine

> **Turn public B2B directories into clean, CRM-ready lead datasets — automatically, repeatably, and politely.**

## Executive Summary

Manual prospecting is slow, inconsistent and expensive. This engine automates the full pipeline — **fetch → extract → clean → export** — and delivers a normalised CSV that can be imported directly into HubSpot, Salesforce, Pipedrive, Zoho or Airtable.

**Business value**

- **CRM readiness:** consistent schema (`Company Name, Phone, Email, City, Website`), trimmed whitespace, lower-cased emails/URLs, no duplicates.
- **Time-to-lead:** hours of copy-paste reduced to a single command.
- **Compliance-minded:** custom User-Agent, request throttling (1.5 s), timeouts and retry limits to respect target servers.
- **Adaptable:** target sites are described through CSS selectors in `config.py` — no code changes needed for typical directory layouts.
- **Vertical-agnostic:** demoed with Biotech / Life Sciences data, applicable to any B2B niche.

## Repository Architecture

```
.
├── config.py                # Headers, timeout, delay, selectors, output settings
├── main.py                  # Orchestrator: scrape -> clean -> export (with logging)
├── modules/
│   ├── __init__.py
│   ├── scraper.py           # B2BDirectoryScraper: HTTP requests + HTML parsing
│   └── data_cleaner.py      # DataCleaner: Pandas normalisation, dedupe, CSV export
├── b2b_leads_dataset.csv    # Sample output dataset
├── requirements.txt         # requests, beautifulsoup4, pandas
└── README.md
```

## Sample Output

Excerpt of `b2b_leads_dataset.csv` (simulated Biotech companies):

| Company Name | Phone | Email | City | Website |
|---|---|---|---|---|
| NeuroGenix Therapeutics | +34 932 145 870 | info@neurogenix.example | Barcelona | https://www.neurogenix.example |
| BioVantis Labs | +49 89 4520 1180 | contact@biovantis.example | Munich | https://www.biovantis.example |
| Helixor Diagnostics | +44 20 7946 0321 | sales@helixor.example | London | https://www.helixor.example |
| Cellumina Biosciences | +31 20 794 5566 | hello@cellumina.example | Amsterdam | https://www.cellumina.example |
| Proteomix Systems | +41 61 555 0142 | bd@proteomix.example | Basel | https://www.proteomix.example |

## Production Setup

```bash
git clone https://github.com/biellluch-ia/b2b-lead-engine.git
cd b2b-lead-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Running without arguments executes an offline demo. For live extraction, set `TARGET_URLS` and `SELECTORS` in `config.py`, or pass URLs directly:

```bash
python main.py --url https://directory.example.com/companies --output leads.csv
```

> Always review the target site's Terms of Service and `robots.txt` before scraping.

## Hire Me

Need a custom lead-generation pipeline (site-specific scrapers, pagination, enrichment, scheduled runs, direct CRM/Airtable/Google Sheets sync)?

- **Upwork:** _add your profile link_
- **Email:** oriolbiel08@gmail.com
- **GitHub:** https://github.com/biellluch-ia

Available for fixed-price projects and ongoing automation retainers.

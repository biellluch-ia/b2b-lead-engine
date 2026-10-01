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
├── profiles/                # JSON scraping profiles (selectors, pagination)
│   ├── asebio.json
│   ├── template.json
│   └── sandbox_quotes.json
├── modules/
│   ├── __init__.py
│   ├── scraper.py           # B2BDirectoryScraper: HTTP, robots.txt, pagination, parsing
│   └── data_cleaner.py      # DataCleaner: Pandas normalisation, dedupe, CSV export
├── tests/                   # Offline pytest suite (29 tests)
├── b2b_leads_dataset.csv    # Public sample (real companies, generic mailboxes only)
├── requirements.txt         # requests, beautifulsoup4, pandas
└── README.md
```

## Live Demo Dataset

The engine was validated end-to-end against the public member directory of **AseBio** (Spanish Biotechnology Association): **333 member pages crawled, 330 unique companies extracted** (after de-duplication), in ~15 minutes with polite throttling.

| Field | Coverage |
|---|---|
| Company Name | 100% |
| Email | 96% |
| Website | 98% |
| City | 99% |
| Phone | 89% |
| Fully complete rows | 84% |

Excerpt of the public sample (`b2b_leads_dataset.csv`, real companies, role mailboxes only):

| Company Name | Phone | Email | City | Website |
|---|---|---|---|---|
| Polar NanoPharma | +34 977 167 539 | contact@polarnanopharma.com | L´Arboç | https://polarnanopharma.com |
| Capital Cell | +34 931 004 287 | info@capitalcell.net | Barcelona | http://capitalcell.net |
| Olavide Neuron STX S.L. | +34 657 816 904 | info@onestx.bio | Camas | https://onestx.bio |
| Cool Chain Logistics, SL | +34 913 439 986 | info@coolchain.es | Madrid | https://www.coolchain.es |
| SunRock Biopharma S.L. | +34 881 975 523 | admin@sunrockbiopharma.com | Santiago de Compostela | https://www.sunrockbiopharma.com/es |
| Ability Pharmaceuticals, SA | +34 935 824 411 | contact@abilitypharma.com | Bellaterra | http://www.abilitypharma.com |
| Noray Bioinformatics, SLU - NorayBio | +34 944 036 998 | info@noraybio.com | Derio | http://www.noraybio.com |
| Operon, SA | +34 976 503 597 | sales@operon.es | Cuarte de Huerva | http://www.operon.es |

**[View the sample delivery as a Google Sheet](https://docs.google.com/spreadsheets/d/1aoclYSowv5Ne_19K8RoRGW4C-UeH10pfrq8RND6O3m0/edit?usp=sharing)** (read-only: leads + quality report tabs).

### Data protection & compliance

- Only publicly listed company contact data was collected; `robots.txt` and the site's legal notice were reviewed first (no restriction on automated access found).
- The full dataset is **not** published. Named personal mailboxes (e.g. `firstname.lastname@`) are personal data under GDPR; this repository ships only a sample restricted to generic role mailboxes (`info@`, `contact@`, `sales@`...).
- For client projects, lawful basis (e.g. legitimate interest, B2B) and opt-out handling are the client's responsibility; I can build the workflow accordingly.

## Production Setup

```bash
git clone https://github.com/biellluch-ia/b2b-lead-engine.git
cd b2b-lead-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Running without arguments executes an offline demo. Live extraction is driven by **JSON scraping profiles** in `profiles/` (start URLs, CSS selectors, pagination, page limit):

```bash
cp profiles/template.json profiles/my_directory.json   # adapt selectors
python main.py --profile my_directory --output leads.csv
```

The AseBio demo (listing page -> one detail page per company, resumable thanks to an on-disk page cache):

```bash
python main.py --profile asebio --output data/asebio_full.csv --sample-output b2b_leads_dataset.csv
```

A ready-made technical validation profile runs against a public scraping sandbox (demonstrates live fetch, pagination, deduplication):

```bash
python main.py --profile sandbox_quotes
```

Built-in safeguards: `robots.txt` checks, request throttling, timeouts, retries with a final retry pass, on-disk page cache (resume interrupted runs) and a per-profile page limit.

> Always review the target site's Terms of Service and `robots.txt` before scraping.

## Testing

29 offline unit and end-to-end tests (no network required): parsing, selector fallbacks, pagination, `robots.txt`, retries, disk cache, cleaning rules and the CLI.

```bash
pip install -r requirements-dev.txt
pytest
```

## License

MIT - see [LICENSE](LICENSE).

## Hire Me

Need a custom lead-generation pipeline (site-specific scrapers, pagination, enrichment, scheduled runs, direct CRM/Airtable/Google Sheets sync)?

- **Upwork:** https://www.upwork.com/freelancers/~01b7e8294d07b1e4e5
- **Email:** biellluch8@gmail.com
- **GitHub:** https://github.com/biellluch-ia

Available for fixed-price projects and ongoing automation retainers.

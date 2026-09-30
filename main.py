"""Entry point: scrape -> clean -> export."""

from __future__ import annotations

import argparse
import logging
import sys

import config
from modules import B2BDirectoryScraper, DataCleaner

logger = logging.getLogger("b2b-engine")

# Offline demo page (simulated companies) so the pipeline runs without network.
DEMO_HTML = """
<html><body>
<div class="company-card"><h2 class="company-name">  NeuroGenix Therapeutics </h2>
  <span class="phone">+34 932 145 870</span><a href="mailto:info@neurogenix.example">mail</a>
  <span class="city">Barcelona</span><a class="website" href="https://www.neurogenix.example">site</a></div>
<div class="company-card"><h2 class="company-name">BioVantis Labs</h2>
  <span class="phone">+49 89 4520 1180</span><a href="mailto:contact@biovantis.example">mail</a>
  <span class="city">Munich</span><a class="website" href="https://www.biovantis.example">site</a></div>
<div class="company-card"><h2 class="company-name">Helixor Diagnostics</h2>
  <span class="phone">+44 20 7946 0321</span><a href="mailto:sales@helixor.example">mail</a>
  <span class="city">London</span><a class="website" href="https://www.helixor.example">site</a></div>
<div class="company-card"><h2 class="company-name">Cellumina Biosciences</h2>
  <span class="phone">+31 20 794 5566</span><a href="mailto:hello@cellumina.example">mail</a>
  <span class="city">Amsterdam</span><a class="website" href="https://www.cellumina.example">site</a></div>
<div class="company-card"><h2 class="company-name">Proteomix Systems</h2>
  <span class="phone">+41 61 555 0142</span><a href="mailto:bd@proteomix.example">mail</a>
  <span class="city">Basel</span><a class="website" href="https://www.proteomix.example">site</a></div>
<div class="company-card"><h2 class="company-name">BioVantis Labs</h2>
  <span class="phone">+49 89 4520 1180</span><a href="mailto:contact@biovantis.example">mail</a>
  <span class="city">Munich</span><a class="website" href="https://www.biovantis.example">site</a></div>
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="B2B directory lead extraction engine")
    parser.add_argument("--url", action="append", help="Directory URL to scrape (repeatable)")
    parser.add_argument("--output", default=config.OUTPUT_FILE, help="Output CSV path")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    scraper = B2BDirectoryScraper()
    cleaner = DataCleaner()

    urls = args.url or config.TARGET_URLS
    if urls:
        logger.info("Starting live extraction for %d URL(s)", len(urls))
        records = scraper.scrape(urls)
    else:
        logger.info("No target URLs configured - running offline demo mode")
        records = scraper.parse(DEMO_HTML)

    if not records:
        logger.error("No records extracted; nothing to export")
        return 1

    logger.info("Raw records: %d", len(records))
    df = cleaner.clean(cleaner.to_dataframe(records))
    cleaner.export(df, args.output)
    logger.info("Done. %d clean leads ready for CRM import.", len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())

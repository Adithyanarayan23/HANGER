import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

import app.scraping.websites  # noqa: F401 - Ensure registered scrapers are loaded
from app.database.session import SessionLocal
from app.schemas.product import ProductCreate
from app.scraping.product_normalizer import NormalizationError, ProductNormalizer
from app.scraping.scraper_config import ScraperConfig
from app.scraping.scraper_registry import ScraperRegistry, scraper_registry
from app.services import product_service


@dataclass
class ScrapingSummary:
    """Structured summary of a single website scraping and ingestion run."""

    website_id: str
    products_discovered: int = 0
    products_normalized: int = 0
    products_inserted: int = 0
    products_updated: int = 0
    duplicate_products_skipped: int = 0
    invalid_products_skipped: int = 0
    failed_extractions: int = 0
    execution_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ScraperManager:
    """
    Orchestrates the end-to-end scraping pipeline:
      1. Look up a registered website scraper by website_id
      2. Execute extraction
      3. Normalize each raw product dictionary via ProductNormalizer
      4. Validate via ProductCreate Pydantic schema
      5. Persist idempotently via product_service.upsert_scraped_product
      6. Return a complete ScrapingSummary
    """

    def __init__(
        self,
        registry: Optional[ScraperRegistry] = None,
        config: Optional[ScraperConfig] = None,
    ) -> None:
        self.registry: ScraperRegistry = registry or scraper_registry
        self.config: Optional[ScraperConfig] = config

    def run_scraper(
        self,
        website_id: str,
        db: Session,
        scraper_kwargs: Optional[Dict[str, Any]] = None,
    ) -> ScrapingSummary:
        start_time = time.perf_counter()
        summary = ScrapingSummary(website_id=website_id)

        scraper_cls = self.registry.get_scraper_class(website_id)
        init_kwargs = dict(scraper_kwargs or {})
        if self.config is not None and "config" not in init_kwargs:
            init_kwargs["config"] = self.config

        scraper = scraper_cls(**init_kwargs)

        try:
            raw_products = scraper.scrape_products()
        except Exception as exc:
            summary.failed_extractions += 1
            summary.errors.append(f"Scraper execution error: {exc}")
            summary.execution_duration_seconds = round(time.perf_counter() - start_time, 4)
            return summary

        summary.products_discovered = len(raw_products)

        for idx, raw_item in enumerate(raw_products, start=1):
            if raw_item is None or (isinstance(raw_item, dict) and raw_item.get("_extraction_error")):
                summary.failed_extractions += 1
                err_msg = (
                    raw_item.get("_extraction_error")
                    if isinstance(raw_item, dict)
                    else "Empty extraction result"
                )
                summary.errors.append(f"Item #{idx} extraction failed: {err_msg}")
                continue

            # Step A: Normalize raw fields
            try:
                normalized_dict = ProductNormalizer.normalize(
                    raw_item,
                    base_url=scraper.base_url,
                )
                summary.products_normalized += 1
            except NormalizationError as exc:
                summary.invalid_products_skipped += 1
                summary.errors.append(f"Item #{idx} normalization skipped: {exc}")
                continue

            # Step B: Validate with existing ProductCreate Pydantic schema
            try:
                validated_product = ProductCreate(**normalized_dict)
            except ValidationError as exc:
                summary.invalid_products_skipped += 1
                summary.errors.append(f"Item #{idx} Pydantic validation skipped: {exc.errors()[0]['msg']}")
                continue

            # Step C: Persist through existing Product Service (idempotent upsert)
            try:
                _, status_label = product_service.upsert_scraped_product(
                    db=db,
                    product_in=validated_product,
                )
                if status_label == "inserted":
                    summary.products_inserted += 1
                elif status_label == "updated":
                    summary.products_updated += 1
                else:
                    summary.duplicate_products_skipped += 1
            except Exception as exc:
                summary.failed_extractions += 1
                summary.errors.append(f"Item #{idx} database ingestion error: {exc}")

        summary.execution_duration_seconds = round(time.perf_counter() - start_time, 4)
        return summary


def main() -> None:
    """Command-line entrypoint to run a registered scraper locally."""
    parser = argparse.ArgumentParser(
        description="Execute a registered HANGER website scraper and ingest products into PostgreSQL."
    )
    parser.add_argument(
        "--website",
        type=str,
        default="local_fixture",
        help="Registered website identifier (e.g., 'local_fixture'). Use --list to view available IDs.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered website scraper identifiers and exit.",
    )
    args = parser.parse_args()

    if args.list:
        print("Registered website scrapers:", scraper_registry.list_registered_websites())
        return

    manager = ScraperManager()
    with SessionLocal() as db:
        summary = manager.run_scraper(website_id=args.website, db=db)
        print(json.dumps(summary.to_dict(), indent=2))


if __name__ == "__main__":
    main()

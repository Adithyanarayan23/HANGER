"""Modular web scraping and product ingestion package for HANGER."""

from app.scraping.base_scraper import BaseScraper
from app.scraping.product_normalizer import NormalizationError, ProductNormalizer
from app.scraping.scraper_config import DEFAULT_SCRAPER_CONFIG, ScraperConfig
from app.scraping.scraper_manager import ScraperManager, ScrapingSummary
from app.scraping.scraper_registry import ScraperRegistry, scraper_registry

__all__ = [
    "BaseScraper",
    "ProductNormalizer",
    "NormalizationError",
    "ScraperConfig",
    "DEFAULT_SCRAPER_CONFIG",
    "ScraperManager",
    "ScrapingSummary",
    "ScraperRegistry",
    "scraper_registry",
]

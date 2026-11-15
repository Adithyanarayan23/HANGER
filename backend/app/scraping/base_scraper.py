from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.scraping.scraper_config import DEFAULT_SCRAPER_CONFIG, ScraperConfig


class BaseScraper(ABC):
    """
    Abstract base class defining the consistent contract that every
    website-specific fashion scraper must implement.
    """

    website_id: str = ""
    source_website_name: str = ""
    base_url: str = ""

    def __init__(self, config: Optional[ScraperConfig] = None) -> None:
        if not self.website_id or not self.source_website_name or not self.base_url:
            raise ValueError(
                f"{self.__class__.__name__} must define website_id, source_website_name, and base_url."
            )
        self.config: ScraperConfig = config or DEFAULT_SCRAPER_CONFIG

    @abstractmethod
    def fetch_listing_pages(self) -> List[str]:
        """
        Fetch one or more product listing pages (handling pagination where supported)
        and return raw HTML strings for each page.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_product_urls(self, listing_html: str) -> List[str]:
        """Extract product detail page URLs (or inline product cards) from a listing HTML page."""
        raise NotImplementedError

    @abstractmethod
    def extract_product_data(self, raw_source: str, product_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract raw product attributes from a product page HTML or card block.
        Returns an unnormalized dictionary of raw scraped values.
        """
        raise NotImplementedError

    @abstractmethod
    def scrape_products(self) -> List[Dict[str, Any]]:
        """
        Execute the full extraction flow for this website and return a list
        of raw product dictionaries ready for normalization.
        """
        raise NotImplementedError

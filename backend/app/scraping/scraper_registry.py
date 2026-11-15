from typing import Dict, List, Type

from app.scraping.base_scraper import BaseScraper


class ScraperRegistry:
    """
    Central registry mapping website identifiers (e.g., 'fixture_demo')
    to their concrete BaseScraper subclasses.
    Allows new website scrapers to be registered without modifying ScraperManager.
    """

    def __init__(self) -> None:
        self._scrapers: Dict[str, Type[BaseScraper]] = {}

    def register(self, scraper_cls: Type[BaseScraper]) -> Type[BaseScraper]:
        """Register a BaseScraper subclass by its website_id."""
        if not issubclass(scraper_cls, BaseScraper):
            raise TypeError(f"{scraper_cls} must inherit from BaseScraper.")
        website_id = getattr(scraper_cls, "website_id", "").strip()
        if not website_id:
            raise ValueError(f"{scraper_cls.__name__} must define a non-empty website_id.")
        self._scrapers[website_id] = scraper_cls
        return scraper_cls

    def get_scraper_class(self, website_id: str) -> Type[BaseScraper]:
        """Retrieve a registered scraper class or raise KeyError if not registered."""
        key = (website_id or "").strip()
        if key not in self._scrapers:
            available = ", ".join(sorted(self._scrapers.keys())) or "none"
            raise KeyError(
                f"Unregistered website identifier '{website_id}'. "
                f"Registered websites: {available}"
            )
        return self._scrapers[key]

    def list_registered_websites(self) -> List[str]:
        """Return a sorted list of all registered website identifiers."""
        return sorted(self._scrapers.keys())


# Global singleton registry instance
scraper_registry = ScraperRegistry()

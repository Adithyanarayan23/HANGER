from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for responsible HTTP and browser scraping."""

    user_agent: str = "HangerCatalogBot/1.0 (+http://localhost:5173; responsible-fashion-indexer)"
    request_timeout_seconds: float = 15.0
    max_retries: int = 2
    retry_Delay_seconds: float = 1.5
    request_delay_seconds: float = 1.0
    max_pages_per_run: int = 5
    respect_robots_txt: bool = True
    default_currency: str = "INR"
    default_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        }
    )


DEFAULT_SCRAPER_CONFIG = ScraperConfig()

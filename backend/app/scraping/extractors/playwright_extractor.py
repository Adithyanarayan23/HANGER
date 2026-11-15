import time
from typing import Optional

from app.scraping.scraper_config import DEFAULT_SCRAPER_CONFIG, ScraperConfig


class PlaywrightExtractor:
    """
    Context-managed Playwright extractor for JavaScript-rendered product pages.
    Reuses a single browser instance across multiple page navigations during a run
    and guarantees clean teardown of pages, browser context, and Playwright process.
    """

    def __init__(self, config: Optional[ScraperConfig] = None, headless: bool = True) -> None:
        self.config: ScraperConfig = config or DEFAULT_SCRAPER_CONFIG
        self.headless: bool = headless
        self._playwright = None
        self._browser = None
        self._context = None

    def start(self) -> None:
        """Launch Playwright and a reusable browser instance if not already running."""
        if self._browser is not None:
            return
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            user_agent=self.config.user_agent,
            extra_http_headers=self.config.default_headers,
        )

    def close(self) -> None:
        """Close browser context, browser, and Playwright driver cleanly."""
        if self._context is not None:
            try:
                self._context.close()
            finally:
                self._context = None

        if self._browser is not None:
            try:
                self._browser.close()
            finally:
                self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            finally:
                self._playwright = None

    def __enter__(self) -> "PlaywrightExtractor":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def fetch_rendered_html(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
    ) -> str:
        """
        Navigate to a URL using a page from the shared browser context,
        wait for the target product selector (if provided), and return rendered HTML.
        Never attempts to solve or bypass CAPTCHAs or login walls.
        """
        if self._context is None:
            self.start()

        if self.config.request_delay_seconds > 0:
            time.sleep(self.config.request_delay_seconds)

        page = self._context.new_page()
        timeout_ms = int(self.config.request_timeout_seconds * 1000)
        try:
            response = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            if response and response.status in (403, 429):
                raise PermissionError(
                    f"Access restricted (HTTP {response.status}) at {url}. Stopping browser extraction."
                )

            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=timeout_ms)

            return page.content()
        finally:
            page.close()

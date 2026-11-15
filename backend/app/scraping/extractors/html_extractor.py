import time
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup, Tag

from app.scraping.scraper_config import DEFAULT_SCRAPER_CONFIG, ScraperConfig


class AccessRestrictedError(Exception):
    """Raised when a website returns HTTP 403, HTTP 429, or disallows scraping in robots.txt."""
    pass


class HtmlExtractor:
    """
    Reusable HTTPX + BeautifulSoup utility for fetching public HTML pages
    and safely extracting text, attributes, links, and images using CSS selectors.
    """

    def __init__(self, config: Optional[ScraperConfig] = None) -> None:
        self.config: ScraperConfig = config or DEFAULT_SCRAPER_CONFIG
        headers = {
            **self.config.default_headers,
            "User-Agent": self.config.user_agent,
        }
        self._client = httpx.Client(
            headers=headers,
            timeout=self.config.request_timeout_seconds,
            follow_redirects=True,
        )
        self._robots_cache: dict[str, RobotFileParser] = {}

    def close(self) -> None:
        """Close the underlying HTTPX client."""
        self._client.close()

    def __enter__(self) -> "HtmlExtractor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check robots.txt before fetching a live URL when respect_robots_txt is enabled."""
        if not self.config.respect_robots_txt:
            return True

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots_cache:
            rp = RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            try:
                resp = self._client.get(robots_url)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except httpx.HTTPError:
                rp.allow_all = True
            self._robots_cache[origin] = rp

        return self._robots_cache[origin].can_fetch(self.config.user_agent, url)

    def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a public URL with configurable retries,
        request delays, and responsible handling of HTTP 403 / 429.
        """
        if not self.is_allowed_by_robots(url):
            raise AccessRestrictedError(f"Scraping disallowed by robots.txt for URL: {url}")

        last_exc: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(self.config.retry_Delay_seconds * attempt)
                elif self.config.request_delay_seconds > 0:
                    time.sleep(self.config.request_delay_seconds)

                response = self._client.get(url)

                if response.status_code in (403, 429):
                    raise AccessRestrictedError(
                        f"Access restricted or rate-limited (HTTP {response.status_code}) for {url}. "
                        "Stopping request rather than bypassing restriction."
                    )

                response.raise_for_status()
                return response.text

            except AccessRestrictedError:
                raise
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc

        raise RuntimeError(f"Failed to fetch {url} after {self.config.max_retries + 1} attempts: {last_exc}")

    @staticmethod
    def parse_html(html: str) -> BeautifulSoup:
        """Parse an HTML string into a BeautifulSoup tree."""
        return BeautifulSoup(html or "", "html.parser")

    @staticmethod
    def select_elements(root: BeautifulSoup | Tag, selector: str) -> List[Tag]:
        """Return all matching HTML elements for a CSS selector, or an empty list."""
        if not root or not selector:
            return []
        try:
            return list(root.select(selector))
        except Exception:
            return []

    @staticmethod
    def extract_text(root: BeautifulSoup | Tag, selector: Optional[str] = None) -> Optional[str]:
        """Extract and strip text from a CSS selector (or from the element itself)."""
        if not root:
            return None
        target = root.select_one(selector) if selector else root
        if not target:
            return None
        text = " ".join(target.get_text(separator=" ", strip=True).split())
        return text if text else None

    @staticmethod
    def extract_attribute(
        root: BeautifulSoup | Tag,
        selector: Optional[str],
        attribute: str,
    ) -> Optional[str]:
        """Extract an HTML attribute (e.g., data-product-id, href, src) safely."""
        if not root or not attribute:
            return None
        target = root.select_one(selector) if selector else root
        if not target:
            return None
        val = target.get(attribute)
        if isinstance(val, list):
            val = " ".join(val)
        if isinstance(val, str):
            val = val.strip()
            return val if val else None
        return None

    @classmethod
    def extract_texts_list(cls, root: BeautifulSoup | Tag, selector: str) -> List[str]:
        """Extract a list of non-empty text strings for all matching elements (e.g., sizes)."""
        items: List[str] = []
        for el in cls.select_elements(root, selector):
            txt = " ".join(el.get_text(separator=" ", strip=True).split())
            if txt and txt not in items:
                items.append(txt)
        return items

    @classmethod
    def extract_image_urls(
        cls,
        root: BeautifulSoup | Tag,
        selector: str,
        base_url: str = "",
        attributes: tuple[str, ...] = ("src", "data-src"),
    ) -> List[str]:
        """Extract image URLs from matching img elements and resolve relative URLs."""
        urls: List[str] = []
        for el in cls.select_elements(root, selector):
            raw_url = None
            for attr in attributes:
                candidate = el.get(attr)
                if isinstance(candidate, str) and candidate.strip():
                    raw_url = candidate.strip()
                    break
            if not raw_url:
                continue
            if raw_url.startswith("data:"):
                continue
            resolved = urljoin(base_url, raw_url) if base_url else raw_url
            parsed = urlparse(resolved)
            if parsed.scheme in ("http", "https") and parsed.netloc and resolved not in urls:
                urls.append(resolved)
        return urls

    @classmethod
    def extract_links(
        cls,
        root: BeautifulSoup | Tag,
        selector: str,
        base_url: str = "",
    ) -> List[str]:
        """Extract href links from matching anchor elements and resolve relative URLs."""
        links: List[str] = []
        for el in cls.select_elements(root, selector):
            href = el.get("href")
            if not isinstance(href, str) or not href.strip():
                continue
            resolved = urljoin(base_url, href.strip()) if base_url else href.strip()
            parsed = urlparse(resolved)
            if parsed.scheme in ("http", "https") and parsed.netloc and resolved not in links:
                links.append(resolved)
        return links

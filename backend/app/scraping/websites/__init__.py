"""
Website-specific scrapers package.

Real fashion website scrapers will be added and registered here once their target URLs
and terms/robots policies are reviewed.
For local verification and testing, a deterministic local HTML fixture scraper
(`LocalFixtureScraper`) is provided without making fake live network claims.
"""

from typing import Any, Dict, List, Optional

from bs4 import Tag

from app.scraping.base_scraper import BaseScraper
from app.scraping.extractors.html_extractor import HtmlExtractor
from app.scraping.scraper_config import ScraperConfig
from app.scraping.scraper_registry import scraper_registry

SAMPLE_FIXTURE_LISTING_HTML = """
<!DOCTYPE html>
<html lang="en">
<body>
  <section class="catalog-grid">
    <article class="product-item" data-sku="FX-101">
      <a class="product-link" href="/catalog/linen-safari-jacket">
        <img class="product-img" src="/media/jackets/safari-front.jpg" data-src="/media/jackets/safari-side.jpg" />
        <span class="brand-name">  Atelier Linen  </span>
        <h2 class="product-title">  Unlined   Belgian Linen Safari Jacket </h2>
      </a>
      <p class="product-desc">Breathable four-pocket safari jacket crafted from 100% Belgian flax.</p>
      <span class="product-category">Outerwear</span>
      <span class="product-subcategory">Jackets</span>
      <span class="product-color">Sand</span>
      <div class="price-box">
        <span class="sale-price">₹ 8,490.00</span>
        <span class="mrp-price">Rs. 10,990</span>
      </div>
      <ul class="size-list">
        <li>S</li>
        <li>M</li>
        <li>L</li>
      </ul>
    </article>

    <article class="product-item" data-sku="FX-102">
      <a class="product-link" href="https://fixture-atelier.example.com/catalog/pleated-trouser">
        <img class="product-img" src="/media/trousers/pleated-charcoal.jpg" />
        <span class="brand-name">Studio Minimal</span>
        <h2 class="product-title">Double-Pleated Wool Trousers</h2>
      </a>
      <p class="product-desc">High-waisted wide-leg tailored wool trousers.</p>
      <span class="product-category">Bottomwear</span>
      <span class="product-color">Charcoal</span>
      <div class="price-box">
        <span class="sale-price">INR 6,250</span>
      </div>
      <ul class="size-list">
        <li>30</li>
        <li>32</li>
        <li>34</li>
      </ul>
    </article>
  </section>
</body>
</html>
"""


@scraper_registry.register
class LocalFixtureScraper(BaseScraper):
    """
    Deterministic local HTML fixture scraper used to verify the end-to-end
    extraction -> normalization -> validation -> PostgreSQL ingestion pipeline
    without making external network calls or inventing fake live stores.
    """

    website_id = "local_fixture"
    source_website_name = "Fixture Atelier Store"
    base_url = "https://fixture-atelier.example.com"

    def __init__(
        self,
        config: Optional[ScraperConfig] = None,
        html_pages: Optional[List[str]] = None,
    ) -> None:
        super().__init__(config=config)
        self._html_pages = html_pages if html_pages is not None else [SAMPLE_FIXTURE_LISTING_HTML]

    def fetch_listing_pages(self) -> List[str]:
        return list(self._html_pages)

    def extract_product_urls(self, listing_html: str) -> List[str]:
        soup = HtmlExtractor.parse_html(listing_html)
        return HtmlExtractor.extract_links(soup, "article.product-item a.product-link", base_url=self.base_url)

    def extract_product_data(self, card: Tag | str, product_url: Optional[str] = None) -> Dict[str, Any]:
        node = HtmlExtractor.parse_html(card) if isinstance(card, str) else card
        link = product_url or HtmlExtractor.extract_attribute(node, "a.product-link", "href")

        imgs = HtmlExtractor.extract_image_urls(
            node,
            "img.product-img",
            base_url=self.base_url,
            attributes=("src",),
        )
        alt_imgs = HtmlExtractor.extract_image_urls(
            node,
            "img.product-img",
            base_url=self.base_url,
            attributes=("data-src",),
        )
        for u in alt_imgs:
            if u not in imgs:
                imgs.append(u)

        return {
            "name": HtmlExtractor.extract_text(node, ".product-title"),
            "description": HtmlExtractor.extract_text(node, ".product-desc"),
            "brand": HtmlExtractor.extract_text(node, ".brand-name"),
            "category": HtmlExtractor.extract_text(node, ".product-category"),
            "subcategory": HtmlExtractor.extract_text(node, ".product-subcategory"),
            "color": HtmlExtractor.extract_text(node, ".product-color"),
            "price": HtmlExtractor.extract_text(node, ".sale-price"),
            "original_price": HtmlExtractor.extract_text(node, ".mrp-price"),
            "sizes": HtmlExtractor.extract_texts_list(node, ".size-list li"),
            "image_urls": imgs,
            "is_available": True,
            "source_website": self.source_website_name,
            "source_product_id": HtmlExtractor.extract_attribute(node, None, "data-sku")
            or HtmlExtractor.extract_attribute(node, "article.product-item", "data-sku"),
            "product_url": link,
        }

    def scrape_products(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for page_html in self.fetch_listing_pages():
            soup = HtmlExtractor.parse_html(page_html)
            cards = HtmlExtractor.select_elements(soup, "article.product-item")
            for card in cards:
                results.append(self.extract_product_data(card))
        return results

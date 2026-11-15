from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.database.connection import engine
from app.models.product import Product
from app.schemas.product import ProductCreate
from app.scraping.extractors.html_extractor import HtmlExtractor
from app.scraping.product_normalizer import NormalizationError, ProductNormalizer
from app.scraping.scraper_manager import ScraperManager
from app.scraping.websites import LocalFixtureScraper


FIXTURE_HTML_MULTI_CASE = """
<!DOCTYPE html>
<html>
<body>
  <section class="catalog-grid">
    <!-- 1. Valid product with relative URLs, messy whitespace, ₹ currency, and original_price -->
    <article class="product-item" data-sku="TEST-SKU-001">
      <a class="product-link" href="/products/raw-selvedge-jacket">
        <img class="product-img" src="/images/denim-front.jpg" data-src="/images/denim-back.jpg" />
        <span class="brand-name">   Korra   </span>
        <h2 class="product-title">  Raw   Selvedge Denim   Trucker Jacket  </h2>
      </a>
      <p class="product-desc">  13.5oz shuttle-loom red-line selvedge denim jacket.  </p>
      <span class="product-category">Outerwear</span>
      <span class="product-subcategory">Denim Jackets</span>
      <span class="product-color">Indigo</span>
      <div class="price-box">
        <span class="sale-price">₹ 6,490.00</span>
        <span class="mrp-price">Rs. 7,990</span>
      </div>
      <ul class="size-list">
        <li>S</li>
        <li>M</li>
        <li>L</li>
      </ul>
    </article>

    <!-- 2. Valid product with missing optional fields (no description, no color, no original_price) -->
    <article class="product-item" data-sku="TEST-SKU-002">
      <a class="product-link" href="https://fixture-atelier.example.com/products/merino-knit">
        <img class="product-img" src="https://fixture-atelier.example.com/images/merino.jpg" />
        <span class="brand-name">Uniqlo U</span>
        <h2 class="product-title">Extra Fine Merino Crewneck</h2>
      </a>
      <span class="product-category">Topwear</span>
      <div class="price-box">
        <span class="sale-price">INR 2,990</span>
      </div>
    </article>

    <!-- 3. Invalid product: non-numeric price ('Price on Request') -> should be skipped safely -->
    <article class="product-item" data-sku="TEST-SKU-BAD-PRICE">
      <a class="product-link" href="/products/couture-gown">
        <span class="brand-name">Atelier Archive</span>
        <h2 class="product-title">Bespoke Silk Gown</h2>
      </a>
      <span class="product-category">Dresses</span>
      <div class="price-box">
        <span class="sale-price">Price on Request</span>
      </div>
    </article>

    <!-- 4. Invalid product: missing required brand -> should be skipped without inventing brand -->
    <article class="product-item" data-sku="TEST-SKU-NO-BRAND">
      <a class="product-link" href="/products/mystery-shirt">
        <h2 class="product-title">Unbranded Linen Shirt</h2>
      </a>
      <span class="product-category">Topwear</span>
      <div class="price-box">
        <span class="sale-price">₹ 3,500</span>
      </div>
    </article>
  </section>
</body>
</html>
"""

FIXTURE_HTML_PRICE_DROP_UPDATE = """
<!DOCTYPE html>
<html>
<body>
  <section class="catalog-grid">
    <!-- Updated price for TEST-SKU-001 (dropped to ₹5,990.00), while description & color are missing in this scrape -->
    <article class="product-item" data-sku="TEST-SKU-001">
      <a class="product-link" href="/products/raw-selvedge-jacket">
        <span class="brand-name">Korra</span>
        <h2 class="product-title">Raw Selvedge Denim Trucker Jacket</h2>
      </a>
      <span class="product-category">Outerwear</span>
      <div class="price-box">
        <span class="sale-price">₹ 5,990.00</span>
      </div>
    </article>
  </section>
</body>
</html>
"""


def run_all_phase4_tests() -> None:
    scraper = LocalFixtureScraper(html_pages=[FIXTURE_HTML_MULTI_CASE])
    raw_items = scraper.scrape_products()
    assert len(raw_items) == 4
    first_raw = raw_items[0]

    # 1. Product name extraction
    assert "Raw" in first_raw["name"] and "Selvedge" in first_raw["name"]
    print("[1] Product name extraction -> PASSED:", repr(first_raw["name"]))

    # 2. Brand extraction
    assert first_raw["brand"] == "Korra"
    print("[2] Brand extraction -> PASSED:", repr(first_raw["brand"]))

    # 3. Price extraction
    assert first_raw["price"] == "₹ 6,490.00"
    assert first_raw["original_price"] == "Rs. 7,990"
    print("[3] Price extraction -> PASSED:", first_raw["price"], "| MRP:", first_raw["original_price"])

    # 4. Image URL extraction (including relative src and data-src)
    assert len(first_raw["image_urls"]) == 2
    assert first_raw["image_urls"][0] == "https://fixture-atelier.example.com/images/denim-front.jpg"
    print("[4] Image URL extraction -> PASSED:", first_raw["image_urls"])

    # 5. Product URL extraction
    urls = scraper.extract_product_urls(FIXTURE_HTML_MULTI_CASE)
    assert urls[0] == "https://fixture-atelier.example.com/products/raw-selvedge-jacket"
    print("[5] Product URL extraction -> PASSED:", urls[0])

    # 6. Missing fields handling (optional fields None vs required fields raising NormalizationError)
    second_norm = ProductNormalizer.normalize(raw_items[1], base_url=scraper.base_url)
    assert second_norm["description"] is None
    assert second_norm["color"] is None
    assert second_norm["original_price"] is None
    assert second_norm["sizes"] == []
    try:
        ProductNormalizer.normalize(raw_items[3], base_url=scraper.base_url)
        raise AssertionError("Expected NormalizationError for missing brand")
    except NormalizationError as exc:
        print("[6] Missing fields (optional None & required rejected without guessing) -> PASSED:", exc)

    # 7. Invalid prices rejected
    try:
        ProductNormalizer.normalize(raw_items[2], base_url=scraper.base_url)
        raise AssertionError("Expected NormalizationError for 'Price on Request'")
    except NormalizationError as exc:
        print("[7] Invalid price rejection -> PASSED:", exc)

    # 8. Currency normalization ('₹', 'Rs.', 'INR', '$')
    dec_inr, curr_inr = ProductNormalizer.parse_price_and_currency("₹ 6,490.00")
    dec_rs, curr_rs = ProductNormalizer.parse_price_and_currency("Rs. 7,990")
    dec_usd, curr_usd = ProductNormalizer.parse_price_and_currency("$120.50")
    assert (dec_inr, curr_inr) == (Decimal("6490.00"), "INR")
    assert (dec_rs, curr_rs) == (Decimal("7990.00"), "INR")
    assert (dec_usd, curr_usd) == (Decimal("120.50"), "USD")
    print("[8] Currency normalization -> PASSED: ₹/Rs.->INR, $->USD")

    # 9. Relative image URL conversion & invalid data: URI removal
    norm_imgs = ProductNormalizer.normalize_image_urls(
        ["/img/a.jpg", "data:image/png;base64,xyz", "", "https://cdn.example.com/b.jpg"],
        base_url="https://store.example.com",
    )
    assert norm_imgs == [
        "https://store.example.com/img/a.jpg",
        "https://cdn.example.com/b.jpg",
    ]
    print("[9] Relative image URL conversion & filtering -> PASSED:", norm_imgs)

    # 10. Complete Product normalization
    first_norm = ProductNormalizer.normalize(first_raw, base_url=scraper.base_url)
    assert first_norm["name"] == "Raw Selvedge Denim Trucker Jacket"
    assert first_norm["price"] == Decimal("6490.00")
    assert first_norm["original_price"] == Decimal("7990.00")
    assert first_norm["currency"] == "INR"
    print("[10] Product normalization -> PASSED:", first_norm["name"], first_norm["price"])

    # 11. Pydantic ProductCreate validation
    validated = ProductCreate(**first_norm)
    assert validated.name == "Raw Selvedge Denim Trucker Jacket"
    assert str(validated.product_url) == "https://fixture-atelier.example.com/products/raw-selvedge-jacket"
    print("[11] Pydantic ProductCreate validation -> PASSED")

    # 12, 13, 14. End-to-End ScraperManager -> Product Service -> PostgreSQL Insertion, Duplicate Skip, and Safe Update
    # Use a real PostgreSQL connection wrapped in a SAVEPOINT transaction so test rows roll back cleanly
    connection = engine.connect()
    outer_tx = connection.begin()
    TestingSession = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    db = TestingSession()
    try:
        manager = ScraperManager()

        # Run #1: 4 items discovered -> 2 valid inserted, 2 invalid skipped
        run1 = manager.run_scraper(
            website_id="local_fixture",
            db=db,
            scraper_kwargs={"html_pages": [FIXTURE_HTML_MULTI_CASE]},
        )
        assert run1.products_discovered == 4
        assert run1.products_normalized == 2
        assert run1.products_inserted == 2
        assert run1.invalid_products_skipped == 2
        print("[13] Database insertion via ScraperManager -> PASSED:", run1.to_dict())

        # Verify rows in PostgreSQL
        db_item = db.execute(
            select(Product).where(Product.source_product_id == "TEST-SKU-001")
        ).scalar_one()
        assert db_item.price == Decimal("6490.00")
        assert db_item.color == "Indigo"

        # Run #2: Re-running exact same scrape -> 0 inserted, 0 updated, 2 duplicate_products_skipped
        run2 = manager.run_scraper(
            website_id="local_fixture",
            db=db,
            scraper_kwargs={"html_pages": [FIXTURE_HTML_MULTI_CASE]},
        )
        assert run2.products_inserted == 0
        assert run2.products_updated == 0
        assert run2.duplicate_products_skipped == 2
        print("[12] Duplicate product handling (idempotent skip) -> PASSED:", run2.to_dict())

        # Run #3: Price drop on TEST-SKU-001 while description/color/images are missing in new scrape
        run3 = manager.run_scraper(
            website_id="local_fixture",
            db=db,
            scraper_kwargs={"html_pages": [FIXTURE_HTML_PRICE_DROP_UPDATE]},
        )
        assert run3.products_inserted == 0
        assert run3.products_updated == 1
        db.refresh(db_item)
        assert db_item.price == Decimal("5990.00")
        # Crucial check: existing description, color, and image_urls were NOT overwritten with None/empty!
        assert db_item.color == "Indigo"
        assert db_item.description == "13.5oz shuttle-loom red-line selvedge denim jacket."
        assert len(db_item.image_urls) == 2
        print(
            "[14] Database update (updated price to 5990.00 while preserving existing color/description/images) -> PASSED"
        )

    finally:
        db.close()
        outer_tx.rollback()
        connection.close()

    print("\nALL 14 PHASE 4 SCRAPING & INGESTION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_phase4_tests()

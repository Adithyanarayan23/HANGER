import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

CURRENCY_MAP = {
    "₹": "INR",
    "rs.": "INR",
    "rs": "INR",
    "inr": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
}


class NormalizationError(ValueError):
    """Raised when required product fields are missing or unrecoverable during normalization."""
    pass


class ProductNormalizer:
    """
    Normalizes raw scraped dictionaries from any website-specific scraper
    into a clean dictionary matching the ProductCreate Pydantic schema.
    Never invents missing required fields, categories, colors, or descriptions.
    """

    @staticmethod
    def clean_whitespace(value: Optional[Any]) -> Optional[str]:
        """Collapse repeated internal whitespace and strip leading/trailing spaces."""
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        cleaned = " ".join(value.split())
        return cleaned if cleaned else None

    @classmethod
    def parse_price_and_currency(
        cls,
        raw_price: Any,
        explicit_currency: Optional[str] = None,
        default_currency: str = "INR",
    ) -> Tuple[Optional[Decimal], str]:
        """
        Extract a Decimal price and currency code from raw price strings such as:
        '₹ 7,490.00', 'Rs. 4,200', 'INR 1,999', or numeric values.
        Returns (Decimal, currency_code) or (None, currency_code) if invalid/missing.
        """
        detected_currency = cls.clean_whitespace(explicit_currency)
        if detected_currency:
            detected_currency = CURRENCY_MAP.get(detected_currency.lower(), detected_currency.upper())

        if raw_price is None or raw_price == "":
            return None, detected_currency or default_currency

        if isinstance(raw_price, Decimal):
            if raw_price < 0:
                raise NormalizationError(f"Price cannot be negative: {raw_price}")
            return raw_price.quantize(Decimal("0.01")), detected_currency or default_currency

        if isinstance(raw_price, (int, float)) and not isinstance(raw_price, bool):
            dec = Decimal(str(raw_price))
            if dec < 0:
                raise NormalizationError(f"Price cannot be negative: {raw_price}")
            return dec.quantize(Decimal("0.01")), detected_currency or default_currency

        text = str(raw_price).strip()
        if not text:
            return None, detected_currency or default_currency

        # Detect currency symbol or prefix if not explicitly provided
        lower_text = text.lower()
        if not detected_currency:
            for token, code in CURRENCY_MAP.items():
                if token in lower_text:
                    detected_currency = code
                    break

        final_currency = detected_currency or default_currency

        # Remove currency prefixes/words and commas, then match numeric pattern
        cleaned_numeric = re.sub(r"(?i)(inr|rs\.?|usd|eur|gbp|[₹$€£,\s])", "", text)
        match = re.search(r"^-?\d+(?:\.\d+)?$", cleaned_numeric)
        if not match:
            raise NormalizationError(f"Invalid price format: '{raw_price}'")

        try:
            amount = Decimal(match.group(0))
        except InvalidOperation as exc:
            raise NormalizationError(f"Invalid decimal price: '{raw_price}'") from exc

        if amount < 0:
            raise NormalizationError(f"Price cannot be negative: '{raw_price}'")

        return amount.quantize(Decimal("0.01")), final_currency

    @staticmethod
    def normalize_url(raw_url: Optional[str], base_url: str = "") -> Optional[str]:
        """Convert relative URLs to absolute HTTP/HTTPS URLs and reject invalid schemes."""
        if not raw_url or not isinstance(raw_url, str):
            return None
        trimmed = raw_url.strip()
        if not trimmed or trimmed.startswith(("javascript:", "mailto:", "data:")):
            return None
        resolved = urljoin(base_url, trimmed) if base_url else trimmed
        parsed = urlparse(resolved)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return None
        return resolved

    @classmethod
    def normalize_image_urls(cls, raw_images: Any, base_url: str = "") -> List[str]:
        """Normalize a list (or single string) of image URLs into unique, valid absolute URLs."""
        if not raw_images:
            return []
        if isinstance(raw_images, str):
            raw_images = [raw_images]
        if not isinstance(raw_images, (list, tuple, set)):
            return []

        normalized: List[str] = []
        for item in raw_images:
            valid_url = cls.normalize_url(item, base_url=base_url)
            if valid_url and valid_url not in normalized:
                normalized.append(valid_url)
        return normalized

    @classmethod
    def normalize_sizes(cls, raw_sizes: Any) -> List[str]:
        """Normalize available sizes into a clean list of unique strings."""
        if not raw_sizes:
            return []
        if isinstance(raw_sizes, str):
            raw_sizes = [s for s in re.split(r"[,/|]", raw_sizes)]
        if not isinstance(raw_sizes, (list, tuple, set)):
            return []

        sizes: List[str] = []
        for item in raw_sizes:
            cleaned = cls.clean_whitespace(item)
            if cleaned and cleaned not in sizes:
                sizes.append(cleaned)
        return sizes

    @classmethod
    def normalize(cls, raw_data: Dict[str, Any], base_url: str = "") -> Dict[str, Any]:
        """
        Transform a raw scraped product dictionary into the standardized structure
        compatible with ProductCreate. Raises NormalizationError if required fields
        are missing or invalid without inventing fake data.
        """
        if not isinstance(raw_data, dict):
            raise NormalizationError("Raw product data must be a dictionary.")

        effective_base = base_url or raw_data.get("base_url") or ""

        name = cls.clean_whitespace(raw_data.get("name"))
        brand = cls.clean_whitespace(raw_data.get("brand"))
        category = cls.clean_whitespace(raw_data.get("category"))
        source_website = cls.clean_whitespace(raw_data.get("source_website"))
        product_url = cls.normalize_url(cls.clean_whitespace(raw_data.get("product_url")), effective_base)

        if not name:
            raise NormalizationError("Missing required field: 'name'")
        if not brand:
            raise NormalizationError("Missing required field: 'brand'")
        if not category:
            raise NormalizationError("Missing required field: 'category'")
        if not source_website:
            raise NormalizationError("Missing required field: 'source_website'")
        if not product_url:
            raise NormalizationError("Missing or invalid required field: 'product_url'")

        price, currency = cls.parse_price_and_currency(
            raw_data.get("price"),
            explicit_currency=raw_data.get("currency"),
        )
        if price is None:
            raise NormalizationError("Missing required field: 'price'")

        raw_orig = raw_data.get("original_price")
        original_price: Optional[Decimal] = None
        if raw_orig is not None and str(raw_orig).strip() != "":
            original_price, _ = cls.parse_price_and_currency(raw_orig, explicit_currency=currency)

        raw_avail = raw_data.get("is_available")
        if isinstance(raw_avail, bool):
            is_available = raw_avail
        elif isinstance(raw_avail, str):
            is_available = raw_avail.strip().lower() not in ("false", "0", "out of stock", "sold out", "no")
        else:
            is_available = True

        return {
            "name": name,
            "description": cls.clean_whitespace(raw_data.get("description")),
            "brand": brand,
            "category": category,
            "subcategory": cls.clean_whitespace(raw_data.get("subcategory")),
            "color": cls.clean_whitespace(raw_data.get("color")),
            "price": price,
            "original_price": original_price,
            "currency": currency,
            "sizes": cls.normalize_sizes(raw_data.get("sizes")),
            "image_urls": cls.normalize_image_urls(raw_data.get("image_urls"), base_url=effective_base),
            "is_available": is_available,
            "source_website": source_website,
            "source_product_id": cls.clean_whitespace(raw_data.get("source_product_id")),
            "product_url": product_url,
        }

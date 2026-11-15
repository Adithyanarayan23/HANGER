import re
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional


@dataclass
class ProcessedQuery:
    """
    Holds the cleaned natural-language query for semantic embedding alongside
    any explicit structured filters confidently extracted from the query text.
    """

    original_query: str
    cleaned_query: str
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None


KNOWN_COLORS = [
    "black",
    "white",
    "ivory",
    "blue",
    "navy",
    "red",
    "green",
    "olive",
    "beige",
    "sand",
    "camel",
    "brown",
    "espresso",
    "charcoal",
    "grey",
    "gray",
    "indigo",
    "pink",
    "yellow",
]

CATEGORY_SYNONYMS = {
    "ethnic wear": ["ethnic", "kurti", "kurtis", "kurta", "chanderi", "saree", "lehenga"],
    "dresses": ["dress", "dresses", "gown", "slip dress"],
    "topwear": ["topwear", "shirt", "shirts", "t-shirt", "tee", "knit", "sweater", "top", "blouse"],
    "bottomwear": ["bottomwear", "trouser", "trousers", "pants", "jeans", "denim"],
    "outerwear": ["outerwear", "jacket", "jackets", "overshirt", "trench", "coat", "blazer"],
    "footwear": ["footwear", "shoes", "loafers", "sneakers", "boots", "heels"],
    "accessories": ["accessories", "bag", "handbag", "sunglasses", "belt", "watch"],
}


class QueryProcessor:
    """
    Prepares user natural-language queries for hybrid RAG retrieval:
    1. Cleans extra whitespace without altering semantic meaning.
    2. Extracts explicit price constraints ('under ₹1,000', 'between ₹500 and ₹1,500', 'above ₹1,000').
    3. Extracts explicit colour, category, or brand matches when confidently present.
    4. Never invents constraints that the user did not specify.
    """

    _NUM_PATTERN = r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)"

    @classmethod
    def _parse_amount(cls, raw_num: str) -> Decimal:
        cleaned = raw_num.replace(",", "").strip()
        return Decimal(cleaned)

    @classmethod
    def extract_price_constraints(
        cls,
        text: str,
    ) -> tuple[Optional[Decimal], Optional[Decimal]]:
        lower = text.lower()
        min_price: Optional[Decimal] = None
        max_price: Optional[Decimal] = None

        # Pattern 1: "between X and Y" or "from X to Y"
        between_match = re.search(
            rf"(?:between|from)\s+{cls._NUM_PATTERN}\s+(?:and|to|-)\s+{cls._NUM_PATTERN}",
            lower,
        )
        if between_match:
            first = cls._parse_amount(between_match.group(1))
            second = cls._parse_amount(between_match.group(2))
            return min(first, second), max(first, second)

        # Pattern 2: "under X", "below X", "less than X", "up to X", "within X"
        under_match = re.search(
            rf"(?:under|below|less\s+than|up\s+to|within|max)\s+{cls._NUM_PATTERN}",
            lower,
        )
        if under_match:
            max_price = cls._parse_amount(under_match.group(1))

        # Pattern 3: "above X", "over X", "more than X", "at least X", "starting from X"
        above_match = re.search(
            rf"(?:above|over|more\s+than|at\s+least|min|starting\s+from)\s+{cls._NUM_PATTERN}",
            lower,
        )
        if above_match:
            min_price = cls._parse_amount(above_match.group(1))

        if min_price is not None and max_price is not None and min_price > max_price:
            min_price, max_price = max_price, min_price

        return min_price, max_price

    @staticmethod
    def extract_color(text: str, catalog_colors: Optional[List[str]] = None) -> Optional[str]:
        candidates = catalog_colors if catalog_colors else KNOWN_COLORS
        lower = text.lower()
        for color in candidates:
            c_clean = color.strip().lower()
            if c_clean and re.search(rf"\b{re.escape(c_clean)}\b", lower):
                return color.strip().title()
        return None

    @staticmethod
    def extract_category(text: str, catalog_categories: Optional[List[str]] = None) -> Optional[str]:
        lower = text.lower()
        if catalog_categories:
            for cat in catalog_categories:
                c_clean = cat.strip().lower()
                if c_clean and re.search(rf"\b{re.escape(c_clean)}\b", lower):
                    return cat.strip()

        for canonical_cat, keywords in CATEGORY_SYNONYMS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", lower):
                    if catalog_categories:
                        for db_cat in catalog_categories:
                            if db_cat.strip().lower() == canonical_cat.lower():
                                return db_cat.strip()
                    return canonical_cat.title()
        return None

    @staticmethod
    def extract_brand(text: str, catalog_brands: Optional[List[str]] = None) -> Optional[str]:
        if not catalog_brands:
            return None
        lower = text.lower()
        # Sort longest brand names first so 'Massimo Dutti' matches before single words
        for brand in sorted(catalog_brands, key=lambda b: len(b or ""), reverse=True):
            b_clean = (brand or "").strip()
            if b_clean and re.search(rf"\b{re.escape(b_clean.lower())}\b", lower):
                return b_clean
        return None

    @classmethod
    def process(
        cls,
        query: str,
        catalog_brands: Optional[List[str]] = None,
        catalog_categories: Optional[List[str]] = None,
        catalog_colors: Optional[List[str]] = None,
    ) -> ProcessedQuery:
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        cleaned = " ".join(query.strip().split())
        min_price, max_price = cls.extract_price_constraints(cleaned)
        color = cls.extract_color(cleaned, catalog_colors=catalog_colors)
        category = cls.extract_category(cleaned, catalog_categories=catalog_categories)
        brand = cls.extract_brand(cleaned, catalog_brands=catalog_brands)

        return ProcessedQuery(
            original_query=query,
            cleaned_query=cleaned,
            min_price=min_price,
            max_price=max_price,
            category=category,
            brand=brand,
            color=color,
        )

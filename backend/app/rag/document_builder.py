import hashlib
from typing import Tuple

from app.models.product import Product


class DocumentBuilder:
    """
    Converts a Product SQLAlchemy record into a deterministic, human-readable text
    representation for semantic embedding and computes its SHA-256 content_hash.

    Rules:
    - Uses only actual product fields from PostgreSQL.
    - Excludes missing or empty fields.
    - Excludes unstable URLs (product_url, image_urls) and numeric price (handled via SQL filters).
    - Produces deterministic output and SHA-256 hash so unchanged products are skipped.
    """

    @staticmethod
    def _clean(value: object) -> str:
        if value is None:
            return ""
        text = " ".join(str(value).strip().split())
        return text.rstrip(".")

    @classmethod
    def build_document(cls, product: Product) -> str:
        """
        Build canonical semantic document string in the format:
        title: <Name> | text: Brand: <Brand>. Category: <Category>. ...
        """
        title = cls._clean(product.name)
        segments: list[str] = []

        brand = cls._clean(product.brand)
        if brand:
            segments.append(f"Brand: {brand}.")

        category = cls._clean(product.category)
        if category:
            segments.append(f"Category: {category}.")

        subcategory = cls._clean(product.subcategory)
        if subcategory and subcategory.lower() != category.lower():
            segments.append(f"Subcategory: {subcategory}.")

        color = cls._clean(product.color)
        if color:
            segments.append(f"Colour: {color}.")

        if product.sizes:
            clean_sizes = [cls._clean(s) for s in product.sizes if cls._clean(s)]
            if clean_sizes:
                segments.append(f"Sizes: {', '.join(clean_sizes)}.")

        description = cls._clean(product.description)
        if description:
            segments.append(f"Description: {description}.")

        body = " ".join(segments)
        return f"title: {title} | text: {body}".strip()

    @staticmethod
    def compute_content_hash(document_text: str) -> str:
        """Compute deterministic SHA-256 hex digest of the canonical document text."""
        normalized = (document_text or "").strip().encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    @classmethod
    def build_document_with_hash(cls, product: Product) -> Tuple[str, str]:
        """Return (document_text, content_hash) for a Product instance."""
        doc = cls.build_document(product)
        return doc, cls.compute_content_hash(doc)

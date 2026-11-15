from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_embedding import ProductEmbedding


@dataclass
class RetrievedProductMatch:
    """Pairs an actual PostgreSQL Product ORM record with its cosine similarity score."""

    product: Product
    similarity_score: float


class VectorStore:
    """
    Manages storage and pgvector cosine-distance similarity search over
    the `product_embeddings` table joined with `products`.
    """

    @staticmethod
    def get_embedding_by_product_id(db: Session, product_id: int) -> Optional[ProductEmbedding]:
        stmt = select(ProductEmbedding).where(ProductEmbedding.product_id == product_id)
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def upsert_product_embedding(
        cls,
        db: Session,
        product_id: int,
        embedding: List[float],
        embedding_model: str,
        content_hash: str,
    ) -> ProductEmbedding:
        """Insert or update the embedding record for a product_id."""
        existing = cls.get_embedding_by_product_id(db, product_id)
        if existing is None:
            record = ProductEmbedding(
                product_id=product_id,
                embedding=embedding,
                embedding_model=embedding_model,
                content_hash=content_hash,
            )
            db.add(record)
        else:
            existing.embedding = embedding
            existing.embedding_model = embedding_model
            existing.content_hash = content_hash
            record = existing

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def search_similar_products(
        db: Session,
        query_embedding: List[float],
        top_k: int = 5,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        color: Optional[str] = None,
        only_available: bool = True,
    ) -> List[RetrievedProductMatch]:
        """
        Execute a single SQL query joining `Product` and `ProductEmbedding`,
        filtering by strict SQL metadata constraints, and ordering by
        pgvector cosine distance (`ProductEmbedding.embedding.cosine_distance(query_embedding)`).
        """
        distance_expr = ProductEmbedding.embedding.cosine_distance(query_embedding).label("distance")

        stmt = (
            select(Product, distance_expr)
            .join(ProductEmbedding, ProductEmbedding.product_id == Product.id)
        )

        if only_available:
            stmt = stmt.where(Product.is_available.is_(True))

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if brand and brand.strip():
            stmt = stmt.where(Product.brand.ilike(brand.strip()))

        if category and category.strip():
            stmt = stmt.where(Product.category.ilike(category.strip()))

        if color and color.strip():
            stmt = stmt.where(Product.color.ilike(color.strip()))

        stmt = stmt.order_by(distance_expr.asc()).limit(top_k)

        rows = db.execute(stmt).all()
        matches: List[RetrievedProductMatch] = []
        for product_obj, distance_val in rows:
            dist = float(distance_val) if distance_val is not None else 1.0
            # Cosine similarity = 1 - cosine_distance, clamped to [0.0, 1.0]
            similarity = max(0.0, min(1.0, round(1.0 - dist, 4)))
            matches.append(
                RetrievedProductMatch(
                    product=product_obj,
                    similarity_score=similarity,
                )
            )
        return matches

from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_embedding import ProductEmbedding
from app.rag.query_processor import ProcessedQuery
from app.rag.vector_store import RetrievedProductMatch, VectorStore


class HybridRetriever:
    """
    Combines semantic vector similarity search (pgvector cosine distance)
    with strict PostgreSQL structured filters (price range, brand, category,
    color, and availability).
    """

    @staticmethod
    def get_catalog_dimensions(db: Session) -> Tuple[List[str], List[str], List[str]]:
        """Return distinct (brands, categories, colors) currently present in PostgreSQL."""
        brands = [
            r[0]
            for r in db.execute(
                select(Product.brand).where(Product.brand.is_not(None)).distinct()
            ).all()
            if r[0]
        ]
        categories = [
            r[0]
            for r in db.execute(
                select(Product.category).where(Product.category.is_not(None)).distinct()
            ).all()
            if r[0]
        ]
        colors = [
            r[0]
            for r in db.execute(
                select(Product.color).where(Product.color.is_not(None)).distinct()
            ).all()
            if r[0]
        ]
        return brands, categories, colors

    @staticmethod
    def count_catalog_and_embeddings(db: Session) -> Tuple[int, int]:
        """Return (total_products_count, total_embeddings_count)."""
        total_products = db.execute(select(func.count(Product.id))).scalar_one() or 0
        total_embeddings = db.execute(select(func.count(ProductEmbedding.id))).scalar_one() or 0
        return int(total_products), int(total_embeddings)

    @classmethod
    def retrieve(
        cls,
        db: Session,
        processed_query: ProcessedQuery,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[RetrievedProductMatch]:
        """
        Retrieve up to top_k products satisfying both semantic similarity and
        explicit user constraints.

        Price and availability constraints are always enforced strictly.
        If soft categorical/color extraction yields 0 matches because a product's
        category label differs slightly (e.g., 'Kurtis' vs 'Ethnic Wear'), falls back
        to strict price + availability + semantic vector ranking.
        """
        matches = VectorStore.search_similar_products(
            db=db,
            query_embedding=query_embedding,
            top_k=top_k,
            min_price=processed_query.min_price,
            max_price=processed_query.max_price,
            brand=processed_query.brand,
            category=processed_query.category,
            color=processed_query.color,
            only_available=True,
        )

        if not matches and (processed_query.category or processed_query.color):
            matches = VectorStore.search_similar_products(
                db=db,
                query_embedding=query_embedding,
                top_k=top_k,
                min_price=processed_query.min_price,
                max_price=processed_query.max_price,
                brand=processed_query.brand,
                category=None,
                color=None,
                only_available=True,
            )

        return matches

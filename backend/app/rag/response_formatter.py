from typing import List

from app.rag.query_processor import ProcessedQuery
from app.rag.vector_store import RetrievedProductMatch
from app.schemas.rag import RAGProductItem, RAGQueryResponse


class ResponseFormatter:
    """
    Formats retrieved PostgreSQL Product records and the AI-generated explanation
    into a validated RAGQueryResponse.

    Guarantees:
    - Product fields (id, name, brand, price, currency, product_url, etc.) are read
      exclusively from the PostgreSQL Product ORM objects—never from LLM output.
    - Re-verifies hard filters (availability, min_price, max_price) before returning.
    """

    @staticmethod
    def _satisfies_hard_filters(
        match: RetrievedProductMatch,
        processed_query: ProcessedQuery,
    ) -> bool:
        product = match.product
        if not product.is_available:
            return False
        if processed_query.min_price is not None and product.price < processed_query.min_price:
            return False
        if processed_query.max_price is not None and product.price > processed_query.max_price:
            return False
        if processed_query.brand and product.brand.lower() != processed_query.brand.lower():
            return False
        return True

    @classmethod
    def format_response(
        cls,
        processed_query: ProcessedQuery,
        retrieved_matches: List[RetrievedProductMatch],
        answer: str,
    ) -> RAGQueryResponse:
        verified_items: List[RAGProductItem] = []

        for match in retrieved_matches:
            if not cls._satisfies_hard_filters(match, processed_query):
                continue
            p = match.product
            verified_items.append(
                RAGProductItem(
                    id=p.id,
                    name=p.name,
                    brand=p.brand,
                    category=p.category,
                    subcategory=p.subcategory,
                    price=p.price,
                    original_price=p.original_price,
                    currency=p.currency,
                    color=p.color,
                    sizes=list(p.sizes or []),
                    image_urls=list(p.image_urls or []),
                    is_available=p.is_available,
                    source_website=p.source_website,
                    product_url=p.product_url,
                    similarity_score=match.similarity_score,
                )
            )

        final_answer = (
            answer.strip()
            if verified_items and answer and answer.strip()
            else "No matching products were found in the catalogue for your search criteria."
        )

        return RAGQueryResponse(
            query=processed_query.cleaned_query,
            answer=final_answer,
            products=verified_items,
            total_results=len(verified_items),
        )

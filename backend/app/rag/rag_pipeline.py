import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.product import Product
from app.rag.document_builder import DocumentBuilder
from app.rag.embedding_service import (
    EmbeddingConfigurationError,
    EmbeddingServiceError,
    GeminiEmbeddingService,
)
from app.rag.llm_service import GeminiLLMService, LLMServiceError
from app.rag.query_processor import QueryProcessor
from app.rag.response_formatter import ResponseFormatter
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import VectorStore
from app.schemas.rag import RAGQueryResponse


@dataclass
class EmbeddingBatchSummary:
    """Summary of a CLI product embedding generation run."""

    total_products_checked: int = 0
    embeddings_created: int = 0
    embeddings_updated: int = 0
    unchanged_skipped: int = 0
    failed_count: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class RAGPipeline:
    """
    Central orchestrator for HANGER's Retrieval-Augmented Generation (RAG) flow:
    User Query -> QueryProcessor -> Gemini Query Embedding -> HybridRetriever
    -> Grounded Prompt -> GeminiLLMService -> ResponseFormatter -> RAGQueryResponse
    """

    def __init__(
        self,
        embedding_service: Optional[GeminiEmbeddingService] = None,
        llm_service: Optional[GeminiLLMService] = None,
    ) -> None:
        self.embedding_service = embedding_service or GeminiEmbeddingService()
        self.llm_service = llm_service or GeminiLLMService()

    def run(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
    ) -> RAGQueryResponse:
        # 1. Check catalogue and embedding availability before making external calls
        total_products, total_embeddings = HybridRetriever.count_catalog_and_embeddings(db)

        brands, categories, colors = HybridRetriever.get_catalog_dimensions(db)
        processed = QueryProcessor.process(
            query=query,
            catalog_brands=brands,
            catalog_categories=categories,
            catalog_colors=colors,
        )

        if total_products == 0:
            return RAGQueryResponse(
                query=processed.cleaned_query,
                answer="The product catalogue is currently empty.",
                products=[],
                total_results=0,
            )

        if total_embeddings == 0:
            return RAGQueryResponse(
                query=processed.cleaned_query,
                answer="No product embeddings are currently indexed. Run the embedding generation CLI first.",
                products=[],
                total_results=0,
            )

        # 2. Generate 768-d query embedding (RETRIEVAL_QUERY)
        query_vector = self.embedding_service.embed_query(processed.cleaned_query)

        # 3. Hybrid retrieval (pgvector cosine similarity + SQL structured filters)
        matches = HybridRetriever.retrieve(
            db=db,
            processed_query=processed,
            query_embedding=query_vector,
            top_k=top_k,
        )

        if not matches:
            return RAGQueryResponse(
                query=processed.cleaned_query,
                answer="No matching products were found in the catalogue for your search criteria.",
                products=[],
                total_results=0,
            )

        # 4. Generate grounded natural-language explanation via Gemini
        #    If Gemini LLM fails transiently, fall back gracefully to returning retrieved products
        try:
            explanation = self.llm_service.generate_explanation(
                user_query=processed.cleaned_query,
                retrieved_matches=matches,
            )
        except LLMServiceError:
            explanation = (
                f"Found {len(matches)} matching product(s) in our catalogue based on your search criteria."
            )

        # 5. Format and verify hard filters against PostgreSQL Product records
        return ResponseFormatter.format_response(
            processed_query=processed,
            retrieved_matches=matches,
            answer=explanation,
        )

    def sync_product_embeddings(
        self,
        db: Session,
        product_id: Optional[int] = None,
        force_reembed: bool = False,
    ) -> EmbeddingBatchSummary:
        """
        CLI workflow to generate or update embeddings for existing PostgreSQL products.
        - Skips products whose SHA-256 content_hash and embedding_model are unchanged.
        - Re-embeds products when content_hash or model changes.
        - Continues batch processing if an individual product fails.
        """
        summary = EmbeddingBatchSummary()

        stmt = select(Product).order_by(Product.id.asc())
        if product_id is not None:
            stmt = stmt.where(Product.id == product_id)

        products = list(db.execute(stmt).scalars().all())
        summary.total_products_checked = len(products)

        for product in products:
            try:
                doc_text, content_hash = DocumentBuilder.build_document_with_hash(product)
                existing = VectorStore.get_embedding_by_product_id(db, product.id)

                if (
                    existing is not None
                    and not force_reembed
                    and existing.content_hash == content_hash
                    and existing.embedding_model == self.embedding_service.model_name
                ):
                    summary.unchanged_skipped += 1
                    continue

                is_new = existing is None
                vector = self.embedding_service.embed_document(doc_text)
                VectorStore.upsert_product_embedding(
                    db=db,
                    product_id=product.id,
                    embedding=vector,
                    embedding_model=self.embedding_service.model_name,
                    content_hash=content_hash,
                )
                if is_new:
                    summary.embeddings_created += 1
                else:
                    summary.embeddings_updated += 1

            except (EmbeddingConfigurationError, EmbeddingServiceError, Exception) as exc:
                db.rollback()
                summary.failed_count += 1
                summary.errors.append(f"Product id={product.id}: {exc}")

        return summary


def main() -> None:
    """
    Command-line entrypoint for generating and updating product embeddings:
      - All products:        python -m app.rag.rag_pipeline --all
      - Specific product ID: python -m app.rag.rag_pipeline --product-id 1
      - Stale/changed only:  python -m app.rag.rag_pipeline --stale-only
    """
    parser = argparse.ArgumentParser(
        description="Generate or update 768-d Gemini embeddings for HANGER products in PostgreSQL."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all products and generate embeddings for new or changed items.",
    )
    parser.add_argument(
        "--product-id",
        type=int,
        default=None,
        help="Generate or update the embedding for a single specific product ID.",
    )
    parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Re-embed only products whose content hash has changed or lack an embedding.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if content_hash is unchanged.",
    )
    args = parser.parse_args()

    pipeline = RAGPipeline()
    with SessionLocal() as db:
        result = pipeline.sync_product_embeddings(
            db=db,
            product_id=args.product_id,
            force_reembed=args.force,
        )
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()

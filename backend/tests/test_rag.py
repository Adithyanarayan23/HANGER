import math
from decimal import Decimal
from typing import List
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api.endpoints.rag import get_rag_pipeline
from app.database.connection import engine
from app.database.session import get_db
from app.main import app
from app.models.product import Product
from app.models.product_embedding import ProductEmbedding
from app.rag.document_builder import DocumentBuilder
from app.rag.embedding_service import (
    EmbeddingConfigurationError,
    EmbeddingServiceError,
    GeminiEmbeddingService,
)
from app.rag.llm_service import GeminiLLMService
from app.rag.prompt_templates import build_grounded_recommendation_prompt
from app.rag.query_processor import QueryProcessor
from app.rag.rag_pipeline import RAGPipeline
from app.rag.response_formatter import ResponseFormatter
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import RetrievedProductMatch, VectorStore
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import product_service


def make_basis_vector(primary_index: int, secondary_index: int = -1, dims: int = 768) -> List[float]:
    """Create a deterministic 768-d unit vector pointing along primary_index."""
    vec = [0.0] * dims
    vec[primary_index] = 1.0
    if secondary_index >= 0:
        vec[secondary_index] = 0.5
    return GeminiEmbeddingService.normalize_vector(vec)


class MockGenAIClient:
    """Deterministic mock for google.genai.Client to test embedding and LLM services without API charges."""

    def __init__(self) -> None:
        self.models = MagicMock()
        self.last_embed_kwargs = None
        self.last_generate_kwargs = None

        def fake_embed_content(**kwargs):
            self.last_embed_kwargs = kwargs
            text = str(kwargs.get("contents", "")).lower()
            # Assign orthogonal directions based on fashion keywords so semantic similarity is deterministic
            if "kurti" in text or "ethnic" in text:
                raw_vec = make_basis_vector(0, 1)
            elif "dress" in text or "party" in text:
                raw_vec = make_basis_vector(2, 3)
            elif "linen" in text or "overshirt" in text:
                raw_vec = make_basis_vector(4, 5)
            else:
                raw_vec = make_basis_vector(10)

            emb_obj = MagicMock()
            emb_obj.values = raw_vec
            resp = MagicMock()
            resp.embeddings = [emb_obj]
            return resp

        def fake_generate_content(**kwargs):
            self.last_generate_kwargs = kwargs
            resp = MagicMock()
            resp.text = (
                "Based on our retrieved catalogue, the Blue Cotton Kurti by Fabindia (899.00 INR) "
                "is an ideal breathable ethnic option under your ₹1,000 budget."
            )
            return resp

        self.models.embed_content.side_effect = fake_embed_content
        self.models.generate_content.side_effect = fake_generate_content


def run_all_phase5_rag_tests() -> None:
    # -------------------------------------------------------------------------
    # Test 1 & 2: Product document generation & deterministic SHA-256 content_hash
    # -------------------------------------------------------------------------
    sample_product = Product(
        id=101,
        name="Blue Cotton Kurti",
        brand="Fabindia",
        category="Ethnic Wear",
        subcategory="Kurtis",
        color="Blue",
        price=Decimal("899.00"),
        currency="INR",
        sizes=["S", "M", "L"],
        image_urls=["https://example.com/kurti.jpg"],
        is_available=True,
        source_website="Myntra",
        source_product_id="MYN-KURTI-101",
        product_url="https://example.com/product/101",
        description="Lightweight cotton kurti suitable for casual college wear.",
    )
    doc1, hash1 = DocumentBuilder.build_document_with_hash(sample_product)
    doc2, hash2 = DocumentBuilder.build_document_with_hash(sample_product)
    assert doc1 == doc2
    assert hash1 == hash2 and len(hash1) == 64
    assert "title: Blue Cotton Kurti | text: Brand: Fabindia. Category: Ethnic Wear." in doc1
    assert "https://example.com" not in doc1  # Unstable URLs excluded from semantic document
    print("[1] Product document generation -> PASSED:", doc1)
    print("[2] Deterministic SHA-256 content hash -> PASSED:", hash1[:16] + "...")

    # -------------------------------------------------------------------------
    # Test 3, 4, 5: Gemini Embedding Service configuration, 768-d validation & task_type
    # -------------------------------------------------------------------------
    unconfigured_emb = GeminiEmbeddingService(api_key="")
    try:
        unconfigured_emb.embed_query("test")
        raise AssertionError("Expected EmbeddingConfigurationError when GEMINI_API_KEY is missing")
    except EmbeddingConfigurationError as exc:
        print("[3] Gemini embedding configuration check (missing API key caught) -> PASSED:", exc)

    mock_client = MockGenAIClient()
    emb_service = GeminiEmbeddingService(
        api_key="mock-key",
        model_name="gemini-embedding-001",
        dimensions=768,
        client=mock_client,
    )

    try:
        emb_service.validate_and_normalize([0.1, 0.2, 0.3])
        raise AssertionError("Expected dimension mismatch error")
    except EmbeddingServiceError as exc:
        print("[4] Embedding dimension validation (rejects non-768 vector) -> PASSED:", exc)

    doc_vec = emb_service.embed_document(doc1)
    assert len(doc_vec) == 768
    assert math.isclose(math.sqrt(sum(x * x for x in doc_vec)), 1.0, rel_tol=1e-5)
    assert mock_client.last_embed_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert mock_client.last_embed_kwargs["config"].output_dimensionality == 768

    query_vec = emb_service.embed_query("Find me a comfortable blue ethnic outfit under ₹1,000")
    assert len(query_vec) == 768
    assert mock_client.last_embed_kwargs["config"].task_type == "RETRIEVAL_QUERY"
    print("[5] Document (RETRIEVAL_DOCUMENT) & Query (RETRIEVAL_QUERY) 768-d unit vectors -> PASSED")

    # -------------------------------------------------------------------------
    # Test 8, 9, 10, 11 (QueryProcessor extraction): Price, Brand, Category, Colour
    # -------------------------------------------------------------------------
    pq1 = QueryProcessor.process(
        "Find me a comfortable blue ethnic outfit for college under ₹1,000",
        catalog_brands=["Fabindia", "Zara", "COS"],
        catalog_categories=["Ethnic Wear", "Dresses", "Outerwear"],
        catalog_colors=["Blue", "Black", "Sand"],
    )
    assert pq1.max_price == Decimal("1000")
    assert pq1.min_price is None
    assert pq1.color == "Blue"
    assert pq1.category == "Ethnic Wear"

    pq_between = QueryProcessor.process("Show me Fabindia kurtis between ₹500 and ₹1,500", catalog_brands=["Fabindia"])
    assert pq_between.min_price == Decimal("500")
    assert pq_between.max_price == Decimal("1500")
    assert pq_between.brand == "Fabindia"

    pq_above = QueryProcessor.process("Minimal black dresses above ₹2,000")
    assert pq_above.min_price == Decimal("2000")
    assert pq_above.color == "Black"
    print("[QueryProcessor] Price (under/between/above), Brand, Category & Colour extraction -> PASSED")

    # -------------------------------------------------------------------------
    # Test 18 & 19: Grounded Prompt Construction & Response Formatter Guardrails
    # -------------------------------------------------------------------------
    match_item = RetrievedProductMatch(product=sample_product, similarity_score=0.9234)
    grounded_prompt = build_grounded_recommendation_prompt("blue kurti under 1000", [match_item])
    assert "<RETRIEVED_PRODUCTS_DATA>" in grounded_prompt
    assert "Blue Cotton Kurti" in grounded_prompt
    assert "899.00 INR" in grounded_prompt
    print("[18] Grounded Gemini prompt construction -> PASSED")

    # Verify ResponseFormatter never lets LLM text overwrite product prices or URLs,
    # and filters out any product that violates explicit hard price constraints
    over_budget_product = Product(
        id=999,
        name="Hallucinated Expensive Saree",
        brand="FakeBrand",
        category="Ethnic Wear",
        color="Blue",
        price=Decimal("5000.00"),
        currency="INR",
        sizes=["Free"],
        image_urls=[],
        is_available=True,
        source_website="Test",
        product_url="https://example.com/999",
    )
    formatted = ResponseFormatter.format_response(
        processed_query=pq1,  # max_price = 1000
        retrieved_matches=[
            match_item,
            RetrievedProductMatch(product=over_budget_product, similarity_score=0.99),
        ],
        answer="Even if the LLM mentions a ₹5000 product or fake URL, products[] comes strictly from PostgreSQL.",
    )
    assert formatted.total_results == 1
    assert formatted.products[0].id == 101
    assert formatted.products[0].price == Decimal("899.00")
    assert formatted.products[0].product_url == "https://example.com/product/101"
    print("[19] Product response formatting & hard-filter verification -> PASSED")

    # -------------------------------------------------------------------------
    # Database-Backed Tests (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20)
    # -------------------------------------------------------------------------
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
        llm_service = GeminiLLMService(
            api_key="mock-key",
            model_name="gemini-2.5-flash",
            client=mock_client,
        )
        pipeline = RAGPipeline(embedding_service=emb_service, llm_service=llm_service)

        # Test 14: Empty product catalogue
        empty_res = pipeline.run(db=db, query="Find blue cotton kurtis under ₹1,000", top_k=5)
        assert empty_res.total_results == 0
        assert "empty" in empty_res.answer.lower()
        print("[14] Empty product catalogue handling -> PASSED:", empty_res.answer)

        # Insert 3 real products into PostgreSQL via Product Service
        p_kurti = product_service.create_product(
            db,
            ProductCreate(
                name="Blue Cotton Kurti",
                description="Lightweight cotton kurti suitable for college wear.",
                brand="Fabindia",
                category="Ethnic Wear",
                subcategory="Kurtis",
                color="Blue",
                price=Decimal("899.00"),
                currency="INR",
                sizes=["S", "M", "L"],
                image_urls=["https://example.com/kurti.jpg"],
                is_available=True,
                source_website="Myntra",
                source_product_id="RAG-TEST-1",
                product_url="https://example.com/p/1",
            ),
        )
        p_dress = product_service.create_product(
            db,
            ProductCreate(
                name="Minimal Black Party Slip Dress",
                description="Sleek minimal black midi dress for evening parties.",
                brand="Zara",
                category="Dresses",
                color="Black",
                price=Decimal("3490.00"),
                currency="INR",
                sizes=["XS", "S", "M"],
                image_urls=["https://example.com/dress.jpg"],
                is_available=True,
                source_website="Zara India",
                source_product_id="RAG-TEST-2",
                product_url="https://example.com/p/2",
            ),
        )
        p_linen = product_service.create_product(
            db,
            ProductCreate(
                name="Beige Belgian Linen Shirt",
                description="Relaxed breathable beige linen shirt.",
                brand="Massimo Dutti",
                category="Topwear",
                color="Beige",
                price=Decimal("4990.00"),
                currency="INR",
                sizes=["M", "L"],
                image_urls=["https://example.com/linen.jpg"],
                is_available=True,
                source_website="Ajio Luxe",
                source_product_id="RAG-TEST-3",
                product_url="https://example.com/p/3",
            ),
        )

        # Test 15: Embedding generation for existing products
        batch1 = pipeline.sync_product_embeddings(db=db)
        assert batch1.total_products_checked == 3
        assert batch1.embeddings_created == 3
        assert batch1.unchanged_skipped == 0
        print("[15] Embedding generation for existing products -> PASSED:", batch1.to_dict())

        # Test 16: Skipping unchanged embeddings on second run
        batch2 = pipeline.sync_product_embeddings(db=db)
        assert batch2.embeddings_created == 0
        assert batch2.embeddings_updated == 0
        assert batch2.unchanged_skipped == 3
        print("[16] Skipping unchanged embeddings -> PASSED:", batch2.to_dict())

        # Test 17: Product update marks embedding as stale via content_hash & re-embeds only changed product
        assert product_service.is_product_embedding_stale(db, p_kurti) is False
        product_service.update_product(
            db,
            p_kurti.id,
            ProductUpdate(description="Updated handblock cotton kurti for college and daily wear."),
        )
        assert product_service.is_product_embedding_stale(db, p_kurti) is True
        batch3 = pipeline.sync_product_embeddings(db=db)
        assert batch3.embeddings_updated == 1
        assert batch3.unchanged_skipped == 2
        assert product_service.is_product_embedding_stale(db, p_kurti) is False
        print("[17] Stale embedding detection & selective update -> PASSED:", batch3.to_dict())

        # Test 6 & 7: VectorStore storage & cosine similarity retrieval
        kurti_query_vec = emb_service.embed_query("comfortable blue ethnic kurti")
        sim_matches = VectorStore.search_similar_products(db=db, query_embedding=kurti_query_vec, top_k=3)
        assert len(sim_matches) == 3
        assert sim_matches[0].product.id == p_kurti.id
        assert sim_matches[0].similarity_score > sim_matches[1].similarity_score
        print(
            "[6 & 7] Vector storage & pgvector cosine similarity ranking -> PASSED: top match =",
            sim_matches[0].product.name,
            "score =",
            sim_matches[0].similarity_score,
        )

        # Test 8, 9, 10, 11: Structured SQL filters in VectorStore
        price_filtered = VectorStore.search_similar_products(
            db=db, query_embedding=kurti_query_vec, max_price=Decimal("1000.00")
        )
        assert len(price_filtered) == 1 and price_filtered[0].product.id == p_kurti.id
        print("[8] Structured price filtering (<= 1000) -> PASSED")

        brand_filtered = VectorStore.search_similar_products(
            db=db, query_embedding=kurti_query_vec, brand="Zara"
        )
        assert len(brand_filtered) == 1 and brand_filtered[0].product.id == p_dress.id
        print("[9] Structured brand filtering ('Zara') -> PASSED")

        cat_filtered = VectorStore.search_similar_products(
            db=db, query_embedding=kurti_query_vec, category="Topwear"
        )
        assert len(cat_filtered) == 1 and cat_filtered[0].product.id == p_linen.id
        print("[10] Structured category filtering ('Topwear') -> PASSED")

        color_filtered = VectorStore.search_similar_products(
            db=db, query_embedding=kurti_query_vec, color="Black"
        )
        assert len(color_filtered) == 1 and color_filtered[0].product.id == p_dress.id
        print("[11] Structured colour filtering ('Black') -> PASSED")

        # Test 12: End-to-End Hybrid Retrieval via RAGPipeline
        rag_result = pipeline.run(
            db=db,
            query="Find me a comfortable blue ethnic outfit for college under ₹1,000",
            top_k=5,
        )
        assert rag_result.total_results == 1
        assert rag_result.products[0].id == p_kurti.id
        assert rag_result.products[0].price == Decimal("899.00")
        print("[12] End-to-end Hybrid Retrieval & Grounded RAG response -> PASSED")

        # Test 13: No matching products (e.g., budget under ₹200)
        no_match_res = pipeline.run(
            db=db,
            query="Find me a blue ethnic outfit under ₹200",
            top_k=5,
        )
        assert no_match_res.total_results == 0
        assert no_match_res.products == []
        print("[13] No matching products graceful response -> PASSED:", no_match_res.answer)

        # Test 20: POST /api/v1/rag/query FastAPI Endpoint
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_rag_pipeline] = lambda: pipeline
        with TestClient(app) as client:
            api_resp = client.post(
                "/api/v1/rag/query",
                json={
                    "query": "Find me a comfortable blue ethnic outfit for college under ₹1,000",
                    "top_k": 5,
                },
            )
            assert api_resp.status_code == 200, api_resp.text
            body = api_resp.json()
            assert body["total_results"] == 1
            assert body["products"][0]["name"] == "Blue Cotton Kurti"
            assert body["products"][0]["price"] == "899.00"
            assert body["products"][0]["product_url"] == "https://example.com/p/1"

            # Verify validation error on empty query or invalid top_k
            bad_resp = client.post("/api/v1/rag/query", json={"query": "   ", "top_k": 0})
            assert bad_resp.status_code == 422
            print("[20] POST /api/v1/rag/query API endpoint & validation -> PASSED")

    finally:
        app.dependency_overrides.clear()
        db.close()
        outer_tx.rollback()
        connection.close()

    print("\nALL 20 PHASE 5 RAG TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_phase5_rag_tests()

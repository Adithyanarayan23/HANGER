"""HANGER Retrieval-Augmented Generation (RAG) package."""

from app.rag.document_builder import DocumentBuilder
from app.rag.embedding_service import (
    EmbeddingConfigurationError,
    EmbeddingServiceError,
    GeminiEmbeddingService,
)
from app.rag.llm_service import GeminiLLMService, LLMServiceError
from app.rag.query_processor import ProcessedQuery, QueryProcessor
from app.rag.rag_pipeline import EmbeddingBatchSummary, RAGPipeline
from app.rag.response_formatter import ResponseFormatter
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import RetrievedProductMatch, VectorStore

__all__ = [
    "DocumentBuilder",
    "GeminiEmbeddingService",
    "EmbeddingConfigurationError",
    "EmbeddingServiceError",
    "GeminiLLMService",
    "LLMServiceError",
    "QueryProcessor",
    "ProcessedQuery",
    "HybridRetriever",
    "VectorStore",
    "RetrievedProductMatch",
    "ResponseFormatter",
    "RAGPipeline",
    "EmbeddingBatchSummary",
]

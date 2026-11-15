import math
from typing import List, Optional

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingConfigurationError(RuntimeError):
    """Raised when GEMINI_API_KEY or embedding configuration is missing or invalid."""
    pass


class EmbeddingServiceError(RuntimeError):
    """Raised when the Gemini embedding API call fails or returns an invalid vector."""
    pass


class GeminiEmbeddingService:
    """
    Service for generating 768-dimensional unit-normalized embeddings using
    the official google-genai SDK and gemini-embedding-001.

    - Product documents use task_type='RETRIEVAL_DOCUMENT'
    - User search queries use task_type='RETRIEVAL_QUERY'
    - Vectors are L2-normalized to unit length before storage/search.
    - Client is initialized lazily so importing modules never triggers network calls.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        dimensions: Optional[int] = None,
        client: Optional[object] = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name: str = model_name or settings.GEMINI_EMBEDDING_MODEL
        self.dimensions: int = dimensions or settings.GEMINI_EMBEDDING_DIMENSIONS
        self._client = client

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        key = (self._api_key or "").strip()
        if not key:
            raise EmbeddingConfigurationError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in backend/.env."
            )
        self._client = genai.Client(api_key=key)
        return self._client

    @staticmethod
    def normalize_vector(vector: List[float]) -> List[float]:
        """Normalize a vector to unit L2 norm for accurate cosine similarity."""
        norm = math.sqrt(sum(float(x) * float(x) for x in vector))
        if norm <= 0.0:
            raise EmbeddingServiceError("Cannot normalize a zero-magnitude embedding vector.")
        return [float(x) / norm for x in vector]

    def validate_and_normalize(self, raw_values: List[float]) -> List[float]:
        """Validate exact dimensionality (768) and L2-normalize the vector."""
        if not raw_values or len(raw_values) != self.dimensions:
            actual = len(raw_values) if raw_values else 0
            raise EmbeddingServiceError(
                f"Expected embedding dimension {self.dimensions}, but received {actual}."
            )
        return self.normalize_vector(raw_values)

    def _embed(self, text: str, task_type: str) -> List[float]:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("Cannot generate embedding for empty text.")

        client = self._get_client()
        try:
            response = client.models.embed_content(
                model=self.model_name,
                contents=cleaned,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimensions,
                ),
            )
        except Exception as exc:
            raise EmbeddingServiceError(
                f"Gemini embedding request failed ({type(exc).__name__})."
            ) from exc

        if not response or not getattr(response, "embeddings", None):
            raise EmbeddingServiceError("Gemini API returned an empty embeddings response.")

        raw_values = list(response.embeddings[0].values)
        return self.validate_and_normalize(raw_values)

    def embed_document(self, document_text: str) -> List[float]:
        """Generate a 768-d unit-normalized embedding for a product document (RETRIEVAL_DOCUMENT)."""
        return self._embed(document_text, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, query_text: str) -> List[float]:
        """Generate a 768-d unit-normalized embedding for a user search query (RETRIEVAL_QUERY)."""
        return self._embed(query_text, task_type="RETRIEVAL_QUERY")

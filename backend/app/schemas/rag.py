from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RAGQueryRequest(BaseModel):
    """Request schema for POST /api/v1/rag/query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural-language fashion search query",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of matching products to retrieve",
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_non_empty_query(cls, v: str) -> str:
        if isinstance(v, str):
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Search query cannot be empty or whitespace only.")
            return trimmed
        return v


class RAGProductItem(BaseModel):
    """Product item returned inside RAGQueryResponse, read directly from PostgreSQL."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    category: str
    subcategory: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    currency: str
    color: Optional[str] = None
    sizes: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    is_available: bool
    source_website: str
    product_url: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    """Final structured response returned by the RAG pipeline."""

    query: str
    answer: str
    products: List[RAGProductItem] = Field(default_factory=list)
    total_results: int

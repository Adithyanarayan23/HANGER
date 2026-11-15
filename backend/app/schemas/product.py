from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(default=None, description="Product description")
    brand: str = Field(..., min_length=1, max_length=120, description="Brand name")
    category: str = Field(..., min_length=1, max_length=100, description="Main product category")
    subcategory: Optional[str] = Field(default=None, max_length=100, description="Optional subcategory")
    color: Optional[str] = Field(default=None, max_length=80, description="Product colour")
    price: Decimal = Field(..., ge=0, description="Current product price (non-negative)")
    original_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Original price before discount (non-negative)",
    )
    currency: str = Field(default="INR", min_length=1, max_length=10, description="Currency code")
    sizes: List[str] = Field(default_factory=list, description="Available sizes")
    image_urls: List[str] = Field(default_factory=list, description="Product image URLs")
    is_available: bool = Field(default=True, description="Whether the product is in stock")
    source_website: str = Field(..., min_length=1, max_length=100, description="Source store or website")
    source_product_id: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Original product identifier from the source website",
    )
    product_url: AnyHttpUrl = Field(..., description="Valid HTTP/HTTPS URL to the original product page")

    @field_validator("name", "brand", "category", "source_website", mode="before")
    @classmethod
    def validate_non_empty_trimmed(cls, v: str) -> str:
        if isinstance(v, str):
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Field cannot be empty or whitespace only.")
            return trimmed
        return v

    @field_validator("source_product_id", mode="before")
    @classmethod
    def normalize_source_product_id(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for partial updates to an existing product (all fields optional)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=80)
    price: Optional[Decimal] = Field(default=None, ge=0)
    original_price: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=1, max_length=10)
    sizes: Optional[List[str]] = Field(default=None)
    image_urls: Optional[List[str]] = Field(default=None)
    is_available: Optional[bool] = Field(default=None)
    source_website: Optional[str] = Field(default=None, min_length=1, max_length=100)
    source_product_id: Optional[str] = Field(default=None, max_length=150)
    product_url: Optional[AnyHttpUrl] = Field(default=None)

    @field_validator("name", "brand", "category", "source_website", mode="before")
    @classmethod
    def validate_optional_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Field cannot be empty or whitespace only.")
            return trimmed
        return v

    @field_validator("source_product_id", mode="before")
    @classmethod
    def normalize_optional_source_id(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class ProductResponse(BaseModel):
    """Schema returned to clients, including database ID and timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    brand: str
    category: str
    subcategory: Optional[str] = None
    color: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    currency: str
    sizes: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    is_available: bool
    source_website: str
    source_product_id: Optional[str] = None
    product_url: str
    created_at: datetime
    updated_at: datetime

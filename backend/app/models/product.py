from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.product_embedding import ProductEmbedding


class Product(Base):
    """SQLAlchemy model representing a fashion product collected from partner stores."""

    __tablename__ = "products"

    # Product identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Product classification
    brand: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)

    # Pricing (Numeric(10, 2) avoids IEEE 754 floating-point rounding issues)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, index=True)
    original_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR", server_default="INR")

    # Product attributes (PostgreSQL native ARRAY of strings)
    sizes: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )
    image_urls: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default=text("'{}'::text[]"),
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    # Source information
    source_website: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_product_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    product_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    embedding_record: Mapped[Optional["ProductEmbedding"]] = relationship(
        "ProductEmbedding",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Enforce uniqueness on (source_website, source_product_id) only when source_product_id is NOT NULL
        Index(
            "uq_products_source_website_product_id",
            "source_website",
            "source_product_id",
            unique=True,
            postgresql_where=text("source_product_id IS NOT NULL"),
        ),
    )

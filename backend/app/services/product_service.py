from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_embedding import ProductEmbedding
from app.rag.document_builder import DocumentBuilder
from app.schemas.product import ProductCreate, ProductUpdate


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Retrieve a single product by its primary key ID."""
    return db.get(Product, product_id)


def get_product_by_source(
    db: Session,
    source_website: str,
    source_product_id: Optional[str],
) -> Optional[Product]:
    """Check if a product with the same (source_website, source_product_id) already exists."""
    if not source_product_id:
        return None
    stmt = select(Product).where(
        Product.source_website == source_website,
        Product.source_product_id == source_product_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def is_product_embedding_stale(db: Session, product: Product) -> bool:
    """
    Check whether a product lacks an embedding or its current semantic document
    content_hash differs from the stored ProductEmbedding.content_hash.
    Does not call external APIs synchronously during CRUD operations.
    """
    stmt = select(ProductEmbedding).where(ProductEmbedding.product_id == product.id)
    emb = db.execute(stmt).scalar_one_or_none()
    if emb is None:
        return True
    _, current_hash = DocumentBuilder.build_document_with_hash(product)
    return emb.content_hash != current_hash


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Create and persist a new product in PostgreSQL, guarding against duplicate source IDs."""
    if product_in.source_product_id:
        existing = get_product_by_source(
            db,
            source_website=product_in.source_website,
            source_product_id=product_in.source_product_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Product from '{product_in.source_website}' with source_product_id "
                    f"'{product_in.source_product_id}' already exists (id={existing.id})."
                ),
            )

    payload = product_in.model_dump()
    payload["product_url"] = str(product_in.product_url)

    db_product = Product(**payload)
    db.add(db_product)
    try:
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate source product record violates uniqueness constraint.",
        ) from exc


def get_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    color: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Product]:
    """Retrieve and filter products with search, attribute filters, price range, and pagination."""
    stmt = select(Product)

    if search and search.strip():
        stmt = stmt.where(Product.name.ilike(f"%{search.strip()}%"))

    if category and category.strip():
        stmt = stmt.where(Product.category.ilike(category.strip()))

    if brand and brand.strip():
        stmt = stmt.where(Product.brand.ilike(brand.strip()))

    if color and color.strip():
        stmt = stmt.where(Product.color.ilike(color.strip()))

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    stmt = stmt.order_by(Product.id.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_product(
    db: Session,
    product_id: int,
    product_in: ProductUpdate,
) -> Product:
    """Partially update an existing product by ID."""
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )

    update_data = product_in.model_dump(exclude_unset=True)
    if "product_url" in update_data and update_data["product_url"] is not None:
        update_data["product_url"] = str(update_data["product_url"])

    # Check if updating source_website or source_product_id would collide with another record
    new_website = update_data.get("source_website", db_product.source_website)
    new_source_id = update_data.get("source_product_id", db_product.source_product_id)
    if new_source_id:
        conflict = get_product_by_source(db, new_website, new_source_id)
        if conflict and conflict.id != db_product.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Another product from '{new_website}' with source_product_id "
                    f"'{new_source_id}' already exists (id={conflict.id})."
                ),
            )

    for field, value in update_data.items():
        setattr(db_product, field, value)

    try:
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update violates duplicate source product uniqueness constraint.",
        ) from exc


def delete_product(db: Session, product_id: int) -> dict:
    """Delete an existing product by ID."""
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )

    db.delete(db_product)
    db.commit()
    return {
        "message": f"Product with id {product_id} deleted successfully.",
        "deleted_id": product_id,
    }


def upsert_scraped_product(
    db: Session,
    product_in: ProductCreate,
) -> Tuple[Product, str]:
    """
    Idempotent product ingestion for the scraping pipeline.
    Returns (Product, status_label) where status_label is:
      - 'inserted' if a new product record was created
      - 'updated'  if an existing record had non-empty changes applied
      - 'skipped'  if an existing record already matched all non-empty scraped fields

    Rule: Never overwrite valid existing database values with None or empty scraped lists.
    """
    existing: Optional[Product] = None

    if product_in.source_product_id:
        existing = get_product_by_source(
            db,
            source_website=product_in.source_website,
            source_product_id=product_in.source_product_id,
        )
    else:
        stmt = select(Product).where(
            Product.source_website == product_in.source_website,
            Product.product_url == str(product_in.product_url),
        )
        existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        created = create_product(db=db, product_in=product_in)
        return created, "inserted"

    incoming = product_in.model_dump()
    incoming["product_url"] = str(product_in.product_url)

    changed = False
    for field, new_val in incoming.items():
        if new_val is None:
            continue
        if isinstance(new_val, str) and not new_val.strip():
            continue
        if isinstance(new_val, list) and len(new_val) == 0:
            continue

        current_val = getattr(existing, field)
        if current_val != new_val:
            setattr(existing, field, new_val)
            changed = True

    if not changed:
        return existing, "skipped"

    try:
        db.commit()
        db.refresh(existing)
        return existing, "updated"
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scraped product update violated uniqueness constraint.",
        ) from exc

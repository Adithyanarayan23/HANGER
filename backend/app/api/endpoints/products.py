from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
):
    """Store a new fashion product in PostgreSQL."""
    return product_service.create_product(db=db, product_in=product_in)


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="Get and filter products",
)
def read_products(
    search: Optional[str] = Query(default=None, description="Search product names"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    color: Optional[str] = Query(default=None, description="Filter by colour"),
    min_price: Optional[Decimal] = Query(default=None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(default=None, ge=0, description="Maximum price"),
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    """Retrieve a list of products with optional search, filtering, and pagination."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price.",
        )

    return product_service.get_products(
        db=db,
        search=search,
        category=category,
        brand=brand,
        color=color,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a specific product by its primary key ID."""
    product = product_service.get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    return product


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Partially update a product",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Apply partial updates to an existing product."""
    return product_service.update_product(
        db=db,
        product_id=product_id,
        product_in=product_in,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Delete an existing product by ID."""
    return product_service.delete_product(db=db, product_id=product_id)

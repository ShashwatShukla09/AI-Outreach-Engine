from fastapi import APIRouter, HTTPException, status

from app.schemas.product import (
    ProductCreate,
    ProductResponse,
)
from app.services.product_service import (
    create_new_product,
    find_product,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(product: ProductCreate):
    return create_new_product(product)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product_endpoint(product_id: int):
    product = find_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product

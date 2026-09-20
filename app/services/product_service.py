from typing import Optional

from app.repositories.product_repository import (
    create_product,
    get_product,
)
from app.schemas.product import ProductCreate


def create_new_product(product: ProductCreate) -> dict:
    """
    Create a new product after normalising basic text input.
    """

    name = product.name.strip()
    description = product.description.strip()

    value_proposition = (
        product.value_proposition.strip()
        if product.value_proposition
        else None
    )

    target_problem = (
        product.target_problem.strip()
        if product.target_problem
        else None
    )

    return create_product(
        name=name,
        description=description,
        value_proposition=value_proposition,
        target_problem=target_problem,
    )


def find_product(product_id: int) -> Optional[dict]:
    return get_product(product_id)

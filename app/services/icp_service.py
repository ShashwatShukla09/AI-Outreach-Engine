from typing import List

from app.providers.llm.base import ICPProvider
from app.repositories.icp_repository import (
    create_icp,
    get_icp,
    get_icps_for_product,
    update_icp,
    update_icp_status,
)
from app.schemas.icp import (
    ICPResponse,
    ICPUpdate,
)
from app.schemas.product import ProductResponse
from app.services.product_service import find_product


def generate_and_save_icps(
    product_id: int,
    provider: ICPProvider,
) -> List[ICPResponse]:
    product_data = find_product(product_id)

    if product_data is None:
        raise ValueError("Product not found")

    product = ProductResponse(**product_data)

    generation_result = provider.generate_icps(
        product
    )

    saved_icps = []

    for icp in generation_result.icps:
        saved = create_icp(
            product_id=product_id,
            icp=icp,
        )

        saved_icps.append(
            ICPResponse(**saved)
        )

    return saved_icps


def get_saved_icps(
    product_id: int,
) -> List[ICPResponse]:
    rows = get_icps_for_product(product_id)

    return [
        ICPResponse(**row)
        for row in rows
    ]


def edit_icp(
    icp_id: int,
    update: ICPUpdate,
) -> ICPResponse:
    existing = get_icp(icp_id)

    if existing is None:
        raise ValueError("ICP not found")

    if existing["status"] != "DRAFT":
        raise ValueError(
            "Only DRAFT ICPs can be edited."
        )

    updates = update.model_dump(
        exclude_unset=True
    )

    updated = update_icp(
        icp_id=icp_id,
        updates=updates,
    )

    return ICPResponse(**updated)


def approve_icp(
    icp_id: int,
) -> ICPResponse:
    existing = get_icp(icp_id)

    if existing is None:
        raise ValueError("ICP not found")

    if existing["status"] != "DRAFT":
        raise ValueError(
            "Only DRAFT ICPs can be approved."
        )

    updated = update_icp_status(
        icp_id=icp_id,
        status="APPROVED",
    )

    return ICPResponse(**updated)


def reject_icp(
    icp_id: int,
) -> ICPResponse:
    existing = get_icp(icp_id)

    if existing is None:
        raise ValueError("ICP not found")

    if existing["status"] != "DRAFT":
        raise ValueError(
            "Only DRAFT ICPs can be rejected."
        )

    updated = update_icp_status(
        icp_id=icp_id,
        status="REJECTED",
    )

    return ICPResponse(**updated)

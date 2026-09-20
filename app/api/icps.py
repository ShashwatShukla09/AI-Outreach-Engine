from typing import List

from fastapi import APIRouter, HTTPException, status

from app.providers.llm.ollama_provider import OllamaICPProvider
from app.schemas.icp import (
    ICPResponse,
    ICPUpdate,
)
from app.services.icp_service import (
    approve_icp,
    edit_icp,
    generate_and_save_icps,
    get_saved_icps,
    reject_icp,
)
from app.services.product_service import find_product


router = APIRouter(
    tags=["ICP Intelligence"],
)


@router.post(
    "/products/{product_id}/generate-icps",
    response_model=List[ICPResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_icps_endpoint(product_id: int):
    if find_product(product_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    provider = OllamaICPProvider()

    try:
        return generate_and_save_icps(
            product_id=product_id,
            provider=provider,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ICP generation provider is unavailable.",
        ) from exc


@router.get(
    "/products/{product_id}/icps",
    response_model=List[ICPResponse],
)
def get_icps_endpoint(product_id: int):
    if find_product(product_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return get_saved_icps(product_id)


@router.patch(
    "/icps/{icp_id}",
    response_model=ICPResponse,
)
def edit_icp_endpoint(
    icp_id: int,
    update: ICPUpdate,
):
    try:
        return edit_icp(
            icp_id=icp_id,
            update=update,
        )

    except ValueError as exc:
        message = str(exc)

        if message == "ICP not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc


@router.patch(
    "/icps/{icp_id}/approve",
    response_model=ICPResponse,
)
def approve_icp_endpoint(icp_id: int):
    try:
        return approve_icp(icp_id)

    except ValueError as exc:
        message = str(exc)

        if message == "ICP not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc


@router.patch(
    "/icps/{icp_id}/reject",
    response_model=ICPResponse,
)
def reject_icp_endpoint(icp_id: int):
    try:
        return reject_icp(icp_id)

    except ValueError as exc:
        message = str(exc)

        if message == "ICP not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.campaign import (
    CampaignCompanyAdd,
    CampaignCreate,
    CampaignResponse,
    CampaignStatusUpdate,
)
from app.services.campaign_service import (
    add_company,
    change_campaign_status,
    create_new_campaign,
    find_campaign,
    get_all_campaigns,
    list_campaign_companies,
    remove_company,
)


router = APIRouter(
    prefix="/api/campaigns",
    tags=["Campaigns"],
)


def _raise_campaign_error(
    exc: ValueError,
) -> None:
    message = str(exc)

    not_found_messages = {
        "Product not found",
        "ICP not found",
        "Campaign not found",
        "Company not found",
    }

    if message in not_found_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
    ) from exc


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign_endpoint(
    campaign: CampaignCreate,
):
    try:
        return create_new_campaign(
            product_id=campaign.product_id,
            icp_id=campaign.icp_id,
            name=campaign.name,
            market=campaign.market,
        )

    except ValueError as exc:
        _raise_campaign_error(exc)


@router.get(
    "",
    response_model=List[CampaignResponse],
)
def list_campaigns_endpoint():
    return get_all_campaigns()


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
def get_campaign_endpoint(
    campaign_id: int,
):
    try:
        return find_campaign(campaign_id)

    except ValueError as exc:
        _raise_campaign_error(exc)


@router.patch(
    "/{campaign_id}/status",
    response_model=CampaignResponse,
)
def update_campaign_status_endpoint(
    campaign_id: int,
    update: CampaignStatusUpdate,
):
    try:
        return change_campaign_status(
            campaign_id=campaign_id,
            new_status=update.status,
        )

    except ValueError as exc:
        _raise_campaign_error(exc)


@router.post(
    "/{campaign_id}/companies",
    status_code=status.HTTP_201_CREATED,
)
def add_campaign_company_endpoint(
    campaign_id: int,
    payload: CampaignCompanyAdd,
):
    try:
        return add_company(
            campaign_id=campaign_id,
            company_id=payload.company_id,
        )

    except ValueError as exc:
        _raise_campaign_error(exc)


@router.get(
    "/{campaign_id}/companies",
)
def list_campaign_companies_endpoint(
    campaign_id: int,
):
    try:
        return list_campaign_companies(
            campaign_id
        )

    except ValueError as exc:
        _raise_campaign_error(exc)


@router.delete(
    "/{campaign_id}/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_campaign_company_endpoint(
    campaign_id: int,
    company_id: int,
):
    try:
        remove_company(
            campaign_id=campaign_id,
            company_id=company_id,
        )

    except ValueError as exc:
        _raise_campaign_error(exc)

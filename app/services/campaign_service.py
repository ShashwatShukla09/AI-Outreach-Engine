import sqlite3
from typing import List, Optional

from app.repositories.campaign_repository import (
    add_company_to_campaign,
    create_campaign,
    get_campaign,
    get_campaign_companies,
    list_campaigns,
    remove_company_from_campaign,
    update_campaign_status,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.icp_repository import get_icp
from app.repositories.product_repository import get_product


ALLOWED_CAMPAIGN_TRANSITIONS = {
    "DRAFT": {"ACTIVE"},
    "ACTIVE": {"PAUSED", "COMPLETED"},
    "PAUSED": {"ACTIVE", "COMPLETED"},
    "COMPLETED": set(),
}


def create_new_campaign(
    product_id: int,
    icp_id: int,
    name: str,
    market: Optional[str] = None,
) -> dict:
    product = get_product(product_id)

    if product is None:
        raise ValueError("Product not found")

    icp = get_icp(icp_id)

    if icp is None:
        raise ValueError("ICP not found")

    if icp["product_id"] != product_id:
        raise ValueError(
            "ICP does not belong to this product."
        )

    if icp["status"] != "APPROVED":
        raise ValueError(
            "Campaigns require an APPROVED ICP."
        )

    clean_name = name.strip()

    if not clean_name:
        raise ValueError(
            "Campaign name cannot be blank."
        )

    resolved_market = (
        market.strip()
        if market and market.strip()
        else icp["target_market"]
    )

    return create_campaign(
        product_id=product_id,
        icp_id=icp_id,
        name=clean_name,
        market=resolved_market,
    )


def find_campaign(
    campaign_id: int,
) -> dict:
    campaign = get_campaign(campaign_id)

    if campaign is None:
        raise ValueError("Campaign not found")

    return campaign


def get_all_campaigns() -> List[dict]:
    return list_campaigns()


def change_campaign_status(
    campaign_id: int,
    new_status: str,
) -> dict:
    campaign = find_campaign(campaign_id)

    normalized_status = new_status.strip().upper()

    allowed = ALLOWED_CAMPAIGN_TRANSITIONS.get(
        campaign["status"],
        set(),
    )

    if normalized_status not in allowed:
        raise ValueError(
            "Invalid campaign status transition: "
            f"{campaign['status']} -> "
            f"{normalized_status}."
        )

    updated = update_campaign_status(
        campaign_id,
        normalized_status,
    )

    if updated is None:
        raise ValueError("Campaign not found")

    return updated


def add_company(
    campaign_id: int,
    company_id: int,
) -> dict:
    campaign = find_campaign(campaign_id)

    if campaign["status"] == "COMPLETED":
        raise ValueError(
            "Cannot modify a COMPLETED campaign."
        )

    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    if company["icp_id"] != campaign["icp_id"]:
        raise ValueError(
            "Company does not belong to "
            "the campaign ICP."
        )

    try:
        add_company_to_campaign(
            campaign_id,
            company_id,
        )

    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "Company is already in this campaign."
        ) from exc

    return company


def remove_company(
    campaign_id: int,
    company_id: int,
) -> None:
    campaign = find_campaign(campaign_id)

    if campaign["status"] == "COMPLETED":
        raise ValueError(
            "Cannot modify a COMPLETED campaign."
        )

    removed = remove_company_from_campaign(
        campaign_id,
        company_id,
    )

    if not removed:
        raise ValueError(
            "Company is not in this campaign."
        )


def list_campaign_companies(
    campaign_id: int,
) -> List[dict]:
    find_campaign(campaign_id)

    return get_campaign_companies(
        campaign_id
    )

import sqlite3

import pytest

from app.db.database import get_connection
from app.repositories.campaign_repository import (
    add_company_to_campaign,
    create_campaign,
    get_campaign,
    get_campaign_companies,
    list_campaigns,
    remove_company_from_campaign,
    update_campaign_status,
)


def _create_foundation():
    connection = get_connection()

    try:
        product_cursor = connection.execute(
            """
            INSERT INTO products (
                name,
                description
            )
            VALUES (?, ?)
            """,
            (
                "Repository Test Product",
                "Campaign repository test product",
            ),
        )
        product_id = product_cursor.lastrowid

        icp_cursor = connection.execute(
            """
            INSERT INTO icps (
                product_id,
                name,
                target_market,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                product_id,
                "Repository Test ICP",
                "India",
                "APPROVED",
            ),
        )
        icp_id = icp_cursor.lastrowid

        company_cursor = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain
            )
            VALUES (?, ?, ?)
            """,
            (
                icp_id,
                "Repository Test Company",
                "repository-test.example",
            ),
        )
        company_id = company_cursor.lastrowid

        connection.commit()

        return product_id, icp_id, company_id

    finally:
        connection.close()


def test_create_and_get_campaign():
    product_id, icp_id, _ = _create_foundation()

    campaign = create_campaign(
        product_id=product_id,
        icp_id=icp_id,
        name="India Operations",
        market="India",
    )

    assert campaign["name"] == "India Operations"
    assert campaign["product_id"] == product_id
    assert campaign["icp_id"] == icp_id
    assert campaign["market"] == "India"
    assert campaign["status"] == "DRAFT"

    loaded = get_campaign(campaign["id"])

    assert loaded == campaign


def test_get_missing_campaign_returns_none():
    assert get_campaign(999999) is None


def test_list_campaigns_returns_newest_first():
    product_id, icp_id, _ = _create_foundation()

    first = create_campaign(
        product_id,
        icp_id,
        "First Campaign",
        "India",
    )

    second = create_campaign(
        product_id,
        icp_id,
        "Second Campaign",
        "India",
    )

    campaigns = list_campaigns()

    ids = [
        campaign["id"]
        for campaign in campaigns
    ]

    assert ids.index(second["id"]) < ids.index(first["id"])


def test_update_campaign_status():
    product_id, icp_id, _ = _create_foundation()

    campaign = create_campaign(
        product_id,
        icp_id,
        "Lifecycle Campaign",
        "India",
    )

    updated = update_campaign_status(
        campaign["id"],
        "ACTIVE",
    )

    assert updated is not None
    assert updated["status"] == "ACTIVE"


def test_update_missing_campaign_returns_none():
    assert (
        update_campaign_status(
            999999,
            "ACTIVE",
        )
        is None
    )


def test_add_and_list_campaign_company():
    product_id, icp_id, company_id = (
        _create_foundation()
    )

    campaign = create_campaign(
        product_id,
        icp_id,
        "Membership Campaign",
        "India",
    )

    add_company_to_campaign(
        campaign["id"],
        company_id,
    )

    companies = get_campaign_companies(
        campaign["id"]
    )

    assert len(companies) == 1
    assert companies[0]["id"] == company_id
    assert (
        companies[0]["name"]
        == "Repository Test Company"
    )
    assert companies[0]["campaign_added_at"]


def test_duplicate_campaign_company_is_rejected():
    product_id, icp_id, company_id = (
        _create_foundation()
    )

    campaign = create_campaign(
        product_id,
        icp_id,
        "Duplicate Campaign",
        "India",
    )

    add_company_to_campaign(
        campaign["id"],
        company_id,
    )

    with pytest.raises(sqlite3.IntegrityError):
        add_company_to_campaign(
            campaign["id"],
            company_id,
        )


def test_remove_campaign_company():
    product_id, icp_id, company_id = (
        _create_foundation()
    )

    campaign = create_campaign(
        product_id,
        icp_id,
        "Removal Campaign",
        "India",
    )

    add_company_to_campaign(
        campaign["id"],
        company_id,
    )

    removed = remove_company_from_campaign(
        campaign["id"],
        company_id,
    )

    assert removed is True

    assert (
        get_campaign_companies(
            campaign["id"]
        )
        == []
    )

    removed_again = remove_company_from_campaign(
        campaign["id"],
        company_id,
    )

    assert removed_again is False

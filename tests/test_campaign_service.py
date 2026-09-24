import pytest

from app.db.database import get_connection
from app.repositories.campaign_repository import (
    get_campaign_companies,
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


def _create_product(
    name: str = "Campaign Service Product",
) -> int:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO products (
                name,
                description
            )
            VALUES (?, ?)
            """,
            (
                name,
                "Campaign service test product",
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def _create_icp(
    product_id: int,
    status: str = "APPROVED",
    market: str = "India",
) -> int:
    connection = get_connection()

    try:
        cursor = connection.execute(
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
                "Campaign Service ICP",
                market,
                status,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def _create_company(
    icp_id: int,
    name: str = "Campaign Service Company",
) -> int:
    connection = get_connection()

    try:
        cursor = connection.execute(
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
                name,
                f"{name.lower().replace(' ', '-')}.example",
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def _create_valid_campaign():
    product_id = _create_product()
    icp_id = _create_icp(product_id)

    campaign = create_new_campaign(
        product_id=product_id,
        icp_id=icp_id,
        name="India Operations",
    )

    return product_id, icp_id, campaign


def test_create_campaign_from_approved_icp():
    product_id = _create_product()
    icp_id = _create_icp(
        product_id,
        market="India",
    )

    campaign = create_new_campaign(
        product_id=product_id,
        icp_id=icp_id,
        name="  India Logistics  ",
    )

    assert campaign["product_id"] == product_id
    assert campaign["icp_id"] == icp_id
    assert campaign["name"] == "India Logistics"
    assert campaign["market"] == "India"
    assert campaign["status"] == "DRAFT"


def test_campaign_requires_existing_product():
    with pytest.raises(
        ValueError,
        match="Product not found",
    ):
        create_new_campaign(
            product_id=999999,
            icp_id=999999,
            name="Missing Product",
        )


def test_campaign_requires_existing_icp():
    product_id = _create_product()

    with pytest.raises(
        ValueError,
        match="ICP not found",
    ):
        create_new_campaign(
            product_id=product_id,
            icp_id=999999,
            name="Missing ICP",
        )


def test_campaign_rejects_icp_from_other_product():
    product_a = _create_product("Product A")
    product_b = _create_product("Product B")

    icp_id = _create_icp(product_b)

    with pytest.raises(
        ValueError,
        match="ICP does not belong",
    ):
        create_new_campaign(
            product_id=product_a,
            icp_id=icp_id,
            name="Wrong Product",
        )


def test_campaign_requires_approved_icp():
    product_id = _create_product()
    icp_id = _create_icp(
        product_id,
        status="DRAFT",
    )

    with pytest.raises(
        ValueError,
        match="APPROVED ICP",
    ):
        create_new_campaign(
            product_id=product_id,
            icp_id=icp_id,
            name="Draft ICP Campaign",
        )


def test_campaign_name_cannot_be_blank():
    product_id = _create_product()
    icp_id = _create_icp(product_id)

    with pytest.raises(
        ValueError,
        match="cannot be blank",
    ):
        create_new_campaign(
            product_id=product_id,
            icp_id=icp_id,
            name="   ",
        )


def test_find_and_list_campaigns():
    _, _, campaign = _create_valid_campaign()

    found = find_campaign(campaign["id"])

    assert found["id"] == campaign["id"]

    campaigns = get_all_campaigns()

    assert campaign["id"] in [
        item["id"]
        for item in campaigns
    ]


def test_missing_campaign_is_rejected():
    with pytest.raises(
        ValueError,
        match="Campaign not found",
    ):
        find_campaign(999999)


def test_valid_campaign_lifecycle():
    _, _, campaign = _create_valid_campaign()

    active = change_campaign_status(
        campaign["id"],
        "active",
    )

    assert active["status"] == "ACTIVE"

    paused = change_campaign_status(
        campaign["id"],
        "PAUSED",
    )

    assert paused["status"] == "PAUSED"

    active_again = change_campaign_status(
        campaign["id"],
        "ACTIVE",
    )

    assert active_again["status"] == "ACTIVE"

    completed = change_campaign_status(
        campaign["id"],
        "COMPLETED",
    )

    assert completed["status"] == "COMPLETED"


def test_invalid_campaign_transition_is_rejected():
    _, _, campaign = _create_valid_campaign()

    with pytest.raises(
        ValueError,
        match="Invalid campaign status transition",
    ):
        change_campaign_status(
            campaign["id"],
            "COMPLETED",
        )


def test_completed_campaign_cannot_reopen():
    _, _, campaign = _create_valid_campaign()

    change_campaign_status(
        campaign["id"],
        "ACTIVE",
    )

    change_campaign_status(
        campaign["id"],
        "COMPLETED",
    )

    with pytest.raises(
        ValueError,
        match="Invalid campaign status transition",
    ):
        change_campaign_status(
            campaign["id"],
            "ACTIVE",
        )


def test_company_can_be_added_to_matching_campaign():
    _, icp_id, campaign = _create_valid_campaign()

    company_id = _create_company(icp_id)

    company = add_company(
        campaign["id"],
        company_id,
    )

    assert company["id"] == company_id

    companies = list_campaign_companies(
        campaign["id"]
    )

    assert len(companies) == 1
    assert companies[0]["id"] == company_id


def test_company_from_different_icp_is_rejected():
    _, _, campaign = _create_valid_campaign()

    other_product = _create_product(
        "Other Product"
    )
    other_icp = _create_icp(other_product)
    company_id = _create_company(
        other_icp,
        "Wrong ICP Company",
    )

    with pytest.raises(
        ValueError,
        match="does not belong",
    ):
        add_company(
            campaign["id"],
            company_id,
        )


def test_duplicate_company_membership_is_rejected():
    _, icp_id, campaign = _create_valid_campaign()

    company_id = _create_company(icp_id)

    add_company(
        campaign["id"],
        company_id,
    )

    with pytest.raises(
        ValueError,
        match="already in this campaign",
    ):
        add_company(
            campaign["id"],
            company_id,
        )


def test_company_can_be_removed():
    _, icp_id, campaign = _create_valid_campaign()

    company_id = _create_company(icp_id)

    add_company(
        campaign["id"],
        company_id,
    )

    remove_company(
        campaign["id"],
        company_id,
    )

    assert get_campaign_companies(
        campaign["id"]
    ) == []


def test_removing_non_member_is_rejected():
    _, icp_id, campaign = _create_valid_campaign()

    company_id = _create_company(icp_id)

    with pytest.raises(
        ValueError,
        match="not in this campaign",
    ):
        remove_company(
            campaign["id"],
            company_id,
        )


def test_completed_campaign_membership_is_frozen():
    _, icp_id, campaign = _create_valid_campaign()

    existing_company = _create_company(
        icp_id,
        "Existing Company",
    )

    new_company = _create_company(
        icp_id,
        "New Company",
    )

    add_company(
        campaign["id"],
        existing_company,
    )

    change_campaign_status(
        campaign["id"],
        "ACTIVE",
    )

    change_campaign_status(
        campaign["id"],
        "COMPLETED",
    )

    with pytest.raises(
        ValueError,
        match="COMPLETED",
    ):
        add_company(
            campaign["id"],
            new_company,
        )

    with pytest.raises(
        ValueError,
        match="COMPLETED",
    ):
        remove_company(
            campaign["id"],
            existing_company,
        )

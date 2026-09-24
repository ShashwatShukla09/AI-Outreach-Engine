from fastapi.testclient import TestClient

from app.db.database import get_connection
from app.main import app


client = TestClient(app)


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
                "Campaign API Product",
                "Campaign API test product",
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
                "Campaign API ICP",
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
                "Campaign API Company",
                "campaign-api.example",
            ),
        )
        company_id = company_cursor.lastrowid

        connection.commit()

        return product_id, icp_id, company_id

    finally:
        connection.close()


def _create_campaign():
    product_id, icp_id, company_id = (
        _create_foundation()
    )

    response = client.post(
        "/api/campaigns",
        json={
            "product_id": product_id,
            "icp_id": icp_id,
            "name": "India Operations",
            "market": "India",
        },
    )

    assert response.status_code == 201

    return (
        response.json(),
        company_id,
    )


def test_create_campaign_api():
    product_id, icp_id, _ = _create_foundation()

    response = client.post(
        "/api/campaigns",
        json={
            "product_id": product_id,
            "icp_id": icp_id,
            "name": "India Logistics",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product_id
    assert data["icp_id"] == icp_id
    assert data["name"] == "India Logistics"
    assert data["market"] == "India"
    assert data["status"] == "DRAFT"


def test_list_and_get_campaign_api():
    campaign, _ = _create_campaign()

    list_response = client.get(
        "/api/campaigns"
    )

    assert list_response.status_code == 200

    ids = [
        item["id"]
        for item in list_response.json()
    ]

    assert campaign["id"] in ids

    get_response = client.get(
        f"/api/campaigns/{campaign['id']}"
    )

    assert get_response.status_code == 200
    assert (
        get_response.json()["id"]
        == campaign["id"]
    )


def test_missing_campaign_returns_404():
    response = client.get(
        "/api/campaigns/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Campaign not found"
    }


def test_invalid_campaign_creation_returns_409():
    product_id, _, _ = _create_foundation()

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
                "Draft API ICP",
                "India",
                "DRAFT",
            ),
        )

        draft_icp_id = cursor.lastrowid
        connection.commit()

    finally:
        connection.close()

    response = client.post(
        "/api/campaigns",
        json={
            "product_id": product_id,
            "icp_id": draft_icp_id,
            "name": "Invalid Campaign",
        },
    )

    assert response.status_code == 409
    assert "APPROVED ICP" in response.json()["detail"]


def test_campaign_status_api():
    campaign, _ = _create_campaign()

    response = client.patch(
        f"/api/campaigns/{campaign['id']}/status",
        json={
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"


def test_invalid_status_transition_returns_409():
    campaign, _ = _create_campaign()

    response = client.patch(
        f"/api/campaigns/{campaign['id']}/status",
        json={
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 409
    assert (
        "Invalid campaign status transition"
        in response.json()["detail"]
    )


def test_add_list_and_remove_company_api():
    campaign, company_id = _create_campaign()

    add_response = client.post(
        f"/api/campaigns/{campaign['id']}/companies",
        json={
            "company_id": company_id,
        },
    )

    assert add_response.status_code == 201
    assert add_response.json()["id"] == company_id

    list_response = client.get(
        f"/api/campaigns/{campaign['id']}/companies"
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert (
        list_response.json()[0]["id"]
        == company_id
    )

    delete_response = client.delete(
        (
            f"/api/campaigns/{campaign['id']}"
            f"/companies/{company_id}"
        )
    )

    assert delete_response.status_code == 204

    final_response = client.get(
        f"/api/campaigns/{campaign['id']}/companies"
    )

    assert final_response.status_code == 200
    assert final_response.json() == []


def test_duplicate_company_returns_409():
    campaign, company_id = _create_campaign()

    first = client.post(
        f"/api/campaigns/{campaign['id']}/companies",
        json={
            "company_id": company_id,
        },
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/campaigns/{campaign['id']}/companies",
        json={
            "company_id": company_id,
        },
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]
        == "Company is already in this campaign."
    )


def test_missing_company_returns_404():
    campaign, _ = _create_campaign()

    response = client.post(
        f"/api/campaigns/{campaign['id']}/companies",
        json={
            "company_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found"
    }

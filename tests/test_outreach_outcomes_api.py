from fastapi.testclient import TestClient

from app.db.database import get_connection
from app.main import app


client = TestClient(app)


def create_test_outreach(
    status: str = "SENT",
) -> int:
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
                "Outcome API Test Product",
                "Product used for outcome API tests.",
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
                "Outcome API Test ICP",
                "INDIA",
                "APPROVED",
            ),
        )

        icp_id = icp_cursor.lastrowid

        company_cursor = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain,
                country,
                qualification_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                icp_id,
                "Outcome API Test Company",
                f"outcome-api-{product_id}.example",
                "India",
                "QUALIFIED",
            ),
        )

        company_id = company_cursor.lastrowid

        outreach_cursor = connection.execute(
            """
            INSERT INTO outreach_messages (
                company_id,
                channel,
                message_body,
                status
            )
            VALUES (?, 'EMAIL', ?, ?)
            """,
            (
                company_id,
                "API outcome test message.",
                status,
            ),
        )

        outreach_id = outreach_cursor.lastrowid

        connection.commit()

        return outreach_id

    finally:
        connection.close()


def test_api_records_reply_for_sent_outreach():
    outreach_id = create_test_outreach("SENT")

    response = client.post(
        f"/api/outreach/{outreach_id}/outcomes",
        json={
            "outcome_type": "REPLIED",
            "notes": "Prospect replied.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["outreach_id"] == outreach_id
    assert data["outcome"]["outcome_type"] == "REPLIED"
    assert data["outcome"]["notes"] == "Prospect replied."


def test_api_rejects_outcome_for_draft():
    outreach_id = create_test_outreach("DRAFT")

    response = client.post(
        f"/api/outreach/{outreach_id}/outcomes",
        json={
            "outcome_type": "REPLIED",
        },
    )

    assert response.status_code == 409

    assert (
        "SENT outreach"
        in response.json()["detail"]
    )


def test_api_returns_404_for_missing_outreach():
    response = client.post(
        "/api/outreach/999999/outcomes",
        json={
            "outcome_type": "REPLIED",
        },
    )

    assert response.status_code == 404


def test_api_rejects_positive_before_reply():
    outreach_id = create_test_outreach("SENT")

    response = client.post(
        f"/api/outreach/{outreach_id}/outcomes",
        json={
            "outcome_type": "POSITIVE",
        },
    )

    assert response.status_code == 409

    assert (
        "requires REPLIED"
        in response.json()["detail"]
    )


def test_api_records_complete_positive_sequence():
    outreach_id = create_test_outreach("SENT")

    for outcome_type in [
        "REPLIED",
        "POSITIVE",
        "MEETING_BOOKED",
    ]:
        response = client.post(
            f"/api/outreach/{outreach_id}/outcomes",
            json={
                "outcome_type": outcome_type,
            },
        )

        assert response.status_code == 200

    response = client.get(
        f"/api/outreach/{outreach_id}/outcomes"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["outreach_id"] == outreach_id

    assert [
        outcome["outcome_type"]
        for outcome in data["outcomes"]
    ] == [
        "REPLIED",
        "POSITIVE",
        "MEETING_BOOKED",
    ]


def test_api_rejects_duplicate_outcome():
    outreach_id = create_test_outreach("SENT")

    first = client.post(
        f"/api/outreach/{outreach_id}/outcomes",
        json={
            "outcome_type": "REPLIED",
        },
    )

    assert first.status_code == 200

    duplicate = client.post(
        f"/api/outreach/{outreach_id}/outcomes",
        json={
            "outcome_type": "REPLIED",
        },
    )

    assert duplicate.status_code == 409

    assert (
        "already been recorded"
        in duplicate.json()["detail"]
    )


def test_api_get_returns_404_for_missing_outreach():
    response = client.get(
        "/api/outreach/999999/outcomes"
    )

    assert response.status_code == 404

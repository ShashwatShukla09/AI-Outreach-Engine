from fastapi.testclient import TestClient

from app.main import app
from app.providers.llm.mock_provider import (
    MockICPProvider,
)
from app.schemas.product import ProductCreate
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import (
    create_new_product,
)


client = TestClient(app)


def create_replenishment_icp(approve=True):
    product = create_new_product(
        ProductCreate(
            name="Replenishment API Product",
            description=(
                "AI software that helps customer support "
                "teams answer repetitive questions."
            ),
            value_proposition=(
                "Reduce repetitive support work."
            ),
            target_problem=(
                "Support teams spend too much time "
                "answering repeated questions."
            ),
        )
    )

    icps = generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )

    if approve:
        return approve_icp(icps[0].id)

    return icps[0]


def test_replenishment_api_processes_new_accounts():
    icp = create_replenishment_icp()

    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["icp_id"] == icp.id
    assert data["new_accounts"] == 4
    assert data["processed"] == 4

    assert data["qualified"] == 3
    assert data["disqualified"] == 1
    assert data["needs_review"] == 0

    assert data["enriched"] == 1

    assert len(data["processing"]["results"]) == 4
    assert len(data["relevance_results"]) == 3


def test_replenishment_api_is_idempotent_for_same_batch():
    icp = create_replenishment_icp()

    first = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    second = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert first.status_code == 200
    assert first.json()["new_accounts"] == 4

    assert second.status_code == 200

    data = second.json()

    assert data["new_accounts"] == 0
    assert data["processed"] == 0

    assert data["qualified"] == 0
    assert data["disqualified"] == 0
    assert data["needs_review"] == 0
    assert data["enriched"] == 0

    assert data["processing"]["results"] == []
    assert data["relevance_results"] == []


def test_replenishment_api_rejects_draft_icp():
    icp = create_replenishment_icp(
        approve=False
    )

    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert response.status_code == 409

    assert (
        "APPROVED ICP"
        in response.json()["detail"]
    )


def test_replenishment_api_returns_404_for_missing_icp():
    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": 999999999,
            "limit": 100,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "ICP not found"
    }

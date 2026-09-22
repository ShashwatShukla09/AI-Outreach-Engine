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


def create_approved_discovery_icp():
    product = create_new_product(
        ProductCreate(
            name="Discovery API Product",
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

    return approve_icp(icps[0].id)


def test_approved_icp_can_discover_companies_via_api():
    icp = create_approved_discovery_icp()

    response = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["discovered_count"] == 4
    assert len(data["companies"]) == 4

    assert all(
        company["icp_id"] == icp.id
        for company in data["companies"]
    )

    assert all(
        company["qualification_status"]
        == "UNREVIEWED"
        for company in data["companies"]
    )


def test_discovery_api_deduplicates_existing_companies():
    icp = create_approved_discovery_icp()

    first = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    second = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert first.status_code == 201
    assert first.json()["discovered_count"] == 4

    assert second.status_code == 201
    assert second.json()["discovered_count"] == 0
    assert second.json()["companies"] == []


def test_draft_icp_cannot_discover_via_api():
    product = create_new_product(
        ProductCreate(
            name="Draft Discovery Product",
            description=(
                "AI software for customer support teams."
            ),
            value_proposition=(
                "Reduce repetitive support work."
            ),
            target_problem=(
                "Support teams answer repeated questions."
            ),
        )
    )

    icps = generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )

    response = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icps[0].id,
            "limit": 100,
        },
    )

    assert response.status_code == 409

    assert (
        "APPROVED ICP"
        in response.json()["detail"]
    )


def test_missing_icp_returns_404():
    response = client.post(
        "/api/companies/discover",
        json={
            "icp_id": 999999999,
            "limit": 100,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "ICP not found"
    }


def test_discovery_api_processes_discovered_companies():
    icp = create_approved_discovery_icp()

    response = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["discovered_count"] == 4

    processing = data["processing"]

    assert processing["processed_count"] == 4
    assert processing["qualified_count"] == 3
    assert processing["disqualified_count"] == 1
    assert processing["enriched_count"] == 1

    statuses = {
        item["status"]
        for item in processing["results"]
    }

    assert statuses == {
        "QUALIFIED",
        "DISQUALIFIED",
    }


def test_discovery_api_returns_signal_aware_scores():
    icp = create_approved_discovery_icp()

    response = client.post(
        "/api/companies/discover",
        json={
            "icp_id": icp.id,
            "limit": 100,
        },
    )

    assert response.status_code == 201

    data = response.json()

    companies = {
        company["name"]: company
        for company in data["companies"]
    }

    results_by_id = {
        result["company_id"]: result
        for result in data["processing"]["results"]
    }

    nova = results_by_id[
        companies["NovaCart India"]["id"]
    ]

    urban = results_by_id[
        companies["UrbanBasket"]["id"]
    ]

    tiny = results_by_id[
        companies["TinyShop"]["id"]
    ]

    mystery = results_by_id[
        companies["MysteryCommerce"]["id"]
    ]

    assert nova["score"]["total_score"] == 80
    assert nova["score"]["intent_score"] == 20
    assert nova["score"]["priority"] == "HIGH"
    assert (
        nova["signal_processing"]["new_signal_count"]
        == 2
    )

    assert urban["score"]["total_score"] == 70
    assert urban["score"]["intent_score"] == 10
    assert urban["score"]["priority"] == "MEDIUM"

    assert tiny["status"] == "DISQUALIFIED"
    assert tiny["score"] is None

    assert mystery["status"] == "QUALIFIED"
    assert mystery["score"]["total_score"] == 60
    assert mystery["score"]["intent_score"] == 0

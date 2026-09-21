from fastapi.testclient import TestClient

from app.main import app
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.workflows.company_enrichment_workflow import (
    qualify_enrich_requalify,
)
from tests.test_enrichment_queue import (
    create_real_company,
)


client = TestClient(app)


def test_company_intelligence_returns_enrichment_history():
    company = create_real_company()

    result = qualify_enrich_requalify(
        company_id=company.id,
        provider=MockCompanyEnrichmentProvider(),
        provider_name="mock",
    )

    assert result["enriched"] is True

    response = client.get(
        f"/api/companies/{company.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company"]["id"] == company.id
    assert data["company"]["name"] == "MysteryCommerce"

    assert (
        data["company"]["employee_count"]
        == 90
    )

    assert (
        data["company"]["business_model"]
        == "Marketplace"
    )

    assert (
        data["company"]["qualification_status"]
        == "QUALIFIED"
    )

    enrichment_jobs = data["enrichment_jobs"]

    assert len(enrichment_jobs) == 2

    assert {
        job["enrichment_type"]
        for job in enrichment_jobs
    } == {
        "employee_count",
        "business_model",
    }

    assert all(
        job["provider"] == "mock"
        for job in enrichment_jobs
    )

    assert all(
        job["status"] == "COMPLETED"
        for job in enrichment_jobs
    )

    assert all(
        job["completed_at"] is not None
        for job in enrichment_jobs
    )


def test_company_without_enrichment_returns_empty_history():
    mystery = create_real_company()

    connection_company = get_company_by_id(
        mystery.id
    )

    assert connection_company is not None

    response = client.get(
        f"/api/companies/{mystery.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enrichment_jobs"] == []


def test_missing_company_returns_404():
    response = client.get(
        "/api/companies/999999999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Company not found"
    }

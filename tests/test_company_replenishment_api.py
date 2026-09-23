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


def test_replenishment_provider_selects_mock():
    from app.api.companies import (
        get_replenishment_discovery_provider,
    )
    from app.providers.discovery.mock_provider import (
        MockCompanyDiscoveryProvider,
    )

    provider = get_replenishment_discovery_provider(
        source="mock"
    )

    assert isinstance(
        provider,
        MockCompanyDiscoveryProvider,
    )


def test_replenishment_provider_selects_clay_csv(
    tmp_path,
):
    from app.api.companies import (
        get_replenishment_discovery_provider,
    )
    from app.providers.discovery.clay_csv_provider import (
        ClayCSVCompanyDiscoveryProvider,
    )

    csv_path = tmp_path / "companies.csv"

    provider = get_replenishment_discovery_provider(
        source="clay_csv",
        csv_path=str(csv_path),
    )

    assert isinstance(
        provider,
        ClayCSVCompanyDiscoveryProvider,
    )

    assert provider.csv_path == csv_path


def test_clay_csv_source_requires_path():
    from app.api.companies import (
        get_replenishment_discovery_provider,
    )

    try:
        get_replenishment_discovery_provider(
            source="clay_csv"
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "csv_path is required for clay_csv source."
        )
    else:
        raise AssertionError(
            "Expected missing csv_path to fail."
        )


def test_replenishment_provider_rejects_unknown_source():
    from app.api.companies import (
        get_replenishment_discovery_provider,
    )

    try:
        get_replenishment_discovery_provider(
            source="unknown"
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "Unsupported replenishment source: unknown"
        )
    else:
        raise AssertionError(
            "Expected unsupported source to fail."
        )


def test_replenishment_api_processes_clay_csv_source(
    tmp_path,
):
    icp = create_replenishment_icp()

    csv_path = tmp_path / "clay_companies.csv"

    csv_path.write_text(
        "\n".join(
            [
                (
                    "Name,Domain,Country,Industry,Size,"
                    "Description,LinkedIn URL"
                ),
                (
                    "Clay Prospect One,"
                    "https://clay-one.example.com,"
                    "India,E-commerce,100,"
                    "E-commerce company,"
                    "https://linkedin.com/company/clay-one"
                ),
                (
                    "Clay Prospect Two,"
                    "https://clay-two.example.com,"
                    "India,E-commerce,200,"
                    "E-commerce company,"
                    "https://linkedin.com/company/clay-two"
                ),
            ]
        ),
        encoding="utf-8",
    )

    payload = {
        "icp_id": icp.id,
        "limit": 100,
        "source": "clay_csv",
        "csv_path": str(csv_path),
    }

    first = client.post(
        "/api/companies/replenish",
        json=payload,
    )

    assert first.status_code == 200

    first_data = first.json()

    assert first_data["new_accounts"] == 2
    assert first_data["processed"] == 2

    second = client.post(
        "/api/companies/replenish",
        json=payload,
    )

    assert second.status_code == 200

    second_data = second.json()

    assert second_data["new_accounts"] == 0
    assert second_data["processed"] == 0


def test_replenishment_api_requires_clay_csv_path():
    icp = create_replenishment_icp()

    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "source": "clay_csv",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "csv_path is required for clay_csv source."
        )
    }


def test_replenishment_api_rejects_unknown_source():
    icp = create_replenishment_icp()

    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "source": "unknown",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Unsupported replenishment source: unknown"
        )
    }


def test_mock_replenishment_uses_mock_processing_providers():
    from app.api.companies import (
        get_replenishment_processing_providers,
    )
    from app.providers.enrichment.mock_provider import (
        MockCompanyEnrichmentProvider,
    )
    from app.providers.signals.mock_provider import (
        MockSignalProvider,
    )

    providers = get_replenishment_processing_providers(
        "mock"
    )

    assert isinstance(
        providers["enrichment_provider"],
        MockCompanyEnrichmentProvider,
    )
    assert (
        providers["enrichment_provider_name"]
        == "mock"
    )
    assert isinstance(
        providers["signal_provider"],
        MockSignalProvider,
    )


def test_clay_csv_replenishment_never_uses_mock_intelligence():
    from app.api.companies import (
        get_replenishment_processing_providers,
    )
    from app.providers.enrichment.noop_provider import (
        NoOpCompanyEnrichmentProvider,
    )

    providers = get_replenishment_processing_providers(
        "clay_csv"
    )

    assert isinstance(
        providers["enrichment_provider"],
        NoOpCompanyEnrichmentProvider,
    )
    assert (
        providers["enrichment_provider_name"]
        == "none"
    )
    assert providers["signal_provider"] is None


def test_processing_provider_policy_rejects_unknown_source():
    import pytest

    from app.api.companies import (
        get_replenishment_processing_providers,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported replenishment source: unknown",
    ):
        get_replenishment_processing_providers(
            "unknown"
        )


def test_clay_csv_http_replenishment_does_not_fabricate_data(
    tmp_path,
):
    import csv

    from app.repositories.company_repository import (
        find_company_by_domain,
    )
    from app.repositories.enrichment_repository import (
        get_company_enrichment_jobs,
    )
    from app.repositories.signal_repository import (
        get_company_signals,
    )

    icp = create_replenishment_icp()

    csv_path = tmp_path / "real_safe_clay.csv"

    fieldnames = [
        "Name",
        "Domain",
        "Country",
        "Industry",
        "Size",
        "Description",
        "LinkedIn URL",
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerow(
            {
                "Name": "Safe Real Prospect",
                "Domain": "safe-real-prospect.example.com",
                "Country": "India",
                "Industry": "E-commerce",
                "Size": "",
                "Description": (
                    "A real-source test prospect."
                ),
                "LinkedIn URL": "",
            }
        )

    response = client.post(
        "/api/companies/replenish",
        json={
            "icp_id": icp.id,
            "source": "clay_csv",
            "csv_path": str(csv_path),
            "limit": 100,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["new_accounts"] == 1
    assert data["processed"] == 1
    assert data["qualified"] == 0
    assert data["needs_review"] == 1
    assert data["enriched"] == 0

    company = find_company_by_domain(
        icp_id=icp.id,
        domain="safe-real-prospect.example.com",
    )

    assert company is not None
    assert company["employee_count"] is None
    assert (
        company["qualification_status"]
        == "NEEDS_REVIEW"
    )

    jobs = get_company_enrichment_jobs(
        company["id"]
    )

    assert len(jobs) >= 1

    employee_jobs = [
        job
        for job in jobs
        if job["enrichment_type"]
        == "employee_count"
    ]

    assert len(employee_jobs) == 1
    assert employee_jobs[0]["provider"] == "none"
    assert employee_jobs[0]["status"] == "PENDING"

    signals = get_company_signals(
        company["id"]
    )

    assert signals == []

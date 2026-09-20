from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.schemas.icp import ICPResponse


def make_india_icp():
    return ICPResponse(
        id=1,
        product_id=1,
        name="India E-commerce ICP",
        industries=["E-commerce"],
        company_size_min=50,
        company_size_max=500,
        target_market="INDIA",
        target_countries=["India"],
        business_models=["Direct-to-consumer"],
        buyer_categories=[
            "Customer Support Manager",
        ],
        pain_points=[
            "High repetitive support volume",
        ],
        segment_rationale=(
            "E-commerce companies handle significant "
            "customer support workloads."
        ),
        buyer_rationale=(
            "Support leaders own customer support "
            "operations and efficiency."
        ),
        assumptions=[],
        status="APPROVED",
        reviewed_at="2026-09-20 10:00:00",
        created_at="2026-09-20 09:00:00",
    )


def test_mock_provider_discovers_companies():
    provider = MockCompanyDiscoveryProvider()

    companies = provider.discover_companies(
        make_india_icp()
    )

    assert len(companies) == 4

    assert companies[0].name == "NovaCart India"

    assert all(
        company.source == "mock"
        for company in companies
    )


def test_mock_provider_respects_limit():
    provider = MockCompanyDiscoveryProvider()

    companies = provider.discover_companies(
        make_india_icp(),
        limit=2,
    )

    assert len(companies) == 2


def test_discovered_company_can_have_missing_data():
    from app.schemas.company import CompanyCandidate

    company = CompanyCandidate(
        name="Incomplete Company",
        country="India",
        source="manual",
    )

    assert company.domain is None
    assert company.employee_count is None
    assert company.business_model is None

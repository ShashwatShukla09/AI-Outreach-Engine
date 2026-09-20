import pytest

from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.product import ProductCreate
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import create_new_product


def create_test_icps():
    product = create_new_product(
        ProductCreate(
            name="Discovery Test Product",
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

    return generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )


def test_approved_icp_can_discover_companies():
    icps = create_test_icps()

    approved = approve_icp(
        icps[0].id
    )

    companies = discover_and_save_companies(
        icp_id=approved.id,
        provider=MockCompanyDiscoveryProvider(),
    )

    assert len(companies) == 4

    assert all(
        company.icp_id == approved.id
        for company in companies
    )

    assert all(
        company.qualification_status
        == "UNREVIEWED"
        for company in companies
    )


def test_draft_icp_cannot_discover_companies():
    icps = create_test_icps()

    with pytest.raises(
        ValueError,
        match=(
            "Company discovery requires "
            "an APPROVED ICP"
        ),
    ):
        discover_and_save_companies(
            icp_id=icps[0].id,
            provider=MockCompanyDiscoveryProvider(),
        )


def test_discovery_deduplicates_by_domain():
    icps = create_test_icps()

    approved = approve_icp(
        icps[0].id
    )

    provider = MockCompanyDiscoveryProvider()

    first_run = discover_and_save_companies(
        icp_id=approved.id,
        provider=provider,
    )

    second_run = discover_and_save_companies(
        icp_id=approved.id,
        provider=provider,
    )

    assert len(first_run) == 4
    assert len(second_run) == 0

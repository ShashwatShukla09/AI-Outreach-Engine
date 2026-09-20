from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.product import ProductCreate
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.company_qualification_service import (
    qualify_companies_for_icp,
)
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import create_new_product


def prepare_companies():
    product = create_new_product(
        ProductCreate(
            name="Qualification Test Product",
            description=(
                "AI software that helps support teams "
                "answer repetitive customer questions."
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

    approved = approve_icp(
        icps[0].id
    )

    companies = discover_and_save_companies(
        icp_id=approved.id,
        provider=MockCompanyDiscoveryProvider(),
    )

    return approved, companies


def test_company_qualification():
    approved, companies = prepare_companies()

    results = qualify_companies_for_icp(
        approved.id
    )

    statuses = {
        company.name: result.status
        for company, result in zip(
            companies,
            results,
        )
    }

    assert statuses["NovaCart India"] == "QUALIFIED"
    assert statuses["UrbanBasket"] == "QUALIFIED"

    assert (
        statuses["TinyShop"]
        == "DISQUALIFIED"
    )

    assert (
    statuses["MysteryCommerce"]
    == "NEEDS_REVIEW"
    )


def test_disqualified_company_has_reason():
    approved, companies = prepare_companies()

    results = qualify_companies_for_icp(
        approved.id
    )

    tinyshop_index = next(
        index
        for index, company in enumerate(companies)
        if company.name == "TinyShop"
    )

    result = results[tinyshop_index]

    assert result.status == "DISQUALIFIED"

    assert (
        "Company size is outside the ICP range."
        in result.reasons
    )

def test_incomplete_company_needs_review():
    approved, companies = prepare_companies()

    results = qualify_companies_for_icp(
        approved.id
    )

    mystery_index = next(
        index
        for index, company in enumerate(companies)
        if company.name == "MysteryCommerce"
    )

    result = results[mystery_index]

    assert result.status == "NEEDS_REVIEW"

    assert "employee_count" in result.missing_fields
    assert "business_model" in result.missing_fields
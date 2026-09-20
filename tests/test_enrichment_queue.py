from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.llm.mock_provider import MockICPProvider
from app.repositories.enrichment_repository import (
    get_pending_enrichment_jobs,
)
from app.schemas.product import ProductCreate
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.enrichment_service import (
    queue_missing_company_data,
)
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import create_new_product
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.services.enrichment_service import (
    enrich_company,
    queue_missing_company_data,
)


def create_real_company():
    product = create_new_product(
        ProductCreate(
            name="Enrichment Test Product",
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

    approved = approve_icp(icps[0].id)

    companies = discover_and_save_companies(
        icp_id=approved.id,
        provider=MockCompanyDiscoveryProvider(),
    )

    mystery = next(
        company
        for company in companies
        if company.name == "MysteryCommerce"
    )

    return mystery


def test_missing_fields_create_enrichment_jobs():
    company = create_real_company()

    jobs = queue_missing_company_data(
        company_id=company.id,
        missing_fields=[
            "employee_count",
            "business_model",
        ],
        provider="public",
    )

    assert len(jobs) == 2

    assert all(
        job["company_id"] == company.id
        for job in jobs
    )

    assert all(
        job["status"] == "PENDING"
        for job in jobs
    )

    assert all(
        job["provider"] == "public"
        for job in jobs
    )

    enrichment_types = {
        job["enrichment_type"]
        for job in jobs
    }

    assert enrichment_types == {
        "employee_count",
        "business_model",
    }


def test_qualification_automatically_queues_enrichment():
    company = create_real_company()

    result = qualify_company(company.id)

    assert result.status == "NEEDS_REVIEW"

    assert set(result.missing_fields) == {
        "employee_count",
        "business_model",
    }

    jobs = get_pending_enrichment_jobs()

    company_jobs = [
        job
        for job in jobs
        if job["company_id"] == company.id
    ]

    enrichment_types = {
        job["enrichment_type"]
        for job in company_jobs
    }

    assert enrichment_types == {
        "employee_count",
        "business_model",
    }

def test_enrichment_updates_company_and_completes_jobs():
    company = create_real_company()

    qualification = qualify_company(company.id)

    assert qualification.status == "NEEDS_REVIEW"

    updated = enrich_company(
        company_id=company.id,
        fields=qualification.missing_fields,
        provider=MockCompanyEnrichmentProvider(),
        provider_name="public",
    )

    assert updated["employee_count"] == 90
    assert updated["business_model"] == "Marketplace"

    saved_company = get_company_by_id(
        company.id
    )

    assert saved_company["employee_count"] == 90
    assert (
        saved_company["business_model"]
        == "Marketplace"
    )

    jobs = get_pending_enrichment_jobs()

    company_pending_jobs = [
        job
        for job in jobs
        if job["company_id"] == company.id
    ]

    assert company_pending_jobs == []
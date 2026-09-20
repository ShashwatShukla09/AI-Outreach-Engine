from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from tests.test_enrichment_queue import (
    create_real_company,
)
from app.workflows.company_enrichment_workflow import (
    qualify_enrich_requalify,
)


def test_company_can_be_enriched_and_requalified():
    company = create_real_company()

    result = qualify_enrich_requalify(
        company_id=company.id,
        provider=MockCompanyEnrichmentProvider(),
        provider_name="public",
    )

    assert (
        result["initial_qualification"].status
        == "NEEDS_REVIEW"
    )

    assert result["enriched"] is True

    assert (
        result["updated_company"]["employee_count"]
        == 90
    )

    assert (
        result["updated_company"]["business_model"]
        == "Marketplace"
    )

    assert (
        result["final_qualification"].status
        == "QUALIFIED"
    )

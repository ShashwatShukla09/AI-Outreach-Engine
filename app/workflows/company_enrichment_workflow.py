from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.enrichment_service import (
    enrich_company,
    queue_missing_company_data,
)


def qualify_enrich_requalify(
    company_id: int,
    provider: CompanyEnrichmentProvider,
    provider_name: str,
):
    initial_result = qualify_company(company_id)

    if initial_result.status != "NEEDS_REVIEW":
        return {
            "initial_qualification": initial_result,
            "enriched": False,
            "final_qualification": initial_result,
        }

    queue_missing_company_data(
        company_id=company_id,
        missing_fields=initial_result.missing_fields,
        provider=provider_name,
    )

    updated_company = enrich_company(
        company_id=company_id,
        fields=initial_result.missing_fields,
        provider=provider,
        provider_name=provider_name,
    )

    enriched = any(
        updated_company.get(field) is not None
        for field in initial_result.missing_fields
    )

    final_result = qualify_company(company_id)

    return {
        "initial_qualification": initial_result,
        "enriched": enriched,
        "updated_company": updated_company,
        "final_qualification": final_result,
    }

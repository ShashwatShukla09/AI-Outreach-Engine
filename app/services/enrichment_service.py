from typing import List

from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
    update_company_fields,
)
from app.repositories.enrichment_repository import (
    complete_enrichment_jobs,
    create_enrichment_job,
    find_pending_enrichment_job,
)


def queue_missing_company_data(
    company_id: int,
    missing_fields: List[str],
    provider: str = "public",
) -> List[dict]:
    jobs = []

    for field in missing_fields:
        existing = find_pending_enrichment_job(
            company_id=company_id,
            provider=provider,
            enrichment_type=field,
        )

        if existing is not None:
            jobs.append(existing)
            continue

        job = create_enrichment_job(
            company_id=company_id,
            provider=provider,
            enrichment_type=field,
        )

        jobs.append(job)

    return jobs


def enrich_company(
    company_id: int,
    fields: List[str],
    provider: CompanyEnrichmentProvider,
    provider_name: str,
) -> dict:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    enriched_data = provider.enrich_company(
        company=company,
        fields=fields,
    )

    if not enriched_data:
        return company

    updated_company = update_company_fields(
        company_id=company_id,
        fields=enriched_data,
    )

    complete_enrichment_jobs(
        company_id=company_id,
        provider=provider_name,
        enrichment_types=list(
            enriched_data.keys()
        ),
    )

    return updated_company

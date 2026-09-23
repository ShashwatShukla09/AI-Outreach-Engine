from typing import Dict, Optional

from app.providers.discovery.base import (
    CompanyDiscoveryProvider,
)
from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)
from app.providers.signals.base import (
    SignalProvider,
)
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.company_qualification_service import (
    get_company,
)
from app.workflows.company_intelligence_workflow import (
    process_company_batch,
)
from app.workflows.company_relevance_workflow import (
    assess_and_save_company_relevance,
)


def replenish_companies(
    icp_id: int,
    discovery_provider: CompanyDiscoveryProvider,
    enrichment_provider: CompanyEnrichmentProvider,
    enrichment_provider_name: str,
    signal_provider: Optional[SignalProvider] = None,
    limit: int = 100,
) -> Dict:
    """
    Discover and fully process only NEW companies.

    Discovery handles deduplication. Newly saved companies
    then pass through the existing intelligence pipeline:
    qualification -> selective enrichment -> requalification
    -> scoring/signals.

    Companies that finish QUALIFIED also receive a Clearlyy
    relevance assessment.
    """

    new_companies = discover_and_save_companies(
        icp_id=icp_id,
        provider=discovery_provider,
        limit=limit,
    )

    company_ids = [
        company.id
        for company in new_companies
    ]

    processing = process_company_batch(
        company_ids=company_ids,
        enrichment_provider=enrichment_provider,
        enrichment_provider_name=enrichment_provider_name,
        signal_provider=signal_provider,
    )

    relevance_results = []

    for result in processing["results"]:
        if result["status"] != "QUALIFIED":
            continue

        company = get_company(
            result["company_id"]
        )

        relevance_results.append(
            assess_and_save_company_relevance(
                company
            )
        )

    priority_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for relevance in relevance_results:
        priority = relevance["priority"]

        if priority in priority_counts:
            priority_counts[priority] += 1

    needs_review_count = sum(
        1
        for result in processing["results"]
        if result["status"] == "NEEDS_REVIEW"
    )

    return {
        "icp_id": icp_id,
        "new_accounts": len(new_companies),
        "processed": processing["processed_count"],
        "qualified": processing["qualified_count"],
        "disqualified": processing["disqualified_count"],
        "needs_review": needs_review_count,
        "enriched": processing["enriched_count"],
        "high_priority": priority_counts["HIGH"],
        "medium_priority": priority_counts["MEDIUM"],
        "low_priority": priority_counts["LOW"],
        "processing": processing,
        "relevance_results": relevance_results,
    }

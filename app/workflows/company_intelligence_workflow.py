from typing import Optional

from app.providers.contacts.base import (
    ContactProvider,
)
from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)
from app.providers.signals.base import (
    SignalProvider,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.workflows.buyer_intelligence_workflow import (
    build_buyer_intelligence,
)
from app.workflows.company_enrichment_workflow import (
    qualify_enrich_requalify,
)
from app.workflows.company_signal_workflow import (
    discover_signals_and_rescore,
)


def process_company_intelligence(
    company_id: int,
    enrichment_provider: CompanyEnrichmentProvider,
    enrichment_provider_name: str,
    signal_provider: Optional[SignalProvider] = None,
    contact_provider: Optional[ContactProvider] = None,
) -> dict:
    qualification = qualify_enrich_requalify(
        company_id=company_id,
        provider=enrichment_provider,
        provider_name=enrichment_provider_name,
    )

    final_qualification = qualification[
        "final_qualification"
    ]

    if final_qualification.status != "QUALIFIED":
        return {
            "company_id": company_id,
            "status": final_qualification.status,
            "enriched": qualification["enriched"],
            "qualification": qualification,
            "score": None,
        }

    score = score_and_save_company(
        company_id=company_id
    )

    signal_processing = None
    buyer_intelligence = None

    if (
        contact_provider is not None
        and signal_provider is not None
    ):
        buyer_intelligence = build_buyer_intelligence(
            company_id=company_id,
            contact_provider=contact_provider,
            signal_provider=signal_provider,
        )

        score = buyer_intelligence["score"]

    elif signal_provider is not None:
        signal_processing = (
            discover_signals_and_rescore(
                company_id=company_id,
                provider=signal_provider,
            )
        )

        score = signal_processing["score"]

    return {
        "company_id": company_id,
        "status": final_qualification.status,
        "enriched": qualification["enriched"],
        "qualification": qualification,
        "signal_processing": signal_processing,
        "buyer_intelligence": buyer_intelligence,
        "score": score,
    }


def process_company_batch(
    company_ids,
    enrichment_provider: CompanyEnrichmentProvider,
    enrichment_provider_name: str,
    signal_provider: Optional[SignalProvider] = None,
    contact_provider: Optional[ContactProvider] = None,
) -> dict:
    results = []

    for company_id in company_ids:
        result = process_company_intelligence(
            company_id=company_id,
            enrichment_provider=enrichment_provider,
            enrichment_provider_name=(
                enrichment_provider_name
            ),
            signal_provider=signal_provider,
            contact_provider=contact_provider,
        )

        results.append(result)

    qualified_count = sum(
        1
        for result in results
        if result["status"] == "QUALIFIED"
    )

    disqualified_count = sum(
        1
        for result in results
        if result["status"] == "DISQUALIFIED"
    )

    enriched_count = sum(
        1
        for result in results
        if result["enriched"]
    )

    return {
        "processed_count": len(results),
        "qualified_count": qualified_count,
        "disqualified_count": disqualified_count,
        "enriched_count": enriched_count,
        "results": results,
    }

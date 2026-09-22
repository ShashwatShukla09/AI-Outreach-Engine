from typing import Dict, List

from app.repositories.company_repository import (
    get_companies_for_icp,
)
from app.repositories.company_relevance_repository import (
    save_company_relevance_assessment,
)
from app.services.clearlyy_relevance_service import (
    assess_clearlyy_relevance,
)


def assess_and_save_company_relevance(
    company: dict,
) -> dict:
    if company["qualification_status"] != "QUALIFIED":
        raise ValueError(
            "Only QUALIFIED companies can be assessed "
            "for relevance."
        )

    assessment = assess_clearlyy_relevance(
        company
    )

    saved = save_company_relevance_assessment(
        company_id=company["id"],
        relevance_score=assessment["relevance_score"],
        priority=assessment["priority"],
        evidence=assessment["evidence_summary"],
    )

    return {
        "company_id": company["id"],
        "company_name": company["name"],
        "relevance_score": saved["relevance_score"],
        "priority": saved["priority"],
        "evidence": assessment["evidence_summary"],
    }


def assess_and_save_icp_relevance(
    icp_id: int,
) -> List[Dict]:
    companies = get_companies_for_icp(
        icp_id
    )

    qualified_companies = [
        company
        for company in companies
        if company["qualification_status"] == "QUALIFIED"
    ]

    results = []

    for company in qualified_companies:
        results.append(
            assess_and_save_company_relevance(
                company
            )
        )

    return results

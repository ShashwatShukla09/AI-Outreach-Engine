from typing import List

from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.contact_repository import (
    get_company_contacts,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.schemas.account_research import (
    AccountResearchBrief,
)


def build_account_research(
    company_id: int,
) -> AccountResearchBrief:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    contacts = get_company_contacts(
        company_id
    )

    signals = get_company_signals(
        company_id
    )

    company_summary = (
        f'{company["name"]} is a '
        f'{company["industry"] or "unknown-industry"} '
        f'company operating in '
        f'{company["country"] or "an unknown market"}'
    )

    if company["employee_count"]:
        company_summary += (
            f' with approximately '
            f'{company["employee_count"]} employees'
        )

    if company["business_model"]:
        company_summary += (
            f' and a '
            f'{company["business_model"]} '
            f'business model'
        )

    company_summary += "."

    why_company: List[str] = []

    if company["industry"]:
        why_company.append(
            f'Industry fit: {company["industry"]}.'
        )

    if company["employee_count"]:
        why_company.append(
            (
                "Company size observed: "
                f'{company["employee_count"]} '
                "employees."
            )
        )

    if company["country"]:
        why_company.append(
            (
                "Target market match: "
                f'{company["country"]}.'
            )
        )

    if company["business_model"]:
        why_company.append(
            (
                "Business model fit: "
                f'{company["business_model"]}.'
            )
        )

    why_now: List[str] = []

    for signal in signals:
        why_now.append(
            (
                f'{signal["title"]} '
                f'[{signal["signal_type"]}, '
                f'{signal["confidence"]} confidence].'
            )
        )

    if not why_now:
        why_now.append(
            "No recognised timing signals found yet."
        )

    relevant_buyers = [
        contact
        for contact in contacts
        if (
            contact["relevance_score"]
            is not None
            and contact["relevance_score"] > 0
        )
    ]

    primary_buyer = None

    if relevant_buyers:
        best_buyer = max(
            relevant_buyers,
            key=lambda contact: (
                contact["relevance_score"]
            ),
        )

        primary_buyer = (
            f'{best_buyer["first_name"]} '
            f'{best_buyer["last_name"]} — '
            f'{best_buyer["job_title"]}'
        )

    pain_points: List[str] = []

    signal_types = {
        signal["signal_type"]
        for signal in signals
    }

    if "SUPPORT_HIRING" in signal_types:
        pain_points.append(
            (
                "Support-team expansion may indicate "
                "growing customer-service workload."
            )
        )

    if "CUSTOMER_PAIN" in signal_types:
        pain_points.append(
            (
                "Customer-pain signals indicate "
                "possible pressure on the current "
                "support experience."
            )
        )

    if "TEAM_GROWTH" in signal_types:
        pain_points.append(
            (
                "Team growth may create additional "
                "operational coordination needs."
            )
        )

    relevant_evidence: List[str] = []

    for signal in signals:
        relevant_evidence.append(
            (
                f'Signal: {signal["title"]} '
                f'from {signal["source"]}.'
            )
        )

    for contact in relevant_buyers:
        relevant_evidence.append(
            (
                "Buyer match: "
                f'{contact["first_name"]} '
                f'{contact["last_name"]}, '
                f'{contact["job_title"]}, '
                f'relevance '
                f'{contact["relevance_score"]}/10.'
            )
        )

    return AccountResearchBrief(
        company_id=company_id,
        company_summary=company_summary,
        why_company=why_company,
        why_now=why_now,
        pain_points=pain_points,
        relevant_evidence=relevant_evidence,
        primary_buyer=primary_buyer,
    )

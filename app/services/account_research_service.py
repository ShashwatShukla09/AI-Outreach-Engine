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
from app.services.buyer_ranking_service import (
    rank_company_buyers,
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

    ranked_buyers = rank_company_buyers(
        contacts
    )

    relevant_buyers = [
        buyer
        for buyer in ranked_buyers
        if buyer["buyer_rank_score"] > 0
    ]

    company_summary = (
        f'{company["name"]} is a '
        f'{company["industry"] or "company"} '
        f'operating in '
        f'{company["country"] or "an unknown market"}'
    )

    if company["employee_count"]:
        company_summary += (
            f' with approximately '
            f'{company["employee_count"]} employees'
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

    if relevant_buyers:
        why_company.append(
            (
                f'{len(relevant_buyers)} '
                "ICP-relevant buyer"
                f'{"s" if len(relevant_buyers) != 1 else ""} '
                "identified."
            )
        )

    why_now: List[str] = []

    for signal in signals:
        date_context = (
            f' ({signal["signal_date"]})'
            if signal.get("signal_date")
            else ""
        )

        why_now.append(
            (
                f'{signal["title"]}{date_context} '
                f'[{signal["signal_type"]}, '
                f'{signal["confidence"]} confidence].'
            )
        )

    if not why_now:
        why_now.append(
            "No verified timing signals found yet."
        )

    pain_points: List[str] = []

    signal_types = {
        signal["signal_type"]
        for signal in signals
    }

    if "WORKFORCE_TRAINING" in signal_types:
        pain_points.append(
            (
                "Workforce-training activity may create "
                "an opportunity to make operational "
                "knowledge easier to deliver consistently."
            )
        )

    if "OPERATIONAL_EXPANSION" in signal_types:
        pain_points.append(
            (
                "Operational expansion or integration may "
                "increase the need for consistent SOP and "
                "process communication across teams."
            )
        )

    if "FACILITY_EXPANSION" in signal_types:
        pain_points.append(
            (
                "Facility expansion may increase onboarding "
                "and process-training requirements for "
                "distributed operational teams."
            )
        )

    if "FRONTLINE_HIRING" in signal_types:
        pain_points.append(
            (
                "Frontline hiring may increase the need for "
                "repeatable onboarding and role-specific "
                "training."
            )
        )

    if "SAFETY_COMPLIANCE" in signal_types:
        pain_points.append(
            (
                "Safety or compliance activity may create "
                "a need for clear and repeatable workforce "
                "communication."
            )
        )

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
                "Customer-pain signals indicate possible "
                "pressure on the current support experience."
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
        evidence = (
            f'Signal: {signal["title"]}'
        )

        if signal.get("signal_date"):
            evidence += (
                f' ({signal["signal_date"]})'
            )

        evidence += (
            f' from {signal["source"]}.'
        )

        relevant_evidence.append(
            evidence
        )

    for buyer in relevant_buyers:
        relevant_evidence.append(
            (
                "Buyer match: "
                f'{buyer["first_name"]} '
                f'{buyer["last_name"]}, '
                f'{buyer["job_title"]}, '
                f'ICP relevance '
                f'{buyer["relevance_score"]}/10, '
                f'buyer rank '
                f'{buyer["buyer_rank_score"]}/100.'
            )
        )

    primary_buyer = None

    if relevant_buyers:
        best_buyer = relevant_buyers[0]

        primary_buyer = (
            f'{best_buyer["first_name"]} '
            f'{best_buyer["last_name"]} — '
            f'{best_buyer["job_title"]} '
            f'— buyer rank '
            f'{best_buyer["buyer_rank_score"]}/100'
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

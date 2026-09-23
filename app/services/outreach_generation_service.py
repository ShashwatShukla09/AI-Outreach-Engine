import json

from app.repositories.account_research_repository import (
    get_account_research,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.contact_repository import (
    get_company_contacts,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.schemas.outreach import OutreachDraft
from app.services.buyer_ranking_service import (
    rank_company_buyers,
)


def _load_json_list(
    value,
):
    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []

    return parsed if isinstance(parsed, list) else []


def _signal_copy(
    signal,
):
    signal_type = signal["signal_type"]
    title = signal["title"]

    if signal_type == "WORKFORCE_TRAINING":
        return (
            f'the training work described as "{title}"'
        )

    if signal_type == "OPERATIONAL_EXPANSION":
        return (
            f'the operations update described as "{title}"'
        )

    if signal_type == "FACILITY_EXPANSION":
        return (
            f'the facility update described as "{title}"'
        )

    if signal_type == "FRONTLINE_HIRING":
        return (
            f'the frontline hiring update described as "{title}"'
        )

    if signal_type == "SAFETY_COMPLIANCE":
        return (
            f'the safety or compliance update described as "{title}"'
        )

    return title


def generate_outreach_draft(
    company_id: int,
) -> OutreachDraft:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    research = get_account_research(
        company_id
    )

    if research is None:
        raise ValueError(
            "Account research must exist before outreach."
        )

    contacts = get_company_contacts(
        company_id
    )

    ranked_buyers = [
        buyer
        for buyer in rank_company_buyers(contacts)
        if buyer["buyer_rank_score"] > 0
    ]

    if not ranked_buyers:
        raise ValueError(
            "No relevant buyer found for outreach."
        )

    primary_buyer = ranked_buyers[0]

    signals = get_company_signals(
        company_id
    )

    why_company = _load_json_list(
        research.get("why_company")
    )

    why_now = _load_json_list(
        research.get("why_now")
    )

    pain_points = _load_json_list(
        research.get("pain_points")
    )

    first_name = primary_buyer["first_name"]
    job_title = primary_buyer["job_title"]
    company_name = company["name"]

    subject = (
        f"{company_name} frontline training"
    )

    if signals:
        signal_references = [
            _signal_copy(signal)
            for signal in signals[:2]
        ]

        if len(signal_references) == 1:
            timing_context = signal_references[0]
        else:
            timing_context = (
                f"{signal_references[0]}, alongside "
                f"{signal_references[1]}"
            )

        timing_line = (
            f"I was looking into {company_name}'s "
            f"operations and came across "
            f"{timing_context}."
        )
    else:
        timing_line = (
            f"I came across {company_name} while "
            "researching operational teams where "
            "frontline training and SOP communication "
            "matter."
        )

    message_body = (
        f"Hi {first_name},\n\n"
        f"{timing_line}\n\n"
        f"Given your role as {job_title}, I thought "
        "this might be relevant. Clearlyy turns SOPs, "
        "manuals and training material into short, "
        "accessible videos for distributed frontline "
        "teams.\n\n"
        "Thought there could be an interesting use "
        f"case at {company_name} around communicating "
        "process updates and operational training "
        "consistently across teams.\n\n"
        f"Worth sending over a short example tailored "
        f"to {company_name}?\n\n"
        "Best,\n"
        "Shashwat"
    )

    evidence_parts = []

    if why_company:
        evidence_parts.append(
            f"Company fit: {why_company[0]}"
        )

    if why_now and signals:
        evidence_parts.append(
            f"Timing evidence: {why_now[0]}"
        )

    if pain_points:
        evidence_parts.append(
            f"Use-case hypothesis: {pain_points[0]}"
        )

    evidence_summary = " ".join(
        evidence_parts
    )

    personalisation_reason = (
        f"Selected {primary_buyer['first_name']} "
        f"{primary_buyer['last_name']} because "
        f"{job_title} ranked highest among the "
        f"identified ICP buyers at "
        f"{primary_buyer['buyer_rank_score']}/100. "
        f"{evidence_summary}"
    ).strip()

    return OutreachDraft(
        company_id=company_id,
        contact_id=primary_buyer["id"],
        channel="EMAIL",
        subject=subject,
        message_body=message_body,
        personalisation_reason=(
            personalisation_reason
        ),
    )

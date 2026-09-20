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

    relevant_contacts = [
        contact
        for contact in contacts
        if (
            contact["relevance_score"]
            is not None
            and contact["relevance_score"] > 0
        )
    ]

    if not relevant_contacts:
        raise ValueError(
            "No relevant buyer found for outreach."
        )

    primary_buyer = max(
        relevant_contacts,
        key=lambda contact: (
            contact["relevance_score"]
        ),
    )

    signals = get_company_signals(
        company_id
    )

    signal_titles = [
        signal["title"]
        for signal in signals
    ]

    if signal_titles:
        timing_context = (
            ", and ".join(signal_titles[:2])
        )
    else:
        timing_context = (
            "your current growth"
        )

    first_name = primary_buyer[
        "first_name"
    ]

    job_title = primary_buyer[
        "job_title"
    ]

    company_name = company["name"]

    subject = (
        f"{company_name} support operations"
    )

    message_body = (
        f"Hi {first_name},\n\n"
        f"I came across {company_name} while "
        f"researching teams in "
        f'{company["industry"] or "your space"}. '
        f"I noticed {timing_context}.\n\n"
        f"Given your role as {job_title}, I thought "
        "this might be relevant. We're exploring "
        "ways AI can reduce repetitive support work "
        "and help growing teams handle customer "
        "requests more efficiently.\n\n"
        "Would it be useful if I sent over a short "
        "example of how the workflow could work?\n\n"
        "Best,\n"
        "Shashwat"
    )

    personalisation_reason = (
        f"Selected {primary_buyer['first_name']} "
        f"{primary_buyer['last_name']} because "
        f"{job_title} matched an approved ICP buyer "
        f"category with relevance score "
        f"{primary_buyer['relevance_score']}/10. "
        f"Timing context used: {timing_context}."
    )

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

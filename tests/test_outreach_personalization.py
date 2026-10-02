from app.repositories.account_research_repository import (
    save_account_research,
)
from app.repositories.contact_repository import (
    create_contact,
    update_contact_relevance,
)
from app.repositories.signal_repository import (
    create_signal,
)
from app.schemas.contact import ContactCandidate
from app.schemas.signal import SignalCreate
from app.services.account_research_service import (
    build_account_research,
)
from app.services.outreach_generation_service import (
    generate_outreach_draft,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_demo_company():
    companies = prepare_scoring_companies()

    company = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    operations_contact = create_contact(
        company.id,
        ContactCandidate(
            first_name="Aarav",
            last_name="Sharma",
            job_title=(
                "Senior Vice President, Operations"
            ),
            email=None,
            linkedin_url=None,
            enrichment_provider="synthetic_test",
        ),
    )

    update_contact_relevance(
        contact_id=operations_contact["id"],
        buyer_category="Operations",
        relevance_score=10,
        relevance_reason=(
            "Synthetic ICP Operations buyer."
        ),
    )

    learning_contact = create_contact(
        company.id,
        ContactCandidate(
            first_name="Meera",
            last_name="Kapoor",
            job_title=(
                "Head of Learning & Development"
            ),
            email=None,
            linkedin_url=None,
            enrichment_provider="synthetic_test",
        ),
    )

    update_contact_relevance(
        contact_id=learning_contact["id"],
        buyer_category="Learning and Development",
        relevance_score=10,
        relevance_reason=(
            "Synthetic ICP learning buyer."
        ),
    )

    create_signal(
        company.id,
        SignalCreate(
            signal_type="WORKFORCE_TRAINING",
            title=(
                "Frontline workforce training programme"
            ),
            description=(
                "Synthetic training signal used only "
                "for automated testing."
            ),
            source="Synthetic Test Source",
            source_url=(
                "https://example.invalid/training"
            ),
            signal_date="2025-04",
            confidence="HIGH",
        ),
    )

    create_signal(
        company.id,
        SignalCreate(
            signal_type="OPERATIONAL_EXPANSION",
            title=(
                "Operational network expansion"
            ),
            description=(
                "Synthetic expansion signal used only "
                "for automated testing."
            ),
            source="Synthetic Test Source",
            source_url=(
                "https://example.invalid/expansion"
            ),
            signal_date="2025-11",
            confidence="HIGH",
        ),
    )

    brief = build_account_research(
        company.id
    )

    save_account_research(
        brief
    )

    return (
        company,
        operations_contact,
        learning_contact,
    )


def test_outreach_uses_ranked_buyer_and_evidence():
    (
        company,
        operations_contact,
        learning_contact,
    ) = prepare_demo_company()

    draft = generate_outreach_draft(
        company.id
    )

    assert draft.channel == "EMAIL"

    assert (
        draft.contact_id
        == learning_contact["id"]
    )

    assert (
        draft.contact_id
        != operations_contact["id"]
    )

    assert "Hi Meera" in draft.message_body

    assert (
        "Frontline workforce training programme"
        in draft.message_body
    )

    assert (
        "Operational network expansion"
        in draft.message_body
    )

    assert "2025-04" not in draft.message_body
    assert "2025-11" not in draft.message_body

    assert "2025-04" in (
        draft.personalisation_reason
    )

    assert "SOP" in draft.message_body

    assert (
        "frontline"
        in draft.message_body.lower()
    )

    assert (
        "reduce repetitive support work"
        not in draft.message_body.lower()
    )

    assert (
        "94/100"
        in draft.personalisation_reason
    )


def test_generation_does_not_save_or_send():
    company, _, _ = (
        prepare_demo_company()
    )

    draft = generate_outreach_draft(
        company.id
    )

    assert draft.company_id == company.id
    assert draft.channel == "EMAIL"

    # generate_outreach_draft() returns an in-memory
    # draft only. Saving, approval and execution are
    # separate workflow boundaries.

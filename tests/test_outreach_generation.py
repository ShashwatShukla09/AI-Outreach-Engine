from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.outreach_repository import (
    get_company_outreach_messages,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.outreach_generation_service import (
    generate_outreach_draft,
)
from app.workflows.account_intelligence_workflow import (
    build_account_intelligence,
)
from app.workflows.outreach_generation_workflow import (
    create_company_outreach,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_outreach_company():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(
        nova.id
    )

    assert qualification.status == "QUALIFIED"

    build_account_intelligence(
        company_id=nova.id,
        contact_provider=MockContactProvider(),
        signal_provider=MockSignalProvider(),
    )

    return nova


def test_outreach_uses_relevant_buyer_and_signals():
    company = prepare_outreach_company()

    draft = generate_outreach_draft(
        company.id
    )

    assert draft.channel == "EMAIL"

    assert "NovaCart India" in (
        draft.subject
    )

    assert "Hi Priya" in draft.message_body

    assert "Recent funding round" in (
        draft.message_body
    )

    assert (
        "Hiring customer support staff"
        in draft.message_body
    )

    assert "Head of Support" in (
        draft.personalisation_reason
    )


def test_outreach_is_saved_as_draft():
    company = prepare_outreach_company()

    result = create_company_outreach(
        company.id
    )

    assert result["saved"]["status"] == "DRAFT"

    messages = (
        get_company_outreach_messages(
            company.id
        )
    )

    assert len(messages) == 1

    assert messages[0]["status"] == "DRAFT"
    assert messages[0]["sent_at"] is None
    assert messages[0]["approved_at"] is None

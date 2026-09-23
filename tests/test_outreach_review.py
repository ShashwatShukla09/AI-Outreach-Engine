import pytest

from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.schemas.outreach import OutreachEdit
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
    edit_outreach,
    reject_outreach_message,
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


def prepare_draft():
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

    result = create_company_outreach(
        nova.id
    )

    return result["saved"]


def test_draft_can_be_edited():
    draft = prepare_draft()

    edited = edit_outreach(
        outreach_id=draft["id"],
        edit=OutreachEdit(
            subject="Quick idea for NovaCart",
            message_body=(
                "Hi Priya,\n\n"
                "I had a quick idea for "
                "NovaCart's support workflow."
            ),
        ),
    )

    assert edited["status"] == "DRAFT"

    assert (
        edited["subject"]
        == "Quick idea for NovaCart"
    )

    assert "quick idea" in (
        edited["message_body"]
    )


def test_draft_can_be_approved():
    draft = prepare_draft()

    approved = approve_outreach_message(
        draft["id"]
    )

    assert approved["status"] == "APPROVED"
    assert approved["approved_at"] is not None
    assert approved["rejected_at"] is None
    assert approved["sent_at"] is None


def test_draft_can_be_rejected():
    draft = prepare_draft()

    rejected = reject_outreach_message(
        draft["id"]
    )

    assert rejected["status"] == "REJECTED"
    assert rejected["rejected_at"] is not None
    assert rejected["approved_at"] is None
    assert rejected["sent_at"] is None


def test_approved_message_cannot_be_edited():
    draft = prepare_draft()

    approve_outreach_message(
        draft["id"]
    )

    with pytest.raises(
        ValueError,
        match="Only DRAFT outreach can be edited",
    ):
        edit_outreach(
            outreach_id=draft["id"],
            edit=OutreachEdit(
                subject="Changed",
                message_body="Changed body",
            ),
        )


def test_rejected_message_cannot_be_approved():
    draft = prepare_draft()

    reject_outreach_message(
        draft["id"]
    )

    with pytest.raises(
        ValueError,
        match="Only DRAFT outreach can be approved",
    ):
        approve_outreach_message(
            draft["id"]
        )


def test_approved_message_cannot_be_rejected():
    draft = prepare_draft()

    approve_outreach_message(
        draft["id"]
    )

    with pytest.raises(
        ValueError,
        match="Only DRAFT outreach can be rejected",
    ):
        reject_outreach_message(
            draft["id"]
        )


def test_edit_creates_audit_event():
    from app.repositories.outreach_event_repository import (
        get_outreach_events,
    )

    draft = prepare_draft()

    edit_outreach(
        outreach_id=draft["id"],
        edit=OutreachEdit(
            subject="Updated NovaCart idea",
            message_body=(
                "Hi Priya,\n\n"
                "Updated outreach message."
            ),
        ),
    )

    events = get_outreach_events(
        draft["id"]
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "EDITED"


def test_approval_creates_audit_event():
    from app.repositories.outreach_event_repository import (
        get_outreach_events,
    )

    draft = prepare_draft()

    approve_outreach_message(
        draft["id"]
    )

    events = get_outreach_events(
        draft["id"]
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "APPROVED"


def test_rejection_creates_audit_event():
    from app.repositories.outreach_event_repository import (
        get_outreach_events,
    )

    draft = prepare_draft()

    reject_outreach_message(
        draft["id"]
    )

    events = get_outreach_events(
        draft["id"]
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "REJECTED"

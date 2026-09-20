import json

import pytest

from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.execution.mock_provider import (
    MockExecutionProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.outreach_event_repository import (
    get_outreach_events,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.outreach_execution_service import (
    execute_outreach,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
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


def test_draft_cannot_be_executed():
    draft = prepare_draft()

    with pytest.raises(
        ValueError,
        match=(
            "Only APPROVED outreach "
            "can be executed"
        ),
    ):
        execute_outreach(
            outreach_id=draft["id"],
            provider=MockExecutionProvider(),
        )

    events = get_outreach_events(
        draft["id"]
    )

    assert events == []


def test_approved_outreach_can_be_executed():
    draft = prepare_draft()

    approve_outreach_message(
        draft["id"]
    )

    result = execute_outreach(
        outreach_id=draft["id"],
        provider=MockExecutionProvider(),
    )

    assert result["message"]["status"] == "SENT"

    assert (
        result["message"]["sent_at"]
        is not None
    )

    assert (
        result["provider_result"]["success"]
        is True
    )

    events = get_outreach_events(
        draft["id"]
    )

    assert len(events) == 2

    assert events[0]["event_type"] == (
        "SEND_ATTEMPTED"
    )

    assert events[1]["event_type"] == "SENT"

    sent_data = json.loads(
        events[1]["event_data"]
    )

    assert sent_data["provider"] == "mock"


def test_sent_outreach_cannot_be_sent_again():
    draft = prepare_draft()

    approve_outreach_message(
        draft["id"]
    )

    execute_outreach(
        outreach_id=draft["id"],
        provider=MockExecutionProvider(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Only APPROVED outreach "
            "can be executed"
        ),
    ):
        execute_outreach(
            outreach_id=draft["id"],
            provider=MockExecutionProvider(),
        )

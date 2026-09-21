from fastapi.testclient import TestClient

from app.main import app
from app.providers.execution.mock_provider import (
    MockExecutionProvider,
)
from app.services.outreach_execution_service import (
    execute_outreach,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
    reject_outreach_message,
)
from tests.test_outreach_execution import (
    prepare_draft,
)


client = TestClient(app)


def test_dashboard_summary_returns_all_outreach_states():
    draft = prepare_draft()

    approved = prepare_draft()
    approve_outreach_message(
        approved["id"]
    )

    sent = prepare_draft()
    approve_outreach_message(
        sent["id"]
    )
    execute_outreach(
        outreach_id=sent["id"],
        provider=MockExecutionProvider(),
    )

    rejected = prepare_draft()
    reject_outreach_message(
        rejected["id"]
    )

    response = client.get(
        "/api/outreach/dashboard/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["metrics"]["pending_review"] >= 1
    assert data["metrics"]["approved"] >= 1
    assert data["metrics"]["sent"] >= 1
    assert data["metrics"]["rejected"] >= 1

    assert any(
        message["id"] == draft["id"]
        for message in data["review_queue"]
    )

    assert any(
        message["id"] == approved["id"]
        for message in data["ready_to_send"]
    )

    assert any(
        message["id"] == sent["id"]
        for message in data["sent_history"]
    )

    assert any(
        message["id"] == rejected["id"]
        for message in data["rejected_history"]
    )

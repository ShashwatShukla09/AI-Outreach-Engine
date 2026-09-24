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
from app.services.outreach_outcome_service import (
    record_outreach_outcome,
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


def test_dashboard_summary_returns_outreach_outcome_metrics():
    baseline_response = client.get(
        "/api/outreach/dashboard/summary"
    )

    assert baseline_response.status_code == 200

    baseline = baseline_response.json()["metrics"]

    sent_ids = []

    for _ in range(4):
        draft = prepare_draft()

        approve_outreach_message(
            draft["id"]
        )

        execute_outreach(
            outreach_id=draft["id"],
            provider=MockExecutionProvider(),
        )

        sent_ids.append(draft["id"])

    record_outreach_outcome(
        sent_ids[0],
        "REPLIED",
    )
    record_outreach_outcome(
        sent_ids[0],
        "POSITIVE",
    )
    record_outreach_outcome(
        sent_ids[0],
        "MEETING_BOOKED",
    )

    record_outreach_outcome(
        sent_ids[1],
        "REPLIED",
    )
    record_outreach_outcome(
        sent_ids[1],
        "POSITIVE",
    )

    record_outreach_outcome(
        sent_ids[2],
        "REPLIED",
    )
    record_outreach_outcome(
        sent_ids[2],
        "NEGATIVE",
    )

    response = client.get(
        "/api/outreach/dashboard/summary"
    )

    assert response.status_code == 200

    metrics = response.json()["metrics"]

    expected_sent = baseline["sent"] + 4
    expected_replied = baseline.get(
        "replied",
        0,
    ) + 3
    expected_positive = baseline.get(
        "positive_replies",
        0,
    ) + 2
    expected_meetings = baseline.get(
        "meetings_booked",
        0,
    ) + 1

    assert metrics["sent"] == expected_sent
    assert metrics["replied"] == expected_replied
    assert (
        metrics["positive_replies"]
        == expected_positive
    )
    assert (
        metrics["meetings_booked"]
        == expected_meetings
    )

    assert metrics["reply_rate"] == round(
        expected_replied
        / expected_sent
        * 100,
        1,
    )

    assert metrics["positive_reply_rate"] == round(
        expected_positive
        / expected_sent
        * 100,
        1,
    )

    assert metrics["meeting_rate"] == round(
        expected_meetings
        / expected_sent
        * 100,
        1,
    )

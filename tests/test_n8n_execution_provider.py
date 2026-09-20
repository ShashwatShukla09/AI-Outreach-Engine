from unittest.mock import Mock, patch

import pytest

from app.providers.execution.n8n_provider import (
    N8nExecutionProvider,
)


def sample_message(
    status="APPROVED",
):
    return {
        "id": 42,
        "company_id": 10,
        "contact_id": 7,
        "channel": "EMAIL",
        "subject": "NovaCart support operations",
        "message_body": "Hi Priya...",
        "status": status,
    }


def sample_contact():
    return {
        "id": 7,
        "first_name": "Priya",
        "last_name": "Sharma",
        "job_title": "Head of Support",
        "email": "priya@novacart.example",
    }


def test_n8n_provider_requires_webhook():
    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):
        with pytest.raises(
            ValueError,
            match="n8n webhook URL is required",
        ):
            N8nExecutionProvider()


def test_n8n_payload_contains_required_data():
    provider = N8nExecutionProvider(
        webhook_url=(
            "http://localhost:5678/"
            "webhook/buyer-outreach"
        )
    )

    payload = provider.build_payload(
        message=sample_message(),
        contact=sample_contact(),
    )

    assert payload == {
        "outreach_message_id": 42,
        "company_id": 10,
        "contact_id": 7,
        "channel": "EMAIL",
        "recipient": (
            "priya@novacart.example"
        ),
        "recipient_first_name": "Priya",
        "recipient_last_name": "Sharma",
        "job_title": "Head of Support",
        "subject": (
            "NovaCart support operations"
        ),
        "message_body": "Hi Priya...",
        "approval_status": "APPROVED",
        "safe_test_mode": True,
    }


def test_safe_test_mode_defaults_true():
    provider = N8nExecutionProvider(
        webhook_url="http://example.test"
    )

    payload = provider.build_payload(
        message=sample_message(),
        contact=sample_contact(),
    )

    assert payload["safe_test_mode"] is True


def test_n8n_provider_blocks_unapproved():
    provider = N8nExecutionProvider(
        webhook_url="http://example.test"
    )

    with pytest.raises(
        ValueError,
        match="Only APPROVED outreach",
    ):
        provider.send(
            message=sample_message(
                status="DRAFT"
            ),
            contact=sample_contact(),
        )


def test_n8n_send_posts_payload():
    provider = N8nExecutionProvider(
        webhook_url="http://example.test"
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "accepted": True,
        "status": "SENT",
        "provider": "safe_test",
        "simulated": True,
    }
    mock_response.raise_for_status.return_value = (
        None
    )

    with patch(
        "app.providers.execution."
        "n8n_provider.httpx.post"
    ) as mock_post:
        mock_post.return_value = mock_response

        result = provider.send(
            message=sample_message(),
            contact=sample_contact(),
        )

    assert result["success"] is True
    assert result["provider"] == "n8n"

    payload = (
        mock_post.call_args.kwargs["json"]
    )

    assert (
        payload["approval_status"]
        == "APPROVED"
    )
    assert payload["safe_test_mode"] is True


def test_n8n_rejects_unaccepted_response():
    provider = N8nExecutionProvider(
        webhook_url="http://example.test"
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "accepted": False,
    }
    mock_response.raise_for_status.return_value = (
        None
    )

    with patch(
        "app.providers.execution."
        "n8n_provider.httpx.post"
    ) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(
            ValueError,
            match=(
                "n8n did not accept "
                "outreach execution"
            ),
        ):
            provider.send(
                message=sample_message(),
                contact=sample_contact(),
            )

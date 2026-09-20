from unittest.mock import patch

import pytest

from app.providers.execution.n8n_provider import (
    N8nExecutionProvider,
)


def sample_message():
    return {
        "id": 42,
        "company_id": 10,
        "contact_id": 7,
        "channel": "EMAIL",
        "subject": "NovaCart support operations",
        "message_body": "Hi Priya...",
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
            "webhook/outreach"
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
    }


def test_n8n_send_posts_payload():
    provider = N8nExecutionProvider(
        webhook_url=(
            "http://localhost:5678/"
            "webhook/outreach"
        )
    )

    mock_response = (
        __import__(
            "unittest.mock",
            fromlist=["Mock"],
        ).Mock()
    )

    mock_response.status_code = 200
    mock_response.json.return_value = {
        "accepted": True,
        "execution_id": "exec-123",
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
    assert result["status_code"] == 200

    mock_post.assert_called_once()

    call = mock_post.call_args

    assert call.kwargs["json"][
        "recipient"
    ] == "priya@novacart.example"

    assert call.kwargs["json"][
        "subject"
    ] == "NovaCart support operations"

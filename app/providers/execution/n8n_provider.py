import os
from typing import Optional

import httpx

from app.providers.execution.base import (
    OutreachExecutionProvider,
)


class N8nExecutionProvider(
    OutreachExecutionProvider
):
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout: float = 15.0,
        safe_test_mode: bool = True,
    ):
        self.webhook_url = (
            webhook_url
            or os.getenv(
                "N8N_OUTREACH_WEBHOOK_URL"
            )
        )

        self.timeout = timeout
        self.safe_test_mode = safe_test_mode

        if not self.webhook_url:
            raise ValueError(
                "n8n webhook URL is required."
            )

    def build_payload(
        self,
        message: dict,
        contact: dict,
    ) -> dict:
        return {
            "outreach_message_id": message["id"],
            "company_id": message["company_id"],
            "contact_id": contact["id"],
            "channel": message["channel"],
            "recipient": contact["email"],
            "recipient_first_name": (
                contact["first_name"]
            ),
            "recipient_last_name": (
                contact["last_name"]
            ),
            "job_title": contact["job_title"],
            "subject": message["subject"],
            "message_body": (
                message["message_body"]
            ),

            # n8n must independently verify that
            # Python already approved this message.
            "approval_status": message["status"],

            # Defaults to True so development cannot
            # accidentally reach the Gmail branch.
            "safe_test_mode": self.safe_test_mode,
        }

    def send(
        self,
        message: dict,
        contact: dict,
    ) -> dict:
        if not contact.get("email"):
            raise ValueError(
                "Contact has no email address."
            )

        if message.get("status") != "APPROVED":
            raise ValueError(
                "Only APPROVED outreach can be "
                "sent to n8n."
            )

        payload = self.build_payload(
            message=message,
            contact=contact,
        )

        response = httpx.post(
            self.webhook_url,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        try:
            response_data = response.json()
        except ValueError:
            response_data = {
                "raw_response": response.text
            }

        if not response_data.get(
            "accepted",
            False,
        ):
            raise ValueError(
                "n8n did not accept outreach "
                "execution."
            )

        return {
            "success": True,
            "provider": "n8n",
            "status_code": response.status_code,
            "response": response_data,
            "recipient": contact["email"],
        }

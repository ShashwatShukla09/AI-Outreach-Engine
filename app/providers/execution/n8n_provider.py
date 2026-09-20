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
    ):
        self.webhook_url = (
            webhook_url
            or os.getenv(
                "N8N_OUTREACH_WEBHOOK_URL"
            )
        )

        self.timeout = timeout

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

        return {
            "success": True,
            "provider": "n8n",
            "status_code": response.status_code,
            "response": response_data,
            "recipient": contact["email"],
        }

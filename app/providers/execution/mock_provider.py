from app.providers.execution.base import (
    OutreachExecutionProvider,
)


class MockExecutionProvider(
    OutreachExecutionProvider
):
    def send(
        self,
        message: dict,
        contact: dict,
    ) -> dict:
        if not contact.get("email"):
            raise ValueError(
                "Contact has no email address."
            )

        return {
            "success": True,
            "provider": "mock",
            "provider_message_id": (
                f'mock-{message["id"]}'
            ),
            "recipient": contact["email"],
        }

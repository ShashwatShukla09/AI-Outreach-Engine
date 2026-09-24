from app.db.database import get_connection
from app.providers.execution.base import (
    OutreachExecutionProvider,
)
from app.repositories.outreach_event_repository import (
    create_outreach_event,
)
from app.repositories.outreach_attribution_snapshot_repository import (
    create_outreach_attribution_snapshot,
)
from app.repositories.outreach_repository import (
    get_outreach_message,
    mark_outreach_sent,
)


def get_contact(
    contact_id: int,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def execute_outreach(
    outreach_id: int,
    provider: OutreachExecutionProvider,
) -> dict:
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise ValueError(
            "Outreach message not found"
        )

    if message["status"] != "APPROVED":
        raise ValueError(
            "Only APPROVED outreach can be executed."
        )

    if message["contact_id"] is None:
        raise ValueError(
            "Outreach message has no contact."
        )

    contact = get_contact(
        message["contact_id"]
    )

    if contact is None:
        raise ValueError(
            "Contact not found"
        )

    create_outreach_event(
        outreach_message_id=outreach_id,
        event_type="SEND_ATTEMPTED",
        event_data={
            "provider": (
                provider.__class__.__name__
            ),
        },
    )

    try:
        provider_result = provider.send(
            message=message,
            contact=contact,
        )

    except Exception as exc:
        create_outreach_event(
            outreach_message_id=outreach_id,
            event_type="SEND_FAILED",
            event_data={
                "error": str(exc),
            },
        )

        raise

    if not provider_result.get(
        "success",
        False,
    ):
        create_outreach_event(
            outreach_message_id=outreach_id,
            event_type="SEND_FAILED",
            event_data=provider_result,
        )

        raise ValueError(
            "Execution provider reported failure."
        )

    sent_message = mark_outreach_sent(
        outreach_id
    )

    create_outreach_attribution_snapshot(
        outreach_id
    )

    sent_event = create_outreach_event(
        outreach_message_id=outreach_id,
        event_type="SENT",
        event_data=provider_result,
    )

    return {
        "message": sent_message,
        "event": sent_event,
        "provider_result": provider_result,
    }

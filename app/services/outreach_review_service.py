from app.repositories.outreach_event_repository import (
    create_outreach_event,
)
from app.repositories.outreach_repository import (
    approve_outreach,
    get_outreach_message,
    reject_outreach,
    update_outreach_draft,
)
from app.schemas.outreach import OutreachEdit


def edit_outreach(
    outreach_id: int,
    edit: OutreachEdit,
) -> dict:
    previous = get_outreach_message(
        outreach_id
    )

    if previous is None:
        raise ValueError(
            "Outreach message not found"
        )

    updated = update_outreach_draft(
        outreach_id=outreach_id,
        subject=edit.subject,
        message_body=edit.message_body,
    )

    create_outreach_event(
        outreach_message_id=outreach_id,
        event_type="EDITED",
        event_data={
            "previous_status": previous["status"],
            "new_status": updated["status"],
            "subject_changed": (
                previous["subject"]
                != updated["subject"]
            ),
            "message_changed": (
                previous["message_body"]
                != updated["message_body"]
            ),
        },
    )

    return updated


def approve_outreach_message(
    outreach_id: int,
) -> dict:
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise ValueError(
            "Outreach message not found"
        )

    if not message["message_body"].strip():
        raise ValueError(
            "Cannot approve an empty message."
        )

    approved = approve_outreach(
        outreach_id
    )

    create_outreach_event(
        outreach_message_id=outreach_id,
        event_type="APPROVED",
        event_data={
            "previous_status": message["status"],
            "new_status": approved["status"],
        },
    )

    return approved


def reject_outreach_message(
    outreach_id: int,
) -> dict:
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise ValueError(
            "Outreach message not found"
        )

    rejected = reject_outreach(
        outreach_id
    )

    create_outreach_event(
        outreach_message_id=outreach_id,
        event_type="REJECTED",
        event_data={
            "previous_status": message["status"],
            "new_status": rejected["status"],
        },
    )

    return rejected

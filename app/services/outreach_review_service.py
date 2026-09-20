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
    return update_outreach_draft(
        outreach_id=outreach_id,
        subject=edit.subject,
        message_body=edit.message_body,
    )


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

    return approve_outreach(
        outreach_id
    )


def reject_outreach_message(
    outreach_id: int,
) -> dict:
    return reject_outreach(
        outreach_id
    )

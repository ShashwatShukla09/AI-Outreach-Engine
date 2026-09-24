from typing import Optional

from app.repositories.outreach_outcome_repository import (
    create_outreach_outcome,
    get_outreach_outcomes,
)
from app.repositories.outreach_repository import (
    get_outreach_message,
)


ALLOWED_OUTCOMES = {
    "REPLIED",
    "POSITIVE",
    "NEGATIVE",
    "MEETING_BOOKED",
}


def record_outreach_outcome(
    outreach_message_id: int,
    outcome_type: str,
    notes: Optional[str] = None,
    occurred_at: Optional[str] = None,
) -> dict:
    outreach = get_outreach_message(
        outreach_message_id
    )

    if outreach is None:
        raise ValueError(
            "Outreach message not found."
        )

    if outreach["status"] != "SENT":
        raise ValueError(
            "Outcomes can only be recorded "
            "for SENT outreach."
        )

    normalised_outcome = (
        outcome_type
        .strip()
        .upper()
    )

    if normalised_outcome not in ALLOWED_OUTCOMES:
        raise ValueError(
            "Unsupported outreach outcome."
        )

    existing_outcomes = get_outreach_outcomes(
        outreach_message_id
    )

    existing_types = {
        outcome["outcome_type"]
        for outcome in existing_outcomes
    }

    if normalised_outcome in existing_types:
        raise ValueError(
            f"{normalised_outcome} has already "
            "been recorded for this outreach."
        )

    if (
        normalised_outcome
        in {
            "POSITIVE",
            "NEGATIVE",
            "MEETING_BOOKED",
        }
        and "REPLIED" not in existing_types
    ):
        raise ValueError(
            f"{normalised_outcome} requires "
            "REPLIED to be recorded first."
        )

    if (
        normalised_outcome == "POSITIVE"
        and "NEGATIVE" in existing_types
    ):
        raise ValueError(
            "Outreach cannot be both "
            "POSITIVE and NEGATIVE."
        )

    if (
        normalised_outcome == "NEGATIVE"
        and "POSITIVE" in existing_types
    ):
        raise ValueError(
            "Outreach cannot be both "
            "POSITIVE and NEGATIVE."
        )

    return create_outreach_outcome(
        outreach_message_id=outreach_message_id,
        outcome_type=normalised_outcome,
        notes=notes,
        occurred_at=occurred_at,
    )


def list_outreach_outcomes(
    outreach_message_id: int,
):
    outreach = get_outreach_message(
        outreach_message_id
    )

    if outreach is None:
        raise ValueError(
            "Outreach message not found."
        )

    return get_outreach_outcomes(
        outreach_message_id
    )

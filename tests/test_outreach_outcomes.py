import pytest

from app.db.database import get_connection
from app.services.outreach_outcome_service import (
    list_outreach_outcomes,
    record_outreach_outcome,
)


def create_test_outreach(
    status: str = "SENT",
) -> int:
    connection = get_connection()

    try:
        product_cursor = connection.execute(
            """
            INSERT INTO products (
                name,
                description
            )
            VALUES (?, ?)
            """,
            (
                "Outcome Test Product",
                "Product used for outreach outcome tests.",
            ),
        )

        product_id = product_cursor.lastrowid

        icp_cursor = connection.execute(
            """
            INSERT INTO icps (
                product_id,
                name,
                target_market,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                product_id,
                "Outcome Test ICP",
                "INDIA",
                "APPROVED",
            ),
        )

        icp_id = icp_cursor.lastrowid

        company_cursor = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain,
                country,
                qualification_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                icp_id,
                "Outcome Test Company",
                f"outcome-{product_id}.example",
                "India",
                "QUALIFIED",
            ),
        )

        company_id = company_cursor.lastrowid

        outreach_cursor = connection.execute(
            """
            INSERT INTO outreach_messages (
                company_id,
                channel,
                message_body,
                status
            )
            VALUES (?, 'EMAIL', ?, ?)
            """,
            (
                company_id,
                "Test outreach message.",
                status,
            ),
        )

        outreach_id = outreach_cursor.lastrowid

        connection.commit()

        return outreach_id

    finally:
        connection.close()


def test_sent_outreach_can_record_reply():
    outreach_id = create_test_outreach("SENT")

    outcome = record_outreach_outcome(
        outreach_id,
        "replied",
        notes="Prospect replied by email.",
    )

    assert outcome["outreach_message_id"] == outreach_id
    assert outcome["outcome_type"] == "REPLIED"
    assert outcome["notes"] == "Prospect replied by email."

    outcomes = list_outreach_outcomes(outreach_id)

    assert len(outcomes) == 1
    assert outcomes[0]["outcome_type"] == "REPLIED"


def test_draft_outreach_cannot_record_outcome():
    outreach_id = create_test_outreach("DRAFT")

    with pytest.raises(
        ValueError,
        match="Outcomes can only be recorded for SENT outreach",
    ):
        record_outreach_outcome(
            outreach_id,
            "REPLIED",
        )


def test_positive_requires_reply_first():
    outreach_id = create_test_outreach("SENT")

    with pytest.raises(
        ValueError,
        match="POSITIVE requires REPLIED",
    ):
        record_outreach_outcome(
            outreach_id,
            "POSITIVE",
        )


def test_meeting_requires_reply_first():
    outreach_id = create_test_outreach("SENT")

    with pytest.raises(
        ValueError,
        match="MEETING_BOOKED requires REPLIED",
    ):
        record_outreach_outcome(
            outreach_id,
            "MEETING_BOOKED",
        )


def test_duplicate_outcome_is_rejected():
    outreach_id = create_test_outreach("SENT")

    record_outreach_outcome(
        outreach_id,
        "REPLIED",
    )

    with pytest.raises(
        ValueError,
        match="REPLIED has already been recorded",
    ):
        record_outreach_outcome(
            outreach_id,
            "REPLIED",
        )


def test_positive_and_negative_are_mutually_exclusive():
    outreach_id = create_test_outreach("SENT")

    record_outreach_outcome(
        outreach_id,
        "REPLIED",
    )

    record_outreach_outcome(
        outreach_id,
        "POSITIVE",
    )

    with pytest.raises(
        ValueError,
        match="cannot be both",
    ):
        record_outreach_outcome(
            outreach_id,
            "NEGATIVE",
        )


def test_positive_then_meeting_booked():
    outreach_id = create_test_outreach("SENT")

    record_outreach_outcome(
        outreach_id,
        "REPLIED",
    )

    record_outreach_outcome(
        outreach_id,
        "POSITIVE",
    )

    record_outreach_outcome(
        outreach_id,
        "MEETING_BOOKED",
        notes="Discovery call booked.",
    )

    outcomes = list_outreach_outcomes(outreach_id)

    assert [
        outcome["outcome_type"]
        for outcome in outcomes
    ] == [
        "REPLIED",
        "POSITIVE",
        "MEETING_BOOKED",
    ]


def test_unsupported_outcome_is_rejected():
    outreach_id = create_test_outreach("SENT")

    with pytest.raises(
        ValueError,
        match="Unsupported outreach outcome",
    ):
        record_outreach_outcome(
            outreach_id,
            "OPENED",
        )


def test_missing_outreach_is_rejected():
    with pytest.raises(
        ValueError,
        match="Outreach message not found",
    ):
        record_outreach_outcome(
            999999,
            "REPLIED",
        )

from typing import Optional

from app.db.database import get_connection
from app.schemas.outreach import OutreachDraft


def create_outreach_draft(
    draft: OutreachDraft,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO outreach_messages (
                company_id,
                contact_id,
                channel,
                subject,
                message_body,
                personalisation_reason,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'DRAFT')
            """,
            (
                draft.company_id,
                draft.contact_id,
                draft.channel,
                draft.subject,
                draft.message_body,
                draft.personalisation_reason,
            ),
        )

        outreach_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_outreach_message(
    outreach_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_company_outreach_messages(
    company_id: int,
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE company_id = ?
            ORDER BY id DESC
            """,
            (company_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def update_outreach_draft(
    outreach_id: int,
    subject: Optional[str],
    message_body: str,
) -> dict:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                "Outreach message not found"
            )

        if row["status"] != "DRAFT":
            raise ValueError(
                "Only DRAFT outreach can be edited."
            )

        connection.execute(
            """
            UPDATE outreach_messages
            SET subject = ?,
                message_body = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                subject,
                message_body,
                outreach_id,
            ),
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(updated)

    finally:
        connection.close()


def approve_outreach(
    outreach_id: int,
) -> dict:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                "Outreach message not found"
            )

        if row["status"] != "DRAFT":
            raise ValueError(
                "Only DRAFT outreach can be approved."
            )

        connection.execute(
            """
            UPDATE outreach_messages
            SET status = 'APPROVED',
                approved_at = CURRENT_TIMESTAMP,
                rejected_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (outreach_id,),
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(updated)

    finally:
        connection.close()


def reject_outreach(
    outreach_id: int,
) -> dict:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                "Outreach message not found"
            )

        if row["status"] != "DRAFT":
            raise ValueError(
                "Only DRAFT outreach can be rejected."
            )

        connection.execute(
            """
            UPDATE outreach_messages
            SET status = 'REJECTED',
                rejected_at = CURRENT_TIMESTAMP,
                approved_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (outreach_id,),
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(updated)

    finally:
        connection.close()


def mark_outreach_sent(
    outreach_id: int,
) -> dict:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                "Outreach message not found"
            )

        if row["status"] != "APPROVED":
            raise ValueError(
                "Only APPROVED outreach can be sent."
            )

        connection.execute(
            """
            UPDATE outreach_messages
            SET status = 'SENT',
                sent_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (outreach_id,),
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM outreach_messages
            WHERE id = ?
            """,
            (outreach_id,),
        ).fetchone()

        return dict(updated)

    finally:
        connection.close()

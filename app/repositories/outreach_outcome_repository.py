from typing import List, Optional

from app.db.database import get_connection


def create_outreach_outcome(
    outreach_message_id: int,
    outcome_type: str,
    notes: Optional[str] = None,
    occurred_at: Optional[str] = None,
) -> dict:
    connection = get_connection()

    try:
        if occurred_at is None:
            cursor = connection.execute(
                """
                INSERT INTO outreach_outcomes (
                    outreach_message_id,
                    outcome_type,
                    notes
                )
                VALUES (?, ?, ?)
                """,
                (
                    outreach_message_id,
                    outcome_type,
                    notes,
                ),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO outreach_outcomes (
                    outreach_message_id,
                    outcome_type,
                    notes,
                    occurred_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    outreach_message_id,
                    outcome_type,
                    notes,
                    occurred_at,
                ),
            )

        outcome_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM outreach_outcomes
            WHERE id = ?
            """,
            (outcome_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_outreach_outcomes(
    outreach_message_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM outreach_outcomes
            WHERE outreach_message_id = ?
            ORDER BY occurred_at, id
            """,
            (outreach_message_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()

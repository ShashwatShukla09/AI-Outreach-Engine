import json
from typing import List, Optional

from app.db.database import get_connection


def create_outreach_event(
    outreach_message_id: int,
    event_type: str,
    event_data: Optional[dict] = None,
) -> dict:
    connection = get_connection()

    try:
        encoded_data = (
            json.dumps(event_data)
            if event_data is not None
            else None
        )

        cursor = connection.execute(
            """
            INSERT INTO outreach_events (
                outreach_message_id,
                event_type,
                event_data
            )
            VALUES (?, ?, ?)
            """,
            (
                outreach_message_id,
                event_type,
                encoded_data,
            ),
        )

        event_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM outreach_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_outreach_events(
    outreach_message_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM outreach_events
            WHERE outreach_message_id = ?
            ORDER BY id
            """,
            (outreach_message_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()

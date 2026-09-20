from typing import List

from app.db.database import get_connection
from app.schemas.signal import SignalCreate


def create_signal(
    company_id: int,
    signal: SignalCreate,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO signals (
                company_id,
                signal_type,
                title,
                description,
                source,
                source_url,
                signal_date,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                signal.signal_type,
                signal.title,
                signal.description,
                signal.source,
                signal.source_url,
                signal.signal_date,
                signal.confidence,
            ),
        )

        signal_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM signals
            WHERE id = ?
            """,
            (signal_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_company_signals(
    company_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM signals
            WHERE company_id = ?
            ORDER BY id
            """,
            (company_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def find_existing_signal(
    company_id: int,
    signal_type: str,
    title: str,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM signals
            WHERE company_id = ?
              AND signal_type = ?
              AND LOWER(title) = LOWER(?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                company_id,
                signal_type,
                title,
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()

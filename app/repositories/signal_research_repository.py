from typing import Optional

from app.db.database import get_connection


RESEARCHED_NO_SIGNALS = "RESEARCHED_NO_SIGNALS"
SIGNALS_FOUND = "SIGNALS_FOUND"


def save_signal_research(
    company_id: int,
    provider: str,
    signals_found: int,
    notes: Optional[str] = None,
) -> dict:
    """
    Record that signal research has completed.

    Zero signals means the company was researched
    but no qualifying signals were found.

    One or more signals means qualifying evidence
    was found.
    """

    status = (
        SIGNALS_FOUND
        if signals_found > 0
        else RESEARCHED_NO_SIGNALS
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO signal_research (
                company_id,
                status,
                provider,
                signals_found,
                notes
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(company_id)
            DO UPDATE SET
                status = excluded.status,
                provider = excluded.provider,
                signals_found = excluded.signals_found,
                notes = excluded.notes,
                researched_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                company_id,
                status,
                provider,
                signals_found,
                notes,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM signal_research
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_signal_research(
    company_id: int,
) -> Optional[dict]:
    """
    Return persisted research state.

    No row means signal research has not run yet.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM signal_research
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_signal_research_status(
    company_id: int,
) -> str:
    """
    Return a convenient three-state representation.

    NOT_RESEARCHED is derived from the absence
    of a database row.
    """

    research = get_signal_research(company_id)

    if research is None:
        return "NOT_RESEARCHED"

    return research["status"]

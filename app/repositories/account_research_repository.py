import json
from typing import Optional

from app.db.database import get_connection
from app.schemas.account_research import (
    AccountResearchBrief,
)


def save_account_research(
    brief: AccountResearchBrief,
) -> dict:
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM account_research
            WHERE company_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (brief.company_id,),
        ).fetchone()

        why_company = json.dumps(
            brief.why_company
        )
        why_now = json.dumps(
            brief.why_now
        )
        pain_points = json.dumps(
            brief.pain_points
        )
        relevant_evidence = json.dumps(
            brief.relevant_evidence
        )

        if existing:
            research_id = existing["id"]

            connection.execute(
                """
                UPDATE account_research
                SET company_summary = ?,
                    why_company = ?,
                    why_now = ?,
                    pain_points = ?,
                    relevant_evidence = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    brief.company_summary,
                    why_company,
                    why_now,
                    pain_points,
                    relevant_evidence,
                    research_id,
                ),
            )

        else:
            cursor = connection.execute(
                """
                INSERT INTO account_research (
                    company_id,
                    company_summary,
                    why_company,
                    why_now,
                    pain_points,
                    relevant_evidence
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    brief.company_id,
                    brief.company_summary,
                    why_company,
                    why_now,
                    pain_points,
                    relevant_evidence,
                ),
            )

            research_id = cursor.lastrowid

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM account_research
            WHERE id = ?
            """,
            (research_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_account_research(
    company_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM account_research
            WHERE company_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()

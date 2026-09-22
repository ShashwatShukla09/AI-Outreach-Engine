import json
from typing import Optional

from app.db.database import get_connection


def save_company_relevance_assessment(
    company_id: int,
    relevance_score: int,
    priority: str,
    evidence: dict,
) -> dict:
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO company_relevance_assessments (
                company_id,
                relevance_score,
                priority,
                evidence_json
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(company_id)
            DO UPDATE SET
                relevance_score = excluded.relevance_score,
                priority = excluded.priority,
                evidence_json = excluded.evidence_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                company_id,
                relevance_score,
                priority,
                json.dumps(evidence),
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM company_relevance_assessments
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_company_relevance_assessment(
    company_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM company_relevance_assessments
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["evidence"] = json.loads(
            result.pop("evidence_json")
        )

        return result

    finally:
        connection.close()

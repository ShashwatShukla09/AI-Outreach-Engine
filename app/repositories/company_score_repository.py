import json
from typing import List, Optional

from app.db.database import get_connection
from app.schemas.scoring import CompanyScoreResult


def save_company_score(
    result: CompanyScoreResult,
) -> dict:
    component_scores = {
        component.name: component.score
        for component in result.components
    }

    explanation = {
        component.name: {
            "score": component.score,
            "max_score": component.max_score,
            "explanation": component.explanation,
        }
        for component in result.components
    }

    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM company_scores
            WHERE company_id = ?
            """,
            (result.company_id,),
        ).fetchone()

        values = (
            component_scores.get("industry", 0),
            component_scores.get("company_size", 0),
            component_scores.get("geography", 0),
            component_scores.get("business_model", 0),
            component_scores.get("buyer_relevance", 0),
            result.intent_score,
            result.data_confidence_score,
            result.total_score,
            result.priority,
            json.dumps(explanation),
        )

        if existing:
            connection.execute(
                """
                UPDATE company_scores
                SET industry_score = ?,
                    company_size_score = ?,
                    geography_score = ?,
                    business_model_score = ?,
                    buyer_relevance_score = ?,
                    intent_score = ?,
                    data_confidence_score = ?,
                    total_score = ?,
                    priority = ?,
                    score_explanation = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = ?
                """,
                values + (result.company_id,),
            )

        else:
            connection.execute(
                """
                INSERT INTO company_scores (
                    company_id,
                    industry_score,
                    company_size_score,
                    geography_score,
                    business_model_score,
                    buyer_relevance_score,
                    intent_score,
                    data_confidence_score,
                    total_score,
                    priority,
                    score_explanation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.company_id,
                    *values,
                ),
            )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM company_scores
            WHERE company_id = ?
            """,
            (result.company_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_company_score(
    company_id: int,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM company_scores
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_ranked_company_scores(
    icp_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                cs.*,
                c.name AS company_name,
                c.domain,
                c.country,
                c.industry
            FROM company_scores AS cs
            JOIN companies AS c
              ON c.id = cs.company_id
            WHERE c.icp_id = ?
            ORDER BY
                cs.total_score DESC,
                cs.data_confidence_score DESC,
                c.name ASC
            """,
            (icp_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()

import json
from typing import List

from app.db.database import get_connection
from app.schemas.icp import ICPDefinition


def create_icp(
    product_id: int,
    icp: ICPDefinition,
) -> dict:
    connection = get_connection()

    try:
        notes_data = {
            "pain_points": icp.pain_points,
            "segment_rationale": icp.segment_rationale,
            "buyer_rationale": icp.buyer_rationale,
            "assumptions": icp.assumptions,
        }

        cursor = connection.execute(
            """
            INSERT INTO icps (
                product_id,
                name,
                industries,
                company_size_min,
                company_size_max,
                target_market,
                target_countries,
                business_models,
                buyer_categories,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                icp.name,
                json.dumps(icp.industries),
                icp.company_size_min,
                icp.company_size_max,
                icp.target_market,
                json.dumps(icp.target_countries),
                json.dumps(icp.business_models),
                json.dumps(icp.buyer_categories),
                json.dumps(notes_data),
            ),
        )

        icp_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM icps
            WHERE id = ?
            """,
            (icp_id,),
        ).fetchone()

        return _deserialize_icp(dict(row))

    finally:
        connection.close()


def get_icps_for_product(
    product_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM icps
            WHERE product_id = ?
            ORDER BY id
            """,
            (product_id,),
        ).fetchall()

        return [
            _deserialize_icp(dict(row))
            for row in rows
        ]

    finally:
        connection.close()


def _deserialize_icp(row: dict) -> dict:
    notes_data = json.loads(
        row["notes"] or "{}"
    )

    return {
        "id": row["id"],
        "product_id": row["product_id"],
        "name": row["name"],
        "industries": json.loads(
            row["industries"] or "[]"
        ),
        "company_size_min": row["company_size_min"],
        "company_size_max": row["company_size_max"],
        "target_market": row["target_market"],
        "target_countries": json.loads(
            row["target_countries"] or "[]"
        ),
        "business_models": json.loads(
            row["business_models"] or "[]"
        ),
        "buyer_categories": json.loads(
            row["buyer_categories"] or "[]"
        ),
        "pain_points": notes_data.get(
            "pain_points",
            [],
        ),
        "segment_rationale": notes_data.get(
            "segment_rationale",
            "",
        ),
        "buyer_rationale": notes_data.get(
            "buyer_rationale",
            "",
        ),
        "assumptions": notes_data.get(
            "assumptions",
            [],
        ),
        "status": row["status"],
        "reviewed_at": row["reviewed_at"],
        "created_at": row["created_at"],

    }


def get_icp(icp_id: int):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM icps
            WHERE id = ?
            """,
            (icp_id,),
        ).fetchone()

        if row is None:
            return None

        return _deserialize_icp(dict(row))

    finally:
        connection.close()


def update_icp_status(
    icp_id: int,
    status: str,
):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE icps
            SET
                status = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                icp_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return get_icp(icp_id)


def update_icp(
    icp_id: int,
    updates: dict,
):
    existing = get_icp(icp_id)

    if existing is None:
        return None

    editable_fields = {
        "name",
        "industries",
        "company_size_min",
        "company_size_max",
        "target_countries",
        "business_models",
        "buyer_categories",
        "pain_points",
        "segment_rationale",
        "buyer_rationale",
        "assumptions",
    }

    updated = dict(existing)

    for key, value in updates.items():
        if key in editable_fields:
            updated[key] = value

    if (
        updated["company_size_min"]
        > updated["company_size_max"]
    ):
        raise ValueError(
            "Minimum company size cannot exceed maximum company size."
        )

    notes_data = {
        "pain_points": updated["pain_points"],
        "segment_rationale": updated["segment_rationale"],
        "buyer_rationale": updated["buyer_rationale"],
        "assumptions": updated["assumptions"],
    }

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE icps
            SET
                name = ?,
                industries = ?,
                company_size_min = ?,
                company_size_max = ?,
                target_countries = ?,
                business_models = ?,
                buyer_categories = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                updated["name"],
                json.dumps(updated["industries"]),
                updated["company_size_min"],
                updated["company_size_max"],
                json.dumps(updated["target_countries"]),
                json.dumps(updated["business_models"]),
                json.dumps(updated["buyer_categories"]),
                json.dumps(notes_data),
                icp_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return get_icp(icp_id)

from typing import List, Optional

from app.db.database import get_connection


def find_pending_enrichment_job(
    company_id: int,
    provider: str,
    enrichment_type: str,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM enrichment_jobs
            WHERE company_id = ?
              AND provider = ?
              AND enrichment_type = ?
              AND status = 'PENDING'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                company_id,
                provider,
                enrichment_type,
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def create_enrichment_job(
    company_id: int,
    provider: str,
    enrichment_type: str,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO enrichment_jobs (
                company_id,
                provider,
                enrichment_type,
                status
            )
            VALUES (?, ?, ?, 'PENDING')
            """,
            (
                company_id,
                provider,
                enrichment_type,
            ),
        )

        job_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM enrichment_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_pending_enrichment_jobs() -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM enrichment_jobs
            WHERE status = 'PENDING'
            ORDER BY id
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def complete_enrichment_jobs(
    company_id: int,
    provider: str,
    enrichment_types: List[str],
) -> None:
    if not enrichment_types:
        return

    connection = get_connection()

    try:
        for enrichment_type in enrichment_types:
            connection.execute(
                """
                UPDATE enrichment_jobs
                SET status = 'COMPLETED',
                    completed_at = CURRENT_TIMESTAMP
                WHERE company_id = ?
                  AND provider = ?
                  AND enrichment_type = ?
                  AND status = 'PENDING'
                """,
                (
                    company_id,
                    provider,
                    enrichment_type,
                ),
            )

        connection.commit()

    finally:
        connection.close()

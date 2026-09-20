from typing import List, Optional

from app.db.database import get_connection
from app.schemas.contact import ContactCandidate


def find_existing_contact(
    company_id: int,
    email: Optional[str],
    first_name: str,
    last_name: str,
    job_title: str,
) -> Optional[dict]:
    connection = get_connection()

    try:
        if email:
            row = connection.execute(
                """
                SELECT *
                FROM contacts
                WHERE company_id = ?
                  AND LOWER(email) = LOWER(?)
                LIMIT 1
                """,
                (
                    company_id,
                    email,
                ),
            ).fetchone()

            if row:
                return dict(row)

        row = connection.execute(
            """
            SELECT *
            FROM contacts
            WHERE company_id = ?
              AND LOWER(first_name) = LOWER(?)
              AND LOWER(last_name) = LOWER(?)
              AND LOWER(job_title) = LOWER(?)
            LIMIT 1
            """,
            (
                company_id,
                first_name,
                last_name,
                job_title,
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def create_contact(
    company_id: int,
    contact: ContactCandidate,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO contacts (
                company_id,
                first_name,
                last_name,
                job_title,
                email,
                linkedin_url,
                enrichment_provider,
                enrichment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                contact.first_name,
                contact.last_name,
                contact.job_title,
                contact.email,
                contact.linkedin_url,
                contact.enrichment_provider,
                "ENRICHED",
            ),
        )

        contact_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_company_contacts(
    company_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM contacts
            WHERE company_id = ?
            ORDER BY
                relevance_score DESC,
                id ASC
            """,
            (company_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def update_contact_relevance(
    contact_id: int,
    buyer_category: Optional[str],
    relevance_score: int,
    relevance_reason: str,
) -> dict:
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE contacts
            SET buyer_category = ?,
                relevance_score = ?,
                relevance_reason = ?
            WHERE id = ?
            """,
            (
                buyer_category,
                relevance_score,
                relevance_reason,
                contact_id,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()

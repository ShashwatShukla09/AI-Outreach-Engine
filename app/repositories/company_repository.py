from typing import List, Optional

from app.db.database import get_connection
from app.schemas.company import CompanyCandidate


def find_company_by_domain(
    icp_id: int,
    domain: str,
) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE icp_id = ?
              AND LOWER(domain) = LOWER(?)
            """,
            (icp_id, domain),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def create_company(
    icp_id: int,
    market: str,
    company: CompanyCandidate,
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO companies (
                icp_id,
                name,
                domain,
                country,
                market,
                industry,
                employee_count,
                business_model,
                description,
                linkedin_url,
                source,
                source_url,
                qualification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                icp_id,
                company.name.strip(),
                company.domain.strip()
                if company.domain
                else None,
                company.country,
                market,
                company.industry,
                company.employee_count,
                company.business_model,
                company.description,
                company.linkedin_url,
                company.source,
                company.source_url,
                "UNREVIEWED",
            ),
        )

        company_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_companies_for_icp(
    icp_id: int,
) -> List[dict]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE icp_id = ?
            ORDER BY id
            """,
            (icp_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def update_company_fields(
    company_id: int,
    fields: dict,
) -> dict:
    allowed_fields = {
        "country",
        "industry",
        "employee_count",
        "business_model",
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        row = get_company_by_id(company_id)

        if row is None:
            raise ValueError("Company not found")

        return row

    assignments = ", ".join(
        f"{field} = ?"
        for field in updates
    )

    values = list(updates.values())
    values.append(company_id)

    connection = get_connection()

    try:
        connection.execute(
            f"""
            UPDATE companies
            SET {assignments}
            WHERE id = ?
            """,
            values,
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        if row is None:
            raise ValueError("Company not found")

        return dict(row)

    finally:
        connection.close()


def get_company_by_id(
    company_id: int,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None

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

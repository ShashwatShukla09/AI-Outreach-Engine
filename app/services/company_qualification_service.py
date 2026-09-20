from typing import List

from app.db.database import get_connection
from app.repositories.icp_repository import get_icp
from app.schemas.icp import ICPResponse
from app.schemas.qualification import QualificationResult
from app.services.enrichment_service import (
    queue_missing_company_data,
)

def get_company(company_id: int):
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


def update_qualification_status(
    company_id: int,
    status: str,
) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE companies
            SET qualification_status = ?
            WHERE id = ?
            """,
            (status, company_id),
        )

        connection.commit()

    finally:
        connection.close()


def normalise(value: str) -> str:
    return value.strip().lower()


def matches_any(
    value: str,
    allowed_values: List[str],
) -> bool:
    normalised_value = normalise(value)

    return any(
        normalised_value == normalise(allowed)
        for allowed in allowed_values
    )


def qualify_company(
    company_id: int,
) -> QualificationResult:
    company = get_company(company_id)

    if company is None:
        raise ValueError("Company not found")

    icp_data = get_icp(company["icp_id"])

    if icp_data is None:
        raise ValueError("ICP not found")

    icp = ICPResponse(**icp_data)

    if icp.status != "APPROVED":
        raise ValueError(
            "Qualification requires an APPROVED ICP."
        )

    reasons = []
    missing_fields = []
    hard_failures = []

    # Geography
    if not company["country"]:
        missing_fields.append("country")

    elif not matches_any(
        company["country"],
        icp.target_countries,
    ):
        hard_failures.append(
            "Company country is outside the ICP target countries."
        )

    else:
        reasons.append(
            "Company country matches the ICP."
        )

    # Industry
    if not company["industry"]:
        missing_fields.append("industry")

    elif not matches_any(
        company["industry"],
        icp.industries,
    ):
        hard_failures.append(
            "Company industry does not match the ICP."
        )

    else:
        reasons.append(
            "Company industry matches the ICP."
        )

    # Company size
    if company["employee_count"] is None:
        missing_fields.append("employee_count")

    elif not (
        icp.company_size_min
        <= company["employee_count"]
        <= icp.company_size_max
    ):
        hard_failures.append(
            "Company size is outside the ICP range."
        )

    else:
        reasons.append(
            "Company size is within the ICP range."
        )

    # Business model
    if not company["business_model"]:
        missing_fields.append("business_model")

    elif not matches_any(
        company["business_model"],
        icp.business_models,
    ):
        hard_failures.append(
            "Company business model does not match the ICP."
        )

    else:
        reasons.append(
            "Company business model matches the ICP."
        )

    if hard_failures:
        status = "DISQUALIFIED"
        reasons.extend(hard_failures)

    elif missing_fields:
        status = "NEEDS_REVIEW"
    else:
        status = "QUALIFIED"

    queue_missing_company_data(
        company_id=company_id,
        missing_fields=missing_fields,
        provider="public",
    )

    update_qualification_status(
        company_id=company_id,
        status=status,
    )

    return QualificationResult(
        company_id=company_id,
        status=status,
        reasons=reasons,
        missing_fields=missing_fields,
    )


def qualify_companies_for_icp(
    icp_id: int,
) -> List[QualificationResult]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE icp_id = ?
            ORDER BY id
            """,
            (icp_id,),
        ).fetchall()

    finally:
        connection.close()

    return [
        qualify_company(row["id"])
        for row in rows
    ]

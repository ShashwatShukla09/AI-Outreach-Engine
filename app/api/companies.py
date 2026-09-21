from fastapi import APIRouter, HTTPException

from app.db.database import get_connection
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.repositories.contact_repository import (
    get_company_contacts,
)
from app.repositories.enrichment_repository import (
    get_company_enrichment_jobs,
)
from app.repositories.signal_repository import (
    get_company_signals,
)


router = APIRouter(
    prefix="/api/companies",
    tags=["companies"],
)


def get_company_outreach_status(
    company_id: int,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                status,
                subject,
                approved_at,
                rejected_at,
                sent_at
            FROM outreach_messages
            WHERE company_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def build_company_intelligence(company: dict):
    company_id = company["id"]

    score = get_company_score(company_id)
    signals = get_company_signals(company_id)
    contacts = get_company_contacts(company_id)

    primary_buyer = contacts[0] if contacts else None

    outreach = get_company_outreach_status(
        company_id
    )

    enrichment_jobs = get_company_enrichment_jobs(
        company_id
    )

    return {
        "company": company,
        "score": score,
        "signals": signals,
        "primary_buyer": primary_buyer,
        "contacts_count": len(contacts),
        "outreach": outreach,
        "enrichment_jobs": enrichment_jobs,
    }


@router.get("")
def list_companies():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM companies
            ORDER BY id
            """
        ).fetchall()

        companies = [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()

    return {
        "count": len(companies),
        "companies": [
            build_company_intelligence(company)
            for company in companies
        ],
    }


@router.get("/{company_id}")
def get_company_intelligence(
    company_id: int,
):
    company = get_company_by_id(company_id)

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return build_company_intelligence(company)

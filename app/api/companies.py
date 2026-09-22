from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.db.database import get_connection
from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.repositories.company_relevance_repository import (
    get_company_relevance_assessment,
)
from app.repositories.contact_repository import (
    get_company_contacts,
)
from app.services.buyer_ranking_service import (
    rank_company_buyers,
)
from app.repositories.enrichment_repository import (
    get_company_enrichment_jobs,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.repositories.signal_research_repository import (
    get_signal_research,
)
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.workflows.company_intelligence_workflow import (
    process_company_batch,
)


class CompanyDiscoveryRequest(BaseModel):
    icp_id: int = Field(..., ge=1)
    limit: int = Field(default=100, ge=1, le=1000)


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
    relevance = get_company_relevance_assessment(
        company_id
    )
    signals = get_company_signals(company_id)

    signal_research = get_signal_research(
        company_id
    )

    if signal_research is None:
        signal_research = {
            "status": "NOT_RESEARCHED",
            "provider": None,
            "signals_found": 0,
            "notes": None,
            "researched_at": None,
            "updated_at": None,
        }

    contacts = get_company_contacts(company_id)

    ranked_buyers = rank_company_buyers(
        contacts
    )

    primary_buyer = (
        ranked_buyers[0]
        if ranked_buyers
        and ranked_buyers[0][
            "buyer_rank_score"
        ] > 0
        else None
    )

    outreach = get_company_outreach_status(
        company_id
    )

    enrichment_jobs = get_company_enrichment_jobs(
        company_id
    )

    return {
        "company": company,
        "score": score,
        "relevance": relevance,
        "signals": signals,
        "signal_research": signal_research,
        "primary_buyer": primary_buyer,
        "ranked_buyers": ranked_buyers,
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


@router.post(
    "/discover",
    status_code=status.HTTP_201_CREATED,
)
def discover_companies(
    request: CompanyDiscoveryRequest,
):
    provider = MockCompanyDiscoveryProvider()

    try:
        companies = discover_and_save_companies(
            icp_id=request.icp_id,
            provider=provider,
            limit=request.limit,
        )

    except ValueError as exc:
        message = str(exc)

        if message == "ICP not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc

    processing = process_company_batch(
        company_ids=[
            company.id
            for company in companies
        ],
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
    )

    return {
        "discovered_count": len(companies),
        "companies": [
            company.model_dump()
            for company in companies
        ],
        "processing": processing,
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

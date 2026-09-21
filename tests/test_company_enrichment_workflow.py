from app.db.database import get_connection
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.repositories.enrichment_repository import (
    get_pending_enrichment_jobs,
)
from app.workflows.company_enrichment_workflow import (
    qualify_enrich_requalify,
)
from tests.test_enrichment_queue import (
    create_real_company,
)


def get_company_enrichment_jobs(
    company_id: int,
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM enrichment_jobs
            WHERE company_id = ?
            ORDER BY id
            """,
            (company_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def test_company_can_be_enriched_and_requalified():
    company = create_real_company()

    result = qualify_enrich_requalify(
        company_id=company.id,
        provider=MockCompanyEnrichmentProvider(),
        provider_name="mock",
    )

    assert (
        result["initial_qualification"].status
        == "NEEDS_REVIEW"
    )

    assert result["enriched"] is True

    assert (
        result["updated_company"]["employee_count"]
        == 90
    )

    assert (
        result["updated_company"]["business_model"]
        == "Marketplace"
    )

    assert (
        result["final_qualification"].status
        == "QUALIFIED"
    )

    jobs = get_company_enrichment_jobs(
        company.id
    )

    assert len(jobs) == 2

    assert {
        job["enrichment_type"]
        for job in jobs
    } == {
        "employee_count",
        "business_model",
    }

    assert all(
        job["provider"] == "mock"
        for job in jobs
    )

    assert all(
        job["status"] == "COMPLETED"
        for job in jobs
    )

    assert all(
        job["completed_at"] is not None
        for job in jobs
    )

    pending_jobs = get_pending_enrichment_jobs()

    assert not any(
        job["company_id"] == company.id
        for job in pending_jobs
    )

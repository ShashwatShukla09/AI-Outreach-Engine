from app.repositories.outreach_repository import (
    create_outreach_draft,
)
from app.services.outreach_generation_service import (
    generate_outreach_draft,
)


def create_company_outreach(
    company_id: int,
) -> dict:
    draft = generate_outreach_draft(
        company_id
    )

    saved = create_outreach_draft(
        draft
    )

    return {
        "draft": draft,
        "saved": saved,
    }

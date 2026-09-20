import json

from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.account_research_repository import (
    get_account_research,
    save_account_research,
)
from app.services.account_research_service import (
    build_account_research,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.workflows.buyer_intelligence_workflow import (
    build_buyer_intelligence,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_intelligent_company():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(
        nova.id
    )

    assert qualification.status == "QUALIFIED"

    build_buyer_intelligence(
        company_id=nova.id,
        contact_provider=MockContactProvider(),
        signal_provider=MockSignalProvider(),
    )

    return nova


def test_account_research_uses_verified_data():
    company = prepare_intelligent_company()

    brief = build_account_research(
        company.id
    )

    assert brief.company_id == company.id

    assert "NovaCart India" in (
        brief.company_summary
    )

    assert "E-commerce" in (
        brief.company_summary
    )

    assert len(brief.why_company) == 4
    assert len(brief.why_now) == 2

    assert brief.primary_buyer is not None

    assert (
        "Head of Support"
        in brief.primary_buyer
        or "COO"
        in brief.primary_buyer
    )


def test_account_research_builds_pain_hypothesis():
    company = prepare_intelligent_company()

    brief = build_account_research(
        company.id
    )

    assert any(
        "customer-service workload" in item
        for item in brief.pain_points
    )


def test_account_research_is_persisted():
    company = prepare_intelligent_company()

    brief = build_account_research(
        company.id
    )

    save_account_research(brief)

    saved = get_account_research(
        company.id
    )

    assert saved is not None

    why_company = json.loads(
        saved["why_company"]
    )

    why_now = json.loads(
        saved["why_now"]
    )

    assert len(why_company) == 4
    assert len(why_now) == 2


def test_account_research_updates_instead_of_duplicates():
    company = prepare_intelligent_company()

    brief = build_account_research(
        company.id
    )

    first = save_account_research(
        brief
    )

    second = save_account_research(
        brief
    )

    assert first["id"] == second["id"]

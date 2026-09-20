import json

from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.account_research_repository import (
    get_account_research,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.workflows.account_intelligence_workflow import (
    build_account_intelligence,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_novacart():
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

    return nova


def test_complete_account_intelligence_workflow():
    company = prepare_novacart()

    result = build_account_intelligence(
        company_id=company.id,
        contact_provider=MockContactProvider(),
        signal_provider=MockSignalProvider(),
    )

    assert result["score"].total_score == 90
    assert result["score"].priority == "HIGH"

    assert len(result["contacts"]) == 3
    assert len(result["signals"]) == 2

    assert result["primary_buyer"] is not None

    brief = result["research_brief"]

    assert "NovaCart India" in (
        brief.company_summary
    )

    assert len(brief.why_company) == 4
    assert len(brief.why_now) == 2

    saved = get_account_research(
        company.id
    )

    assert saved is not None

    assert len(
        json.loads(saved["why_company"])
    ) == 4

    assert len(
        json.loads(saved["why_now"])
    ) == 2


def test_account_intelligence_rerun_is_safe():
    company = prepare_novacart()

    contact_provider = MockContactProvider()
    signal_provider = MockSignalProvider()

    first = build_account_intelligence(
        company_id=company.id,
        contact_provider=contact_provider,
        signal_provider=signal_provider,
    )

    second = build_account_intelligence(
        company_id=company.id,
        contact_provider=contact_provider,
        signal_provider=signal_provider,
    )

    assert (
        first["saved_research"]["id"]
        == second["saved_research"]["id"]
    )

    assert len(second["contacts"]) == 3
    assert len(second["signals"]) == 2

    assert second["score"].total_score == 90

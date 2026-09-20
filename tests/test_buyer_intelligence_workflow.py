from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
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


def test_complete_buyer_intelligence_workflow():
    company = prepare_novacart()

    result = build_buyer_intelligence(
        company_id=company.id,
        contact_provider=MockContactProvider(),
        signal_provider=MockSignalProvider(),
    )

    assert len(result["contacts"]) == 3
    assert len(result["signals"]) == 2

    assert result["primary_buyer"] is not None

    assert (
        result["primary_buyer"][
            "relevance_score"
        ]
        == 10
    )

    assert result["score"].icp_fit_score == 60
    assert result["score"].intent_score == 20
    assert result["score"].data_confidence_score == 10

    assert result["score"].total_score == 90
    assert result["score"].priority == "HIGH"


def test_workflow_is_idempotent():
    company = prepare_novacart()

    contact_provider = MockContactProvider()
    signal_provider = MockSignalProvider()

    first = build_buyer_intelligence(
        company_id=company.id,
        contact_provider=contact_provider,
        signal_provider=signal_provider,
    )

    second = build_buyer_intelligence(
        company_id=company.id,
        contact_provider=contact_provider,
        signal_provider=signal_provider,
    )

    assert len(first["new_contacts"]) == 3
    assert len(first["new_signals"]) == 2

    assert len(second["new_contacts"]) == 0
    assert len(second["new_signals"]) == 0

    assert len(second["contacts"]) == 3
    assert len(second["signals"]) == 2

    assert second["score"].total_score == 90
    assert second["score"].priority == "HIGH"

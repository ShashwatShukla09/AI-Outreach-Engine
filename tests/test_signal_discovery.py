from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.signal_discovery_service import (
    discover_and_save_signals,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def get_novacart():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(nova.id)

    assert qualification.status == "QUALIFIED"

    return nova


def test_signal_provider_discovers_signals():
    company = get_novacart()

    provider = MockSignalProvider()

    signals = provider.discover_signals(
        {
            "id": company.id,
            "name": company.name,
        }
    )

    assert len(signals) == 2

    signal_types = {
        signal.signal_type
        for signal in signals
    }

    assert signal_types == {
        "FUNDING",
        "SUPPORT_HIRING",
    }


def test_discovered_signals_are_saved():
    company = get_novacart()

    saved = discover_and_save_signals(
        company_id=company.id,
        provider=MockSignalProvider(),
    )

    assert len(saved) == 2

    database_signals = get_company_signals(
        company.id
    )

    assert len(database_signals) == 2


def test_repeated_discovery_does_not_duplicate():
    company = get_novacart()

    provider = MockSignalProvider()

    first = discover_and_save_signals(
        company_id=company.id,
        provider=provider,
    )

    second = discover_and_save_signals(
        company_id=company.id,
        provider=provider,
    )

    assert len(first) == 2
    assert len(second) == 0

    database_signals = get_company_signals(
        company.id
    )

    assert len(database_signals) == 2

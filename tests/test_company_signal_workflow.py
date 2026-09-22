from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.workflows.company_signal_workflow import (
    discover_signals_and_rescore,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_company():
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

    baseline = score_and_save_company(
        nova.id
    )

    assert baseline.total_score == 60
    assert baseline.priority == "MEDIUM"

    return nova


def test_signal_workflow_reprioritises_company():
    company = prepare_company()

    result = discover_signals_and_rescore(
        company_id=company.id,
        provider=MockSignalProvider(),
    )

    assert result["new_signal_count"] == 2

    assert result["score"].intent_score == 20
    assert result["score"].total_score == 80
    assert result["score"].priority == "HIGH"

    saved = get_company_score(
        company.id
    )

    assert saved["intent_score"] == 20
    assert saved["total_score"] == 80
    assert saved["priority"] == "HIGH"


def test_repeated_signal_workflow_is_idempotent():
    company = prepare_company()

    first = discover_signals_and_rescore(
        company_id=company.id,
        provider=MockSignalProvider(),
    )

    second = discover_signals_and_rescore(
        company_id=company.id,
        provider=MockSignalProvider(),
    )

    assert first["new_signal_count"] == 2
    assert second["new_signal_count"] == 0

    assert second["score"].intent_score == 20
    assert second["score"].total_score == 80
    assert second["score"].priority == "HIGH"


def test_repeated_signal_research_preserves_signals_found_state():
    from app.repositories.signal_research_repository import (
        get_signal_research,
    )

    company = prepare_company()

    first = discover_signals_and_rescore(
        company_id=company.id,
        provider=MockSignalProvider(),
        provider_name="mock",
    )

    second = discover_signals_and_rescore(
        company_id=company.id,
        provider=MockSignalProvider(),
        provider_name="mock",
    )

    assert first["new_signal_count"] == 2
    assert first["total_signal_count"] == 2

    assert second["new_signal_count"] == 0
    assert second["total_signal_count"] == 2

    assert (
        second["signal_research"]["status"]
        == "SIGNALS_FOUND"
    )

    assert (
        second["signal_research"]["signals_found"]
        == 2
    )

    persisted = get_signal_research(
        company.id
    )

    assert persisted is not None
    assert persisted["status"] == "SIGNALS_FOUND"
    assert persisted["signals_found"] == 2

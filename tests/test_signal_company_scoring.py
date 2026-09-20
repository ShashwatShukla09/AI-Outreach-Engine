import json

from app.repositories.company_score_repository import (
    get_company_score,
)
from app.repositories.signal_repository import (
    create_signal,
)
from app.schemas.signal import SignalCreate
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def test_signals_increase_company_score():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualify_company(nova.id)

    baseline = score_and_save_company(
        nova.id
    )

    assert baseline.total_score == 60
    assert baseline.priority == "MEDIUM"

    create_signal(
        company_id=nova.id,
        signal=SignalCreate(
            signal_type="FUNDING",
            title="Recent funding round",
            source="mock",
            confidence="HIGH",
        ),
    )

    create_signal(
        company_id=nova.id,
        signal=SignalCreate(
            signal_type="SUPPORT_HIRING",
            title="Hiring customer support staff",
            source="mock",
            confidence="HIGH",
        ),
    )

    rescored = score_and_save_company(
        nova.id
    )

    assert rescored.intent_score == 20
    assert rescored.total_score == 80
    assert rescored.priority == "HIGH"


def test_signal_explanation_is_persisted():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualify_company(nova.id)

    create_signal(
        company_id=nova.id,
        signal=SignalCreate(
            signal_type="FUNDING",
            title="Recent funding round",
            source="mock",
            confidence="HIGH",
        ),
    )

    score_and_save_company(nova.id)

    saved = get_company_score(nova.id)

    explanation = json.loads(
        saved["score_explanation"]
    )

    assert "intent" in explanation
    assert explanation["intent"]["score"] == 10
    assert "FUNDING: +10" in (
        explanation["intent"]["explanation"]
    )

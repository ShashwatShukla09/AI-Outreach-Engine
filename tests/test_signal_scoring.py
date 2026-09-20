from app.repositories.signal_repository import (
    create_signal,
)
from app.schemas.signal import SignalCreate
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.signal_scoring_service import (
    calculate_intent_score,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def get_qualified_company():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    result = qualify_company(nova.id)

    assert result.status == "QUALIFIED"

    return nova


def test_high_confidence_signal_adds_full_weight():
    company = get_qualified_company()

    create_signal(
        company_id=company.id,
        signal=SignalCreate(
            signal_type="FUNDING",
            title="Company raised a new funding round",
            description="Recent funding event.",
            source="mock",
            confidence="HIGH",
        ),
    )

    score = calculate_intent_score(
        company.id
    )

    assert score == 10


def test_confidence_changes_signal_weight():
    company = get_qualified_company()

    create_signal(
        company_id=company.id,
        signal=SignalCreate(
            signal_type="CUSTOMER_PAIN",
            title="Customer complaints increasing",
            description=(
                "Public customer complaints indicate "
                "support pressure."
            ),
            source="mock",
            confidence="MEDIUM",
        ),
    )

    score = calculate_intent_score(
        company.id
    )

    assert score == 6


def test_intent_score_is_capped_at_thirty():
    company = get_qualified_company()

    signals = [
        ("FUNDING", "Funding event"),
        ("SUPPORT_HIRING", "Support hiring"),
        ("CUSTOMER_PAIN", "Customer pain"),
        ("TEAM_GROWTH", "Team growth"),
        ("PRODUCT_LAUNCH", "Product launch"),
    ]

    for signal_type, title in signals:
        create_signal(
            company_id=company.id,
            signal=SignalCreate(
                signal_type=signal_type,
                title=title,
                source="mock",
                confidence="HIGH",
            ),
        )

    score = calculate_intent_score(
        company.id
    )

    assert score == 30

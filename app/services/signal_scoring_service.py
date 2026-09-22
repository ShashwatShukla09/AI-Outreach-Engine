from datetime import date, datetime
from typing import Dict, List, Optional

from app.repositories.signal_repository import (
    get_company_signals,
)


SIGNAL_WEIGHTS: Dict[str, int] = {
    # Clearlyy-relevant operational buying signals.
    "FRONTLINE_HIRING": 10,
    "FACILITY_EXPANSION": 10,
    "WORKFORCE_TRAINING": 10,
    "OPERATIONAL_EXPANSION": 8,
    "SAFETY_COMPLIANCE": 7,

    # Legacy/demo signals retained for backward
    # compatibility with existing test/demo data.
    "SUPPORT_HIRING": 10,
    "FUNDING": 10,
    "CUSTOMER_PAIN": 8,
    "TEAM_GROWTH": 7,
    "PRODUCT_LAUNCH": 5,
}


CONFIDENCE_MULTIPLIERS: Dict[str, float] = {
    "HIGH": 1.0,
    "MEDIUM": 0.7,
    "LOW": 0.4,
}


def parse_signal_date(
    value: Optional[str],
) -> Optional[date]:
    """
    Parse supported signal dates.

    Real evidence may provide either:
    YYYY-MM-DD
    YYYY-MM

    Month-only dates are represented using the
    first day of that month. This is deterministic
    and avoids inventing a precise event day.
    """

    if not value:
        return None

    cleaned = value.strip()

    formats = (
        "%Y-%m-%d",
        "%Y-%m",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                cleaned,
                date_format,
            ).date()
        except ValueError:
            continue

    return None


def get_recency_multiplier(
    signal_date: Optional[str],
    as_of_date: Optional[date] = None,
) -> float:
    """
    Return deterministic signal recency weight.

    Undated signals retain full weight for
    backward compatibility with legacy/demo data.

    Real CSV evidence requires a signal date.
    """

    parsed_date = parse_signal_date(
        signal_date
    )

    if parsed_date is None:
        return 1.0

    reference_date = (
        as_of_date
        if as_of_date is not None
        else date.today()
    )

    age_days = (
        reference_date - parsed_date
    ).days

    # Future-dated evidence should not receive
    # more than full weight.
    if age_days <= 90:
        return 1.0

    if age_days <= 180:
        return 0.8

    if age_days <= 365:
        return 0.5

    if age_days <= 730:
        return 0.25

    return 0.0


def get_intent_score_details(
    company_id: int,
) -> dict:
    signals = get_company_signals(company_id)

    raw_score = 0
    contributions: List[dict] = []

    for signal in signals:
        base_score = SIGNAL_WEIGHTS.get(
            signal["signal_type"],
            0,
        )

        confidence_multiplier = (
            CONFIDENCE_MULTIPLIERS.get(
                signal["confidence"],
                0.0,
            )
        )

        recency_multiplier = (
            get_recency_multiplier(
                signal["signal_date"]
            )
        )

        weighted_score = round(
            base_score
            * confidence_multiplier
            * recency_multiplier
        )

        raw_score += weighted_score

        contributions.append(
            {
                "signal_id": signal["id"],
                "signal_type": signal["signal_type"],
                "title": signal["title"],
                "confidence": signal["confidence"],
                "signal_date": signal["signal_date"],
                "base_score": base_score,
                "confidence_multiplier": (
                    confidence_multiplier
                ),
                "recency_multiplier": (
                    recency_multiplier
                ),
                "weighted_score": weighted_score,
            }
        )

    return {
        "score": min(raw_score, 30),
        "raw_score": raw_score,
        "capped": raw_score > 30,
        "contributions": contributions,
    }


def calculate_intent_score(
    company_id: int,
) -> int:
    details = get_intent_score_details(
        company_id
    )

    return details["score"]

from typing import Dict, List

from app.repositories.signal_repository import (
    get_company_signals,
)


SIGNAL_WEIGHTS: Dict[str, int] = {
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

        weighted_score = round(
            base_score
            * confidence_multiplier
        )

        raw_score += weighted_score

        contributions.append(
            {
                "signal_id": signal["id"],
                "signal_type": signal["signal_type"],
                "title": signal["title"],
                "confidence": signal["confidence"],
                "base_score": base_score,
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

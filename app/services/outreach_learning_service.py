from typing import List

from app.services.outreach_performance_service import (
    get_outreach_performance,
)


DIMENSIONS = (
    ("by_industry", "industry"),
    ("by_buyer_category", "buyer category"),
    ("by_business_model", "business model"),
    ("by_signal_type", "signal type"),
    ("by_product", "product"),
    ("by_icp", "ICP"),
    ("by_market", "market"),
    ("by_country", "country"),
)


def _build_learning(
    dimension: str,
    metrics: dict,
) -> dict:
    segment = metrics["segment"]
    sent = metrics["sent"]
    evidence_status = metrics["evidence_status"]

    if evidence_status == "INSUFFICIENT_DATA":
        message = (
            f"{segment} has only {sent} sent outreach "
            f"sample{'s' if sent != 1 else ''}. "
            "More data is needed before drawing a conclusion."
        )

        return {
            "dimension": dimension,
            "segment": segment,
            "status": evidence_status,
            "message": message,
            "metrics": metrics,
        }

    message = (
        f"{segment} currently has a "
        f"{metrics['reply_rate']}% reply rate, "
        f"{metrics['positive_reply_rate']}% positive reply rate, "
        f"and {metrics['meeting_rate']}% meeting rate "
        f"across {sent} sent outreach messages."
    )

    return {
        "dimension": dimension,
        "segment": segment,
        "status": evidence_status,
        "message": message,
        "metrics": metrics,
    }


def get_outreach_learnings() -> List[dict]:
    performance = get_outreach_performance()

    learnings = []

    for performance_key, dimension in DIMENSIONS:
        for metrics in performance[performance_key]:
            learnings.append(
                _build_learning(
                    dimension=dimension,
                    metrics=metrics,
                )
            )

    return learnings

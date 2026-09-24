from collections import defaultdict
from typing import Dict, List

from app.repositories.outreach_performance_repository import (
    get_sent_outreach_performance_rows,
    get_sent_outreach_signal_rows,
)


def _evidence_status(sent: int) -> str:
    if sent == 0:
        return "NO_DATA"

    if sent < 5:
        return "INSUFFICIENT_DATA"

    return "EARLY_SIGNAL"


def _calculate_metrics(rows: List[dict]) -> dict:
    sent = len(rows)

    replied = sum(
        int(row["replied"])
        for row in rows
    )

    positive = sum(
        int(row["positive"])
        for row in rows
    )

    negative = sum(
        int(row["negative"])
        for row in rows
    )

    meetings_booked = sum(
        int(row["meeting_booked"])
        for row in rows
    )

    if sent:
        reply_rate = round(
            replied / sent * 100,
            1,
        )

        positive_reply_rate = round(
            positive / sent * 100,
            1,
        )

        negative_reply_rate = round(
            negative / sent * 100,
            1,
        )

        meeting_rate = round(
            meetings_booked / sent * 100,
            1,
        )

    else:
        reply_rate = 0.0
        positive_reply_rate = 0.0
        negative_reply_rate = 0.0
        meeting_rate = 0.0

    return {
        "sent": sent,
        "replied": replied,
        "positive": positive,
        "negative": negative,
        "meetings_booked": meetings_booked,
        "reply_rate": reply_rate,
        "positive_reply_rate": positive_reply_rate,
        "negative_reply_rate": negative_reply_rate,
        "meeting_rate": meeting_rate,
        "evidence_status": _evidence_status(sent),
    }


def _group_performance(
    rows: List[dict],
    field: str,
) -> List[dict]:
    grouped = defaultdict(list)

    for row in rows:
        value = row.get(field)

        if value is None:
            value = "Unknown"
        elif isinstance(value, str):
            value = value.strip() or "Unknown"

        grouped[value].append(row)

    results = []

    for value, group_rows in grouped.items():
        results.append(
            {
                "segment": value,
                **_calculate_metrics(group_rows),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            -item["sent"],
            str(item["segment"]).lower(),
        ),
    )


def get_outreach_performance() -> Dict:
    rows = get_sent_outreach_performance_rows()
    signal_rows = get_sent_outreach_signal_rows()

    return {
        "overall": _calculate_metrics(rows),
        "by_industry": _group_performance(
            rows,
            "industry",
        ),
        "by_buyer_category": _group_performance(
            rows,
            "buyer_category",
        ),
        "by_business_model": _group_performance(
            rows,
            "business_model",
        ),
        "by_signal_type": _group_performance(
            signal_rows,
            "signal_type",
        ),
    }

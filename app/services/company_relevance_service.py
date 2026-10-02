from typing import Dict, List


INDUSTRY_SIGNALS = {
    "logistics",
    "supply chain",
    "transportation",
}

FRONTLINE_SIGNALS = {
    "warehouse",
    "warehousing",
    "last mile",
    "last-mile",
    "delivery",
    "fleet",
    "driver",
    "drivers",
    "rider",
    "riders",
    "fulfilment",
    "fulfillment",
    "distribution",
}

OPERATION_SIGNALS = {
    "operations",
    "operational",
    "facility",
    "facilities",
    "hub",
    "hubs",
    "sorting",
    "distribution centre",
    "distribution center",
}

EXCLUDED_INDUSTRY_SIGNALS = {
    "airlines and aviation",
    "airport",
    "airline",
}


def _find_matches(
    text: str,
    signals: set,
) -> List[str]:
    return sorted(
        signal
        for signal in signals
        if signal in text
    )


def assess_company_relevance(
    company: dict,
) -> Dict:
    name = str(company.get("name") or "")
    industry = str(company.get("industry") or "")
    description = str(
        company.get("description") or ""
    )

    evidence_text = " ".join(
        [name, industry, description]
    ).lower()

    industry_text = industry.lower()

    industry_matches = _find_matches(
        evidence_text,
        INDUSTRY_SIGNALS,
    )

    frontline_matches = _find_matches(
        evidence_text,
        FRONTLINE_SIGNALS,
    )

    operation_matches = _find_matches(
        evidence_text,
        OPERATION_SIGNALS,
    )

    excluded_matches = _find_matches(
        industry_text,
        EXCLUDED_INDUSTRY_SIGNALS,
    )

    score = 0

    # Broad industry fit: maximum 4 points.
    score += min(
        len(industry_matches) * 2,
        4,
    )

    # Direct frontline evidence carries most weight.
    score += min(
        len(frontline_matches) * 3,
        12,
    )

    # Additional operational evidence.
    score += min(
        len(operation_matches) * 2,
        4,
    )

    # Clay discovery can contain adjacent industries such
    # as airlines and airports. Penalise those explicitly.
    if excluded_matches:
        score -= 8

    score = max(0, min(score, 20))

    # HIGH requires actual frontline evidence.
    if (
        score >= 12
        and len(frontline_matches) >= 2
        and not excluded_matches
    ):
        priority = "HIGH"

    elif (
        score >= 6
        and len(frontline_matches) >= 1
        and not excluded_matches
    ):
        priority = "MEDIUM"

    else:
        priority = "LOW"

    return {
        "company_name": company.get("name"),
        "relevance_score": score,
        "priority": priority,
        "industry_matches": industry_matches,
        "frontline_matches": frontline_matches,
        "operation_matches": operation_matches,
        "excluded_matches": excluded_matches,
        "evidence_summary": {
            "industry": industry_matches,
            "frontline": frontline_matches,
            "operations": operation_matches,
            "excluded": excluded_matches,
        },
    }

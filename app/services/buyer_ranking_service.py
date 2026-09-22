from typing import Dict, List


FUNCTION_SCORES = {
    "Learning and Development": 50,
    "Training": 50,
    "Workforce Enablement": 50,
    "Safety and Compliance": 45,
    "Operations": 40,
    "Human Resources": 35,
    "People": 35,
}


SENIORITY_SCORES = {
    "chief": 30,
    "c-level": 30,
    "senior vice president": 28,
    "svp": 28,
    "vice president": 26,
    "vp": 26,
    "head": 24,
    "director": 20,
    "general manager": 18,
    "manager": 14,
}


SPECIFIC_OWNERSHIP_TERMS = {
    "learning",
    "development",
    "training",
    "workforce",
    "capability",
    "safety",
    "compliance",
    "ehs",
    "hse",
}


def _normalise(value: str) -> str:
    return " ".join(
        value.lower()
        .replace("&", " and ")
        .replace("-", " ")
        .replace(",", " ")
        .split()
    )


def _get_seniority_score(
    job_title: str,
) -> int:
    title = _normalise(job_title)

    # Ordered deliberately so "senior vice president"
    # is detected before "vice president".
    for seniority, score in SENIORITY_SCORES.items():
        if seniority in title:
            return score

    return 0


def _get_specificity_score(
    job_title: str,
) -> int:
    title = _normalise(job_title)

    matches = [
        term
        for term in SPECIFIC_OWNERSHIP_TERMS
        if term in title.split()
    ]

    if len(matches) >= 2:
        return 20

    if len(matches) == 1:
        return 15

    if "operations" in title.split():
        return 10

    return 0


def rank_buyer(
    contact: dict,
) -> Dict:
    relevance_score = (
        contact.get("relevance_score")
        or 0
    )

    buyer_category = contact.get(
        "buyer_category"
    )

    if (
        relevance_score <= 0
        or not buyer_category
    ):
        return {
            "contact_id": contact.get("id"),
            "buyer_rank_score": 0,
            "rank_label": "NOT_RELEVANT",
            "function_score": 0,
            "seniority_score": 0,
            "specificity_score": 0,
            "ranking_reason": (
                "Contact is not an evaluated "
                "ICP-matching buyer."
            ),
        }

    function_score = FUNCTION_SCORES.get(
        buyer_category,
        0,
    )

    seniority_score = _get_seniority_score(
        contact.get("job_title") or ""
    )

    specificity_score = (
        _get_specificity_score(
            contact.get("job_title") or ""
        )
    )

    total = (
        function_score
        + seniority_score
        + specificity_score
    )

    if total >= 85:
        label = "PRIMARY"
    elif total >= 70:
        label = "SECONDARY"
    else:
        label = "RELEVANT"

    return {
        "contact_id": contact.get("id"),
        "buyer_rank_score": total,
        "rank_label": label,
        "function_score": function_score,
        "seniority_score": seniority_score,
        "specificity_score": specificity_score,
        "ranking_reason": (
            f"{buyer_category} contributes "
            f"{function_score}/50 function fit; "
            f"{contact.get('job_title')} contributes "
            f"{seniority_score}/30 seniority and "
            f"{specificity_score}/20 title specificity."
        ),
    }


def rank_company_buyers(
    contacts: List[dict],
) -> List[dict]:
    ranked = []

    for contact in contacts:
        ranking = rank_buyer(contact)

        ranked.append(
            {
                **contact,
                **ranking,
            }
        )

    return sorted(
        ranked,
        key=lambda contact: (
            contact["buyer_rank_score"],
            contact.get("relevance_score") or 0,
        ),
        reverse=True,
    )

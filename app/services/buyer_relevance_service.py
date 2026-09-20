import re
from typing import List, Optional, Tuple

from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.contact_repository import (
    get_company_contacts,
    update_contact_relevance,
)
from app.repositories.icp_repository import get_icp
from app.schemas.icp import ICPResponse


ROLE_ALIASES = {
    "founder": {
        "founder",
        "cofounder",
        "co founder",
        "chief executive officer",
        "ceo",
    },
    "coo": {
        "coo",
        "chief operating officer",
        "operations director",
    },
    "head of support": {
        "head of support",
        "head of customer support",
        "customer support head",
        "support director",
        "director of customer support",
    },
}


def normalise_title(value: str) -> str:
    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(value.split())


def canonical_role(
    title: str,
) -> str:
    normalised = normalise_title(title)

    for role, aliases in ROLE_ALIASES.items():
        if normalised in aliases:
            return role

    return normalised


def find_best_buyer_match(
    job_title: str,
    buyer_categories: List[str],
) -> Tuple[Optional[str], int, str]:
    contact_role = canonical_role(job_title)

    for buyer_category in buyer_categories:
        buyer_role = canonical_role(
            buyer_category
        )

        if contact_role == buyer_role:
            return (
                buyer_category,
                10,
                (
                    f"{job_title} matches ICP buyer "
                    f"category {buyer_category}."
                ),
            )

    return (
        None,
        0,
        (
            f"{job_title} does not match an "
            "approved ICP buyer category."
        ),
    )


def evaluate_company_buyers(
    company_id: int,
) -> List[dict]:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    icp_data = get_icp(company["icp_id"])

    if icp_data is None:
        raise ValueError("ICP not found")

    icp = ICPResponse(**icp_data)

    if icp.status != "APPROVED":
        raise ValueError(
            "Buyer evaluation requires an APPROVED ICP."
        )

    contacts = get_company_contacts(
        company_id
    )

    evaluated = []

    for contact in contacts:
        (
            buyer_category,
            relevance_score,
            relevance_reason,
        ) = find_best_buyer_match(
            job_title=contact["job_title"],
            buyer_categories=icp.buyer_categories,
        )

        updated = update_contact_relevance(
            contact_id=contact["id"],
            buyer_category=buyer_category,
            relevance_score=relevance_score,
            relevance_reason=relevance_reason,
        )

        evaluated.append(updated)

    return evaluated

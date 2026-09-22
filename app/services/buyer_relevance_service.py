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

    "operations": {
        "operations",
        "head of operations",
        "vp operations",
        "vice president operations",
        "director of operations",
        "operations director",
        "chief operations officer",
        "general manager operations",
        "operations manager",
    },

    "learning and development": {
        "learning and development",
        "learning development",
        "l and d",
        "l d",
        "head of learning and development",
        "head of learning development",
        "head learning and development",
        "head of l and d",
        "head of l d",
        "director learning and development",
        "director of learning and development",
        "learning and development director",
        "learning and development manager",
        "l and d head",
        "l and d manager",
        "l d head",
        "l d manager",
    },

    "training": {
        "training",
        "head of training",
        "training head",
        "director of training",
        "training director",
        "training manager",
    },

    "human resources": {
        "human resources",
        "hr",
        "head of human resources",
        "head of hr",
        "hr head",
        "human resources director",
        "hr director",
        "human resources manager",
        "hr manager",
        "chief human resources officer",
        "chro",
    },

    "people": {
        "people",
        "head of people",
        "people head",
        "people director",
        "director of people",
        "chief people officer",
        "cpo",
    },

    "workforce enablement": {
        "workforce enablement",
        "head of workforce enablement",
        "workforce enablement manager",
        "workforce development",
        "head of workforce development",
        "capability development",
        "head of capability development",
        "capability development manager",
    },

    "safety and compliance": {
        "safety and compliance",
        "head of safety and compliance",
        "safety head",
        "head of safety",
        "safety manager",
        "compliance head",
        "head of compliance",
        "compliance manager",
        "ehs head",
        "head of ehs",
        "ehs manager",
        "hse head",
        "head of hse",
        "hse manager",
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

        # Real-world Operations titles often contain
        # organisational qualifiers, for example:
        # "Senior Vice President, UTR Operations".
        #
        # Match those conservatively while preventing
        # unrelated functions such as Sales Operations
        # or Marketing Operations from becoming buyers.
        if buyer_role == "operations":
            blocked_operations_functions = {
                "marketing",
                "sales",
                "revenue",
                "finance",
                "financial",
                "legal",
                "people",
                "hr",
                "human resources",
            }

            has_operations = (
                "operations" in contact_role.split()
            )

            has_blocked_function = any(
                blocked in contact_role
                for blocked
                in blocked_operations_functions
            )

            seniority_signals = {
                "chief",
                "head",
                "director",
                "vice president",
                "vp",
                "general manager",
            }

            has_seniority = any(
                seniority in contact_role
                for seniority in seniority_signals
            )

            if (
                has_operations
                and has_seniority
                and not has_blocked_function
            ):
                return (
                    buyer_category,
                    10,
                    (
                        f"{job_title} is a senior "
                        "Operations role matching ICP "
                        f"buyer category {buyer_category}."
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

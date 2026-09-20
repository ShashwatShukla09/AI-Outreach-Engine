from typing import List

from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.icp_repository import get_icp
from app.schemas.icp import ICPResponse
from app.schemas.scoring import (
    CompanyScoreResult,
    ScoreComponent,
)
from app.repositories.company_score_repository import (
    save_company_score,
)
from app.services.signal_scoring_service import (
    get_intent_score_details,
)

def normalise(value: str) -> str:
    return value.strip().lower()


def matches_any(
    value: str,
    allowed_values: List[str],
) -> bool:
    normalised_value = normalise(value)

    return any(
        normalised_value == normalise(allowed)
        for allowed in allowed_values
    )


def score_company(
    company_id: int,
) -> CompanyScoreResult:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    if company["qualification_status"] != "QUALIFIED":
        raise ValueError(
            "Only QUALIFIED companies can be scored."
        )

    icp_data = get_icp(company["icp_id"])

    if icp_data is None:
        raise ValueError("ICP not found")

    icp = ICPResponse(**icp_data)

    components = []

    # Industry: 15
    industry_score = 0

    if (
        company["industry"]
        and matches_any(
            company["industry"],
            icp.industries,
        )
    ):
        industry_score = 15

    components.append(
        ScoreComponent(
            name="industry",
            score=industry_score,
            max_score=15,
            explanation=(
                "Company industry matches the ICP."
                if industry_score
                else "Company industry does not match the ICP."
            ),
        )
    )

    # Company size: 15
    size_score = 0

    if (
        company["employee_count"] is not None
        and icp.company_size_min
        <= company["employee_count"]
        <= icp.company_size_max
    ):
        size_score = 15

    components.append(
        ScoreComponent(
            name="company_size",
            score=size_score,
            max_score=15,
            explanation=(
                "Company size is within the ICP range."
                if size_score
                else "Company size is outside the ICP range."
            ),
        )
    )

    # Geography: 10
    geography_score = 0

    if (
        company["country"]
        and matches_any(
            company["country"],
            icp.target_countries,
        )
    ):
        geography_score = 10

    components.append(
        ScoreComponent(
            name="geography",
            score=geography_score,
            max_score=10,
            explanation=(
                "Company geography matches the ICP."
                if geography_score
                else "Company geography does not match the ICP."
            ),
        )
    )

    # Business model: 10
    business_model_score = 0

    if (
        company["business_model"]
        and matches_any(
            company["business_model"],
            icp.business_models,
        )
    ):
        business_model_score = 10

    components.append(
        ScoreComponent(
            name="business_model",
            score=business_model_score,
            max_score=10,
            explanation=(
                "Company business model matches the ICP."
                if business_model_score
                else (
                    "Company business model does not "
                    "match the ICP."
                )
            ),
        )
    )

    # Buyer relevance: 10
    #
    # We have not discovered contacts yet, so we do
    # not invent this score.
    buyer_relevance_score = 0

    components.append(
        ScoreComponent(
            name="buyer_relevance",
            score=buyer_relevance_score,
            max_score=10,
            explanation=(
                "Buyer relevance has not been "
                "evaluated yet."
            ),
        )
    )

    icp_fit_score = (
        industry_score
        + size_score
        + geography_score
        + business_model_score
        + buyer_relevance_score
    )

    intent_details = get_intent_score_details(
        company_id
    )

    intent_score = intent_details["score"]

    if intent_details["contributions"]:
        intent_explanation = "; ".join(
            (
                f'{item["signal_type"]}: '
                f'+{item["weighted_score"]}'
            )
            for item in intent_details["contributions"]
        )
    else:
        intent_explanation = (
            "No recognised intent signals found."
        )

    components.append(
        ScoreComponent(
            name="intent",
            score=intent_score,
            max_score=30,
            explanation=intent_explanation,
        )
    )


    # All four core company attributes are present
    # because this company has already qualified.
    data_confidence_score = 10

    total_score = (
        icp_fit_score
        + intent_score
        + data_confidence_score
    )

    if total_score >= 80:
        priority = "HIGH"
    elif total_score >= 60:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return CompanyScoreResult(
        company_id=company_id,
        icp_fit_score=icp_fit_score,
        intent_score=intent_score,
        data_confidence_score=data_confidence_score,
        total_score=total_score,
        priority=priority,
        components=components,
    )

def score_and_save_company(
    company_id: int,
) -> CompanyScoreResult:
    result = score_company(company_id)

    save_company_score(result)

    return result
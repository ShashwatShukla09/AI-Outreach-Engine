from app.repositories.company_score_repository import (
    get_company_score,
    get_ranked_company_scores,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def test_company_score_is_persisted():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualify_company(nova.id)

    result = score_and_save_company(nova.id)

    saved = get_company_score(nova.id)

    assert saved is not None

    assert saved["company_id"] == nova.id
    assert saved["industry_score"] == 15
    assert saved["company_size_score"] == 15
    assert saved["geography_score"] == 10
    assert saved["business_model_score"] == 10
    assert saved["buyer_relevance_score"] == 0
    assert saved["intent_score"] == 0
    assert saved["data_confidence_score"] == 10

    assert saved["total_score"] == result.total_score
    assert saved["priority"] == "MEDIUM"


def test_rescoring_updates_instead_of_duplicating():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualify_company(nova.id)

    score_and_save_company(nova.id)
    score_and_save_company(nova.id)

    ranked = get_ranked_company_scores(
        nova.icp_id
    )

    nova_rows = [
        row
        for row in ranked
        if row["company_id"] == nova.id
    ]

    assert len(nova_rows) == 1


def test_ranked_scores_return_highest_first():
    companies = prepare_scoring_companies()

    qualified_companies = []

    for company in companies:
        result = qualify_company(company.id)

        if result.status == "QUALIFIED":
            qualified_companies.append(company)
            score_and_save_company(company.id)

    assert qualified_companies

    ranked = get_ranked_company_scores(
        qualified_companies[0].icp_id
    )

    scores = [
        row["total_score"]
        for row in ranked
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )

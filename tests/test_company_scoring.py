import pytest

from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.product import ProductCreate
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.company_scoring_service import (
    score_company,
)
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import create_new_product


def prepare_scoring_companies():
    product = create_new_product(
        ProductCreate(
            name="Scoring Test Product",
            description=(
                "AI software that helps support teams "
                "answer repetitive customer questions."
            ),
            value_proposition=(
                "Reduce repetitive support work."
            ),
            target_problem=(
                "Support teams spend too much time "
                "answering repeated questions."
            ),
        )
    )

    icps = generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )

    approved = approve_icp(icps[0].id)

    companies = discover_and_save_companies(
        icp_id=approved.id,
        provider=MockCompanyDiscoveryProvider(),
    )

    return companies


def test_qualified_company_gets_explainable_score():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(nova.id)

    assert qualification.status == "QUALIFIED"

    result = score_company(nova.id)

    assert result.icp_fit_score == 50
    assert result.intent_score == 0
    assert result.data_confidence_score == 10
    assert result.total_score == 60
    assert result.priority == "MEDIUM"

    component_scores = {
        component.name: component.score
        for component in result.components
    }


    assert component_scores == {
    "industry": 15,
    "company_size": 15,
    "geography": 10,
    "business_model": 10,
    "buyer_relevance": 0,
    "intent": 0,
}


def test_unqualified_company_cannot_be_scored():
    companies = prepare_scoring_companies()

    tiny = next(
        company
        for company in companies
        if company.name == "TinyShop"
    )

    qualification = qualify_company(tiny.id)

    assert qualification.status == "DISQUALIFIED"

    with pytest.raises(
        ValueError,
        match="Only QUALIFIED companies can be scored",
    ):
        score_company(tiny.id)

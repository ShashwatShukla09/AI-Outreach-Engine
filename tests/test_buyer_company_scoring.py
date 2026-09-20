from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.services.buyer_relevance_service import (
    evaluate_company_buyers,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.services.contact_discovery_service import (
    discover_and_save_contacts,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def test_matching_buyer_increases_company_score():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualify_company(nova.id)

    baseline = score_and_save_company(
        nova.id
    )

    assert baseline.icp_fit_score == 50
    assert baseline.total_score == 60

    discover_and_save_contacts(
        company_id=nova.id,
        provider=MockContactProvider(),
    )

    evaluate_company_buyers(
        nova.id
    )

    rescored = score_and_save_company(
        nova.id
    )

    assert rescored.icp_fit_score == 60
    assert rescored.total_score == 70
    assert rescored.priority == "MEDIUM"

    components = {
        component.name: component
        for component in rescored.components
    }

    assert (
        components["buyer_relevance"].score
        == 10
    )

    assert "Priya Sharma" in (
        components[
            "buyer_relevance"
        ].explanation
    )

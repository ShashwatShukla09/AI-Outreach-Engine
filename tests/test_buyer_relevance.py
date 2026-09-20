from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.services.buyer_relevance_service import (
    evaluate_company_buyers,
    find_best_buyer_match,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.contact_discovery_service import (
    discover_and_save_contacts,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def prepare_contacts():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(
        nova.id
    )

    assert qualification.status == "QUALIFIED"

    discover_and_save_contacts(
        company_id=nova.id,
        provider=MockContactProvider(),
    )

    return nova


def test_role_alias_matches_buyer_category():
    category, score, reason = (
        find_best_buyer_match(
            job_title="Head of Customer Support",
            buyer_categories=[
                "Founder",
                "COO",
                "Head of Support",
            ],
        )
    )

    assert category == "Head of Support"
    assert score == 10
    assert "matches" in reason


def test_irrelevant_role_gets_zero():
    category, score, reason = (
        find_best_buyer_match(
            job_title="Marketing Manager",
            buyer_categories=[
                "Founder",
                "COO",
                "Head of Support",
            ],
        )
    )

    assert category is None
    assert score == 0
    assert "does not match" in reason


def test_company_contacts_are_evaluated():
    company = prepare_contacts()

    evaluated = evaluate_company_buyers(
        company.id
    )

    scores = {
        contact["job_title"]:
        contact["relevance_score"]
        for contact in evaluated
    }

    assert scores["Head of Support"] == 10
    assert scores["COO"] == 10
    assert scores["Marketing Manager"] == 0

    categories = {
        contact["job_title"]:
        contact["buyer_category"]
        for contact in evaluated
    }

    assert (
        categories["Head of Support"]
        == "Head of Support"
    )

    assert categories["COO"] == "COO"
    assert categories["Marketing Manager"] is None

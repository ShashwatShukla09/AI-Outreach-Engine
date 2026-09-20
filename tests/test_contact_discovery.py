from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.repositories.contact_repository import (
    get_company_contacts,
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


def get_novacart():
    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    qualification = qualify_company(nova.id)

    assert qualification.status == "QUALIFIED"

    return nova


def test_contact_provider_discovers_people():
    company = get_novacart()

    provider = MockContactProvider()

    contacts = provider.discover_contacts(
        {
            "id": company.id,
            "name": company.name,
        }
    )

    assert len(contacts) == 3

    titles = {
        contact.job_title
        for contact in contacts
    }

    assert titles == {
        "Head of Support",
        "COO",
        "Marketing Manager",
    }


def test_contacts_are_saved():
    company = get_novacart()

    saved = discover_and_save_contacts(
        company_id=company.id,
        provider=MockContactProvider(),
    )

    assert len(saved) == 3

    contacts = get_company_contacts(
        company.id
    )

    assert len(contacts) == 3


def test_repeated_contact_discovery_is_idempotent():
    company = get_novacart()

    provider = MockContactProvider()

    first = discover_and_save_contacts(
        company_id=company.id,
        provider=provider,
    )

    second = discover_and_save_contacts(
        company_id=company.id,
        provider=provider,
    )

    assert len(first) == 3
    assert len(second) == 0

    contacts = get_company_contacts(
        company.id
    )

    assert len(contacts) == 3

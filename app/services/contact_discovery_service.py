from typing import List

from app.providers.contacts.base import (
    ContactProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.contact_repository import (
    create_contact,
    find_existing_contact,
)


def discover_and_save_contacts(
    company_id: int,
    provider: ContactProvider,
) -> List[dict]:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    discovered = provider.discover_contacts(
        company
    )

    saved = []

    for contact in discovered:
        existing = find_existing_contact(
            company_id=company_id,
            email=contact.email,
            first_name=contact.first_name,
            last_name=contact.last_name,
            job_title=contact.job_title,
        )

        if existing is not None:
            continue

        created = create_contact(
            company_id=company_id,
            contact=contact,
        )

        saved.append(created)

    return saved

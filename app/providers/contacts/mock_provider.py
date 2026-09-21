from typing import List

from app.providers.contacts.base import (
    ContactProvider,
)
from app.schemas.contact import ContactCandidate


class MockContactProvider(ContactProvider):
    def discover_contacts(
        self,
        company: dict,
    ) -> List[ContactCandidate]:

        contacts_by_company = {
            "NovaCart India": [
                ContactCandidate(
                    first_name="Priya",
                    last_name="Sharma",
                    job_title="Head of Support",
                    email="priya@novacart.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
                ContactCandidate(
                    first_name="Arjun",
                    last_name="Mehta",
                    job_title="COO",
                    email="arjun@novacart.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
                ContactCandidate(
                    first_name="Riya",
                    last_name="Kapoor",
                    job_title="Marketing Manager",
                    email="riya@novacart.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
            ],

            "UrbanBasket": [
                ContactCandidate(
                    first_name="Ananya",
                    last_name="Rao",
                    job_title="Head of Support",
                    email="ananya@urbanbasket.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
                ContactCandidate(
                    first_name="Kabir",
                    last_name="Malhotra",
                    job_title="COO",
                    email="kabir@urbanbasket.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
            ],

            "Northstar Software": [
                ContactCandidate(
                    first_name="Emily",
                    last_name="Carter",
                    job_title="Head of Customer Success",
                    email="emily@northstar.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
                ContactCandidate(
                    first_name="James",
                    last_name="Wilson",
                    job_title="COO",
                    email="james@northstar.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
            ],

            "Atlas Systems": [
                ContactCandidate(
                    first_name="Daniel",
                    last_name="Reed",
                    job_title="Head of Customer Success",
                    email="daniel@atlas.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
                ContactCandidate(
                    first_name="Sophie",
                    last_name="Turner",
                    job_title="Operations Manager",
                    email="sophie@atlas.example",
                    linkedin_url=None,
                    enrichment_provider="mock",
                ),
            ],
        }

        return contacts_by_company.get(
            company["name"],
            [],
        )

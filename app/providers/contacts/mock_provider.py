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
        if company["name"] == "NovaCart India":
            return [
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
            ]

        return []

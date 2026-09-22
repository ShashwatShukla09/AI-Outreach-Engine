import csv
from pathlib import Path
from typing import List, Optional

from app.providers.contacts.base import (
    ContactProvider,
)
from app.schemas.contact import ContactCandidate


class ClayCSVContactProvider(ContactProvider):
    def __init__(
        self,
        csv_path: str,
    ):
        self.csv_path = Path(csv_path)

    @staticmethod
    def _clean(
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        return cleaned

    @staticmethod
    def _normalise_company_name(
        value: str,
    ) -> str:
        return " ".join(
            value.lower().strip().split()
        )

    def discover_contacts(
        self,
        company: dict,
    ) -> List[ContactCandidate]:
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Contact CSV not found: "
                f"{self.csv_path}"
            )

        target_company = (
            self._normalise_company_name(
                company["name"]
            )
        )

        contacts = []

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            for row in reader:
                company_name = self._clean(
                    row.get("Company Name")
                )

                if not company_name:
                    continue

                if (
                    self._normalise_company_name(
                        company_name
                    )
                    != target_company
                ):
                    continue

                first_name = self._clean(
                    row.get("First Name")
                )
                last_name = self._clean(
                    row.get("Last Name")
                )
                job_title = self._clean(
                    row.get("Job Title")
                )

                if (
                    not first_name
                    or not last_name
                    or not job_title
                ):
                    continue

                contacts.append(
                    ContactCandidate(
                        first_name=first_name,
                        last_name=last_name,
                        job_title=job_title,
                        email=self._clean(
                            row.get("Email")
                        ),
                        linkedin_url=self._clean(
                            row.get("LinkedIn URL")
                        ),
                        enrichment_provider=(
                            "clay_csv"
                        ),
                    )
                )

        return contacts

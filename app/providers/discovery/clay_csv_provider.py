import csv
import re
from pathlib import Path
from typing import List, Optional

from app.providers.discovery.base import (
    CompanyDiscoveryProvider,
)
from app.schemas.company import CompanyCandidate
from app.schemas.icp import ICPResponse


class ClayCSVCompanyDiscoveryProvider(
    CompanyDiscoveryProvider
):
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    @staticmethod
    def _clean(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _normalise_domain(
        value: Optional[str],
    ) -> Optional[str]:
        value = ClayCSVCompanyDiscoveryProvider._clean(
            value
        )

        if value is None:
            return None

        value = re.sub(
            r"^https?://",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = value.split("/")[0]
        value = value.lower()

        if value.startswith("www."):
            value = value[4:]

        return value or None

    @staticmethod
    def _employee_count(
        value: Optional[str],
    ) -> Optional[int]:
        value = ClayCSVCompanyDiscoveryProvider._clean(
            value
        )

        if value is None:
            return None

        numbers = [
            int(number.replace(",", ""))
            for number in re.findall(
                r"\d[\d,]*",
                value,
            )
        ]

        if not numbers:
            return None

        if len(numbers) == 1:
            return numbers[0]

        return round(
            (numbers[0] + numbers[1]) / 2
        )

    def discover_companies(
        self,
        icp: ICPResponse,
        limit: int = 100,
    ) -> List[CompanyCandidate]:
        if not self.csv_path.exists():
            raise ValueError(
                "Clay CSV file not found: "
                f"{self.csv_path}"
            )

        companies = []

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                name = self._clean(row.get("Name"))
                domain = self._normalise_domain(
                    row.get("Domain")
                )

                if not name:
                    continue

                company = CompanyCandidate(
                    name=name,
                    domain=domain,
                    country=self._clean(
                        row.get("Country")
                    ),
                    industry=self._clean(
                        row.get("Industry")
                    ),
                    employee_count=self._employee_count(
                        row.get("Size")
                    ),
                    business_model=None,
                    description=self._clean(
                        row.get("Description")
                    ),
                    linkedin_url=self._clean(
                        row.get("LinkedIn URL")
                    ),
                    source="clay_csv",
                )

                companies.append(company)

                if len(companies) >= limit:
                    break

        return companies

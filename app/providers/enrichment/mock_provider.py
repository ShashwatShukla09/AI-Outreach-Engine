from typing import Any, Dict, List

from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)


class MockCompanyEnrichmentProvider(
    CompanyEnrichmentProvider
):
    def enrich_company(
        self,
        company: dict,
        fields: List[str],
    ) -> Dict[str, Any]:
        mock_data = {
            "employee_count": 90,
            "business_model": "Marketplace",
            "industry": "E-commerce",
            "country": "India",
        }

        return {
            field: mock_data[field]
            for field in fields
            if field in mock_data
        }

from typing import List

from app.providers.discovery.base import (
    CompanyDiscoveryProvider,
)
from app.schemas.company import CompanyCandidate
from app.schemas.icp import ICPResponse


class MockCompanyDiscoveryProvider(
    CompanyDiscoveryProvider
):
    def discover_companies(
        self,
        icp: ICPResponse,
        limit: int = 100,
    ) -> List[CompanyCandidate]:
        if icp.target_market == "INDIA":
            companies = [
                CompanyCandidate(
                    name="NovaCart India",
                    domain="novacart.example",
                    country="India",
                    industry="E-commerce",
                    employee_count=120,
                    business_model="Marketplace",
                    source="mock",
                ),
                CompanyCandidate(
                    name="UrbanBasket",
                    domain="urbanbasket.example",
                    country="India",
                    industry="E-commerce",
                    employee_count=180,
                    business_model="Marketplace",
                    source="mock",
                ),
                CompanyCandidate(
                    name="TinyShop",
                    domain="tinyshop.example",
                    country="India",
                    industry="E-commerce",
                    employee_count=12,
                    business_model="Marketplace",
                    source="mock",
                ),
                CompanyCandidate(
                    name="MysteryCommerce",
                    domain="mysterycommerce.example",
                    country="India",
                    industry="E-commerce",
                    employee_count=None,
                    business_model=None,
                    source="mock",
                ),
            ]

        else:
            companies = [
                CompanyCandidate(
                    name="Northstar Software",
                    domain="northstar.example",
                    country="United Kingdom",
                    industry="SaaS",
                    employee_count=120,
                    business_model="B2B SaaS",
                    source="mock",
                ),
                CompanyCandidate(
                    name="Atlas Systems",
                    domain="atlas.example",
                    country="United States",
                    industry="SaaS",
                    employee_count=180,
                    business_model="B2B SaaS",
                    source="mock",
                ),
            ]

        return companies[:limit]

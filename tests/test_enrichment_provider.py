from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)


def test_mock_enrichment_provider():
    provider = MockCompanyEnrichmentProvider()

    company = {
        "id": 1,
        "name": "MysteryCommerce",
        "country": "India",
        "industry": "E-commerce",
        "employee_count": None,
        "business_model": None,
    }

    result = provider.enrich_company(
        company=company,
        fields=[
            "employee_count",
            "business_model",
        ],
    )

    assert result == {
        "employee_count": 90,
        "business_model": "Marketplace",
    }


def test_provider_only_returns_requested_fields():
    provider = MockCompanyEnrichmentProvider()

    result = provider.enrich_company(
        company={"name": "MysteryCommerce"},
        fields=["employee_count"],
    )

    assert result == {
        "employee_count": 90,
    }

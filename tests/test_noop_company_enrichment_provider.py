from app.providers.enrichment.noop_provider import (
    NoOpCompanyEnrichmentProvider,
)


def test_noop_enrichment_never_invents_values():
    provider = NoOpCompanyEnrichmentProvider()

    company = {
        "id": 1,
        "name": "Real Logistics Company",
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

    assert result == {}


def test_noop_enrichment_returns_empty_for_any_fields():
    provider = NoOpCompanyEnrichmentProvider()

    result = provider.enrich_company(
        company={
            "id": 1,
            "name": "Real Company",
        },
        fields=[
            "industry",
            "country",
            "employee_count",
        ],
    )

    assert result == {}

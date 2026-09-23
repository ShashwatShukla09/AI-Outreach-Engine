from app.providers.discovery.clay_csv_provider import (
    ClayCSVCompanyDiscoveryProvider,
)
from app.schemas.icp import ICPResponse


def make_icp():
    return ICPResponse(
        id=1,
        product_id=1,
        name="Clearlyy Logistics ICP",
        industries=["Logistics"],
        company_size_min=200,
        company_size_max=100000,
        target_market="INDIA",
        target_countries=["India"],
        business_models=[],
        buyer_categories=["Operations"],
        pain_points=["Frontline training"],
        segment_rationale="Test rationale.",
        buyer_rationale="Test rationale.",
        assumptions=[],
        status="APPROVED",
        reviewed_at="2026-09-23 10:00:00",
        created_at="2026-09-23 09:00:00",
    )


def write_clay_csv(path):
    path.write_text(
        "\n".join(
            [
                (
                    "Name,Domain,Country,Industry,Size,"
                    "Description,LinkedIn URL"
                ),
                (
                    "Alpha Logistics,"
                    "https://www.alpha.example.com/about,"
                    "India,Logistics,\"1,001-5,000\","
                    "Large logistics network,"
                    "https://linkedin.com/company/alpha"
                ),
                (
                    "Beta Supply,"
                    "WWW.BETA.EXAMPLE.COM,"
                    "India,Logistics,501-1000,"
                    "Supply chain operator,"
                    "https://linkedin.com/company/beta"
                ),
            ]
        ),
        encoding="utf-8",
    )


def test_clay_csv_provider_normalises_companies(tmp_path):
    csv_path = tmp_path / "companies.csv"
    write_clay_csv(csv_path)

    provider = ClayCSVCompanyDiscoveryProvider(
        str(csv_path)
    )

    companies = provider.discover_companies(
        icp=make_icp(),
        limit=100,
    )

    assert len(companies) == 2

    alpha = companies[0]
    beta = companies[1]

    assert alpha.name == "Alpha Logistics"
    assert alpha.domain == "alpha.example.com"
    assert alpha.employee_count == 3000
    assert alpha.source == "clay_csv"

    assert beta.domain == "beta.example.com"
    assert beta.employee_count == 750


def test_clay_csv_provider_respects_limit(tmp_path):
    csv_path = tmp_path / "companies.csv"
    write_clay_csv(csv_path)

    provider = ClayCSVCompanyDiscoveryProvider(
        str(csv_path)
    )

    companies = provider.discover_companies(
        icp=make_icp(),
        limit=1,
    )

    assert len(companies) == 1
    assert companies[0].name == "Alpha Logistics"


def test_clay_csv_provider_rejects_missing_file(
    tmp_path,
):
    provider = ClayCSVCompanyDiscoveryProvider(
        str(tmp_path / "missing.csv")
    )

    try:
        provider.discover_companies(
            icp=make_icp()
        )
    except ValueError as exc:
        assert "Clay CSV file not found" in str(exc)
    else:
        raise AssertionError(
            "Expected missing Clay CSV to fail."
        )

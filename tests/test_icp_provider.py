from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.product import ProductResponse


def test_mock_provider_generates_two_markets():
    product = ProductResponse(
        id=1,
        name="AI Support Copilot",
        description=(
            "AI software that helps customer support "
            "teams answer repetitive questions."
        ),
        value_proposition=(
            "Reduce repetitive support work."
        ),
        target_problem=(
            "Support teams spend too much time "
            "answering repetitive questions."
        ),
        created_at="2026-09-20 10:00:00",
    )

    provider = MockICPProvider()

    result = provider.generate_icps(product)

    assert result.product_id == 1
    assert len(result.icps) == 2

    markets = {
        icp.target_market
        for icp in result.icps
    }

    assert markets == {
        "INDIA",
        "INTERNATIONAL",
    }


def test_mock_provider_returns_buyer_categories():
    product = ProductResponse(
        id=1,
        name="AI Support Copilot",
        description=(
            "AI software for customer support teams."
        ),
        value_proposition=None,
        target_problem=None,
        created_at="2026-09-20 10:00:00",
    )

    provider = MockICPProvider()

    result = provider.generate_icps(product)

    for icp in result.icps:
        assert len(icp.buyer_categories) > 0


def test_mock_provider_returns_valid_company_sizes():
    product = ProductResponse(
        id=1,
        name="AI Support Copilot",
        description=(
            "AI software for customer support teams."
        ),
        value_proposition=None,
        target_problem=None,
        created_at="2026-09-20 10:00:00",
    )

    provider = MockICPProvider()

    result = provider.generate_icps(product)

    for icp in result.icps:
        assert icp.company_size_min >= 1
        assert icp.company_size_max >= icp.company_size_min

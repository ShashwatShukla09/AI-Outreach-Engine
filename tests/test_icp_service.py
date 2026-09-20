from app.providers.llm.mock_provider import MockICPProvider
from app.schemas.product import ProductCreate
from app.services.icp_service import (
    generate_and_save_icps,
)
from app.services.product_service import create_new_product


def test_generate_and_save_icps():
    product = create_new_product(
        ProductCreate(
            name="ICP Service Test Product",
            description=(
                "AI software that helps support teams "
                "automate repetitive customer questions."
            ),
            value_proposition=(
                "Reduce repetitive support work."
            ),
            target_problem=(
                "Support teams spend too much time "
                "answering repeated questions."
            ),
        )
    )

    provider = MockICPProvider()

    saved_icps = generate_and_save_icps(
        product_id=product["id"],
        provider=provider,
    )

    assert len(saved_icps) == 2

    markets = {
        icp.target_market
        for icp in saved_icps
    }

    assert markets == {
        "INDIA",
        "INTERNATIONAL",
    }

    for icp in saved_icps:
        assert icp.id is not None
        assert icp.product_id == product["id"]
        assert len(icp.pain_points) > 0
        assert len(icp.buyer_categories) > 0

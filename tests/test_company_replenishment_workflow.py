from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.providers.llm.mock_provider import (
    MockICPProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.schemas.product import ProductCreate
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import (
    create_new_product,
)
from app.workflows.company_replenishment_workflow import (
    replenish_companies,
)


def create_approved_replenishment_icp():
    product = create_new_product(
        ProductCreate(
            name="Replenishment Test Product",
            description=(
                "AI software that helps customer support "
                "teams answer repetitive questions."
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

    icps = generate_and_save_icps(
        product_id=product["id"],
        provider=MockICPProvider(),
    )

    return approve_icp(icps[0].id)


def run_replenishment(icp_id):
    return replenish_companies(
        icp_id=icp_id,
        discovery_provider=(
            MockCompanyDiscoveryProvider()
        ),
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
        limit=100,
    )


def test_replenishment_processes_only_new_companies():
    icp = create_approved_replenishment_icp()

    result = run_replenishment(
        icp.id
    )

    assert result["icp_id"] == icp.id

    assert result["new_accounts"] == 4
    assert result["processed"] == 4

    assert result["qualified"] == 3
    assert result["disqualified"] == 1
    assert result["needs_review"] == 0

    assert result["enriched"] == 1

    assert len(
        result["processing"]["results"]
    ) == 4

    assert len(
        result["relevance_results"]
    ) == 3

    assert (
        result["high_priority"]
        + result["medium_priority"]
        + result["low_priority"]
        == 3
    )


def test_replenishment_deduplicates_on_second_run():
    icp = create_approved_replenishment_icp()

    first = run_replenishment(
        icp.id
    )

    second = run_replenishment(
        icp.id
    )

    assert first["new_accounts"] == 4

    assert second["new_accounts"] == 0
    assert second["processed"] == 0

    assert second["qualified"] == 0
    assert second["disqualified"] == 0
    assert second["needs_review"] == 0
    assert second["enriched"] == 0

    assert second["processing"]["results"] == []
    assert second["relevance_results"] == []

    assert second["high_priority"] == 0
    assert second["medium_priority"] == 0
    assert second["low_priority"] == 0

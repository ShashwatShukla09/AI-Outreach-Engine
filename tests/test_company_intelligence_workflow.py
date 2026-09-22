from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.contacts.mock_provider import (
    MockContactProvider,
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
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.schemas.product import ProductCreate
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.icp_service import (
    approve_icp,
    generate_and_save_icps,
)
from app.services.product_service import (
    create_new_product,
)
from app.workflows.company_intelligence_workflow import (
    process_company_intelligence,
)


def prepare_discovered_companies():
    product = create_new_product(
        ProductCreate(
            name="Intelligence Workflow Product",
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

    approved = approve_icp(icps[0].id)

    companies = discover_and_save_companies(
        icp_id=approved.id,
        provider=MockCompanyDiscoveryProvider(),
    )

    return companies


def test_qualified_company_is_scored():
    companies = prepare_discovered_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    result = process_company_intelligence(
        company_id=nova.id,
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
    )

    assert result["status"] == "QUALIFIED"
    assert result["enriched"] is False
    assert result["score"] is not None

    saved_score = get_company_score(nova.id)

    assert saved_score is not None
    assert saved_score["total_score"] == 60


def test_incomplete_company_is_enriched_then_scored():
    companies = prepare_discovered_companies()

    mystery = next(
        company
        for company in companies
        if company.name == "MysteryCommerce"
    )

    result = process_company_intelligence(
        company_id=mystery.id,
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
    )

    assert result["status"] == "QUALIFIED"
    assert result["enriched"] is True
    assert result["score"] is not None

    assert (
        result["qualification"][
            "initial_qualification"
        ].status
        == "NEEDS_REVIEW"
    )

    assert (
        result["qualification"][
            "final_qualification"
        ].status
        == "QUALIFIED"
    )

    saved_score = get_company_score(mystery.id)

    assert saved_score is not None


def test_disqualified_company_stops_before_scoring():
    companies = prepare_discovered_companies()

    tiny = next(
        company
        for company in companies
        if company.name == "TinyShop"
    )

    result = process_company_intelligence(
        company_id=tiny.id,
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
    )

    assert result["status"] == "DISQUALIFIED"
    assert result["enriched"] is False
    assert result["score"] is None

    assert get_company_score(tiny.id) is None


def test_discovered_company_batch_is_processed():
    companies = prepare_discovered_companies()

    from app.workflows.company_intelligence_workflow import (
        process_company_batch,
    )

    result = process_company_batch(
        company_ids=[
            company.id
            for company in companies
        ],
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
    )

    assert result["processed_count"] == 4
    assert result["qualified_count"] == 3
    assert result["disqualified_count"] == 1
    assert result["enriched_count"] == 1

    statuses = {
        company.name: company_result["status"]
        for company, company_result in zip(
            companies,
            result["results"],
        )
    }

    assert statuses == {
        "NovaCart India": "QUALIFIED",
        "UrbanBasket": "QUALIFIED",
        "TinyShop": "DISQUALIFIED",
        "MysteryCommerce": "QUALIFIED",
    }


def test_qualified_company_discovers_signals_and_rescores():
    companies = prepare_discovered_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    result = process_company_intelligence(
        company_id=nova.id,
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
    )

    assert result["status"] == "QUALIFIED"

    assert result["signal_processing"] is not None
    assert (
        result["signal_processing"]["new_signal_count"]
        == 2
    )

    assert result["score"].total_score == 80
    assert result["score"].intent_score == 20
    assert result["score"].priority == "HIGH"

    saved_score = get_company_score(nova.id)

    assert saved_score is not None
    assert saved_score["total_score"] == 80
    assert saved_score["intent_score"] == 20
    assert saved_score["priority"] == "HIGH"


def test_company_batch_discovers_signals_and_rescores():
    companies = prepare_discovered_companies()

    from app.workflows.company_intelligence_workflow import (
        process_company_batch,
    )

    result = process_company_batch(
        company_ids=[
            company.id
            for company in companies
        ],
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
    )

    results_by_name = {
        company.name: company_result
        for company, company_result in zip(
            companies,
            result["results"],
        )
    }

    nova = results_by_name["NovaCart India"]
    urban = results_by_name["UrbanBasket"]
    tiny = results_by_name["TinyShop"]
    mystery = results_by_name["MysteryCommerce"]

    assert nova["score"].total_score == 80
    assert nova["score"].intent_score == 20
    assert nova["score"].priority == "HIGH"
    assert (
        nova["signal_processing"]["new_signal_count"]
        == 2
    )

    assert urban["score"].total_score == 70
    assert urban["score"].intent_score == 10
    assert urban["score"].priority == "MEDIUM"
    assert (
        urban["signal_processing"]["new_signal_count"]
        == 1
    )

    assert tiny["status"] == "DISQUALIFIED"
    assert tiny["score"] is None

    assert mystery["status"] == "QUALIFIED"
    assert mystery["score"].total_score == 60
    assert mystery["score"].intent_score == 0


def test_qualified_company_builds_buyer_intelligence():
    companies = prepare_discovered_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    result = process_company_intelligence(
        company_id=nova.id,
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
        contact_provider=MockContactProvider(),
    )

    assert result["status"] == "QUALIFIED"

    buyer = result["buyer_intelligence"]

    assert buyer is not None
    assert len(buyer["contacts"]) == 3
    assert buyer["primary_buyer"] is not None

    assert (
        buyer["primary_buyer"]["relevance_score"]
        == 10
    )

    assert (
        buyer["primary_buyer"]["job_title"]
        == "Head of Support"
    )

    assert result["score"].icp_fit_score == 60
    assert result["score"].intent_score == 20
    assert result["score"].data_confidence_score == 10
    assert result["score"].total_score == 90
    assert result["score"].priority == "HIGH"

    saved_score = get_company_score(nova.id)

    assert saved_score is not None

    assert saved_score["industry_score"] == 15
    assert saved_score["company_size_score"] == 15
    assert saved_score["geography_score"] == 10
    assert saved_score["business_model_score"] == 10
    assert saved_score["buyer_relevance_score"] == 10
    assert saved_score["intent_score"] == 20
    assert saved_score["data_confidence_score"] == 10
    assert saved_score["total_score"] == 90
    assert saved_score["priority"] == "HIGH"


def test_company_batch_builds_buyer_intelligence():
    companies = prepare_discovered_companies()

    from app.workflows.company_intelligence_workflow import (
        process_company_batch,
    )

    result = process_company_batch(
        company_ids=[
            company.id
            for company in companies
        ],
        enrichment_provider=(
            MockCompanyEnrichmentProvider()
        ),
        enrichment_provider_name="mock",
        signal_provider=MockSignalProvider(),
        contact_provider=MockContactProvider(),
    )

    results_by_name = {
        company.name: company_result
        for company, company_result in zip(
            companies,
            result["results"],
        )
    }

    nova = results_by_name["NovaCart India"]
    urban = results_by_name["UrbanBasket"]
    tiny = results_by_name["TinyShop"]
    mystery = results_by_name["MysteryCommerce"]

    assert nova["buyer_intelligence"] is not None
    assert (
        nova["buyer_intelligence"][
            "primary_buyer"
        ]["job_title"]
        == "Head of Support"
    )
    assert nova["score"].total_score == 90
    assert nova["score"].priority == "HIGH"

    assert urban["buyer_intelligence"] is not None
    assert (
        urban["buyer_intelligence"][
            "primary_buyer"
        ]["job_title"]
        == "Head of Support"
    )

    assert tiny["status"] == "DISQUALIFIED"
    assert tiny["score"] is None

    assert mystery["status"] == "QUALIFIED"
    assert mystery["buyer_intelligence"] is not None
    assert (
        mystery["buyer_intelligence"][
            "primary_buyer"
        ]
        is None
    )

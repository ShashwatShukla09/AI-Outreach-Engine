from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.discovery.mock_provider import (
    MockCompanyDiscoveryProvider,
)
from app.providers.enrichment.mock_provider import (
    MockCompanyEnrichmentProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.icp_repository import (
    create_icp,
    update_icp_status,
)
from app.repositories.product_repository import (
    create_product,
)
from app.schemas.icp import ICPDefinition
from app.services.company_discovery_service import (
    discover_and_save_companies,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.workflows.account_intelligence_workflow import (
    build_account_intelligence,
)
from app.workflows.company_enrichment_workflow import (
    qualify_enrich_requalify,
)
from app.workflows.outreach_generation_workflow import (
    create_company_outreach,
)


def build_india_icp() -> ICPDefinition:
    return ICPDefinition(
        name="India Commerce Operations",
        industries=["E-commerce"],
        company_size_min=50,
        company_size_max=250,
        target_market="INDIA",
        target_countries=["India"],
        business_models=["Marketplace"],
        buyer_categories=[
            "Head of Support",
            "COO",
            "Head of Customer Success",
            "Operations Manager",
        ],
        pain_points=[
            "High-volume customer support operations",
            "Manual customer operations workflows",
            "Scaling support without proportional headcount",
        ],
        segment_rationale=(
            "Growing Indian commerce companies often need "
            "more scalable customer operations."
        ),
        buyer_rationale=(
            "Support and operations leaders own the workflows "
            "that the product is designed to improve."
        ),
        assumptions=[
            "Companies in this segment have recurring support volume.",
            "Operations teams are open to workflow automation.",
        ],
    )


def build_international_icp() -> ICPDefinition:
    return ICPDefinition(
        name="International B2B SaaS Operations",
        industries=["SaaS"],
        company_size_min=50,
        company_size_max=250,
        target_market="INTERNATIONAL",
        target_countries=[
            "United Kingdom",
            "United States",
        ],
        business_models=["B2B SaaS"],
        buyer_categories=[
            "Head of Customer Success",
            "COO",
            "Operations Manager",
            "Head of Support",
        ],
        pain_points=[
            "Scaling customer-facing operations",
            "Manual customer success workflows",
            "Increasing operational workload",
        ],
        segment_rationale=(
            "Growing B2B SaaS companies frequently need "
            "more efficient customer-facing operations."
        ),
        buyer_rationale=(
            "Customer success and operations leaders are "
            "responsible for these workflows and outcomes."
        ),
        assumptions=[
            "Customer-facing teams use repeatable workflows.",
            "Operational efficiency is a meaningful priority.",
        ],
    )


def create_approved_icp(
    product_id: int,
    definition: ICPDefinition,
) -> dict:
    created = create_icp(
        product_id=product_id,
        icp=definition,
    )

    approved = update_icp_status(
        icp_id=created["id"],
        status="APPROVED",
    )

    return approved


def process_company(
    company,
    enrichment_provider,
    contact_provider,
    signal_provider,
):
    print()
    print("-" * 64)
    print(f'COMPANY: {company.name}')
    print("-" * 64)

    qualification = qualify_enrich_requalify(
        company_id=company.id,
        provider=enrichment_provider,
        provider_name="mock",
    )

    final_qualification = qualification[
        "final_qualification"
    ]

    print(
        "Qualification:",
        final_qualification.status,
    )

    if qualification["enriched"]:
        print("Enrichment:    YES")
    else:
        print("Enrichment:    NO")

    if final_qualification.status != "QUALIFIED":
        print(
            "Pipeline:      stopped before scoring"
        )
        return {
            "company_id": company.id,
            "company_name": company.name,
            "qualification": final_qualification.status,
            "priority": None,
            "outreach_id": None,
        }

    initial_score = score_and_save_company(
        company.id
    )

    print(
        "Initial score:  ",
        initial_score.total_score,
        f"({initial_score.priority})",
    )

    intelligence = build_account_intelligence(
        company_id=company.id,
        contact_provider=contact_provider,
        signal_provider=signal_provider,
    )

    final_score = intelligence["score"]
    primary_buyer = intelligence[
        "primary_buyer"
    ]

    print(
        "Final score:    ",
        final_score.total_score,
        f"({final_score.priority})",
    )

    print(
        "Signals:        ",
        len(intelligence["signals"]),
    )

    print(
        "Contacts:       ",
        len(intelligence["contacts"]),
    )

    if primary_buyer:
        print(
            "Primary buyer: ",
            (
                f'{primary_buyer["first_name"]} '
                f'{primary_buyer["last_name"]} — '
                f'{primary_buyer["job_title"]}'
            ),
        )
    else:
        print(
            "Primary buyer:  None"
        )

    outreach_id = None

    if (
        primary_buyer is not None
        and final_score.priority in {
            "HIGH",
            "MEDIUM",
        }
    ):
        outreach = create_company_outreach(
            company.id
        )

        outreach_id = outreach["saved"]["id"]

        print(
            "Outreach:       DRAFT",
            f'#{outreach_id}',
        )
    else:
        print(
            "Outreach:       not generated"
        )

    return {
        "company_id": company.id,
        "company_name": company.name,
        "qualification": (
            final_qualification.status
        ),
        "priority": final_score.priority,
        "score": final_score.total_score,
        "outreach_id": outreach_id,
    }


def main():
    print()
    print("=" * 64)
    print("AI BUYER INTELLIGENCE — DEMO SEED")
    print("=" * 64)

    product = create_product(
        name="AI Customer Operations Platform",
        description=(
            "An AI automation platform that helps "
            "customer-facing teams reduce repetitive "
            "operational work."
        ),
        value_proposition=(
            "Automate repetitive customer operations "
            "while keeping humans in control."
        ),
        target_problem=(
            "Growing companies accumulate manual support "
            "and customer operations workflows."
        ),
    )

    print()
    print(
        f'Product created: #{product["id"]} '
        f'{product["name"]}'
    )

    india_icp = create_approved_icp(
        product_id=product["id"],
        definition=build_india_icp(),
    )

    international_icp = create_approved_icp(
        product_id=product["id"],
        definition=build_international_icp(),
    )

    print(
        f'India ICP:       #{india_icp["id"]} APPROVED'
    )
    print(
        "International:   "
        f'#{international_icp["id"]} APPROVED'
    )

    discovery_provider = (
        MockCompanyDiscoveryProvider()
    )
    enrichment_provider = (
        MockCompanyEnrichmentProvider()
    )
    contact_provider = MockContactProvider()
    signal_provider = MockSignalProvider()

    india_companies = discover_and_save_companies(
        icp_id=india_icp["id"],
        provider=discovery_provider,
        limit=100,
    )

    international_companies = (
        discover_and_save_companies(
            icp_id=international_icp["id"],
            provider=discovery_provider,
            limit=100,
        )
    )

    companies = (
        india_companies
        + international_companies
    )

    print()
    print(
        f"Discovered companies: {len(companies)}"
    )

    results = []

    for company in companies:
        result = process_company(
            company=company,
            enrichment_provider=(
                enrichment_provider
            ),
            contact_provider=contact_provider,
            signal_provider=signal_provider,
        )

        results.append(result)

    print()
    print("=" * 64)
    print("DEMO SUMMARY")
    print("=" * 64)

    for result in results:
        score = result.get("score")

        score_text = (
            str(score)
            if score is not None
            else "—"
        )

        priority = (
            result["priority"]
            if result["priority"]
            else "—"
        )

        outreach = (
            f'#{result["outreach_id"]}'
            if result["outreach_id"]
            else "—"
        )

        print(
            f'{result["company_name"]:<22} '
            f'{result["qualification"]:<13} '
            f'score={score_text:<4} '
            f'priority={priority:<6} '
            f'outreach={outreach}'
        )

    print()
    print("✓ Demo seed completed")


if __name__ == "__main__":
    main()

from app.providers.llm.base import ICPProvider
from app.schemas.icp import (
    ICPDefinition,
    ICPGenerationResult,
)
from app.schemas.product import ProductResponse


class MockICPProvider(ICPProvider):
    """
    Deterministic ICP provider for development and testing.
    """

    def generate_icps(
        self,
        product: ProductResponse,
    ) -> ICPGenerationResult:

        india_icp = ICPDefinition(
            name=f"India ICP for {product.name}",
            industries=[
                "SaaS",
                "Fintech",
                "E-commerce",
            ],
            company_size_min=20,
            company_size_max=200,
            target_market="INDIA",
            target_countries=["India"],
            business_models=[
                "B2B SaaS",
                "Marketplace",
            ],
            buyer_categories=[
                "Founder",
                "COO",
                "Head of Support",
            ],
            pain_points=[
                "High repetitive support workload",
                "Slow customer response times",
                "Fragmented company knowledge",
            ],
            segment_rationale=(
                "Growing digital businesses can develop enough "
                "support volume for automation to create value."
            ),
            buyer_rationale=(
                "These roles typically influence support operations, "
                "efficiency, tooling, or company-level purchasing."
            ),
            assumptions=[
                "The company operates a meaningful support function.",
                "A material share of support questions are repetitive.",
            ],
        )

        international_icp = ICPDefinition(
            name=f"International ICP for {product.name}",
            industries=[
                "SaaS",
                "Fintech",
                "E-commerce",
            ],
            company_size_min=50,
            company_size_max=500,
            target_market="INTERNATIONAL",
            target_countries=[
                "United Kingdom",
                "United States",
            ],
            business_models=[
                "B2B SaaS",
                "Marketplace",
            ],
            buyer_categories=[
                "VP Customer Support",
                "Head of Customer Experience",
                "VP Operations",
            ],
            pain_points=[
                "Scaling support costs",
                "Large repetitive ticket volumes",
                "Knowledge consistency across support teams",
            ],
            segment_rationale=(
                "Larger international support organisations may have "
                "greater ticket volume and operational complexity."
            ),
            buyer_rationale=(
                "These roles commonly own customer support performance, "
                "operations, or tooling decisions."
            ),
            assumptions=[
                "The company has an established support organisation.",
                "Support automation is compatible with its workflows.",
            ],
        )

        return ICPGenerationResult(
            product_id=product.id,
            icps=[
                india_icp,
                international_icp,
            ],
        )

from typing import Any, Dict, List

from app.providers.enrichment.base import (
    CompanyEnrichmentProvider,
)


class NoOpCompanyEnrichmentProvider(
    CompanyEnrichmentProvider
):
    """
    Safe enrichment provider that never fabricates data.

    Use this when no verified enrichment source is
    available. Missing fields remain missing so the
    company can stay in NEEDS_REVIEW.
    """

    def enrich_company(
        self,
        company: dict,
        fields: List[str],
    ) -> Dict[str, Any]:
        return {}

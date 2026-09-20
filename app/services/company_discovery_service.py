from typing import List

from app.providers.discovery.base import (
    CompanyDiscoveryProvider,
)
from app.repositories.company_repository import (
    create_company,
    find_company_by_domain,
)
from app.repositories.icp_repository import get_icp
from app.schemas.company import CompanyResponse
from app.schemas.icp import ICPResponse


def discover_and_save_companies(
    icp_id: int,
    provider: CompanyDiscoveryProvider,
    limit: int = 100,
) -> List[CompanyResponse]:
    icp_data = get_icp(icp_id)

    if icp_data is None:
        raise ValueError("ICP not found")

    icp = ICPResponse(**icp_data)

    if icp.status != "APPROVED":
        raise ValueError(
            "Company discovery requires an APPROVED ICP."
        )

    candidates = provider.discover_companies(
        icp=icp,
        limit=limit,
    )

    saved_companies = []

    for candidate in candidates:
        if candidate.domain:
            existing = find_company_by_domain(
                icp_id=icp.id,
                domain=candidate.domain,
            )

            if existing is not None:
                continue

        saved = create_company(
            icp_id=icp.id,
            market=icp.target_market,
            company=candidate,
        )

        saved_companies.append(
            CompanyResponse(**saved)
        )

    return saved_companies

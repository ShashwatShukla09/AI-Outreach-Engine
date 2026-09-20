from abc import ABC, abstractmethod
from typing import List

from app.schemas.company import CompanyCandidate
from app.schemas.icp import ICPResponse


class CompanyDiscoveryProvider(ABC):
    @abstractmethod
    def discover_companies(
        self,
        icp: ICPResponse,
        limit: int = 100,
    ) -> List[CompanyCandidate]:
        raise NotImplementedError

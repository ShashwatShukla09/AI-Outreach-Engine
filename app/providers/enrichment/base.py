from abc import ABC, abstractmethod
from typing import Any, Dict, List


class CompanyEnrichmentProvider(ABC):
    @abstractmethod
    def enrich_company(
        self,
        company: dict,
        fields: List[str],
    ) -> Dict[str, Any]:
        raise NotImplementedError

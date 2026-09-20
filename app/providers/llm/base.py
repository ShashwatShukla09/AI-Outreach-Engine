from abc import ABC, abstractmethod

from app.schemas.icp import ICPGenerationResult
from app.schemas.product import ProductResponse


class ICPProvider(ABC):
    """
    Contract that every ICP-generation provider must follow.
    """

    @abstractmethod
    def generate_icps(
        self,
        product: ProductResponse,
    ) -> ICPGenerationResult:
        """
        Generate structured ICP definitions for a product.
        """
        raise NotImplementedError

from abc import ABC, abstractmethod
from typing import List

from app.schemas.contact import ContactCandidate


class ContactProvider(ABC):
    @abstractmethod
    def discover_contacts(
        self,
        company: dict,
    ) -> List[ContactCandidate]:
        raise NotImplementedError

from abc import ABC, abstractmethod
from typing import List

from app.schemas.signal import SignalCreate


class SignalProvider(ABC):
    @abstractmethod
    def discover_signals(
        self,
        company: dict,
    ) -> List[SignalCreate]:
        raise NotImplementedError

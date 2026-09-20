from abc import ABC, abstractmethod


class OutreachExecutionProvider(ABC):
    @abstractmethod
    def send(
        self,
        message: dict,
        contact: dict,
    ) -> dict:
        raise NotImplementedError

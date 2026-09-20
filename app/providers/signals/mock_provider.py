from typing import List

from app.providers.signals.base import (
    SignalProvider,
)
from app.schemas.signal import SignalCreate


class MockSignalProvider(SignalProvider):
    def discover_signals(
        self,
        company: dict,
    ) -> List[SignalCreate]:
        if company["name"] == "NovaCart India":
            return [
                SignalCreate(
                    signal_type="FUNDING",
                    title="Recent funding round",
                    description=(
                        "Company recently raised "
                        "additional capital."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
                SignalCreate(
                    signal_type="SUPPORT_HIRING",
                    title=(
                        "Hiring customer support staff"
                    ),
                    description=(
                        "Company is expanding its "
                        "customer support team."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
            ]

        return []

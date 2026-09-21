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

        signals_by_company = {
            "NovaCart India": [
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
                    title="Hiring customer support staff",
                    description=(
                        "Company is expanding its "
                        "customer support team."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
            ],

            "UrbanBasket": [
                SignalCreate(
                    signal_type="SUPPORT_HIRING",
                    title="Expanding support operations",
                    description=(
                        "Company is hiring additional "
                        "customer support staff."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
            ],

            "Northstar Software": [
                SignalCreate(
                    signal_type="FUNDING",
                    title="Growth funding announced",
                    description=(
                        "Company recently announced "
                        "new growth funding."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
                SignalCreate(
                    signal_type="SUPPORT_HIRING",
                    title="Customer success team expansion",
                    description=(
                        "Company is expanding its "
                        "customer-facing operations team."
                    ),
                    source="mock",
                    confidence="HIGH",
                ),
            ],

            "Atlas Systems": [
                SignalCreate(
                    signal_type="SUPPORT_HIRING",
                    title="Customer operations hiring",
                    description=(
                        "Company is recruiting for "
                        "customer operations roles."
                    ),
                    source="mock",
                    confidence="MEDIUM",
                ),
            ],
        }

        return signals_by_company.get(
            company["name"],
            [],
        )

from app.providers.signals.base import (
    SignalProvider,
)
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.services.signal_discovery_service import (
    discover_and_save_signals,
)


def discover_signals_and_rescore(
    company_id: int,
    provider: SignalProvider,
) -> dict:
    previous_score = get_company_score(
        company_id
    )

    discovered_signals = (
        discover_and_save_signals(
            company_id=company_id,
            provider=provider,
        )
    )

    score = score_and_save_company(
        company_id
    )

    return {
        "previous_score": previous_score,
        "new_signals": discovered_signals,
        "new_signal_count": len(
            discovered_signals
        ),
        "score": score,
    }

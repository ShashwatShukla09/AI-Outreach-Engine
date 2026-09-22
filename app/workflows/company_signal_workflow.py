from app.providers.signals.base import (
    SignalProvider,
)
from app.repositories.company_score_repository import (
    get_company_score,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.repositories.signal_research_repository import (
    save_signal_research,
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
    provider_name: str = "unknown",
) -> dict:
    """
    Run signal research, persist its state,
    and recalculate the company score.

    new_signal_count means newly inserted evidence.

    total_signal_count means all currently persisted
    qualifying signal evidence for the company.

    Research state is based on total evidence, so an
    idempotent rerun cannot incorrectly turn
    SIGNALS_FOUND into RESEARCHED_NO_SIGNALS.
    """

    previous_score = get_company_score(
        company_id
    )

    discovered_signals = (
        discover_and_save_signals(
            company_id=company_id,
            provider=provider,
        )
    )

    all_signals = get_company_signals(
        company_id
    )

    research = save_signal_research(
        company_id=company_id,
        provider=provider_name,
        signals_found=len(all_signals),
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
        "total_signal_count": len(
            all_signals
        ),
        "signal_research": research,
        "score": score,
    }

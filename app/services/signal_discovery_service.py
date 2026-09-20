from typing import List

from app.providers.signals.base import (
    SignalProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.signal_repository import (
    create_signal,
    find_existing_signal,
)


def discover_and_save_signals(
    company_id: int,
    provider: SignalProvider,
) -> List[dict]:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    discovered = provider.discover_signals(
        company
    )

    saved = []

    for signal in discovered:
        existing = find_existing_signal(
            company_id=company_id,
            signal_type=signal.signal_type,
            title=signal.title,
        )

        if existing is not None:
            continue

        created = create_signal(
            company_id=company_id,
            signal=signal,
        )

        saved.append(created)

    return saved

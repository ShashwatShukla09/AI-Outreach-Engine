from app.providers.contacts.base import (
    ContactProvider,
)
from app.providers.signals.base import (
    SignalProvider,
)
from app.repositories.company_repository import (
    get_company_by_id,
)
from app.repositories.contact_repository import (
    get_company_contacts,
)
from app.repositories.signal_repository import (
    get_company_signals,
)
from app.services.buyer_relevance_service import (
    evaluate_company_buyers,
)
from app.services.company_scoring_service import (
    score_and_save_company,
)
from app.services.contact_discovery_service import (
    discover_and_save_contacts,
)
from app.services.signal_discovery_service import (
    discover_and_save_signals,
)


def build_buyer_intelligence(
    company_id: int,
    contact_provider: ContactProvider,
    signal_provider: SignalProvider,
) -> dict:
    company = get_company_by_id(company_id)

    if company is None:
        raise ValueError("Company not found")

    new_contacts = discover_and_save_contacts(
        company_id=company_id,
        provider=contact_provider,
    )

    evaluated_contacts = (
        evaluate_company_buyers(
            company_id
        )
    )

    new_signals = discover_and_save_signals(
        company_id=company_id,
        provider=signal_provider,
    )

    score = score_and_save_company(
        company_id
    )

    contacts = get_company_contacts(
        company_id
    )

    signals = get_company_signals(
        company_id
    )

    ranked_contacts = sorted(
        contacts,
        key=lambda contact: (
            contact["relevance_score"]
            if contact["relevance_score"]
            is not None
            else -1
        ),
        reverse=True,
    )

    primary_buyer = (
        ranked_contacts[0]
        if ranked_contacts
        and ranked_contacts[0][
            "relevance_score"
        ] > 0
        else None
    )

    return {
        "company": company,
        "new_contacts": new_contacts,
        "evaluated_contacts": (
            evaluated_contacts
        ),
        "contacts": contacts,
        "primary_buyer": primary_buyer,
        "new_signals": new_signals,
        "signals": signals,
        "score": score,
    }

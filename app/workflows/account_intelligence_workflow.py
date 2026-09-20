from app.providers.contacts.base import (
    ContactProvider,
)
from app.providers.signals.base import (
    SignalProvider,
)
from app.repositories.account_research_repository import (
    save_account_research,
)
from app.services.account_research_service import (
    build_account_research,
)
from app.workflows.buyer_intelligence_workflow import (
    build_buyer_intelligence,
)


def build_account_intelligence(
    company_id: int,
    contact_provider: ContactProvider,
    signal_provider: SignalProvider,
) -> dict:
    buyer_intelligence = (
        build_buyer_intelligence(
            company_id=company_id,
            contact_provider=contact_provider,
            signal_provider=signal_provider,
        )
    )

    research_brief = build_account_research(
        company_id
    )

    saved_research = save_account_research(
        research_brief
    )

    return {
        "company": buyer_intelligence[
            "company"
        ],
        "score": buyer_intelligence[
            "score"
        ],
        "contacts": buyer_intelligence[
            "contacts"
        ],
        "primary_buyer": buyer_intelligence[
            "primary_buyer"
        ],
        "signals": buyer_intelligence[
            "signals"
        ],
        "research_brief": research_brief,
        "saved_research": saved_research,
    }

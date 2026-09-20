import os

from app.providers.contacts.mock_provider import (
    MockContactProvider,
)
from app.providers.execution.n8n_provider import (
    N8nExecutionProvider,
)
from app.providers.signals.mock_provider import (
    MockSignalProvider,
)
from app.repositories.outreach_event_repository import (
    get_outreach_events,
)
from app.repositories.outreach_repository import (
    get_outreach_message,
)
from app.services.company_qualification_service import (
    qualify_company,
)
from app.services.outreach_execution_service import (
    execute_outreach,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
)
from app.workflows.account_intelligence_workflow import (
    build_account_intelligence,
)
from app.workflows.outreach_generation_workflow import (
    create_company_outreach,
)
from tests.test_company_scoring import (
    prepare_scoring_companies,
)


def main():
    webhook_url = os.getenv(
        "N8N_OUTREACH_WEBHOOK_URL"
    )

    if not webhook_url:
        raise ValueError(
            "N8N_OUTREACH_WEBHOOK_URL is not set."
        )

    print("\n1. Preparing NovaCart...")

    companies = prepare_scoring_companies()

    nova = next(
        company
        for company in companies
        if company.name == "NovaCart India"
    )

    print(
        f"   Company: {nova.name} "
        f"(ID {nova.id})"
    )

    qualification = qualify_company(
        nova.id
    )

    print(
        f"   Qualification: "
        f"{qualification.status}"
    )

    if qualification.status != "QUALIFIED":
        raise ValueError(
            "NovaCart is not qualified."
        )

    print(
        "\n2. Building account intelligence..."
    )

    intelligence = build_account_intelligence(
        company_id=nova.id,
        contact_provider=MockContactProvider(),
        signal_provider=MockSignalProvider(),
    )

    primary_buyer = intelligence[
        "primary_buyer"
    ]

    print(
        "   Primary buyer: "
        f'{primary_buyer["first_name"]} '
        f'{primary_buyer["last_name"]}'
    )

    print(
        "   Score: "
        f'{intelligence["score"].total_score}/100'
    )

    print(
        "\n3. Generating outreach..."
    )

    outreach_result = create_company_outreach(
        nova.id
    )

    draft = outreach_result["saved"]
    outreach_id = draft["id"]

    print(
        f"   Outreach ID: {outreach_id}"
    )
    print(
        f'   Status: {draft["status"]}'
    )
    print(
        f'   Recipient contact ID: '
        f'{draft["contact_id"]}'
    )

    print(
        "\n4. Human approval simulation..."
    )

    approved = approve_outreach_message(
        outreach_id
    )

    print(
        f'   Status: {approved["status"]}'
    )

    if approved["status"] != "APPROVED":
        raise ValueError(
            "Outreach was not approved."
        )

    print(
        "\n5. Sending to REAL n8n webhook..."
    )
    print(
        "   safe_test_mode = True"
    )
    print(
        "   No real email will be sent."
    )

    provider = N8nExecutionProvider(
        webhook_url=webhook_url,
        safe_test_mode=True,
    )

    result = execute_outreach(
        outreach_id=outreach_id,
        provider=provider,
    )

    print(
        "\n6. n8n response received."
    )

    provider_response = result[
        "provider_result"
    ]

    print(
        "   Provider: "
        f'{provider_response["provider"]}'
    )

    n8n_response = provider_response[
        "response"
    ]

    print(
        "   n8n accepted: "
        f'{n8n_response.get("accepted")}'
    )

    print(
        "   n8n provider: "
        f'{n8n_response.get("provider")}'
    )

    print(
        "   Simulated: "
        f'{n8n_response.get("simulated")}'
    )

    print(
        "\n7. Checking database..."
    )

    final_message = get_outreach_message(
        outreach_id
    )

    print(
        "   Final status: "
        f'{final_message["status"]}'
    )

    print(
        "   sent_at: "
        f'{final_message["sent_at"]}'
    )

    print(
        "\n8. Outreach events:"
    )

    events = get_outreach_events(
        outreach_id
    )

    for event in events:
        print(
            f'   - {event["event_type"]}'
        )

    assert final_message["status"] == "SENT"

    assert [
        event["event_type"]
        for event in events
    ] == [
        "SEND_ATTEMPTED",
        "SENT",
    ]

    assert (
        n8n_response.get("accepted")
        is True
    )

    assert (
        n8n_response.get("simulated")
        is True
    )

    print(
        "\n================================"
    )
    print(
        "END-TO-END SAFE TEST PASSED"
    )
    print(
        "================================"
    )


if __name__ == "__main__":
    main()

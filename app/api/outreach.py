from fastapi import APIRouter, HTTPException
from app.db.database import get_connection

from app.providers.execution.n8n_provider import (
    N8nExecutionProvider,
)
from app.repositories.outreach_event_repository import (
    get_outreach_events,
)

from app.repositories.outreach_repository import (
    get_outreach_message,
    list_outreach_messages,
)
from app.schemas.outreach import OutreachEdit
from app.services.outreach_execution_service import (
    execute_outreach,
)
from app.services.outreach_review_service import (
    approve_outreach_message,
    edit_outreach,
    reject_outreach_message,
)


router = APIRouter(
    prefix="/api/outreach",
    tags=["outreach"],
)


def build_review_state(
    message: dict,
) -> dict:
    status = message["status"]

    return {
        "status": status,
        "can_edit": status == "DRAFT",
        "can_approve": status == "DRAFT",
        "can_reject": status == "DRAFT",
        "can_execute": status == "APPROVED",
    }


@router.get("/{outreach_id}/review")
def get_outreach_review(
    outreach_id: int,
):
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Outreach message not found.",
        )

    return {
        "outreach": message,
        "review": build_review_state(
            message
        ),
    }


@router.put("/{outreach_id}")
def edit_outreach_endpoint(
    outreach_id: int,
    edit: OutreachEdit,
):
    try:
        message = edit_outreach(
            outreach_id=outreach_id,
            edit=edit,
        )

    except ValueError as exc:
        error = str(exc)

        if error == "Outreach message not found":
            raise HTTPException(
                status_code=404,
                detail=error,
            )

        raise HTTPException(
            status_code=409,
            detail=error,
        )

    return {
        "outreach": message,
        "review": build_review_state(
            message
        ),
    }


@router.post("/{outreach_id}/approve")
def approve_outreach_endpoint(
    outreach_id: int,
):
    try:
        message = approve_outreach_message(
            outreach_id
        )

    except ValueError as exc:
        error = str(exc)

        if error == "Outreach message not found":
            raise HTTPException(
                status_code=404,
                detail=error,
            )

        raise HTTPException(
            status_code=409,
            detail=error,
        )

    return {
        "outreach": message,
        "review": build_review_state(
            message
        ),
    }


@router.post("/{outreach_id}/reject")
def reject_outreach_endpoint(
    outreach_id: int,
):
    try:
        message = reject_outreach_message(
            outreach_id
        )

    except ValueError as exc:
        error = str(exc)

        if error == "Outreach message not found":
            raise HTTPException(
                status_code=404,
                detail=error,
            )

        raise HTTPException(
            status_code=409,
            detail=error,
        )

    return {
        "outreach": message,
        "review": build_review_state(
            message
        ),
    }


@router.post("/{outreach_id}/execute")
def execute_outreach_endpoint(
    outreach_id: int,
):
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Outreach message not found",
        )

    if message["status"] != "APPROVED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only APPROVED outreach "
                "can be executed."
            ),
        )

    try:
        provider = N8nExecutionProvider(
            safe_test_mode=True,
        )

        result = execute_outreach(
            outreach_id=outreach_id,
            provider=provider,
        )

    except ValueError as exc:
        error = str(exc)

        if error == "Contact not found":
            raise HTTPException(
                status_code=404,
                detail=error,
            )

        raise HTTPException(
            status_code=409,
            detail=error,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Outreach execution provider "
                f"failed: {exc}"
            ),
        )

    sent_message = result["message"]

    return {
        "outreach": sent_message,
        "review": build_review_state(
            sent_message
        ),
        "execution": {
            "event": result["event"],
            "provider_result": (
                result["provider_result"]
            ),
        },
    }


@router.get("/{outreach_id}/events")
def get_outreach_events_endpoint(
    outreach_id: int,
):
    message = get_outreach_message(
        outreach_id
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Outreach message not found.",
        )

    events = get_outreach_events(
        outreach_message_id=outreach_id
    )

    return {
        "outreach_id": outreach_id,
        "status": message["status"],
        "events": events,
    }

@router.get("/dashboard/summary")
def get_outreach_dashboard_summary():
    drafts = list_outreach_messages(
        status="DRAFT",
        limit=1000,
    )

    approved = list_outreach_messages(
        status="APPROVED",
        limit=1000,
    )

    sent = list_outreach_messages(
        status="SENT",
        limit=1000,
    )

    rejected = list_outreach_messages(
        status="REJECTED",
        limit=1000,
    )

    connection = get_connection()

    try:
        qualified_companies = connection.execute(
            """
            SELECT COUNT(*)
            FROM companies
            WHERE qualification_status = 'QUALIFIED'
            """
        ).fetchone()[0]

        high_intent = connection.execute(
            """
            SELECT COUNT(*)
            FROM companies c
            WHERE c.qualification_status = 'QUALIFIED'
              AND (
                  SELECT cs.priority
                  FROM company_scores cs
                  WHERE cs.company_id = c.id
                  ORDER BY cs.id DESC
                  LIMIT 1
              ) = 'HIGH'
            """
        ).fetchone()[0]
    finally:
        connection.close()

    return {
        "metrics": {
            "qualified_companies": qualified_companies,
            "high_intent": high_intent,
            "pending_review": len(drafts),
            "approved": len(approved),
            "sent": len(sent),
            "rejected": len(rejected),
        },
        "review_queue": drafts[:10],
        "ready_to_send": approved[:10],
        "sent_history": sent[:10],
    }

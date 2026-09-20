from typing import Optional

from pydantic import BaseModel, Field


class OutreachDraft(BaseModel):
    company_id: int
    contact_id: int
    channel: str = "EMAIL"
    subject: Optional[str] = None
    message_body: str
    personalisation_reason: str


class OutreachResponse(BaseModel):
    id: int
    company_id: int
    contact_id: Optional[int]
    channel: str
    subject: Optional[str]
    message_body: str
    personalisation_reason: Optional[str]
    status: str
    approved_at: Optional[str]
    rejected_at: Optional[str]
    sent_at: Optional[str]
    created_at: str
    updated_at: str


class OutreachEdit(BaseModel):
    subject: Optional[str] = Field(
        default=None,
        max_length=300,
    )
    message_body: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

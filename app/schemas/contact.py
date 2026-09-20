from typing import Optional

from pydantic import BaseModel, Field


class ContactCandidate(BaseModel):
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )
    job_title: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )
    email: Optional[str] = Field(
        default=None,
        max_length=300,
    )
    linkedin_url: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    enrichment_provider: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )


class ContactResponse(BaseModel):
    id: int
    company_id: int
    first_name: str
    last_name: str
    job_title: str
    buyer_category: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    enrichment_provider: Optional[str]
    enrichment_status: Optional[str]
    relevance_score: Optional[int]
    relevance_reason: Optional[str]
    created_at: str

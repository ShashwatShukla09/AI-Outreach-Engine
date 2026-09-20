from typing import Optional

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    signal_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )
    title: str = Field(
        ...,
        min_length=2,
        max_length=300,
    )
    description: Optional[str] = Field(
        default=None,
        max_length=3000,
    )
    source: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    signal_date: Optional[str] = None
    confidence: str = Field(
        default="MEDIUM",
        pattern="^(LOW|MEDIUM|HIGH)$",
    )


class SignalResponse(SignalCreate):
    id: int
    company_id: int
    created_at: str

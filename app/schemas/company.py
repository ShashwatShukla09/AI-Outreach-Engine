from typing import Optional

from pydantic import BaseModel, Field


class CompanyCandidate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=300,
    )

    domain: Optional[str] = Field(
        default=None,
        max_length=300,
    )

    country: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    industry: Optional[str] = Field(
        default=None,
        max_length=200,
    )

    employee_count: Optional[int] = Field(
        default=None,
        ge=1,
    )

    business_model: Optional[str] = Field(
        default=None,
        max_length=200,
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


class CompanyResponse(BaseModel):
    id: int
    icp_id: int

    name: str
    domain: Optional[str]
    country: Optional[str]
    market: Optional[str]
    industry: Optional[str]
    employee_count: Optional[int]
    business_model: Optional[str]

    source: Optional[str]
    source_url: Optional[str]

    qualification_status: str
    created_at: str

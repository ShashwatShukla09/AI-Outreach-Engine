from typing import List, Optional

from pydantic import BaseModel, Field


class ICPDefinition(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    industries: List[str] = Field(
        ...,
        min_length=1,
    )

    company_size_min: int = Field(
        ...,
        ge=1,
    )

    company_size_max: int = Field(
        ...,
        ge=1,
    )

    target_market: str = Field(
        ...,
        pattern="^(INDIA|INTERNATIONAL)$",
    )

    target_countries: List[str] = Field(
        default_factory=list,
    )

    business_models: List[str] = Field(
        default_factory=list,
    )

    buyer_categories: List[str] = Field(
        ...,
        min_length=1,
    )

    pain_points: List[str] = Field(
        ...,
        min_length=1,
    )

    segment_rationale: str = Field(
        ...,
        min_length=10,
    )

    buyer_rationale: str = Field(
        ...,
        min_length=10,
    )

    assumptions: List[str] = Field(
        default_factory=list,
    )


class ICPGenerationResult(BaseModel):
    product_id: int

    icps: List[ICPDefinition] = Field(
        ...,
        min_length=1,
    )

class ICPResponse(ICPDefinition):
    id: int
    product_id: int
    status: str
    reviewed_at: Optional[str] = None
    created_at: str


class ICPUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    industries: Optional[List[str]] = None

    company_size_min: Optional[int] = Field(
        default=None,
        ge=1,
    )

    company_size_max: Optional[int] = Field(
        default=None,
        ge=1,
    )

    target_countries: Optional[List[str]] = None
    business_models: Optional[List[str]] = None
    buyer_categories: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None

    segment_rationale: Optional[str] = Field(
        default=None,
        min_length=10,
    )

    buyer_rationale: Optional[str] = Field(
        default=None,
        min_length=10,
    )

    assumptions: Optional[List[str]] = None

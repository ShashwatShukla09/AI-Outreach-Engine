from typing import Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=3000,
    )

    value_proposition: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    target_problem: Optional[str] = Field(
        default=None,
        max_length=2000,
    )


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    value_proposition: Optional[str]
    target_problem: Optional[str]
    created_at: str

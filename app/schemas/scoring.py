from typing import List

from pydantic import BaseModel, Field


class ScoreComponent(BaseModel):
    name: str
    score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    explanation: str


class CompanyScoreResult(BaseModel):
    company_id: int
    icp_fit_score: int = Field(..., ge=0, le=60)
    intent_score: int = Field(..., ge=0, le=30)
    data_confidence_score: int = Field(..., ge=0, le=10)
    total_score: int = Field(..., ge=0, le=100)
    priority: str
    components: List[ScoreComponent]

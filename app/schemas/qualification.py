from typing import List

from pydantic import BaseModel


class QualificationResult(BaseModel):
    company_id: int
    status: str
    reasons: List[str]
    missing_fields: List[str]

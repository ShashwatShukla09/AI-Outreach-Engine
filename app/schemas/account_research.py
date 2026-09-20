from typing import List, Optional

from pydantic import BaseModel


class AccountResearchBrief(BaseModel):
    company_id: int
    company_summary: str
    why_company: List[str]
    why_now: List[str]
    pain_points: List[str]
    relevant_evidence: List[str]
    primary_buyer: Optional[str] = None

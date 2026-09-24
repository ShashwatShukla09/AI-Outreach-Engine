from typing import Optional

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    product_id: int
    icp_id: int
    name: str
    market: Optional[str] = None


class CampaignResponse(BaseModel):
    id: int
    product_id: int
    icp_id: int
    name: str
    market: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class CampaignStatusUpdate(BaseModel):
    status: str


class CampaignCompanyAdd(BaseModel):
    company_id: int

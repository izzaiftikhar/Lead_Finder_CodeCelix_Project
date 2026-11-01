from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    country: str = 'UAE'
    niche: str = 'All'
    city: str = 'All'
    limit: int = Field(default=50, ge=1, le=200)
    query: str = ''


class LeadResponse(BaseModel):
    id: int
    business_name: str
    country: str
    city: str
    niche: str
    website: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_status: Optional[str] = None
    automation_status: Optional[str] = None
    chatbot_status: Optional[str] = None
    lead_score: Optional[int] = None
    evidence: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    mode: str
    database: str
    real_discovery: bool


class OptionsResponse(BaseModel):
    countries: list[str]
    cities: list[str]
    niches: list[str]


class LeadsResponse(BaseModel):
    items: list[LeadResponse]
    demo: bool


class SearchResponse(BaseModel):
    job_id: str
    status: str
    accepted: int
    requested: int
    message: str
    notice: str
    items: list[LeadResponse]


class ResetDemoResponse(BaseModel):
    ok: bool
    message: str
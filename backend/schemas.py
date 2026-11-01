from typing import Optional
from pydantic import BaseModel, Field


class Creds(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)


class Filters(BaseModel):
    whatsapp_confirmed_only: bool = True
    no_chatbot_only: bool = False
    manual_whatsapp_only: bool = False
    website_required: bool = False
    exclude_previously_exported: bool = True


class JobCreate(BaseModel):
    country: str = Field(max_length=2)
    niche: str = Field(max_length=30)
    city_ids: list[int] = Field(default_factory=list, max_length=500)
    all_cities: bool = False
    lead_count: int = 50
    mode: str = "live"
    filters: Filters = Filters()


class Feedback(BaseModel):
    value: str  # CORRECT | WRONG_WHATSAPP | WRONG_CHATBOT | NOT_RELEVANT


class NicheToggle(BaseModel):
    country: str
    niche: str
    enabled: bool


class KeywordIn(BaseModel):
    id: Optional[int] = None
    niche: str
    region: str = "ANY"
    lang: str = "en"
    keyword: str = Field(min_length=1, max_length=100)
    enabled: bool = True


class SignatureIn(BaseModel):
    id: Optional[int] = None
    vendor: str = Field(min_length=1, max_length=60)
    kind: str = "LIVE_CHAT"
    scope: str = "chatbot"
    pattern: str = Field(min_length=3, max_length=200)
    enabled: bool = True


class LimitIn(BaseModel):
    key: str
    value: float


class SuppressIn(BaseModel):
    value: str = Field(min_length=3, max_length=300)

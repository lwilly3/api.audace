"""
Schemas Pydantic pour l'integration Google Analytics 4 (GA4).

Schemas de validation pour les proprietes GA4 et les reponses analytiques
retournees par le backend vers le frontend.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# ═══ GA4 Properties ═══

class GaPropertyCreate(BaseModel):
    """Creation d'une propriete GA4."""
    property_id: str
    display_name: str
    website_url: Optional[str] = None


class GaPropertyResponse(BaseModel):
    """Reponse pour une propriete GA4."""
    id: int
    property_id: str
    display_name: str
    website_url: Optional[str] = None
    created_by: int
    created_at: datetime
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# ═══ Realtime ═══

class GaRealtimeResponse(BaseModel):
    """Donnees temps reel GA4 (30 dernieres minutes)."""
    active_users: int = 0
    pageviews: int = 0
    events: int = 0
    top_pages: list[dict] = []
    top_sources: list[dict] = []
    by_device: list[dict] = []
    by_country: list[dict] = []


# ═══ Overview ═══

class GaOverviewResponse(BaseModel):
    """Vue d'ensemble des metriques GA4 avec comparaison periode precedente."""
    active_users: int = 0
    new_users: int = 0
    sessions: int = 0
    page_views: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0
    engagement_rate: float = 0.0
    engaged_sessions: int = 0
    events_count: int = 0
    active_users_change: float = 0.0
    sessions_change: float = 0.0
    page_views_change: float = 0.0
    bounce_rate_change: float = 0.0
    period_start: str = ""
    period_end: str = ""


# ═══ Traffic Sources ═══

class GaSourceItem(BaseModel):
    source: str
    medium: str
    sessions: int = 0
    users: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0
    conversions: int = 0


class GaSourcesResponse(BaseModel):
    items: list[GaSourceItem] = []
    total_sessions: int = 0


# ═══ Top Pages ═══

class GaPageItem(BaseModel):
    page_title: str
    page_path: str
    page_views: int = 0
    users: int = 0
    avg_time_on_page: float = 0.0
    bounce_rate: float = 0.0
    entrances: int = 0


class GaPagesResponse(BaseModel):
    items: list[GaPageItem] = []
    total_page_views: int = 0


# ═══ Geography ═══

class GaGeoItem(BaseModel):
    country: str
    city: Optional[str] = None
    users: int = 0
    sessions: int = 0
    page_views: int = 0


class GaGeographyResponse(BaseModel):
    by_country: list[GaGeoItem] = []
    by_city: list[GaGeoItem] = []


# ═══ Technology ═══

class GaTechItem(BaseModel):
    name: str
    users: int = 0
    sessions: int = 0
    percentage: float = 0.0


class GaTechnologyResponse(BaseModel):
    by_browser: list[GaTechItem] = []
    by_os: list[GaTechItem] = []
    by_device: list[GaTechItem] = []


# ═══ Time Series (Trends) ═══

class GaTrendPoint(BaseModel):
    date: str
    active_users: int = 0
    sessions: int = 0
    page_views: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0


class GaTrendsResponse(BaseModel):
    points: list[GaTrendPoint] = []
    period_start: str = ""
    period_end: str = ""

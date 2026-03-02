from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# =============================================
# Schemas pour les Alertes Publiques (P3)
# =============================================

class PublicAlertCreate(BaseModel):
    """Schema pour creer une alerte publique."""
    title: str = Field(..., max_length=255, description="Titre de l'alerte")
    message: str = Field(..., description="Contenu du message")
    alert_type: str = Field(default="info", description="Type: info, warning, urgent")
    is_active: bool = Field(default=True)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    url: Optional[str] = Field(None, max_length=500, description="Lien CTA optionnel")

    model_config = ConfigDict(from_attributes=True)


class PublicAlertUpdate(BaseModel):
    """Schema pour mettre a jour une alerte publique."""
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    alert_type: Optional[str] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PublicAlertResponse(BaseModel):
    """Schema de reponse pour une alerte publique."""
    id: int
    title: str
    message: str
    alert_type: str
    is_active: bool
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================
# Schemas pour Now Playing (P1)
# =============================================

class NowPlayingPresenter(BaseModel):
    """Animateur dans le contexte now-playing."""
    id: int
    name: str
    biography: Optional[str] = None
    profilePicture: Optional[str] = None
    isMainPresenter: bool = False

    model_config = ConfigDict(from_attributes=True)


class NowPlayingSegment(BaseModel):
    """Segment en cours dans le contexte now-playing."""
    id: int
    title: str
    type: str
    duration: int
    position: int
    startTime: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NowPlayingShow(BaseModel):
    """Emission dans le contexte now-playing."""
    id: int
    title: str
    type: str
    broadcast_date: Optional[datetime] = None
    duration: int
    status: str
    description: Optional[str] = None
    emission_title: Optional[str] = None
    presenters: List[NowPlayingPresenter] = []
    current_segment: Optional[NowPlayingSegment] = None

    model_config = ConfigDict(from_attributes=True)


class NowPlayingResponse(BaseModel):
    """Reponse de l'endpoint now-playing."""
    current_show: Optional[NowPlayingShow] = None
    next_show: Optional[NowPlayingShow] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================
# Schemas pour la Grille des Programmes (P2)
# =============================================

class ScheduleShowEntry(BaseModel):
    """Entree de la grille des programmes."""
    id: int
    title: str
    type: str
    broadcast_date: Optional[datetime] = None
    duration: int
    status: str
    description: Optional[str] = None
    emission_title: Optional[str] = None
    presenter_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WeeklyScheduleResponse(BaseModel):
    """Reponse de l'endpoint schedule."""
    week_start: str
    week_end: str
    days: Dict[str, List[ScheduleShowEntry]]

    model_config = ConfigDict(from_attributes=True)


# =============================================
# Schemas pour les Animateurs Publics (P4)
# =============================================

class PublicPresenterResponse(BaseModel):
    """Profil public d'un animateur."""
    id: int
    name: str
    biography: Optional[str] = None
    profilePicture: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================
# Schemas pour les Statistiques d'Ecoute (P6)
# =============================================

class ListenEventCreate(BaseModel):
    """Schema pour enregistrer un evenement d'ecoute."""
    session_id: str = Field(..., max_length=100)
    event_type: str = Field(..., description="play, pause, stop, heartbeat")
    duration: int = Field(default=0, ge=0)
    page_url: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class DailyListenBreakdown(BaseModel):
    """Repartition journaliere des ecoutes."""
    date: str
    count: int
    unique_sessions: int


class ListenStatsResponse(BaseModel):
    """Reponse de l'endpoint listen-stats."""
    total_listens_today: int = 0
    unique_sessions_today: int = 0
    avg_duration_seconds: float = 0.0
    peak_hour: Optional[int] = None
    total_listens_week: int = 0
    daily_breakdown: List[DailyListenBreakdown] = []

    model_config = ConfigDict(from_attributes=True)

"""
Schémas Pydantic pour le module Social.

Définit les schémas de validation pour les requêtes et réponses
de l'API Social (comptes, posts, commentaires, messages, stats).
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ════════════════════════════════════════════════════════════════
# COMPTES SOCIAUX
# ════════════════════════════════════════════════════════════════

class SocialAccountResponse(BaseModel):
    """Réponse pour un compte social connecté."""
    id: int
    platform: str
    account_name: str
    account_id: str
    account_type: str = "page"
    avatar_url: Optional[str] = None
    profile_picture: Optional[str] = None
    profile_url: Optional[str] = None
    followers_count: Optional[int] = None
    connected_by: int
    connected_at: datetime
    token_expires_at: Optional[datetime] = None
    is_active: bool = True
    permissions: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class SocialAccountStatusResponse(BaseModel):
    """Statut du token d'un compte."""
    valid: bool
    expires_at: Optional[datetime] = None


class OAuthRedirectResponse(BaseModel):
    """Réponse OAuth - URL de redirection."""
    redirect_url: str
    state: str


# ════════════════════════════════════════════════════════════════
# PUBLICATIONS
# ════════════════════════════════════════════════════════════════

class SocialPostResultResponse(BaseModel):
    """Résultat de publication par plateforme/compte."""
    account_id: int
    account_name: Optional[str] = None
    platform: str
    status: str = "pending"
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    impressions: int = 0
    clicks: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SocialPostCreate(BaseModel):
    """Données pour créer un post."""
    content: str = Field(..., min_length=1, max_length=63206, description="Contenu du post")
    media_urls: list[str] = Field(default=[], description="URLs des médias")
    link_url: Optional[str] = Field(None, description="URL du lien partagé")
    hashtags: list[str] = Field(default=[], description="Hashtags")
    platforms: list[str] = Field(default=[], description="Plateformes cibles")
    target_accounts: list[str] = Field(default=[], description="IDs des comptes cibles")
    scheduled_at: Optional[datetime] = Field(None, description="Date de publication planifiée")

    model_config = ConfigDict(from_attributes=True)


class SocialPostUpdate(BaseModel):
    """Données pour modifier un post (tous les champs optionnels)."""
    content: Optional[str] = Field(None, min_length=1, max_length=63206)
    media_urls: Optional[list[str]] = None
    link_url: Optional[str] = None
    hashtags: Optional[list[str]] = None
    platforms: Optional[list[str]] = None
    target_accounts: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SocialPostResponse(BaseModel):
    """Réponse complète pour un post."""
    id: int
    content: str
    media_urls: list[str] = []
    link_url: Optional[str] = None
    hashtags: list[str] = []
    platforms: list[str] = []
    target_accounts: list[str] = []
    status: str = "draft"
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_by: int
    created_by_name: Optional[str] = None
    is_synced: bool = False
    created_at: datetime
    updated_at: datetime
    results: list[SocialPostResultResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SchedulePostRequest(BaseModel):
    """Requête pour planifier un post."""
    scheduled_at: datetime = Field(..., description="Date de publication planifiée")


# ════════════════════════════════════════════════════════════════
# INBOX — COMMENTAIRES
# ════════════════════════════════════════════════════════════════

class SocialCommentResponse(BaseModel):
    """Réponse pour un commentaire."""
    id: int
    platform_comment_id: str
    post_id: Optional[int] = None
    post_content: Optional[str] = None
    account_id: int
    account_name: Optional[str] = None
    platform: str
    author_name: str
    author_avatar: Optional[str] = None
    author_platform_id: str
    content: str
    parent_comment_id: Optional[int] = None
    is_read: bool = False
    is_hidden: bool = False
    sentiment: Optional[str] = None
    likes_count: int = 0
    created_at: datetime
    replies: list["SocialCommentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class ReplyToCommentRequest(BaseModel):
    """Requête pour répondre à un commentaire."""
    content: str = Field(..., min_length=1, max_length=8000, description="Contenu de la réponse")


# ════════════════════════════════════════════════════════════════
# INBOX — MESSAGES
# ════════════════════════════════════════════════════════════════

class SocialMessageResponse(BaseModel):
    """Réponse pour un message privé."""
    id: int
    conversation_id: int
    platform_message_id: str
    account_id: int
    account_name: Optional[str] = None
    platform: str
    sender_name: str
    sender_avatar: Optional[str] = None
    sender_platform_id: str
    content: str
    direction: str = "inbound"
    is_read: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialConversationResponse(BaseModel):
    """Réponse pour une conversation."""
    id: int
    account_id: int
    platform: str
    participant_name: str
    participant_avatar: Optional[str] = None
    last_message: Optional[SocialMessageResponse] = None
    last_message_at: Optional[datetime] = None
    updated_at: datetime
    unread_count: int = 0
    messages: list[SocialMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ReplyToConversationRequest(BaseModel):
    """Requête pour répondre dans une conversation."""
    content: str = Field(..., min_length=1, max_length=8000, description="Contenu du message")


# ════════════════════════════════════════════════════════════════
# STATISTIQUES
# ════════════════════════════════════════════════════════════════

class PlatformStatsResponse(BaseModel):
    """Statistiques par plateforme."""
    platform: str
    posts_count: int = 0
    impressions: int = 0
    engagements: int = 0
    clicks: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    followers: int = 0
    followers_growth: int = 0


class BestTimeSlotResponse(BaseModel):
    """Meilleur horaire de publication."""
    platform: str
    day_of_week: int
    day_name: str
    hour: int
    avg_engagement: float = 0.0
    engagement_score: float = 0.0
    posts_count: int = 0
    score: str = "medium"  # high, medium, low


class TimeSeriesPointResponse(BaseModel):
    """Point de données temporel."""
    date: str
    impressions: int = 0
    clicks: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0


class SocialAnalyticsOverviewResponse(BaseModel):
    """Vue d'ensemble des statistiques."""
    total_posts: int = 0
    total_published: int = 0
    total_scheduled: int = 0
    total_drafts: int = 0
    total_impressions: int = 0
    total_clicks: int = 0
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    total_reach: int = 0
    avg_engagement_rate: float = 0.0
    followers_total: int = 0
    followers_growth: int = 0
    impressions_change: float = 0.0
    engagements_change: float = 0.0
    reach_change: float = 0.0
    engagement_rate_change: float = 0.0
    total_engagements: int = 0
    top_hashtags: list[str] = []
    top_platforms: list[str] = []
    period_start: str = ""
    period_end: str = ""


# ════════════════════════════════════════════════════════════════
# ANALYTICS — REACTIONS, FOLLOWERS, VIDEO
# ════════════════════════════════════════════════════════════════

class ReactionsBreakdownResponse(BaseModel):
    """Repartition des reactions par type."""
    like: int = 0
    love: int = 0
    wow: int = 0
    haha: int = 0
    sorry: int = 0
    anger: int = 0
    total: int = 0
    period_start: str = ""
    period_end: str = ""


class FollowerTrendPointResponse(BaseModel):
    """Point de donnees pour la tendance des abonnes."""
    date: str
    total_followers: int = 0
    new_followers: int = 0
    unfollows: int = 0
    net_change: int = 0


class FollowerTrendResponse(BaseModel):
    """Tendance des abonnes avec serie temporelle."""
    current_total: int = 0
    net_change_period: int = 0
    trend: list[FollowerTrendPointResponse] = []
    period_start: str = ""
    period_end: str = ""


class VideoPerformanceResponse(BaseModel):
    """Performance video de la page."""
    total_views: int = 0
    total_view_time_ms: int = 0
    avg_view_time_seconds: float = 0.0
    period_start: str = ""
    period_end: str = ""


# ════════════════════════════════════════════════════════════════
# GENERATION IA DEPUIS URL
# ════════════════════════════════════════════════════════════════

class GenerateFromUrlRequest(BaseModel):
    """Requete pour generer un post a partir d'une URL (article web ou video YouTube)."""
    url: str = Field(..., min_length=10, max_length=2000, description="URL de l'article ou de la video YouTube")
    mode: str = Field("post_engageant", description="Mode de generation: post_engageant, resume, informatif, annonce, resume_video, points_cles")
    custom_instructions: Optional[str] = Field(None, max_length=500, description="Instructions supplementaires de l'utilisateur")


class GenerateFromUrlResponse(BaseModel):
    """Reponse avec le contenu genere par l'IA."""
    generated_content: str = Field(..., description="Contenu genere pour le post")
    source_url: str = Field(..., description="URL source utilisee")
    source_type: str = Field("article", description="Type de source: article ou youtube")
    youtube_metadata: Optional[dict] = Field(None, description="Metadonnees YouTube (video_id, title, author, language, thumbnail_url)")

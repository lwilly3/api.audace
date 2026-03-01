"""
Modèles SQLAlchemy pour le module Social.

Tables :
- social_accounts         : Comptes sociaux connectés via OAuth
- social_posts            : Publications multi-plateformes
- social_post_results     : Résultats de publication par compte/plateforme
- social_comments         : Commentaires reçus (inbox)
- social_conversations    : Conversations de messages privés
- social_messages         : Messages privés individuels
- social_page_insights    : Métriques page-level quotidiennes (Facebook Insights)

Tous les modèles utilisent le soft delete (BaseModel).
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, Date,
    ForeignKey, func, Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from app.db.database import Base


# ────────────────────────────────────────────────────────────────
# Base avec soft delete
# ────────────────────────────────────────────────────────────────

class SocialBaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


# ────────────────────────────────────────────────────────────────
# COMPTES SOCIAUX
# ────────────────────────────────────────────────────────────────

class SocialAccount(SocialBaseModel):
    """Compte social connecté via OAuth (Facebook, Instagram, LinkedIn, X)."""
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False, index=True)  # facebook, instagram, linkedin, twitter
    account_name = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=False)  # ID sur la plateforme
    account_type = Column(String(20), nullable=False, default="page")  # page, profile, business
    avatar_url = Column(Text, nullable=True)
    profile_picture = Column(Text, nullable=True)
    profile_url = Column(Text, nullable=True)
    followers_count = Column(Integer, nullable=True, default=0)

    # OAuth tokens (chiffrés en production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Métadonnées
    connected_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(ARRAY(String), default=[], nullable=False)

    # Relations
    posts = relationship("SocialPostResult", back_populates="account", cascade="all, delete-orphan")
    comments = relationship("SocialComment", back_populates="account", cascade="all, delete-orphan")
    conversations = relationship("SocialConversation", back_populates="account", cascade="all, delete-orphan")
    page_insights = relationship("SocialPageInsight", back_populates="account", cascade="all, delete-orphan")


# ────────────────────────────────────────────────────────────────
# PUBLICATIONS
# ────────────────────────────────────────────────────────────────

class SocialPost(SocialBaseModel):
    """Publication multi-plateformes."""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    media_urls = Column(ARRAY(String), default=[], nullable=False)
    link_url = Column(Text, nullable=True)
    hashtags = Column(ARRAY(String), default=[], nullable=False)
    platforms = Column(ARRAY(String), default=[], nullable=False)  # ['facebook', 'instagram']
    target_accounts = Column(ARRAY(String), default=[], nullable=False)  # IDs des comptes cibles

    # Statut
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, scheduled, publishing, published, error

    # Dates
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Auteur
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relations
    results = relationship("SocialPostResult", back_populates="post", cascade="all, delete-orphan")


# ────────────────────────────────────────────────────────────────
# RÉSULTATS DE PUBLICATION
# ────────────────────────────────────────────────────────────────

class SocialPostResult(SocialBaseModel):
    """Résultat de publication d'un post sur un compte spécifique."""
    __tablename__ = "social_post_results"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(20), nullable=False)

    # Statut de publication
    status = Column(String(20), nullable=False, default="pending")  # pending, published, error
    platform_post_id = Column(String(255), nullable=True)  # ID du post sur la plateforme
    platform_post_url = Column(Text, nullable=True)
    platform_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Métriques d'engagement
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    engagement_rate = Column(Float, default=0.0, nullable=False)

    # Relations
    post = relationship("SocialPost", back_populates="results")
    account = relationship("SocialAccount", back_populates="posts")


# ────────────────────────────────────────────────────────────────
# COMMENTAIRES (INBOX)
# ────────────────────────────────────────────────────────────────

class SocialComment(SocialBaseModel):
    """Commentaire reçu sur un post social."""
    __tablename__ = "social_comments"

    id = Column(Integer, primary_key=True, index=True)
    platform_comment_id = Column(String(255), nullable=False, unique=True)
    post_id = Column(Integer, ForeignKey("social_posts.id", ondelete="SET NULL"), nullable=True)
    post_content = Column(Text, nullable=True)  # Copie du contenu du post pour référence
    account_id = Column(Integer, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(20), nullable=False, index=True)

    # Auteur du commentaire
    author_name = Column(String(255), nullable=False)
    author_avatar = Column(Text, nullable=True)
    author_platform_id = Column(String(255), nullable=False)

    # Contenu
    content = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("social_comments.id", ondelete="SET NULL"), nullable=True)

    # Statut
    is_read = Column(Boolean, default=False, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    likes_count = Column(Integer, default=0, nullable=False)

    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    account = relationship("SocialAccount", back_populates="comments")
    replies = relationship(
        "SocialComment",
        backref=backref("parent", remote_side=[id]),
        foreign_keys=[parent_comment_id],
        cascade="all, delete-orphan",
        single_parent=True,
    )


# ────────────────────────────────────────────────────────────────
# CONVERSATIONS (MESSAGES PRIVÉS)
# ────────────────────────────────────────────────────────────────

class SocialConversation(SocialBaseModel):
    """Conversation de messages privés avec un utilisateur externe."""
    __tablename__ = "social_conversations"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(20), nullable=False, index=True)
    participant_name = Column(String(255), nullable=False)
    participant_avatar = Column(Text, nullable=True)

    # Compteurs
    unread_count = Column(Integer, default=0, nullable=False)

    # Dates
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    account = relationship("SocialAccount", back_populates="conversations")
    messages = relationship("SocialMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="SocialMessage.created_at")


class SocialMessage(SocialBaseModel):
    """Message privé individuel dans une conversation."""
    __tablename__ = "social_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("social_conversations.id", ondelete="CASCADE"), nullable=False)
    platform_message_id = Column(String(255), nullable=False, unique=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(20), nullable=False)

    # Expéditeur
    sender_name = Column(String(255), nullable=False)
    sender_avatar = Column(Text, nullable=True)
    sender_platform_id = Column(String(255), nullable=False)

    # Contenu
    content = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False, default="inbound")  # inbound, outbound

    # Statut
    is_read = Column(Boolean, default=False, nullable=False)

    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    conversation = relationship("SocialConversation", back_populates="messages")


# ────────────────────────────────────────────────────────────────
# INSIGHTS PAGE (MÉTRIQUES QUOTIDIENNES)
# ────────────────────────────────────────────────────────────────

class SocialPageInsight(SocialBaseModel):
    """Métriques page-level quotidiennes importées depuis Facebook Insights."""
    __tablename__ = "social_page_insights"
    __table_args__ = (
        UniqueConstraint("account_id", "date", name="uq_page_insight_account_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Impressions page
    page_impressions_unique = Column(Integer, default=0, nullable=False)
    page_posts_impressions = Column(Integer, default=0, nullable=False)
    page_posts_impressions_unique = Column(Integer, default=0, nullable=False)
    page_posts_impressions_organic = Column(Integer, default=0, nullable=False)
    page_posts_impressions_paid = Column(Integer, default=0, nullable=False)

    # Engagement page
    page_post_engagements = Column(Integer, default=0, nullable=False)
    page_views_total = Column(Integer, default=0, nullable=False)

    # Followers
    page_follows = Column(Integer, default=0, nullable=False)
    page_daily_follows = Column(Integer, default=0, nullable=False)
    page_daily_unfollows = Column(Integer, default=0, nullable=False)

    # Reactions detaillees
    reactions_like = Column(Integer, default=0, nullable=False)
    reactions_love = Column(Integer, default=0, nullable=False)
    reactions_wow = Column(Integer, default=0, nullable=False)
    reactions_haha = Column(Integer, default=0, nullable=False)
    reactions_sorry = Column(Integer, default=0, nullable=False)
    reactions_anger = Column(Integer, default=0, nullable=False)

    # Video
    page_video_views = Column(Integer, default=0, nullable=False)
    page_video_view_time = Column(Integer, default=0, nullable=False)  # en millisecondes

    # Relations
    account = relationship("SocialAccount", back_populates="page_insights")

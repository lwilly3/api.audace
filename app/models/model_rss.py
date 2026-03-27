"""
Modeles SQLAlchemy pour l'agregateur RSS du module Social.

Tables :
- rss_feeds     : Sources RSS enregistrees
- rss_articles  : Articles collectes depuis les flux RSS
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class RssFeed(Base):
    """Source RSS enregistree."""
    __tablename__ = "rss_feeds"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    category = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    site_url = Column(Text, nullable=True)
    favicon_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    max_articles = Column(Integer, default=100, nullable=False)  # Limite d'articles a conserver
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    articles = relationship("RssArticle", back_populates="feed", cascade="all, delete-orphan")


class RssArticle(Base):
    """Article collecte depuis un flux RSS."""
    __tablename__ = "rss_articles"
    __table_args__ = (
        UniqueConstraint("feed_id", "guid", name="uq_rss_article_feed_guid"),
    )

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False, index=True)
    guid = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    image_url = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    feed = relationship("RssFeed", back_populates="articles")

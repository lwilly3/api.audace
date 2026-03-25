"""
Schemas Pydantic pour l'agregateur RSS du module Social.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# === Feeds ===

class RssFeedCreate(BaseModel):
    title: str
    url: str
    category: Optional[str] = None
    description: Optional[str] = None


class RssFeedUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RssFeedResponse(BaseModel):
    id: int
    title: str
    url: str
    category: Optional[str] = None
    description: Optional[str] = None
    site_url: Optional[str] = None
    favicon_url: Optional[str] = None
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    last_error: Optional[str] = None
    article_count: int = 0
    unread_count: int = 0
    created_by: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# === Articles ===

class RssArticleResponse(BaseModel):
    id: int
    feed_id: int
    feed_title: str = ""
    feed_favicon: Optional[str] = None
    guid: str
    title: str
    url: str
    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    image_url: Optional[str] = None
    is_read: bool
    is_bookmarked: bool
    is_used: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RssArticleListResponse(BaseModel):
    items: list[RssArticleResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# === Stats ===

class RssStatsResponse(BaseModel):
    total_feeds: int
    active_feeds: int
    total_articles: int
    unread_count: int
    bookmarked_count: int
    used_count: int
    feeds_in_error: int


# === Refresh ===

class RssRefreshResult(BaseModel):
    feed_id: int
    feed_title: str
    new_articles: int
    error: Optional[str] = None

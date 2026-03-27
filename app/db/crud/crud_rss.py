"""
CRUD operations pour les flux RSS du module Social.
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status

from app.models.model_rss import RssFeed, RssArticle
from app.schemas.schema_rss import RssFeedCreate, RssFeedUpdate


# === FEEDS ===

def get_rss_feeds(db: Session, active_only: bool = True) -> list[dict]:
    """Liste les flux RSS avec article_count et unread_count."""
    query = db.query(RssFeed)
    if active_only:
        query = query.filter(RssFeed.is_active == True)
    feeds = query.order_by(RssFeed.title).all()

    result = []
    for feed in feeds:
        article_count = db.query(func.count(RssArticle.id)).filter(RssArticle.feed_id == feed.id).scalar() or 0
        unread_count = db.query(func.count(RssArticle.id)).filter(
            RssArticle.feed_id == feed.id, RssArticle.is_read == False
        ).scalar() or 0
        result.append({
            "id": feed.id,
            "title": feed.title,
            "url": feed.url,
            "category": feed.category,
            "description": feed.description,
            "site_url": feed.site_url,
            "favicon_url": feed.favicon_url,
            "is_active": feed.is_active,
            "max_articles": feed.max_articles,
            "last_fetched_at": feed.last_fetched_at,
            "last_error": feed.last_error,
            "article_count": article_count,
            "unread_count": unread_count,
            "created_by": feed.created_by,
            "created_at": feed.created_at,
        })
    return result


def get_rss_feed_by_id(db: Session, feed_id: int) -> RssFeed | None:
    return db.query(RssFeed).filter(RssFeed.id == feed_id).first()


def create_rss_feed(db: Session, data: RssFeedCreate, user_id: int) -> RssFeed:
    existing = db.query(RssFeed).filter(RssFeed.url == data.url).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un flux RSS avec cette URL existe deja",
        )
    feed = RssFeed(
        title=data.title,
        url=data.url,
        category=data.category,
        description=data.description,
        created_by=user_id,
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed


def update_rss_feed(db: Session, feed_id: int, data: RssFeedUpdate) -> RssFeed:
    feed = get_rss_feed_by_id(db, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Flux RSS introuvable")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feed, key, value)
    db.commit()
    db.refresh(feed)
    return feed


def delete_rss_feed(db: Session, feed_id: int) -> bool:
    feed = db.query(RssFeed).filter(RssFeed.id == feed_id).first()
    if not feed:
        return False
    db.delete(feed)
    db.commit()
    return True


# === ARTICLES ===

def get_rss_articles(
    db: Session,
    feed_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    is_used: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Liste les articles avec jointure feed pour feed_title/favicon."""
    query = db.query(RssArticle).join(RssFeed)
    query = query.filter(RssFeed.is_active == True)

    if feed_id:
        query = query.filter(RssArticle.feed_id == feed_id)
    if is_read is not None:
        query = query.filter(RssArticle.is_read == is_read)
    if is_bookmarked is not None:
        query = query.filter(RssArticle.is_bookmarked == is_bookmarked)
    if is_used is not None:
        query = query.filter(RssArticle.is_used == is_used)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            RssArticle.title.ilike(pattern),
            RssArticle.description.ilike(pattern),
            RssArticle.author.ilike(pattern),
        ))

    total = query.count()
    articles = (
        query
        .order_by(RssArticle.published_at.desc().nullslast())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    result = []
    for a in articles:
        result.append({
            "id": a.id,
            "feed_id": a.feed_id,
            "feed_title": a.feed.title if a.feed else "",
            "feed_favicon": a.feed.favicon_url if a.feed else None,
            "guid": a.guid,
            "title": a.title,
            "url": a.url,
            "description": a.description,
            "content": a.content,
            "author": a.author,
            "published_at": a.published_at,
            "image_url": a.image_url,
            "is_read": a.is_read,
            "is_bookmarked": a.is_bookmarked,
            "is_used": a.is_used,
            "created_at": a.created_at,
        })
    return result, total


def get_rss_article_by_id(db: Session, article_id: int) -> dict | None:
    a = db.query(RssArticle).filter(RssArticle.id == article_id).first()
    if not a:
        return None
    return {
        "id": a.id,
        "feed_id": a.feed_id,
        "feed_title": a.feed.title if a.feed else "",
        "feed_favicon": a.feed.favicon_url if a.feed else None,
        "guid": a.guid,
        "title": a.title,
        "url": a.url,
        "description": a.description,
        "content": a.content,
        "author": a.author,
        "published_at": a.published_at,
        "image_url": a.image_url,
        "is_read": a.is_read,
        "is_bookmarked": a.is_bookmarked,
        "is_used": a.is_used,
        "created_at": a.created_at,
    }


def mark_article_read(db: Session, article_id: int) -> RssArticle:
    article = db.query(RssArticle).filter(RssArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")
    article.is_read = True
    db.commit()
    db.refresh(article)
    return article


def toggle_article_bookmark(db: Session, article_id: int) -> RssArticle:
    article = db.query(RssArticle).filter(RssArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")
    article.is_bookmarked = not article.is_bookmarked
    db.commit()
    db.refresh(article)
    return article


def mark_article_used(db: Session, article_id: int) -> RssArticle:
    article = db.query(RssArticle).filter(RssArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")
    article.is_used = True
    db.commit()
    db.refresh(article)
    return article


def get_rss_stats(db: Session) -> dict:
    return {
        "total_feeds": db.query(func.count(RssFeed.id)).scalar() or 0,
        "active_feeds": db.query(func.count(RssFeed.id)).filter(RssFeed.is_active == True).scalar() or 0,
        "total_articles": db.query(func.count(RssArticle.id)).scalar() or 0,
        "unread_count": db.query(func.count(RssArticle.id)).filter(RssArticle.is_read == False).scalar() or 0,
        "bookmarked_count": db.query(func.count(RssArticle.id)).filter(RssArticle.is_bookmarked == True).scalar() or 0,
        "used_count": db.query(func.count(RssArticle.id)).filter(RssArticle.is_used == True).scalar() or 0,
        "feeds_in_error": db.query(func.count(RssFeed.id)).filter(RssFeed.last_error.isnot(None)).scalar() or 0,
    }


def get_rss_categories(db: Session) -> list[str]:
    rows = (
        db.query(RssFeed.category)
        .filter(RssFeed.category.isnot(None), RssFeed.category != "")
        .distinct()
        .order_by(RssFeed.category)
        .all()
    )
    return [r[0] for r in rows]

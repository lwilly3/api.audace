"""
Service de recuperation et parsing des flux RSS.

Utilise feedparser pour supporter RSS 2.0, Atom 1.0, et RSS 1.0.
Le fetch est declenche manuellement (via route) ou periodiquement
(via le scheduler social toutes les 30 min).
"""

import logging
from datetime import datetime, timezone

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.models.model_rss import RssFeed, RssArticle

logger = logging.getLogger("hapson-api")

FETCH_TIMEOUT = 15.0
USER_AGENT = "RadioManager/1.0 (RSS Aggregator)"


def fetch_single_feed(db: Session, feed: RssFeed) -> dict:
    """
    Recupere et parse un flux RSS, insere les nouveaux articles.
    Retourne { new_articles: int, error: str|None }
    """
    new_count = 0
    try:
        response = httpx.get(
            feed.url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        response.raise_for_status()

        parsed = feedparser.parse(response.text)

        if parsed.bozo and not parsed.entries:
            error_msg = str(parsed.bozo_exception) if parsed.bozo_exception else "Feed XML invalide"
            feed.last_error = error_msg
            feed.last_fetched_at = datetime.now(timezone.utc)
            db.commit()
            return {"new_articles": 0, "error": error_msg}

        # Extraire metadata du site au premier fetch
        if not feed.site_url and parsed.feed.get("link"):
            feed.site_url = parsed.feed.get("link")

        # Dedup : charger les guid existants pour ce feed
        existing_guids = set(
            r[0] for r in db.query(RssArticle.guid)
            .filter(RssArticle.feed_id == feed.id)
            .all()
        )

        for entry in parsed.entries:
            guid = entry.get("id") or entry.get("link") or entry.get("title", "")
            if not guid or guid in existing_guids:
                continue

            # Date de publication
            published = None
            for date_field in ("published_parsed", "updated_parsed"):
                raw = entry.get(date_field)
                if raw:
                    try:
                        published = datetime(*raw[:6], tzinfo=timezone.utc)
                        break
                    except (TypeError, ValueError):
                        pass

            # Image (media_content, enclosures, media_thumbnail)
            image_url = _extract_image(entry)

            # Contenu (preferer content complet vs summary)
            content = None
            if entry.get("content"):
                content = entry.content[0].get("value", "")

            description = entry.get("summary", "") or ""

            article = RssArticle(
                feed_id=feed.id,
                guid=guid[:500],
                title=(entry.get("title", "Sans titre") or "Sans titre")[:500],
                url=entry.get("link", ""),
                description=description[:5000] if description else None,
                content=content[:50000] if content else None,
                author=(entry.get("author", "") or "")[:255] or None,
                published_at=published,
                image_url=image_url,
            )
            db.add(article)
            new_count += 1
            existing_guids.add(guid)

        feed.last_fetched_at = datetime.now(timezone.utc)
        feed.last_error = None
        db.commit()

        logger.info(f"RSS feed '{feed.title}' refreshed: {new_count} new articles")
        return {"new_articles": new_count, "error": None}

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}"
        feed.last_error = error_msg
        feed.last_fetched_at = datetime.now(timezone.utc)
        db.commit()
        return {"new_articles": 0, "error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Erreur reseau: {str(e)[:200]}"
        feed.last_error = error_msg
        feed.last_fetched_at = datetime.now(timezone.utc)
        db.commit()
        return {"new_articles": 0, "error": error_msg}
    except Exception as e:
        error_msg = f"Erreur: {str(e)[:200]}"
        logger.error(f"RSS fetch error for feed {feed.id} ({feed.url}): {e}")
        feed.last_error = error_msg
        feed.last_fetched_at = datetime.now(timezone.utc)
        db.commit()
        return {"new_articles": 0, "error": error_msg}


def refresh_all_feeds(db: Session) -> list[dict]:
    """Rafraichit tous les flux actifs. Retourne une liste de resultats."""
    feeds = db.query(RssFeed).filter(RssFeed.is_active == True).all()
    results = []
    for feed in feeds:
        result = fetch_single_feed(db, feed)
        results.append({
            "feed_id": feed.id,
            "feed_title": feed.title,
            **result,
        })
    return results


def _extract_image(entry: dict) -> str | None:
    """Extrait l'URL de l'image depuis media_content, enclosures ou media_thumbnail."""
    if entry.get("media_content"):
        for media in entry.media_content:
            if media.get("medium") == "image" or (media.get("type", "").startswith("image")):
                return media.get("url")
    if entry.get("enclosures"):
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    if entry.get("media_thumbnail"):
        return entry.media_thumbnail[0].get("url")
    return None

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
from sqlalchemy import func

from app.models.model_rss import RssFeed, RssArticle

logger = logging.getLogger("hapson-api")

FETCH_TIMEOUT = 15.0
USER_AGENT = "RadioManager/1.0 (RSS Aggregator)"
DEFAULT_MAX_ARTICLES_PER_FEED = 100  # Limite par defaut de conservation par flux


def cleanup_old_articles(db: Session, feed: RssFeed) -> int:
    """
    Supprime les articles les plus anciens si le flux depasse sa limite.
    Retourne le nombre d'articles supprimes.
    """
    max_articles = feed.max_articles or DEFAULT_MAX_ARTICLES_PER_FEED
    article_count = db.query(func.count(RssArticle.id)).filter(RssArticle.feed_id == feed.id).scalar() or 0

    if article_count <= max_articles:
        return 0

    # Calculer le nombre d'articles a supprimer
    to_delete = article_count - max_articles

    # Recuperer les IDs des articles les plus anciens (ordonne par created_at ASC)
    old_articles = (
        db.query(RssArticle.id)
        .filter(RssArticle.feed_id == feed.id)
        .order_by(RssArticle.created_at.asc())
        .limit(to_delete)
        .all()
    )

    old_article_ids = [a[0] for a in old_articles]

    if old_article_ids:
        deleted_count = db.query(RssArticle).filter(RssArticle.id.in_(old_article_ids)).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old articles from feed {feed.id} (kept max {max_articles})")
        return deleted_count

    return 0


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
            try:
                db.add(article)
                db.commit()  # Commit immédiat pour chaque article
                new_count += 1
                existing_guids.add(guid)
                logger.debug(f"RSS article inserted: feed_id={feed.id}, guid_hash={hash(guid)}")
            except Exception as e:
                db.rollback()  # Rollback local si doublon
                logger.debug(f"RSS article skipped (duplicate or error): feed_id={feed.id}, error={str(e)[:100]}")
                continue

        feed.last_fetched_at = datetime.now(timezone.utc)
        feed.last_error = None
        db.commit()

        # Nettoyer les articles trop anciens
        deleted = cleanup_old_articles(db, feed)

        logger.info(f"RSS feed '{feed.title}' refreshed: {new_count} new articles, {deleted} old articles removed")
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
    logger.info(f"refresh_all_feeds: Starting refresh for {len(feeds)} active feeds")
    results = []
    for i, feed in enumerate(feeds, 1):
        # Capturer feed.id et feed.title AVANT d'appeler fetch_single_feed()
        # pour eviter d'acceder aux attributs si la session est en rollback
        feed_id = feed.id
        feed_title = feed.title
        try:
            logger.debug(f"refresh_all_feeds: Processing feed {i}/{len(feeds)}: {feed_title} (ID: {feed_id})")
            result = fetch_single_feed(db, feed)
            results.append({
                "feed_id": feed_id,
                "feed_title": feed_title,
                **result,
            })
            logger.debug(f"refresh_all_feeds: Feed {feed_id} completed - {result.get('new_articles', 0)} new articles")
        except Exception as e:
            logger.error(f"refresh_all_feeds: Unexpected error on feed {feed_id} ({feed_title}): {e}", exc_info=True)
            # Rollback explicite pour reinitialiser la session
            db.rollback()
            results.append({
                "feed_id": feed_id,
                "feed_title": feed_title,
                "new_articles": 0,
                "error": f"Erreur inattendue: {str(e)[:200]}",
            })
    logger.info(f"refresh_all_feeds: Completed - {len(results)} results returned")
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

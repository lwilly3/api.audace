"""
Routes FastAPI pour l'agregateur RSS du module Social.

Prefix : /rss
Tags : social-rss

Endpoints : CRUD feeds, refresh, articles avec filtres,
actions (lu, favori, utilise), generation IA, stats, categories.
"""

import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.db.crud import crud_rss
from app.schemas.schema_rss import (
    RssFeedCreate, RssFeedUpdate, RssFeedResponse,
    RssArticleResponse, RssArticleListResponse,
    RssStatsResponse, RssRefreshResult,
)
from app.services import rss_service
from app.db.crud.crud_audit_logs import log_action

logger = logging.getLogger("hapson-api")

router = APIRouter(prefix="/rss", tags=["social-rss"])


# ═══ FEEDS CRUD ═══

@router.get("/feeds", response_model=list[RssFeedResponse])
def list_feeds(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Lister les flux RSS."""
    return crud_rss.get_rss_feeds(db, active_only=active_only)


@router.post("/feeds", response_model=RssFeedResponse, status_code=status.HTTP_201_CREATED)
def add_feed(
    data: RssFeedCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Ajouter un flux RSS."""
    feed = crud_rss.create_rss_feed(db, data, current_user.id)
    log_action(db, current_user.id, "create", "rss_feeds", feed.id)
    # Refresh immediat pour charger les premiers articles
    rss_service.fetch_single_feed(db, feed)
    # Recharger pour avoir article_count
    feeds = crud_rss.get_rss_feeds(db, active_only=False)
    return next((f for f in feeds if f["id"] == feed.id), feed)


@router.put("/feeds/{feed_id}", response_model=RssFeedResponse)
def update_feed(
    feed_id: int,
    data: RssFeedUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Modifier un flux RSS."""
    crud_rss.update_rss_feed(db, feed_id, data)
    log_action(db, current_user.id, "update", "rss_feeds", feed_id)
    feeds = crud_rss.get_rss_feeds(db, active_only=False)
    result = next((f for f in feeds if f["id"] == feed_id), None)
    if not result:
        raise HTTPException(status_code=404, detail="Flux RSS introuvable")
    return result


@router.delete("/feeds/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Supprimer un flux RSS (cascade articles)."""
    if not crud_rss.delete_rss_feed(db, feed_id):
        raise HTTPException(status_code=404, detail="Flux RSS introuvable")
    log_action(db, current_user.id, "delete", "rss_feeds", feed_id)


# ═══ REFRESH ═══

@router.post("/feeds/{feed_id}/refresh", response_model=RssRefreshResult)
def refresh_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Rafraichir un flux RSS manuellement."""
    feed = crud_rss.get_rss_feed_by_id(db, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Flux RSS introuvable")
    result = rss_service.fetch_single_feed(db, feed)
    return {"feed_id": feed.id, "feed_title": feed.title, **result}


@router.post("/refresh-all", response_model=list[RssRefreshResult])
def refresh_all(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Rafraichir tous les flux RSS actifs."""
    return rss_service.refresh_all_feeds(db)


# ═══ ARTICLES ═══

@router.get("/articles", response_model=RssArticleListResponse)
def list_articles(
    feed_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    is_bookmarked: Optional[bool] = Query(None),
    is_used: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Lister les articles RSS avec filtres et pagination."""
    items, total = crud_rss.get_rss_articles(
        db, feed_id=feed_id, is_read=is_read, is_bookmarked=is_bookmarked,
        is_used=is_used, search=search, page=page, per_page=per_page,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, math.ceil(total / per_page)),
    }


@router.get("/articles/{article_id}", response_model=RssArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Detail d'un article RSS."""
    article = crud_rss.get_rss_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")
    return article


# ═══ ACTIONS ═══

@router.post("/articles/{article_id}/read", response_model=RssArticleResponse)
def mark_read(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Marquer un article comme lu."""
    crud_rss.mark_article_read(db, article_id)
    return crud_rss.get_rss_article_by_id(db, article_id)


@router.post("/articles/{article_id}/bookmark", response_model=RssArticleResponse)
def toggle_bookmark(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Toggle favori d'un article."""
    crud_rss.toggle_article_bookmark(db, article_id)
    return crud_rss.get_rss_article_by_id(db, article_id)


@router.post("/articles/{article_id}/used", response_model=RssArticleResponse)
def mark_used(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Marquer un article comme utilise par l'IA."""
    crud_rss.mark_article_used(db, article_id)
    return crud_rss.get_rss_article_by_id(db, article_id)


# ═══ GENERATION IA ═══

@router.post("/articles/{article_id}/generate-post")
def generate_post_from_rss(
    article_id: int,
    mode: str = Query("post_engageant"),
    tone: Optional[str] = Query(None),
    custom_instructions: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Generer un post social a partir d'un article RSS via Mistral."""
    from app.services.ai_service import fetch_content_from_url, generate_post_from_article

    article = crud_rss.get_rss_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")

    try:
        content_data = fetch_content_from_url(article["url"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur extraction contenu: {e}")

    # Combiner ton + instructions utilisateur
    tone_map = {
        "professionnel": "Adopte un ton professionnel, precis et factuel.",
        "decontracte": "Adopte un ton decontracte, proche, comme si tu parlais a un ami.",
        "informatif": "Adopte un ton neutre et informatif, axe sur les faits.",
        "enthousiaste": "Adopte un ton enthousiaste et dynamique, avec de l'energie.",
    }
    combined_instructions = ""
    if tone and tone in tone_map:
        combined_instructions += tone_map[tone] + "\n"
    if custom_instructions and custom_instructions.strip():
        combined_instructions += custom_instructions.strip()

    try:
        generated = generate_post_from_article(
            content_data["text"],
            article["url"],
            mode,
            combined_instructions or None,
            source_type=content_data["source_type"],
            source_context=article.get("feed_title"),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur generation IA: {e}")

    # Marquer l'article comme utilise
    crud_rss.mark_article_used(db, article_id)

    return {
        "generated_content": generated,
        "source_url": article["url"],
        "source_title": article["title"],
        "mode": mode,
    }


@router.post("/articles/{article_id}/generate-article")
def generate_article_from_rss(
    article_id: int,
    site: str = Query("audacemagazine"),
    mode: str = Query("article_magazine"),
    tone: Optional[str] = Query(None),
    custom_instructions: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Generer un article WordPress a partir d'un article RSS via Mistral."""
    from app.services.ai_service import generate_article_from_urls

    article = crud_rss.get_rss_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article RSS introuvable")

    # Combiner ton + instructions utilisateur
    tone_map = {
        "professionnel": "Adopte un ton professionnel, precis et factuel.",
        "decontracte": "Adopte un ton decontracte, proche, comme si tu parlais a un ami.",
        "informatif": "Adopte un ton neutre et informatif, axe sur les faits.",
        "enthousiaste": "Adopte un ton enthousiaste et dynamique, avec de l'energie.",
    }
    combined_instructions = ""
    if tone and tone in tone_map:
        combined_instructions += tone_map[tone] + "\n"
    if custom_instructions and custom_instructions.strip():
        combined_instructions += custom_instructions.strip()

    try:
        result = generate_article_from_urls(
            urls=[article["url"]],
            site_key=site,
            mode=mode,
            custom_instructions=combined_instructions or None,
            source_context=article.get("feed_title"),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur generation IA: {e}")

    # Marquer l'article comme utilise
    crud_rss.mark_article_used(db, article_id)

    return result


# ═══ STATS & CATEGORIES ═══

@router.get("/stats", response_model=RssStatsResponse)
def rss_stats(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Statistiques RSS."""
    return crud_rss.get_rss_stats(db)


@router.get("/categories", response_model=list[str])
def rss_categories(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Categories distinctes des flux RSS."""
    return crud_rss.get_rss_categories(db)

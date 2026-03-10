"""
Routes FastAPI pour les articles WordPress.

Proxy vers les sites WordPress (audacemagazine.com et radioaudace.com)
via l'API REST WP (wp-json/wp/v2).

Endpoints :
  GET    /social/articles              — Liste des articles (multi-sites)
  GET    /social/articles/stats        — Statistiques agregees
  POST   /social/articles/generate     — Generer un article via IA
  POST   /social/articles/generate-excerpt — Generer un extrait via IA
  GET    /social/articles/{site}/categories — Categories d'un site
  GET    /social/articles/{site}/{id}  — Detail d'un article
  POST   /social/articles/{site}       — Creer un article
  PUT    /social/articles/{site}/{id}  — Modifier un article
  DELETE /social/articles/{site}/{id}  — Supprimer un article
  POST   /social/articles/{site}/media — Upload d'image
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schema_article import (
    ArticleResponse,
    ArticleListResponse,
    ArticleCreate,
    ArticleUpdate,
    ArticleStatsResponse,
    WpCategory,
    WpFeaturedMedia,
    GenerateArticleRequest,
    GenerateArticleResponse,
    GenerateExcerptRequest,
)
from app.services import wp_article_service
from app.db.crud.crud_audit_logs import log_action
from core.auth import oauth2

logger = logging.getLogger("hapson-api")

router = APIRouter(
    prefix="/social/articles",
    tags=["social-articles"],
)


# ════════════════════════════════════════════════════════════════
# LISTE ET STATS
# ════════════════════════════════════════════════════════════════

@router.get("", response_model=ArticleListResponse)
def list_articles(
    site: Optional[str] = Query(None, description="Filtre par site: audacemagazine ou radioaudace"),
    status: Optional[str] = Query(None, description="Filtre par statut: publish, draft, pending, private"),
    category: Optional[int] = Query(None, description="Filtre par ID de categorie"),
    search: Optional[str] = Query(None, description="Recherche texte"),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Liste des articles WordPress avec filtres et pagination."""
    return wp_article_service.list_articles(
        site_key=site,
        search=search,
        status_filter=status,
        category=category,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=ArticleStatsResponse)
def get_article_stats(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Statistiques agregees des articles WordPress."""
    return wp_article_service.get_article_stats()


# ════════════════════════════════════════════════════════════════
# CATEGORIES
# ════════════════════════════════════════════════════════════════

@router.get("/{site}/categories", response_model=list[WpCategory])
def get_categories(
    site: str,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Categories d'un site WordPress."""
    return wp_article_service.list_categories(site)


# ════════════════════════════════════════════════════════════════
# GENERATION IA (avant les routes {site} pour eviter le conflit)
# ════════════════════════════════════════════════════════════════

@router.post("/generate", response_model=GenerateArticleResponse)
def generate_article(
    body: GenerateArticleRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Generer un article complet a partir d'URLs source via l'IA."""
    from app.services.ai_service import generate_article_from_urls

    result = generate_article_from_urls(
        urls=body.urls,
        site_key=body.site,
        mode=body.mode,
        custom_instructions=body.custom_instructions,
    )
    log_action(db, current_user.id, "ai_generate", "wp_articles", 0)
    return result


@router.post("/generate-excerpt")
def generate_excerpt(
    body: GenerateExcerptRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Generer un extrait optimise OG a partir du contenu d'un article."""
    from app.services.ai_service import generate_article_excerpt

    excerpt = generate_article_excerpt(body.content, body.site)
    log_action(db, current_user.id, "ai_generate", "wp_articles", 0)
    return {"excerpt": excerpt}


# ════════════════════════════════════════════════════════════════
# CRUD ARTICLES
# ════════════════════════════════════════════════════════════════

@router.get("/{site}/{article_id}", response_model=ArticleResponse)
def get_article(
    site: str,
    article_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Detail d'un article WordPress."""
    return wp_article_service.get_article(site, article_id)


@router.post("/{site}", response_model=ArticleResponse)
def create_article(
    site: str,
    data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Creer un article sur un site WordPress."""
    result = wp_article_service.create_article(site, data.model_dump())
    log_action(db, current_user.id, "create", "wp_articles", result.get("id", 0))
    return result


@router.put("/{site}/{article_id}", response_model=ArticleResponse)
def update_article(
    site: str,
    article_id: int,
    data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Modifier un article WordPress."""
    update_data = data.model_dump(exclude_unset=True)
    result = wp_article_service.update_article(site, article_id, update_data)
    log_action(db, current_user.id, "update", "wp_articles", article_id)
    return result


@router.delete("/{site}/{article_id}")
def delete_article(
    site: str,
    article_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Supprimer (corbeille) un article WordPress."""
    result = wp_article_service.delete_article(site, article_id)
    log_action(db, current_user.id, "delete", "wp_articles", article_id)
    return result


# ════════════════════════════════════════════════════════════════
# UPLOAD MEDIA
# ════════════════════════════════════════════════════════════════

@router.post("/{site}/media", response_model=WpFeaturedMedia)
async def upload_media(
    site: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Upload d'une image vers la bibliotheque media WordPress."""
    content = await file.read()
    return wp_article_service.upload_media(
        site,
        file_content=content,
        filename=file.filename or "upload.jpg",
        content_type=file.content_type or "image/jpeg",
    )

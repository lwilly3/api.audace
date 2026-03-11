"""
Service proxy pour l'API REST WordPress.

Interroge les sites WordPress (audacemagazine.com et radioaudace.com)
via wp-json/wp/v2 en utilisant les Application Passwords pour l'authentification.
"""

import logging
import math
from typing import Optional
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")

WP_TIMEOUT = 15.0
WP_USER_AGENT = "RadioManager/1.0 (https://api.radio.audace.ovh)"

# ════════════════════════════════════════════════════════════════
# CONFIGURATION DES SITES
# ════════════════════════════════════════════════════════════════

WP_SITES_CONFIG = {
    "audacemagazine": {
        "url": settings.WP_AUDACEMAGAZINE_URL,
        "user": settings.WP_AUDACEMAGAZINE_USER,
        "password": settings.WP_AUDACEMAGAZINE_APP_PASSWORD,
        "label": "Audace Magazine",
    },
    "radioaudace": {
        "url": settings.WP_RADIOAUDACE_URL,
        "user": settings.WP_RADIOAUDACE_USER,
        "password": settings.WP_RADIOAUDACE_APP_PASSWORD,
        "label": "Radio Audace",
    },
}


def _get_site_config(site_key: str) -> dict:
    """Recupere la config d'un site ou leve une 404."""
    config = WP_SITES_CONFIG.get(site_key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site WordPress inconnu: {site_key}"
        )
    if not config["url"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Site {site_key} non configure (URL manquante)"
        )
    return config


def _wp_api_url(config: dict, endpoint: str) -> str:
    """Construit l'URL de l'API WordPress."""
    base = config["url"].rstrip("/")
    return f"{base}/wp-json/wp/v2/{endpoint}"


def _wp_auth(config: dict) -> Optional[tuple[str, str]]:
    """Retourne le tuple (user, password) pour l'auth Basic, ou None."""
    if config["user"] and config["password"]:
        return (config["user"], config["password"])
    return None


def _handle_wp_error(response: httpx.Response, action: str):
    """Gere les erreurs de l'API WordPress."""
    if response.status_code >= 400:
        try:
            detail = response.json().get("message", response.text[:200])
        except Exception:
            detail = response.text[:200]
        logger.warning(f"WordPress {action}: HTTP {response.status_code} — {detail}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Erreur WordPress: {detail}"
        )


def _strip_html(html: str) -> str:
    """Retire les balises HTML basiques pour l'excerpt."""
    import re
    text = re.sub(r'<[^>]+>', '', html)
    return text.strip()


# ════════════════════════════════════════════════════════════════
# TRANSFORMATION WP → ARTICLE RESPONSE
# ════════════════════════════════════════════════════════════════

def _parse_wp_post(post: dict, site_key: str, categories_map: dict = None, tags_map: dict = None) -> dict:
    """Convertit un post WordPress en dict ArticleResponse."""

    # Image mise en avant
    featured_media = None
    embedded = post.get("_embedded", {})
    wp_media = embedded.get("wp:featuredmedia", [])
    if wp_media and len(wp_media) > 0 and isinstance(wp_media[0], dict):
        media = wp_media[0]
        source = media.get("source_url", "")
        details = media.get("media_details", {})
        sizes = details.get("sizes", {})
        featured_media = {
            "id": media.get("id", 0),
            "url": source,
            "alt": media.get("alt_text", ""),
            "width": sizes.get("full", {}).get("width", details.get("width", 0)),
            "height": sizes.get("full", {}).get("height", details.get("height", 0)),
        }

    # Categories et tags depuis _embedded
    cats = []
    embedded_terms = embedded.get("wp:term", [])
    if embedded_terms and len(embedded_terms) > 0:
        for term in embedded_terms[0]:
            if isinstance(term, dict):
                cats.append({
                    "id": term.get("id", 0),
                    "name": term.get("name", ""),
                    "slug": term.get("slug", ""),
                    "count": term.get("count", 0),
                })

    tags = []
    if embedded_terms and len(embedded_terms) > 1:
        for term in embedded_terms[1]:
            if isinstance(term, dict):
                tags.append({
                    "id": term.get("id", 0),
                    "name": term.get("name", ""),
                    "slug": term.get("slug", ""),
                })

    # Auteur depuis _embedded
    author_name = ""
    authors = embedded.get("author", [])
    if authors and isinstance(authors[0], dict):
        author_name = authors[0].get("name", "")

    # Excerpt : nettoyer le HTML
    excerpt_raw = post.get("excerpt", {}).get("rendered", "")
    excerpt = _strip_html(excerpt_raw)

    return {
        "id": post.get("id"),
        "site": site_key,
        "title": post.get("title", {}).get("rendered", ""),
        "slug": post.get("slug", ""),
        "excerpt": excerpt,
        "content": post.get("content", {}).get("rendered", ""),
        "status": post.get("status", "draft"),
        "author_name": author_name,
        "featured_media": featured_media,
        "categories": cats,
        "tags": tags,
        "link": post.get("link", ""),
        "created_at": post.get("date_gmt", post.get("date", "")),
        "updated_at": post.get("modified_gmt", post.get("modified", "")),
        "views": 0,
    }


# ════════════════════════════════════════════════════════════════
# ARTICLES CRUD
# ════════════════════════════════════════════════════════════════

def list_articles(
    site_key: Optional[str] = None,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    category: Optional[int] = None,
    page: int = 1,
    per_page: int = 12,
) -> dict:
    """
    Liste des articles, eventuellement filtre par site.
    Si site_key est None, interroge les deux sites et merge.
    """
    sites = [site_key] if site_key else list(WP_SITES_CONFIG.keys())
    all_items = []
    total = 0

    for sk in sites:
        config = _get_site_config(sk)
        params: dict = {
            "page": page,
            "per_page": per_page,
            "orderby": "date",
            "order": "desc",
            "_embed": "1",
        }
        if search:
            params["search"] = search
        if status_filter and status_filter != "publish":
            params["status"] = status_filter
        if category:
            params["categories"] = category

        try:
            with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
                auth = _wp_auth(config)
                # Si on veut les brouillons, il faut l'auth
                if status_filter and status_filter != "publish":
                    if not auth:
                        logger.warning(f"WordPress list ({sk}): auth requise pour status={status_filter}")
                        continue
                    response = client.get(
                        _wp_api_url(config, "posts"),
                        params=params,
                        auth=auth,
                    )
                else:
                    response = client.get(
                        _wp_api_url(config, "posts"),
                        params=params,
                        auth=auth,
                    )

                _handle_wp_error(response, f"list_articles({sk})")
                posts = response.json()
                site_total = int(response.headers.get("X-WP-Total", len(posts)))
                total += site_total

                for post in posts:
                    all_items.append(_parse_wp_post(post, sk))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"WordPress list_articles({sk}): {e}")
            continue

    # Trier par date decroissante
    all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total_pages = max(1, math.ceil(total / per_page)) if total > 0 else 1

    return {
        "items": all_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def get_article(site_key: str, article_id: int) -> dict:
    """Recupere un article par son ID."""
    config = _get_site_config(site_key)
    auth = _wp_auth(config)

    with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.get(
            _wp_api_url(config, f"posts/{article_id}"),
            params={"_embed": "1"},
            auth=auth,
        )
        _handle_wp_error(response, f"get_article({site_key}, {article_id})")
        post = response.json()
        return _parse_wp_post(post, site_key)


def create_article(site_key: str, data: dict) -> dict:
    """Cree un article sur un site WordPress."""
    config = _get_site_config(site_key)
    auth = _wp_auth(config)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Credentials WordPress manquants pour {site_key}"
        )

    payload = {
        "title": data["title"],
        "content": data["content"],
        "status": data.get("status", "draft"),
    }
    if data.get("excerpt"):
        payload["excerpt"] = data["excerpt"]
    if data.get("categories"):
        payload["categories"] = data["categories"]
    if data.get("tags"):
        payload["tags"] = data["tags"]
    if data.get("featured_media_id"):
        payload["featured_media"] = data["featured_media_id"]

    with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.post(
            _wp_api_url(config, "posts"),
            json=payload,
            auth=auth,
        )
        _handle_wp_error(response, f"create_article({site_key})")

        # Recharger avec _embed pour avoir les donnees completes
        post_id = response.json().get("id")
        return get_article(site_key, post_id)


def update_article(site_key: str, article_id: int, data: dict) -> dict:
    """Modifie un article existant."""
    config = _get_site_config(site_key)
    auth = _wp_auth(config)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Credentials WordPress manquants pour {site_key}"
        )

    payload = {}
    if data.get("title") is not None:
        payload["title"] = data["title"]
    if data.get("content") is not None:
        payload["content"] = data["content"]
    if data.get("excerpt") is not None:
        payload["excerpt"] = data["excerpt"]
    if data.get("status") is not None:
        payload["status"] = data["status"]
    if data.get("categories") is not None:
        payload["categories"] = data["categories"]
    if data.get("tags") is not None:
        payload["tags"] = data["tags"]
    if "featured_media_id" in data:
        payload["featured_media"] = data["featured_media_id"] or 0

    with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.post(
            _wp_api_url(config, f"posts/{article_id}"),
            json=payload,
            auth=auth,
        )
        _handle_wp_error(response, f"update_article({site_key}, {article_id})")
        return get_article(site_key, article_id)


def delete_article(site_key: str, article_id: int) -> dict:
    """Met un article a la corbeille (trash)."""
    config = _get_site_config(site_key)
    auth = _wp_auth(config)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Credentials WordPress manquants pour {site_key}"
        )

    with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.delete(
            _wp_api_url(config, f"posts/{article_id}"),
            auth=auth,
        )
        _handle_wp_error(response, f"delete_article({site_key}, {article_id})")
        return {"success": True, "id": article_id}


# ════════════════════════════════════════════════════════════════
# CATEGORIES
# ════════════════════════════════════════════════════════════════

def list_categories(site_key: str) -> list[dict]:
    """Liste les categories d'un site WordPress."""
    config = _get_site_config(site_key)

    with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.get(
            _wp_api_url(config, "categories"),
            params={"per_page": 100, "orderby": "count", "order": "desc"},
        )
        _handle_wp_error(response, f"list_categories({site_key})")
        return [
            {
                "id": cat.get("id"),
                "name": cat.get("name", ""),
                "slug": cat.get("slug", ""),
                "count": cat.get("count", 0),
            }
            for cat in response.json()
        ]


# ════════════════════════════════════════════════════════════════
# UPLOAD MEDIA
# ════════════════════════════════════════════════════════════════

def upload_media(site_key: str, file_content: bytes, filename: str, content_type: str) -> dict:
    """Upload une image vers la bibliotheque media WordPress."""
    config = _get_site_config(site_key)
    auth = _wp_auth(config)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Credentials WordPress manquants pour {site_key}"
        )

    with httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
        response = client.post(
            _wp_api_url(config, "media"),
            content=file_content,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            },
            auth=auth,
        )
        _handle_wp_error(response, f"upload_media({site_key})")
        media = response.json()
        details = media.get("media_details", {})
        sizes = details.get("sizes", {})
        return {
            "id": media.get("id"),
            "url": media.get("source_url", ""),
            "alt": media.get("alt_text", ""),
            "width": sizes.get("full", {}).get("width", details.get("width", 0)),
            "height": sizes.get("full", {}).get("height", details.get("height", 0)),
        }


# ════════════════════════════════════════════════════════════════
# STATISTIQUES (AGREGEES)
# ════════════════════════════════════════════════════════════════

def get_article_stats() -> dict:
    """Recupere des statistiques agregees sur les articles des deux sites."""
    total_articles = 0
    total_views = 0
    articles_this_month = 0
    top_articles: list[dict] = []
    by_site: list[dict] = []
    by_category: dict[str, int] = {}

    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")

    for site_key, config in WP_SITES_CONFIG.items():
        if not config["url"]:
            continue

        try:
            auth = _wp_auth(config)
            with httpx.Client(timeout=WP_TIMEOUT, follow_redirects=True, headers={"User-Agent": WP_USER_AGENT}) as client:
                # Total d'articles publies
                response = client.get(
                    _wp_api_url(config, "posts"),
                    params={"per_page": 1, "status": "publish"},
                    auth=auth,
                )
                if response.status_code == 200:
                    site_total = int(response.headers.get("X-WP-Total", 0))
                    total_articles += site_total
                    by_site.append({"site": site_key, "count": site_total, "views": 0})

                # Articles recents pour le top
                response = client.get(
                    _wp_api_url(config, "posts"),
                    params={"per_page": 5, "orderby": "date", "order": "desc", "_embed": "1"},
                    auth=auth,
                )
                if response.status_code == 200:
                    for post in response.json():
                        parsed = _parse_wp_post(post, site_key)
                        top_articles.append({
                            "id": parsed["id"],
                            "site": site_key,
                            "title": parsed["title"],
                            "views": parsed.get("views", 0),
                            "link": parsed["link"],
                        })
                        # Compter les articles du mois
                        if parsed["created_at"].startswith(current_month):
                            articles_this_month += 1
                        # Categories
                        for cat in parsed.get("categories", []):
                            cat_name = cat.get("name", "Autre")
                            by_category[cat_name] = by_category.get(cat_name, 0) + 1

        except Exception as e:
            logger.error(f"WordPress stats ({site_key}): {e}")
            continue

    return {
        "total_articles": total_articles,
        "total_views": total_views,
        "articles_this_month": articles_this_month,
        "top_articles": top_articles[:10],
        "by_site": by_site,
        "by_category": [{"category": k, "count": v} for k, v in sorted(by_category.items(), key=lambda x: -x[1])],
    }

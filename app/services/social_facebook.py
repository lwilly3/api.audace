"""
Service Facebook Graph API pour la synchronisation des donnees.

Gere les appels vers la Graph API v18.0 pour :
- Recuperer la liste des pages Facebook gerees par l'utilisateur
- Importer les posts d'une page
- Importer les commentaires d'un post
- Publier un post sur une page

Toutes les fonctions sont synchrones (httpx.Client).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger("hapson-api")

GRAPH_API_BASE = "https://graph.facebook.com/v18.0"
DEFAULT_TIMEOUT = 30.0


def _graph_get(url: str, params: dict, description: str = "Graph API") -> dict:
    """
    Appel GET generique vers la Graph API avec gestion d'erreurs.

    Args:
        url: URL complete de l'endpoint
        params: Parametres de la requete (access_token inclus)
        description: Description pour les logs d'erreur

    Returns:
        Reponse JSON parsee

    Raises:
        HTTPException en cas d'erreur API
    """
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url, params=params)

        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = (
                error_data.get("error", {}).get("message", response.text[:300])
                if isinstance(error_data, dict) else response.text[:300]
            )
            logger.error(f"{description} echoue: {response.status_code} - {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Facebook API error: {error_msg}"
            )

        return response.json()

    except httpx.TimeoutException:
        logger.error(f"Timeout {description}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de l'appel Facebook ({description})"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau {description}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau Facebook ({description})"
        )


def _graph_post(url: str, data: dict, access_token: str, description: str = "Graph API POST") -> dict:
    """
    Appel POST generique vers la Graph API.
    """
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                url,
                params={"access_token": access_token},
                json=data,
            )

        if response.status_code not in (200, 201):
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = (
                error_data.get("error", {}).get("message", response.text[:300])
                if isinstance(error_data, dict) else response.text[:300]
            )
            logger.error(f"{description} echoue: {response.status_code} - {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Facebook API error: {error_msg}"
            )

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout Facebook ({description})"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau {description}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau Facebook ({description})"
        )


# ════════════════════════════════════════════════════════════════
# PAGES FACEBOOK
# ════════════════════════════════════════════════════════════════

def get_facebook_pages(user_access_token: str) -> list[dict]:
    """
    Recuperer la liste des pages Facebook gerees par l'utilisateur.

    Chaque page contient un `access_token` specifique a la page
    qui permet de lire/publier sur cette page.

    Returns:
        Liste de dicts : {id, name, access_token, category, picture, followers_count}
    """
    url = f"{GRAPH_API_BASE}/me/accounts"
    params = {
        "access_token": user_access_token,
        "fields": "id,name,access_token,category,picture,followers_count",
        "limit": 100,
    }

    data = _graph_get(url, params, "GET /me/accounts")
    pages = data.get("data", [])

    result = []
    for page in pages:
        result.append({
            "id": page.get("id", ""),
            "name": page.get("name", ""),
            "access_token": page.get("access_token", ""),
            "category": page.get("category", ""),
            "picture_url": (
                page.get("picture", {}).get("data", {}).get("url")
                if isinstance(page.get("picture"), dict) else None
            ),
            "followers_count": page.get("followers_count", 0),
        })

    logger.info(f"Facebook: {len(result)} page(s) trouvee(s)")
    return result


# ════════════════════════════════════════════════════════════════
# POSTS DE LA PAGE
# ════════════════════════════════════════════════════════════════

def get_page_posts(
    page_access_token: str,
    page_id: str,
    limit: int = 25,
) -> list[dict]:
    """
    Recuperer les publications d'une page Facebook.

    Utilise /{page-id}/published_posts pour obtenir uniquement
    les posts publies (pas les brouillons/programmes).

    Returns:
        Liste de posts normalises : {id, message, created_time, full_picture,
        permalink_url, shares_count, likes_count, comments_count}
    """
    url = f"{GRAPH_API_BASE}/{page_id}/published_posts"
    params = {
        "access_token": page_access_token,
        "fields": "id,message,created_time,full_picture,permalink_url,shares,attachments,insights.metric(post_impressions,post_clicks_by_type)",
        "limit": limit,
    }

    data = _graph_get(url, params, f"GET /{page_id}/published_posts")
    raw_posts = data.get("data", [])

    posts = []
    for raw in raw_posts:
        # Extraire les metriques des insights
        impressions = 0
        clicks = 0
        insights = raw.get("insights", {}).get("data", [])
        for insight in insights:
            if insight.get("name") == "post_impressions":
                values = insight.get("values", [])
                if values:
                    impressions = values[0].get("value", 0)
            elif insight.get("name") == "post_clicks_by_type":
                values = insight.get("values", [])
                if values:
                    click_data = values[0].get("value", {})
                    if isinstance(click_data, dict):
                        clicks = sum(click_data.values())
                    elif isinstance(click_data, (int, float)):
                        clicks = int(click_data)

        # Extraire le media
        media_urls = []
        full_picture = raw.get("full_picture")
        if full_picture:
            media_urls.append(full_picture)

        # Extraire les attachments pour plus de medias
        attachments = raw.get("attachments", {}).get("data", [])
        for att in attachments:
            sub_attachments = att.get("subattachments", {}).get("data", [])
            for sub in sub_attachments:
                media = sub.get("media", {})
                img = media.get("image", {})
                src = img.get("src")
                if src and src not in media_urls:
                    media_urls.append(src)

        posts.append({
            "platform_post_id": raw.get("id", ""),
            "message": raw.get("message", ""),
            "created_time": raw.get("created_time", ""),
            "permalink_url": raw.get("permalink_url", ""),
            "media_urls": media_urls,
            "shares_count": raw.get("shares", {}).get("count", 0) if isinstance(raw.get("shares"), dict) else 0,
            "impressions": impressions,
            "clicks": clicks,
        })

    logger.info(f"Facebook: {len(posts)} post(s) recupere(s) pour la page {page_id}")
    return posts


def get_post_reactions_count(page_access_token: str, post_id: str) -> dict:
    """
    Recuperer le nombre de reactions (likes) et commentaires d'un post.

    Returns:
        {likes: int, comments: int}
    """
    url = f"{GRAPH_API_BASE}/{post_id}"
    params = {
        "access_token": page_access_token,
        "fields": "likes.summary(true),comments.summary(true)",
    }

    data = _graph_get(url, params, f"GET /{post_id} reactions")

    likes = data.get("likes", {}).get("summary", {}).get("total_count", 0)
    comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)

    return {"likes": likes, "comments": comments}


# ════════════════════════════════════════════════════════════════
# COMMENTAIRES D'UN POST
# ════════════════════════════════════════════════════════════════

def get_post_comments(
    page_access_token: str,
    post_id: str,
    limit: int = 100,
) -> list[dict]:
    """
    Recuperer les commentaires d'un post Facebook.

    Inclut les sous-commentaires (replies) a un niveau de profondeur.

    Returns:
        Liste de commentaires normalises : {id, message, from, created_time, 
        like_count, comment_count, parent_id, replies}
    """
    url = f"{GRAPH_API_BASE}/{post_id}/comments"
    params = {
        "access_token": page_access_token,
        "fields": "id,message,from,created_time,like_count,comment_count,parent",
        "order": "reverse_chronological",
        "limit": limit,
    }

    data = _graph_get(url, params, f"GET /{post_id}/comments")
    raw_comments = data.get("data", [])

    comments = []
    for raw in raw_comments:
        from_data = raw.get("from", {})
        comment = {
            "platform_comment_id": raw.get("id", ""),
            "message": raw.get("message", ""),
            "author_name": from_data.get("name", "Utilisateur Facebook"),
            "author_platform_id": from_data.get("id", "unknown"),
            "created_time": raw.get("created_time", ""),
            "like_count": raw.get("like_count", 0),
            "comment_count": raw.get("comment_count", 0),
            "parent_id": raw.get("parent", {}).get("id") if raw.get("parent") else None,
            "replies": [],
        }

        # Recuperer les sous-commentaires si il y en a
        if comment["comment_count"] > 0:
            try:
                reply_url = f"{GRAPH_API_BASE}/{comment['platform_comment_id']}/comments"
                reply_params = {
                    "access_token": page_access_token,
                    "fields": "id,message,from,created_time,like_count",
                    "limit": 50,
                }
                reply_data = _graph_get(reply_url, reply_params, f"GET replies for {comment['platform_comment_id']}")
                for reply_raw in reply_data.get("data", []):
                    reply_from = reply_raw.get("from", {})
                    comment["replies"].append({
                        "platform_comment_id": reply_raw.get("id", ""),
                        "message": reply_raw.get("message", ""),
                        "author_name": reply_from.get("name", "Utilisateur Facebook"),
                        "author_platform_id": reply_from.get("id", "unknown"),
                        "created_time": reply_raw.get("created_time", ""),
                        "like_count": reply_raw.get("like_count", 0),
                    })
            except Exception as e:
                logger.warning(f"Erreur fetch replies pour {comment['platform_comment_id']}: {e}")

        comments.append(comment)

    logger.info(f"Facebook: {len(comments)} commentaire(s) recupere(s) pour le post {post_id}")
    return comments


# ════════════════════════════════════════════════════════════════
# PUBLICATION SUR FACEBOOK
# ════════════════════════════════════════════════════════════════

def publish_to_page(
    page_access_token: str,
    page_id: str,
    message: str,
    link: Optional[str] = None,
) -> dict:
    """
    Publier un post sur une page Facebook.

    Args:
        page_access_token: Token d'acces de la page
        page_id: ID de la page Facebook
        message: Contenu du post
        link: URL a partager (optionnel)

    Returns:
        {id: "post_id", permalink_url: "..."}
    """
    url = f"{GRAPH_API_BASE}/{page_id}/feed"
    data = {"message": message}
    if link:
        data["link"] = link

    result = _graph_post(url, data, page_access_token, f"POST /{page_id}/feed")

    post_id = result.get("id", "")
    permalink = f"https://www.facebook.com/{post_id}" if post_id else ""

    logger.info(f"Facebook: post publie sur la page {page_id} -> {post_id}")
    return {
        "id": post_id,
        "permalink_url": permalink,
    }


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def parse_facebook_datetime(dt_str: str) -> datetime:
    """
    Parser une date ISO 8601 retournee par Facebook.
    Format: 2026-02-25T14:30:00+0000
    """
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        # Facebook retourne souvent +0000 au lieu de +00:00
        clean = dt_str.replace("+0000", "+00:00")
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)

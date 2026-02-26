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
    Logue la requete et la reponse pour faciliter le debug.
    """
    print(f"[FB API] {description} -> GET {url}", flush=True)
    logger.info(f"[FB API] {description} -> GET {url} (params sans token)")

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url, params=params)

        print(f"[FB API] {description} <- HTTP {response.status_code}", flush=True)
        logger.info(f"[FB API] {description} <- HTTP {response.status_code}")

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = {}
            error_msg = (
                error_data.get("error", {}).get("message", response.text[:500])
                if isinstance(error_data, dict) else response.text[:500]
            )
            error_code = error_data.get("error", {}).get("code", "?")
            error_subcode = error_data.get("error", {}).get("error_subcode", "?")
            print(f"[FB API] ECHOUE: HTTP {response.status_code} code={error_code} subcode={error_subcode} msg={error_msg[:200]}", flush=True)
            logger.error(
                f"[FB API] {description} ECHOUE: HTTP {response.status_code} "
                f"code={error_code} subcode={error_subcode} msg={error_msg}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Facebook API error (code {error_code}): {error_msg}"
            )

        data = response.json()
        # Log le nombre d'elements si c'est une liste paginee
        if isinstance(data.get("data"), list):
            print(f"[FB API] {description} -> {len(data['data'])} element(s)", flush=True)
            logger.info(f"[FB API] {description} -> {len(data['data'])} element(s)")
        return data

    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error(f"[FB API] Timeout {description}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de l'appel Facebook ({description})"
        )
    except httpx.RequestError as e:
        logger.error(f"[FB API] Erreur reseau {description}: {e}")
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

    Essaie d'abord /{page-id}/feed (plus permissif),
    puis fallback sur /{page-id}/published_posts si necessaire.
    N'inclut PAS les insights (necessite read_insights) — les metriques
    sont recuperees separement via les reactions.

    Returns:
        Liste de posts normalises
    """
    # Champs simples — PAS de insights (evite le besoin de read_insights)
    fields = "id,message,created_time,full_picture,permalink_url,shares,attachments"

    # Essayer /{page-id}/feed d'abord (plus tolerant en permissions)
    for endpoint in ["feed", "published_posts"]:
        url = f"{GRAPH_API_BASE}/{page_id}/{endpoint}"
        params = {
            "access_token": page_access_token,
            "fields": fields,
            "limit": limit,
        }

        try:
            data = _graph_get(url, params, f"GET /{page_id}/{endpoint}")
            raw_posts = data.get("data", [])

            if raw_posts:
                logger.info(f"Facebook: {len(raw_posts)} post(s) via /{endpoint}")
                break
            else:
                logger.info(f"Facebook: 0 posts via /{endpoint}, essai suivant...")
                continue
        except HTTPException as e:
            logger.warning(f"Facebook: /{endpoint} echoue ({e.detail}), essai suivant...")
            if endpoint == "published_posts":
                # Dernier essai echoue, retourner vide
                logger.error(f"Facebook: aucun endpoint n'a fonctionne pour la page {page_id}")
                return []
            continue
    else:
        raw_posts = []

    posts = []
    for raw in raw_posts:
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
            "impressions": 0,  # Sera mis a jour via reactions separement
            "clicks": 0,
        })

    logger.info(f"Facebook: {len(posts)} post(s) normalise(s) pour la page {page_id}")
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

    try:
        data = _graph_get(url, params, f"GET /{post_id} reactions")
        likes = data.get("likes", {}).get("summary", {}).get("total_count", 0)
        comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
        return {"likes": likes, "comments": comments}
    except HTTPException as e:
        logger.warning(f"Impossible de recuperer les reactions de {post_id}: {e.detail}")
        return {"likes": 0, "comments": 0}


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

    NOTE: Le champ 'from' peut ne pas etre disponible si l'app n'a pas
    la permission pages_read_user_content. On le demande mais on gere
    gracieusement son absence.

    Returns:
        Liste de commentaires normalises
    """
    url = f"{GRAPH_API_BASE}/{post_id}/comments"
    params = {
        "access_token": page_access_token,
        "fields": "id,message,from,created_time,like_count,comment_count,parent",
        "order": "reverse_chronological",
        "limit": limit,
    }

    try:
        data = _graph_get(url, params, f"GET /{post_id}/comments")
    except HTTPException:
        # Retry sans le champ 'from' (peut echouer si pas de pages_read_user_content)
        logger.warning(f"Retry commentaires sans champ 'from' pour {post_id}")
        params["fields"] = "id,message,created_time,like_count,comment_count,parent"
        try:
            data = _graph_get(url, params, f"GET /{post_id}/comments (sans from)")
        except HTTPException as e:
            logger.error(f"Impossible de recuperer les commentaires de {post_id}: {e.detail}")
            return []

    raw_comments = data.get("data", [])

    comments = []
    for raw in raw_comments:
        from_data = raw.get("from", {}) or {}
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
                    reply_from = reply_raw.get("from", {}) or {}
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

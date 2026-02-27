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

    Essaie d'abord /me/accounts (utilisateur classique).
    Si vide, tente la voie Business API (/me/businesses -> /{biz}/owned_pages)
    pour les System Users avec business_management.

    Returns:
        Liste de dicts : {id, name, access_token, category, picture, followers_count}
    """
    # ── Tentative 1 : /me/accounts (chemin standard) ──
    url = f"{GRAPH_API_BASE}/me/accounts"
    params = {
        "access_token": user_access_token,
        "fields": "id,name,access_token,category,picture,followers_count",
        "limit": 100,
    }

    data = _graph_get(url, params, "GET /me/accounts")
    pages = data.get("data", [])

    # ── Tentative 2 : Business API (System Users) ──
    if not pages:
        logger.info("[FB PAGES] /me/accounts vide, tentative via Business API...")
        print("[FB PAGES] /me/accounts vide, tentative via Business API...", flush=True)
        try:
            biz_url = f"{GRAPH_API_BASE}/me/businesses"
            biz_params = {"access_token": user_access_token, "fields": "id,name", "limit": 10}
            biz_data = _graph_get(biz_url, biz_params, "GET /me/businesses")
            businesses = biz_data.get("data", [])
            print(f"[FB PAGES] {len(businesses)} business(es) trouve(s)", flush=True)

            for biz in businesses:
                biz_id = biz.get("id")
                if not biz_id:
                    continue
                # Essayer owned_pages
                try:
                    pages_url = f"{GRAPH_API_BASE}/{biz_id}/owned_pages"
                    pages_params = {
                        "access_token": user_access_token,
                        "fields": "id,name,access_token,category,picture,followers_count",
                        "limit": 100,
                    }
                    pages_data = _graph_get(pages_url, pages_params, f"GET /{biz_id}/owned_pages")
                    pages = pages_data.get("data", [])
                    if pages:
                        print(f"[FB PAGES] {len(pages)} page(s) via /{biz_id}/owned_pages", flush=True)
                        break
                except HTTPException as e:
                    logger.warning(f"[FB PAGES] /{biz_id}/owned_pages echoue: {e.detail}")

                # Essayer client_pages
                if not pages:
                    try:
                        cp_url = f"{GRAPH_API_BASE}/{biz_id}/client_pages"
                        cp_data = _graph_get(cp_url, pages_params, f"GET /{biz_id}/client_pages")
                        pages = cp_data.get("data", [])
                        if pages:
                            print(f"[FB PAGES] {len(pages)} page(s) via /{biz_id}/client_pages", flush=True)
                            break
                    except HTTPException:
                        pass

        except HTTPException as e:
            logger.warning(f"[FB PAGES] Business API echoue: {e.detail}")
            print(f"[FB PAGES] Business API echoue: {e.detail}", flush=True)

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
    print(f"[FB PAGES] Resultat final: {len(result)} page(s)", flush=True)
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
    # Champs de base
    base_fields = "id,message,created_time,full_picture,permalink_url,shares,attachments"
    # Champs enrichis avec summary likes/comments (peut necessiter pages_read_engagement)
    enriched_fields = base_fields + ",likes.summary(true),comments.summary(true)"

    raw_posts = []
    used_enriched = False

    # Essayer avec les champs enrichis d'abord, puis basiques en fallback
    for fields in [enriched_fields, base_fields]:
        found = False
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
                    used_enriched = (fields == enriched_fields)
                    logger.info(f"Facebook: {len(raw_posts)} post(s) via /{endpoint} (enriched={used_enriched})")
                    print(f"[FB POSTS] {len(raw_posts)} post(s) via /{endpoint} enriched={used_enriched}", flush=True)
                    found = True
                    break
                else:
                    logger.info(f"Facebook: 0 posts via /{endpoint}, essai suivant...")
                    continue
            except HTTPException as e:
                logger.warning(f"Facebook: /{endpoint} echoue ({e.detail}), essai suivant...")
                continue

        if found:
            break
        else:
            if fields == enriched_fields:
                logger.info(f"Facebook: champs enrichis echoues pour {page_id}, fallback basique...")
                print(f"[FB POSTS] Enriched fields failed for {page_id}, falling back to basic", flush=True)
            else:
                logger.error(f"Facebook: aucun endpoint n'a fonctionne pour la page {page_id}")
                return []

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

        # Extraire likes/comments depuis le summary inline
        likes_count = 0
        comments_count = 0
        try:
            likes_summary = raw.get("likes", {})
            if isinstance(likes_summary, dict):
                likes_count = likes_summary.get("summary", {}).get("total_count", 0)
        except Exception:
            pass
        try:
            comments_summary = raw.get("comments", {})
            if isinstance(comments_summary, dict):
                comments_count = comments_summary.get("summary", {}).get("total_count", 0)
        except Exception:
            pass

        posts.append({
            "platform_post_id": raw.get("id", ""),
            "message": raw.get("message", ""),
            "created_time": raw.get("created_time", ""),
            "permalink_url": raw.get("permalink_url", ""),
            "media_urls": media_urls,
            "shares_count": raw.get("shares", {}).get("count", 0) if isinstance(raw.get("shares"), dict) else 0,
            "likes_count": likes_count,
            "comments_count": comments_count,
            "impressions": 0,
            "clicks": 0,
        })

    logger.info(f"Facebook: {len(posts)} post(s) normalise(s) pour la page {page_id}")
    return posts


def get_post_reactions_count(page_access_token: str, post_id: str) -> dict:
    """
    Recuperer le nombre de reactions (likes) et commentaires d'un post.
    Fallback: essaie d'abord likes.summary, puis reactions.summary.

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
        logger.info(f"Reactions {post_id}: likes={likes}, comments={comments}")
        return {"likes": likes, "comments": comments}
    except HTTPException as e:
        logger.warning(f"Reactions {post_id} echoue ({e.detail}), essai reactions.summary...")
        print(f"[FB API] Reactions {post_id} echoue, fallback reactions.summary", flush=True)

    # Fallback: reactions.summary (plus generique)
    try:
        params["fields"] = "reactions.summary(total_count),comments.summary(true)"
        data = _graph_get(url, params, f"GET /{post_id} reactions (fallback)")
        likes = data.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
        logger.info(f"Reactions fallback {post_id}: likes={likes}, comments={comments}")
        return {"likes": likes, "comments": comments}
    except HTTPException as e:
        logger.warning(f"Impossible de recuperer les reactions de {post_id}: {e.detail}")
        print(f"[FB API] Reactions {post_id} completement echoue: {e.detail}", flush=True)
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
# REPONSES AUX COMMENTAIRES
# ════════════════════════════════════════════════════════════════

def reply_to_facebook_comment(
    page_access_token: str,
    comment_id: str,
    message: str,
) -> dict:
    """
    Repondre a un commentaire Facebook via la Graph API.

    L'API Facebook permet de repondre a un commentaire en postant
    sur /{comment_id}/comments avec le page access token.

    Args:
        page_access_token: Token d'acces de la page
        comment_id: ID du commentaire Facebook (platform_comment_id)
        message: Contenu de la reponse

    Returns:
        {id: "reply_comment_id"}
    """
    url = f"{GRAPH_API_BASE}/{comment_id}/comments"
    data = {"message": message}

    result = _graph_post(url, data, page_access_token, f"POST /{comment_id}/comments (reply)")

    reply_id = result.get("id", "")
    logger.info(f"Facebook: reponse publiee sur le commentaire {comment_id} -> {reply_id}")
    return {"id": reply_id}


def like_facebook_comment(
    page_access_token: str,
    comment_id: str,
) -> bool:
    """
    Liker un commentaire Facebook via la Graph API.

    Args:
        page_access_token: Token d'acces de la page
        comment_id: ID du commentaire Facebook (platform_comment_id)

    Returns:
        True si le like a ete envoye
    """
    url = f"{GRAPH_API_BASE}/{comment_id}/likes"
    result = _graph_post(url, {}, page_access_token, f"POST /{comment_id}/likes (like)")
    success = result.get("success", False)
    logger.info(f"Facebook: like {'envoye' if success else 'echoue'} sur commentaire {comment_id}")
    return success


def hide_facebook_comment(
    page_access_token: str,
    comment_id: str,
    hide: bool = True,
) -> bool:
    """
    Masquer ou afficher un commentaire Facebook via la Graph API.

    Args:
        page_access_token: Token d'acces de la page
        comment_id: ID du commentaire Facebook (platform_comment_id)
        hide: True pour masquer, False pour afficher

    Returns:
        True si l'operation a reussi
    """
    url = f"{GRAPH_API_BASE}/{comment_id}"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                url,
                params={"access_token": page_access_token},
                json={"is_hidden": hide},
            )
        if response.status_code == 200:
            logger.info(f"Facebook: commentaire {comment_id} {'masque' if hide else 'affiche'}")
            return True
        logger.warning(f"Facebook: hide comment {comment_id} echoue: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Facebook: erreur hide comment {comment_id}: {e}")
        return False


def delete_facebook_comment(
    page_access_token: str,
    comment_id: str,
) -> bool:
    """
    Supprimer un commentaire Facebook via la Graph API.

    Seuls les commentaires faits par la page elle-meme peuvent etre supprimes.

    Args:
        page_access_token: Token d'acces de la page
        comment_id: ID du commentaire Facebook (platform_comment_id)

    Returns:
        True si la suppression a reussi
    """
    url = f"{GRAPH_API_BASE}/{comment_id}"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.delete(
                url,
                params={"access_token": page_access_token},
            )
        if response.status_code == 200:
            logger.info(f"Facebook: commentaire {comment_id} supprime")
            return True
        logger.warning(f"Facebook: delete comment {comment_id} echoue: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Facebook: erreur delete comment {comment_id}: {e}")
        return False


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
# DIAGNOSTIC / DEBUG
# ════════════════════════════════════════════════════════════════

def debug_token_permissions(access_token: str) -> list[str]:
    """
    Appelle /me/permissions pour voir les permissions accordees au token.
    Appelle aussi /me pour voir l'identite associee au token.
    Purement diagnostic — print dans stdout pour Docker logs.
    """
    granted = []

    # 1. Identite du token
    try:
        url_me = f"{GRAPH_API_BASE}/me"
        params_me = {"access_token": access_token, "fields": "id,name"}
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(url_me, params=params_me)
        me_data = resp.json() if resp.status_code == 200 else {}
        print(f"[DEBUG TOKEN] /me -> {me_data}", flush=True)
        logger.info(f"[DEBUG TOKEN] /me -> {me_data}")
    except Exception as e:
        print(f"[DEBUG TOKEN] /me ERREUR: {e}", flush=True)

    # 2. Permissions du token
    try:
        url_perms = f"{GRAPH_API_BASE}/me/permissions"
        params_perms = {"access_token": access_token}
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(url_perms, params=params_perms)
        if resp.status_code == 200:
            perms_data = resp.json().get("data", [])
            for p in perms_data:
                status = p.get("status", "?")
                perm = p.get("permission", "?")
                granted.append(f"{perm}={status}")
            print(f"[DEBUG TOKEN] Permissions: {granted}", flush=True)
            logger.info(f"[DEBUG TOKEN] Permissions: {granted}")
        else:
            print(f"[DEBUG TOKEN] /me/permissions HTTP {resp.status_code}: {resp.text[:300]}", flush=True)
    except Exception as e:
        print(f"[DEBUG TOKEN] /me/permissions ERREUR: {e}", flush=True)

    # 3. Appel direct /me/accounts avec log de la reponse brute
    try:
        url_accounts = f"{GRAPH_API_BASE}/me/accounts"
        params_acc = {
            "access_token": access_token,
            "fields": "id,name",
            "limit": 10,
        }
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(url_accounts, params=params_acc)
        raw = resp.text[:500]
        print(f"[DEBUG TOKEN] /me/accounts RAW: {raw}", flush=True)
        logger.info(f"[DEBUG TOKEN] /me/accounts RAW: {raw}")
    except Exception as e:
        print(f"[DEBUG TOKEN] /me/accounts ERREUR: {e}", flush=True)

    return granted


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

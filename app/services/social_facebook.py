"""
Service Facebook Graph API pour la synchronisation des donnees.

Gere les appels vers la Graph API v21.0 pour :
- Recuperer la liste des pages Facebook gerees par l'utilisateur
- Importer les posts d'une page
- Importer les commentaires d'un post
- Publier un post sur une page

Toutes les fonctions sont synchrones (httpx.Client).
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Callable

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger("hapson-api")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
DEFAULT_TIMEOUT = 30.0

# Client HTTP réutilisable (connection pooling)
_shared_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    """Client HTTP partagé avec connection pooling."""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _shared_client


def _graph_get(url: str, params: dict, description: str = "Graph API") -> dict:
    """
    Appel GET generique vers la Graph API avec gestion d'erreurs.
    Logue la requete et la reponse pour faciliter le debug.
    """
    print(f"[FB API] {description} -> GET {url}", flush=True)
    logger.info(f"[FB API] {description} -> GET {url} (params sans token)")

    try:
        client = _get_client()
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


def _graph_post(url: str, data: dict, access_token: str, description: str = "Graph API POST", as_form: bool = False) -> dict:
    """
    Appel POST generique vers la Graph API.

    Args:
        as_form: Si True, envoie les donnees en form-encoded (requis pour /{page_id}/photos).
                 Si False, envoie en JSON (comportement par defaut).
    """
    try:
        client = _get_client()
        if as_form:
            response = client.post(
                url,
                params={"access_token": access_token},
                data=data,
            )
        else:
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
    # Champs enrichis avec summary likes/comments + commentaires inline (evite le N+1)
    enriched_fields = base_fields + ",likes.summary(true),comments.limit(50).summary(true){id,message,from,created_time,like_count,comment_count}"

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
        inline_comments = []
        try:
            likes_summary = raw.get("likes", {})
            if isinstance(likes_summary, dict):
                likes_count = likes_summary.get("summary", {}).get("total_count", 0)
        except Exception:
            pass
        try:
            comments_data = raw.get("comments", {})
            if isinstance(comments_data, dict):
                comments_count = comments_data.get("summary", {}).get("total_count", 0)
                # Extraire les commentaires inline (evite le N+1 API call)
                for raw_c in comments_data.get("data", []):
                    from_data = raw_c.get("from", {}) or {}
                    inline_comments.append({
                        "platform_comment_id": raw_c.get("id", ""),
                        "message": raw_c.get("message", ""),
                        "author_name": from_data.get("name", "Utilisateur Facebook"),
                        "author_platform_id": from_data.get("id", "unknown"),
                        "created_time": raw_c.get("created_time", ""),
                        "like_count": raw_c.get("like_count", 0),
                        "comment_count": raw_c.get("comment_count", 0),
                        "replies": [],
                    })
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
            "inline_comments": inline_comments,
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


def get_post_insights(page_access_token: str, post_id: str) -> dict:
    """
    Recuperer les metriques Insights d'un post Facebook (impressions, clics, portee).

    Necessite la permission read_insights sur la page.
    Retourne 0 gracieusement si l'API echoue (permission manquante, post trop ancien, etc.).

    NOTE: Les metriques non-_unique (post_impressions, post_impressions_organic, etc.)
    sont deprecies dans les versions recentes de la Graph API.
    Seules les versions _unique fonctionnent : post_impressions_unique,
    post_impressions_organic_unique, etc.

    Returns:
        {impressions: int, clicks: int, reach: int}
    """
    url = f"{GRAPH_API_BASE}/{post_id}/insights"

    result = {"impressions": 0, "clicks": 0, "reach": 0}

    # ── 1. Impressions et Reach via post_impressions_unique ──
    # post_impressions est deprecie, seul post_impressions_unique fonctionne
    # post_impressions_unique = nombre de personnes uniques ayant vu le post (= reach)
    # post_impressions_organic_unique = reach organique
    params = {
        "access_token": page_access_token,
        "metric": "post_impressions_unique,post_impressions_organic_unique",
        "period": "lifetime",
    }

    try:
        data = _graph_get(url, params, f"GET /{post_id}/insights (impressions_unique)")

        for item in data.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [])
            value = values[0].get("value", 0) if values else 0

            if name == "post_impressions_unique":
                # Utiliser comme impressions (seule metrique dispo)
                result["impressions"] = value
                result["reach"] = value
            elif name == "post_impressions_organic_unique":
                # Si reach pas encore defini, utiliser organic
                if result["reach"] == 0 and value > 0:
                    result["reach"] = value

    except HTTPException as e:
        logger.warning(f"Insights impressions {post_id} echoue: {e.detail}")
        print(f"[FB API] Insights impressions {post_id} echoue: {e.detail[:200]}", flush=True)

    # ── 2. Clics via post_clicks ──
    try:
        clicks_params = {
            "access_token": page_access_token,
            "metric": "post_clicks",
            "period": "lifetime",
        }
        clicks_data = _graph_get(url, clicks_params, f"GET /{post_id}/insights (post_clicks)")

        for item in clicks_data.get("data", []):
            values = item.get("values", [])
            value = values[0].get("value", 0) if values else 0
            if value > 0:
                result["clicks"] = value
                break

    except HTTPException as e:
        logger.warning(f"Insights clicks {post_id} echoue: {e.detail}")
        print(f"[FB API] Insights clicks {post_id} echoue: {e.detail[:200]}", flush=True)

    logger.info(f"Insights {post_id}: impressions={result['impressions']}, clicks={result['clicks']}, reach={result['reach']}")
    print(f"[FB API] Insights {post_id}: imp={result['impressions']} clicks={result['clicks']} reach={result['reach']}", flush=True)
    return result


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
    logger.info(f"[COMMENTS] {len(raw_comments)} commentaires bruts pour {post_id}")

    comments = []
    for raw in raw_comments:
        from_data = raw.get("from", {}) or {}
        author = from_data.get("name", "Utilisateur Facebook")
        if not from_data:
            logger.warning(f"[COMMENTS] Champ 'from' absent pour commentaire {raw.get('id')} — permission pages_read_user_content manquante ?")
        comment = {
            "platform_comment_id": raw.get("id", ""),
            "message": raw.get("message", ""),
            "author_name": author,
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

def _is_image_url(url: str) -> bool:
    """Verifier si une URL pointe vers une image (par extension ou Firebase Storage)."""
    import urllib.parse

    image_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
    lower = url.lower().split("?")[0]
    if any(lower.endswith(ext) for ext in image_exts):
        return True
    # Firebase Storage URLs : le path encode contient l'extension
    if "firebasestorage.googleapis.com" in url and "/o/" in url:
        path = urllib.parse.unquote(url.split("/o/")[1].split("?")[0])
        return any(path.lower().endswith(ext) for ext in image_exts)
    return False


def _upload_photo_from_url(
    page_access_token: str,
    page_id: str,
    image_url: str,
    published: bool = True,
    caption: Optional[str] = None,
) -> dict:
    """
    Uploader une photo sur une page Facebook depuis une URL.
    Facebook telecharge l'image depuis l'URL fournie.

    Args:
        page_access_token: Token d'acces de la page
        page_id: ID de la page Facebook
        image_url: URL publique de l'image (ex: Firebase Storage URL)
        published: False pour upload unpublished (multi-photo), True pour publication directe
        caption: Legende de la photo (= message du post)

    Returns:
        {"id": "photo_id"} — pour unpublished, l'id sert dans attached_media
    """
    url = f"{GRAPH_API_BASE}/{page_id}/photos"
    data = {"url": image_url, "published": str(published).lower()}
    if caption:
        data["caption"] = caption

    return _graph_post(url, data, page_access_token, f"POST /{page_id}/photos (published={published})", as_form=True)


def publish_to_page(
    page_access_token: str,
    page_id: str,
    message: str,
    link: Optional[str] = None,
    media_urls: Optional[list[str]] = None,
) -> dict:
    """
    Publier un post sur une page Facebook.

    Supporte 3 modes :
    - 1 image : publication directe via /{page_id}/photos
    - N images : upload unpublished + /{page_id}/feed avec attached_media
    - Pas d'image : post texte classique via /{page_id}/feed

    Args:
        page_access_token: Token d'acces de la page
        page_id: ID de la page Facebook
        message: Contenu du post
        link: URL a partager (optionnel)
        media_urls: Liste d'URLs de medias a joindre (optionnel)

    Returns:
        {id: "post_id", permalink_url: "..."}
    """
    # Filtrer les images dans media_urls
    image_urls = [u for u in (media_urls or []) if _is_image_url(u)]

    # ── CAS 1 : Une seule image → /{page_id}/photos (publication directe)
    if len(image_urls) == 1:
        result = _upload_photo_from_url(
            page_access_token, page_id, image_urls[0],
            published=True, caption=message,
        )
        photo_id = result.get("id", "")
        post_id = result.get("post_id", photo_id)
        permalink = f"https://www.facebook.com/{post_id}" if post_id else ""
        logger.info(f"Facebook: photo publiee sur page {page_id} -> {photo_id}")
        return {"id": post_id, "permalink_url": permalink}

    # ── CAS 2 : Plusieurs images → unpublished uploads + feed avec attached_media
    if len(image_urls) > 1:
        photo_ids = []
        for img_url in image_urls:
            r = _upload_photo_from_url(
                page_access_token, page_id, img_url, published=False,
            )
            fbid = r.get("id")
            if fbid:
                photo_ids.append(fbid)
                logger.info(f"Facebook: photo unpublished uploadee -> {fbid}")

        # Creer le post avec les photos attachees
        url = f"{GRAPH_API_BASE}/{page_id}/feed"
        data = {"message": message}
        if link:
            data["link"] = link
        for i, fbid in enumerate(photo_ids):
            data[f"attached_media[{i}]"] = f'{{"media_fbid":"{fbid}"}}'

        result = _graph_post(url, data, page_access_token, f"POST /{page_id}/feed (multi-photo)", as_form=True)
        post_id = result.get("id", "")
        permalink = f"https://www.facebook.com/{post_id}" if post_id else ""
        logger.info(f"Facebook: multi-photo post publie -> {post_id}")
        return {"id": post_id, "permalink_url": permalink}

    # ── CAS 3 : Pas d'image → texte seul (comportement original)
    url = f"{GRAPH_API_BASE}/{page_id}/feed"
    data = {"message": message}
    if link:
        data["link"] = link

    result = _graph_post(url, data, page_access_token, f"POST /{page_id}/feed")
    post_id = result.get("id", "")
    permalink = f"https://www.facebook.com/{post_id}" if post_id else ""
    logger.info(f"Facebook: post publie sur la page {page_id} -> {post_id}")
    return {"id": post_id, "permalink_url": permalink}


def get_post_media_urls(page_access_token: str, post_id: str) -> list[str]:
    """
    Recuperer les URLs d'images d'un post publie sur Facebook.

    Appelle GET /{post_id}?fields=full_picture,attachments pour obtenir
    les URLs CDN Facebook des images, apres que Facebook les a copiees.

    Args:
        page_access_token: Token d'acces de la page
        post_id: ID du post Facebook (ex: "123456_789012")

    Returns:
        Liste d'URLs d'images Facebook (CDN). Liste vide si pas d'images.
    """
    params = {
        "access_token": page_access_token,
        "fields": "full_picture,attachments{subattachments{media{image{src}}}}",
    }
    try:
        data = _graph_get(
            f"{GRAPH_API_BASE}/{post_id}", params, f"GET /{post_id} media"
        )
    except Exception as e:
        logger.warning(f"get_post_media_urls: erreur pour {post_id}: {e}")
        return []

    urls: list[str] = []

    # full_picture : image principale du post
    full = data.get("full_picture")
    if full:
        urls.append(full)

    # attachments > subattachments : images supplementaires (multi-photo)
    for att in data.get("attachments", {}).get("data", []):
        for sub in att.get("subattachments", {}).get("data", []):
            src = sub.get("media", {}).get("image", {}).get("src")
            if src and src not in urls:
                urls.append(src)

    return urls


# ════════════════════════════════════════════════════════════════
# INSIGHTS PAGE-LEVEL (METRIQUES QUOTIDIENNES)
# ════════════════════════════════════════════════════════════════

def get_page_level_insights(
    page_access_token: str,
    page_id: str,
    since: str,
    until: str,
) -> list[dict]:
    """
    Recuperer les metriques page-level quotidiennes depuis Facebook Insights.

    Appelle /{page_id}/insights avec period=day et un intervalle since/until.
    Retourne une liste de dicts avec une entree par jour.

    Args:
        page_access_token: Token d'acces de la page
        page_id: ID de la page Facebook
        since: Date de debut (format YYYY-MM-DD)
        until: Date de fin (format YYYY-MM-DD)

    Returns:
        Liste de dicts par jour : {date, page_impressions_unique, page_follows, ...}
    """
    # Metriques fonctionnelles (testees live)
    metrics = [
        "page_impressions_unique",
        "page_posts_impressions",
        "page_posts_impressions_unique",
        "page_posts_impressions_organic",
        "page_posts_impressions_paid",
        "page_post_engagements",
        "page_views_total",
        "page_follows",
        "page_daily_follows_unique",
        "page_daily_unfollows_unique",
        "page_actions_post_reactions_like_total",
        "page_actions_post_reactions_love_total",
        "page_actions_post_reactions_wow_total",
        "page_actions_post_reactions_haha_total",
        "page_actions_post_reactions_sorry_total",
        "page_actions_post_reactions_anger_total",
        "page_video_views",
        "page_video_view_time",
    ]

    url = f"{GRAPH_API_BASE}/{page_id}/insights"
    params = {
        "access_token": page_access_token,
        "metric": ",".join(metrics),
        "period": "day",
        "since": since,
        "until": until,
    }

    try:
        data = _graph_get(url, params, f"GET /{page_id}/insights (page-level)")
    except HTTPException as e:
        logger.warning(f"Page insights {page_id} echoue: {e.detail}")
        print(f"[FB API] Page insights {page_id} echoue: {e.detail[:200]}", flush=True)
        return []

    raw_metrics = data.get("data", [])
    if not raw_metrics:
        return []

    # Organiser les donnees par date
    # Chaque metrique retourne une liste de {end_time, value} pour chaque jour
    days_data: dict[str, dict] = {}

    # Mapping des noms API vers les noms de colonnes du modele
    metric_mapping = {
        "page_impressions_unique": "page_impressions_unique",
        "page_posts_impressions": "page_posts_impressions",
        "page_posts_impressions_unique": "page_posts_impressions_unique",
        "page_posts_impressions_organic": "page_posts_impressions_organic",
        "page_posts_impressions_paid": "page_posts_impressions_paid",
        "page_post_engagements": "page_post_engagements",
        "page_views_total": "page_views_total",
        "page_follows": "page_follows",
        "page_daily_follows_unique": "page_daily_follows",
        "page_daily_unfollows_unique": "page_daily_unfollows",
        "page_actions_post_reactions_like_total": "reactions_like",
        "page_actions_post_reactions_love_total": "reactions_love",
        "page_actions_post_reactions_wow_total": "reactions_wow",
        "page_actions_post_reactions_haha_total": "reactions_haha",
        "page_actions_post_reactions_sorry_total": "reactions_sorry",
        "page_actions_post_reactions_anger_total": "reactions_anger",
        "page_video_views": "page_video_views",
        "page_video_view_time": "page_video_view_time",
    }

    for item in raw_metrics:
        metric_name = item.get("name", "")
        column_name = metric_mapping.get(metric_name)
        if not column_name:
            continue

        for value_entry in item.get("values", []):
            end_time = value_entry.get("end_time", "")
            if not end_time:
                continue
            # Extraire la date (YYYY-MM-DD) depuis end_time
            day_str = end_time[:10]
            if day_str not in days_data:
                days_data[day_str] = {"date": day_str}

            val = value_entry.get("value", 0)
            # Certaines metriques retournent un dict au lieu d'un int
            if isinstance(val, dict):
                val = sum(val.values()) if val else 0
            days_data[day_str][column_name] = val if isinstance(val, int) else 0

    result = sorted(days_data.values(), key=lambda x: x["date"])
    print(f"[FB API] Page insights {page_id}: {len(result)} jour(s) de donnees", flush=True)
    return result


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


# ================================================================
# MESSAGES PRIVES - ENVOI VIA GRAPH API
# ================================================================

def send_facebook_message(
    page_id: str,
    recipient_psid: str,
    message_text: str,
    page_access_token: str,
) -> dict:
    """
    Envoyer un message prive via la page Facebook.

    Utilise l'API Send (POST /{page_id}/messages).
    Le recipient_psid est le Page-Scoped ID du destinataire.

    Docs: https://developers.facebook.com/docs/messenger-platform/send-messages
    """
    url = f"{GRAPH_API_BASE}/{page_id}/messages"
    data = {
        "recipient": {"id": recipient_psid},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE",
    }
    result = _graph_post(url, data, page_access_token, "Send Facebook message")
    logger.info(f"Message envoye a {recipient_psid} via page {page_id}")
    return result

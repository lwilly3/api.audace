"""
Routes FastAPI pour le module Social.

Prefix : /social
Tags : social

Endpoints :
- /social/accounts          — CRUD comptes sociaux connectés
- /social/posts             — CRUD publications multi-plateformes
- /social/comments          — Inbox commentaires
- /social/messages          — Inbox messages privés
- /social/analytics         — Statistiques d'engagement
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import logging

from app.db.database import get_db
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action
from app.db.crud.crud_social import (
    # Comptes
    get_social_accounts,
    get_social_account_by_id,
    disconnect_social_account,
    check_account_token_status,
    upsert_social_account_from_oauth,
    # Sync Facebook
    sync_facebook_account,
    sync_all_facebook_accounts,
    # Posts
    get_social_posts,
    get_social_post_by_id,
    create_social_post,
    update_social_post,
    delete_social_post,
    publish_social_post,
    schedule_social_post,
    # Commentaires
    get_social_comments,
    get_comment_by_id,
    mark_comment_read,
    hide_comment,
    delete_social_comment,
    # Conversations / Messages
    get_conversations,
    get_conversation_by_id,
    # Statistiques
    get_analytics_overview,
    get_platform_stats,
    get_best_times,
    get_engagement_time_series,
    # Nettoyage
    get_database_stats,
    cleanup_database,
)
from app.schemas.schema_social import (
    SocialAccountResponse,
    SocialAccountStatusResponse,
    OAuthRedirectResponse,
    SocialPostResponse,
    SocialPostCreate,
    SocialPostUpdate,
    SchedulePostRequest,
    SocialCommentResponse,
    ReplyToCommentRequest,
    SocialConversationResponse,
    ReplyToConversationRequest,
    SocialAnalyticsOverviewResponse,
    PlatformStatsResponse,
    BestTimeSlotResponse,
    TimeSeriesPointResponse,
)
from app.services.social_oauth import (
    build_authorization_url,
    verify_oauth_state,
    exchange_code_for_token,
    fetch_user_profile,
    SUPPORTED_PLATFORMS,
)
from app.config.config import settings
from app.models.model_user_permissions import UserPermissions
from app.models.model_social import SocialAccount


router = APIRouter(
    prefix="/social",
    tags=["social"],
)


# ════════════════════════════════════════════════════════════════
# COMPTES SOCIAUX
# ════════════════════════════════════════════════════════════════

@router.get("/accounts", response_model=list[SocialAccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Lister tous les comptes sociaux connectés."""
    return get_social_accounts(db)


@router.post("/accounts/connect/{platform}", response_model=OAuthRedirectResponse)
def connect_account(
    platform: str,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Initier la connexion OAuth pour une plateforme sociale.

    Retourne l'URL de redirection vers la page d'autorisation OAuth
    de la plateforme. Le frontend doit rediriger l'utilisateur vers cette URL.

    Plateformes supportees : facebook, instagram, linkedin, twitter
    """
    # Verifier la permission
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )

    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plateforme '{platform}' non supportee. "
                   f"Valides: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )

    redirect_url, state = build_authorization_url(platform, current_user.id)

    log_action(db, current_user.id, "oauth_init", "social_accounts", 0)

    return OAuthRedirectResponse(redirect_url=redirect_url, state=state)


@router.get("/accounts/callback")
def oauth_callback(
    code: str = Query(None, description="Code d'autorisation de la plateforme"),
    state: str = Query(None, description="Parametre state pour validation CSRF"),
    error: str = Query(None, description="Erreur retournee par la plateforme"),
    error_description: str = Query(None, description="Description de l'erreur"),
    db: Session = Depends(get_db),
):
    """
    Callback OAuth2 — recoit le code d'autorisation depuis la plateforme.

    Cet endpoint est appele par le navigateur apres que l'utilisateur
    a autorise l'application sur la plateforme sociale.

    IMPORTANT: Cet endpoint ne requiert PAS d'authentification JWT
    car il est appele via redirect du navigateur depuis la plateforme.
    L'identite utilisateur est recuperee depuis le parametre state signe.
    """
    logger = logging.getLogger("hapson-api")
    frontend_callback = f"{settings.FRONTEND_URL}/social/callback"

    # Erreur retournee par la plateforme
    if error:
        params = urlencode({
            "status": "error",
            "message": error_description or error,
        })
        return RedirectResponse(url=f"{frontend_callback}?{params}")

    # Parametres manquants
    if not code or not state:
        params = urlencode({
            "status": "error",
            "message": "Parametres OAuth manquants (code ou state)",
        })
        return RedirectResponse(url=f"{frontend_callback}?{params}")

    try:
        # 1. Verifier et decoder le state
        state_data = verify_oauth_state(state)
        user_id = state_data["user_id"]
        platform = state_data["platform"]

        # 2. Echanger le code contre des tokens
        token_data = exchange_code_for_token(platform, code, state)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")

        # Calculer l'expiration du token
        token_expires_at = None
        expires_in = token_data.get("expires_in")
        if expires_in:
            token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        # 3. Recuperer le profil utilisateur
        profile = fetch_user_profile(platform, access_token)

        # 4. Sauvegarder / mettre a jour le SocialAccount en BDD
        account = upsert_social_account_from_oauth(
            db=db,
            platform=platform,
            platform_user_id=profile["platform_user_id"],
            account_name=profile["name"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            avatar_url=profile.get("picture_url"),
            connected_by=user_id,
        )

        # Marquer comme profil (c'est le compte utilisateur, pas une page)
        account.account_type = "profile"
        db.commit()

        # 5. Audit log
        log_action(db, user_id, "oauth_connect", "social_accounts", account.id)

        # 6. Rediriger vers le frontend avec succes
        params = urlencode({
            "status": "success",
            "platform": platform,
            "account": profile["name"],
            "account_id": str(account.id),
        })
        return RedirectResponse(url=f"{frontend_callback}?{params}")

    except HTTPException as e:
        params = urlencode({
            "status": "error",
            "message": e.detail if isinstance(e.detail, str) else "Erreur OAuth",
        })
        return RedirectResponse(url=f"{frontend_callback}?{params}")
    except Exception as e:
        logger.error(f"Erreur callback OAuth: {e}", exc_info=True)
        params = urlencode({
            "status": "error",
            "message": "Erreur interne lors de la connexion OAuth",
        })
        return RedirectResponse(url=f"{frontend_callback}?{params}")


@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Déconnecter un compte social et supprimer toutes les données liées."""
    result = disconnect_social_account(db, account_id)
    log_action(db, current_user.id, "disconnect", "social_accounts", account_id)
    return {"success": True, "cascade": result}


@router.get("/accounts/{account_id}/status", response_model=SocialAccountStatusResponse)
def account_status(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Vérifier le statut du token OAuth d'un compte."""
    return check_account_token_status(db, account_id)


# ════════════════════════════════════════════════════════════════
# SYNCHRONISATION FACEBOOK
# ════════════════════════════════════════════════════════════════

@router.post("/accounts/{account_id}/sync")
def sync_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Synchroniser les posts et commentaires Facebook pour un compte.

    Recupere les derniers posts de la page Facebook connectee,
    importe les nouveaux posts et commentaires, et met a jour
    les metriques d'engagement des posts existants.
    """
    result = sync_facebook_account(db, account_id)
    log_action(db, current_user.id, "sync", "social_accounts", account_id)
    return result


@router.post("/sync")
def sync_all(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Synchroniser tous les comptes Facebook actifs.

    Parcourt tous les comptes Facebook connectes et declenche
    la synchronisation des posts et commentaires pour chacun.
    """
    result = sync_all_facebook_accounts(db)
    log_action(db, current_user.id, "sync_all", "social_accounts", 0)
    return result


# ════════════════════════════════════════════════════════════════
# PUBLICATIONS
# ════════════════════════════════════════════════════════════════

@router.get("/posts", response_model=list[SocialPostResponse])
def list_posts(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    platform: Optional[str] = Query(None, description="Filtrer par plateforme"),
    date_from: Optional[str] = Query(None, description="Date de début"),
    date_to: Optional[str] = Query(None, description="Date de fin"),
    search: Optional[str] = Query(None, description="Recherche dans le contenu"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Lister les publications avec filtres."""
    posts = get_social_posts(db, status, platform, date_from, date_to, search)
    # Enrichir avec le nom de l'auteur et le nom du compte par resultat
    accounts_cache = {}
    for post in posts:
        from app.models import User
        user = db.query(User).filter(User.id == post.created_by).first()
        post.created_by_name = f"{user.name} {user.family_name}" if user else None
        # Enrichir chaque result avec account_name (nom de la page)
        for result in post.results:
            if result.account_id not in accounts_cache:
                acc = db.query(SocialAccount).filter(SocialAccount.id == result.account_id).first()
                accounts_cache[result.account_id] = acc.account_name if acc else None
            result.account_name = accounts_cache[result.account_id]
    return posts


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Récupérer un post par ID."""
    post = get_social_post_by_id(db, post_id)
    from app.models import User
    user = db.query(User).filter(User.id == post.created_by).first()
    post.created_by_name = f"{user.name} {user.family_name}" if user else None
    # Enrichir les results avec account_name
    for result in post.results:
        acc = db.query(SocialAccount).filter(SocialAccount.id == result.account_id).first()
        result.account_name = acc.account_name if acc else None
    return post


@router.post("/posts", response_model=SocialPostResponse)
def create_post(
    post_data: SocialPostCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Créer une nouvelle publication."""
    post = create_social_post(db, post_data, current_user.id)
    log_action(db, current_user.id, "create", "social_posts", post.id)
    return post


@router.put("/posts/{post_id}", response_model=SocialPostResponse)
def update_post(
    post_id: int,
    post_data: SocialPostUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Modifier une publication existante."""
    post = update_social_post(db, post_id, post_data)
    log_action(db, current_user.id, "update", "social_posts", post_id)
    return post


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Supprimer une publication et ses résultats (soft delete)."""
    result = delete_social_post(db, post_id)
    log_action(db, current_user.id, "delete", "social_posts", post_id)
    return {"success": True, "cascade": result}


@router.post("/posts/{post_id}/publish", response_model=SocialPostResponse)
def publish_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Publier immédiatement une publication."""
    post = publish_social_post(db, post_id)
    log_action(db, current_user.id, "publish", "social_posts", post_id)
    return post


@router.post("/posts/{post_id}/schedule", response_model=SocialPostResponse)
def schedule_post(
    post_id: int,
    body: SchedulePostRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Planifier la publication d'un post."""
    post = schedule_social_post(db, post_id, body.scheduled_at)
    log_action(db, current_user.id, "schedule", "social_posts", post_id)
    return post


# ════════════════════════════════════════════════════════════════
# INBOX — COMMENTAIRES
# ════════════════════════════════════════════════════════════════

@router.get("/comments", response_model=list[SocialCommentResponse])
def list_comments(
    post_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Lister les commentaires (inbox)."""
    comments = get_social_comments(db, post_id, platform, is_read)
    # Enrichir avec le nom du compte
    for comment in comments:
        try:
            acc = get_social_account_by_id(db, comment.account_id)
            comment.account_name = acc.account_name
        except Exception:
            comment.account_name = None
    return comments


@router.post("/comments/{comment_id}/reply", response_model=SocialCommentResponse)
def reply_to_comment(
    comment_id: int,
    body: ReplyToCommentRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Répondre à un commentaire."""
    parent = get_comment_by_id(db, comment_id)
    # TODO: Envoyer la réponse via l'API de la plateforme
    # Pour l'instant, créer un enregistrement local
    from app.models.model_social import SocialComment as SocialCommentModel
    import secrets
    reply = SocialCommentModel(
        platform_comment_id=f"reply_{secrets.token_hex(8)}",
        post_id=parent.post_id,
        account_id=parent.account_id,
        platform=parent.platform,
        author_name="Radio Manager",
        author_platform_id="self",
        content=body.content,
        parent_comment_id=comment_id,
        is_read=True,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    log_action(db, current_user.id, "reply", "social_comments", comment_id)
    return reply


@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Liker un commentaire."""
    comment = get_comment_by_id(db, comment_id)
    comment.likes_count += 1
    db.commit()
    # TODO: Envoyer le like via l'API plateforme
    return {"success": True}


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Supprimer un commentaire et ses réponses."""
    result = delete_social_comment(db, comment_id)
    log_action(db, current_user.id, "delete", "social_comments", comment_id)
    return {"success": True, "cascade": result}


@router.post("/comments/{comment_id}/hide")
def hide_comment_route(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Masquer un commentaire."""
    result = hide_comment(db, comment_id)
    return {"success": result}


@router.post("/comments/{comment_id}/read")
def mark_read(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Marquer un commentaire comme lu."""
    result = mark_comment_read(db, comment_id)
    return {"success": result}


# ════════════════════════════════════════════════════════════════
# INBOX — MESSAGES PRIVÉS
# ════════════════════════════════════════════════════════════════

@router.get("/messages", response_model=list[SocialConversationResponse])
def list_conversations(
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Lister les conversations de messages privés."""
    conversations = get_conversations(db, platform)
    # Ajouter last_message
    for conv in conversations:
        if conv.messages:
            conv.last_message = conv.messages[-1]
    return conversations


@router.get("/messages/{conversation_id}", response_model=SocialConversationResponse)
def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Récupérer le détail d'une conversation avec ses messages."""
    return get_conversation_by_id(db, conversation_id)


@router.post("/messages/{conversation_id}/reply")
def reply_to_conversation(
    conversation_id: int,
    body: ReplyToConversationRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Répondre dans une conversation."""
    conversation = get_conversation_by_id(db, conversation_id)
    # TODO: Envoyer le message via l'API de la plateforme
    from app.models.model_social import SocialMessage as SocialMessageModel
    import secrets
    message = SocialMessageModel(
        conversation_id=conversation_id,
        platform_message_id=f"msg_{secrets.token_hex(8)}",
        account_id=conversation.account_id,
        platform=conversation.platform,
        sender_name="Radio Manager",
        sender_platform_id="self",
        sender_avatar=None,
        content=body.content,
        direction="outbound",
        is_read=True,
    )
    db.add(message)
    # Mettre à jour la conversation
    from datetime import datetime, timezone
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, current_user.id, "reply", "social_messages", conversation_id)
    return {"success": True}


# ════════════════════════════════════════════════════════════════
# NETTOYAGE & OPTIMISATION BASE DE DONNÉES
# ════════════════════════════════════════════════════════════════

@router.get("/database/stats")
def database_stats(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Statistiques de la base de données du module social.

    Retourne les compteurs d'enregistrements actifs, soft-deletés
    et orphelins pour chaque table.
    Requiert la permission social_manage_accounts.
    """
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )
    return get_database_stats(db)


@router.post("/database/optimize")
def optimize_database(
    hard_delete_days: int = Query(30, ge=-1, le=365, description="Purger les éléments supprimés depuis plus de X jours (0 = tout purger, -1 = orphelins uniquement)"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Optimiser la base de données du module social.

    1. Nettoie les orphelins (données liées à des comptes/posts supprimés)
    2. Purge définitivement les enregistrements soft-deleted :
       - hard_delete_days=0 : purge TOUT immédiatement
       - hard_delete_days=N : purge les éléments supprimés depuis >N jours
       - hard_delete_days=-1 : orphelins uniquement, pas de purge

    Requiert la permission social_manage_accounts.
    """
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )

    result = cleanup_database(db, hard_delete_days)
    log_action(db, current_user.id, "optimize", "social_database", 0)
    return result


# ════════════════════════════════════════════════════════════════
# STATISTIQUES
# ════════════════════════════════════════════════════════════════

@router.get("/analytics/overview", response_model=SocialAnalyticsOverviewResponse)
def analytics_overview(
    period: str = Query("30d", description="Période : 7d, 30d, 90d, 12m"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Vue d'ensemble des statistiques d'engagement."""
    return get_analytics_overview(db, period)


@router.get("/analytics/platforms", response_model=list[PlatformStatsResponse])
def analytics_platforms(
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Statistiques ventilées par plateforme."""
    return get_platform_stats(db, period)


@router.get("/analytics/best-times", response_model=list[BestTimeSlotResponse])
def analytics_best_times(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Meilleurs horaires de publication."""
    return get_best_times(db)


@router.get("/analytics/engagement", response_model=list[TimeSeriesPointResponse])
def analytics_engagement(
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Série temporelle de l'engagement."""
    return get_engagement_time_series(db, period)


# ════════════════════════════════════════════════════════════════
# DIAGNOSTIC — TEST COMPLET DES PERMISSIONS FACEBOOK
# ════════════════════════════════════════════════════════════════

@router.get("/debug/test-page-api")
def debug_test_page_api(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Diagnostic complet Facebook : teste TOUS les tokens et approches.
    - Token user (profil) : permissions, feed avec user_token
    - Token page stocke (Radio Audace) : feed, engagement
    - Token page frais (/me/accounts) : feed, engagement
    """
    import httpx

    GRAPH_API_BASE = "https://graph.facebook.com/v18.0"
    results = {}

    def safe_get(url, params, label=""):
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "OK",
                    "data_count": len(data.get("data", [])),
                    "sample": str(data)[:600],
                }
            else:
                return {"status": f"HTTP {resp.status_code}", "error": resp.text[:400]}
        except Exception as e:
            return {"status": "EXCEPTION", "error": str(e)}

    # ── 1. Charger tous les comptes FB ──
    all_accounts = (
        db.query(SocialAccount)
        .filter(SocialAccount.platform == "facebook", SocialAccount.is_active == True)
        .all()
    )
    results["db_accounts"] = [
        {"id": a.id, "type": a.account_type, "name": a.account_name,
         "fb_id": a.account_id, "has_token": bool(a.access_token)}
        for a in all_accounts
    ]

    profile = next((a for a in all_accounts if a.account_type == "profile"), None)
    page_accounts = [a for a in all_accounts if a.account_type == "page"]

    if not profile:
        return {**results, "error": "Aucun profil Facebook actif"}

    user_token = profile.access_token
    results["profile"] = {"name": profile.account_name, "fb_id": profile.account_id}

    # ── 2. Permissions du USER token ──
    results["user_token_permissions"] = safe_get(
        f"{GRAPH_API_BASE}/me/permissions",
        {"access_token": user_token},
    )

    # ── 3. Pages via /me/accounts (token frais) ──
    fresh_pages = {}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{GRAPH_API_BASE}/me/accounts", params={
                "access_token": user_token,
                "fields": "id,name,access_token,tasks",
                "limit": 50,
            })
        if resp.status_code == 200:
            pages_data = resp.json().get("data", [])
            results["me_accounts"] = [
                {"id": p["id"], "name": p["name"], "tasks": p.get("tasks", [])}
                for p in pages_data
            ]
            for p in pages_data:
                fresh_pages[p["id"]] = p
        else:
            results["me_accounts"] = {"error": resp.text[:300]}
    except Exception as e:
        results["me_accounts"] = {"error": str(e)}

    # ── 4. Test chaque page stockee en DB ──
    for page_acc in page_accounts:
        pid = page_acc.account_id
        pname = page_acc.account_name
        section = f"page_{page_acc.id}_{pname.replace(' ', '_')}"
        page_results = {"fb_id": pid, "name": pname}

        stored_token = page_acc.access_token
        fresh_token = fresh_pages.get(pid, {}).get("access_token")
        fresh_tasks = fresh_pages.get(pid, {}).get("tasks", [])
        page_results["in_me_accounts"] = pid in fresh_pages
        page_results["tasks"] = fresh_tasks
        page_results["has_stored_token"] = bool(stored_token)
        page_results["has_fresh_token"] = bool(fresh_token)

        # Quel token utiliser : frais si dispo, sinon stocke
        test_token = fresh_token or stored_token
        token_label = "fresh" if fresh_token else "stored"
        page_results["token_used"] = token_label

        if not test_token:
            page_results["error"] = "Aucun token disponible"
            results[section] = page_results
            continue

        # 4a. Feed basique
        page_results["feed_basic"] = safe_get(
            f"{GRAPH_API_BASE}/{pid}/feed",
            {"access_token": test_token, "fields": "id,message,shares", "limit": 2},
        )

        # 4b. Feed avec likes.summary + comments.summary
        page_results["feed_likes_comments"] = safe_get(
            f"{GRAPH_API_BASE}/{pid}/feed",
            {"access_token": test_token,
             "fields": "id,message,likes.summary(true),comments.summary(true),shares", "limit": 2},
        )

        # 4c. Feed avec reactions.summary + comments.summary
        page_results["feed_reactions_comments"] = safe_get(
            f"{GRAPH_API_BASE}/{pid}/feed",
            {"access_token": test_token,
             "fields": "id,reactions.summary(total_count),comments.summary(total_count),shares", "limit": 2},
        )

        # Trouver un post_id
        post_id = None
        feed_res = page_results["feed_basic"]
        if feed_res.get("status") == "OK" and feed_res.get("data_count", 0) > 0:
            try:
                import json
                # Le sample contient le JSON tronque, faire un vrai appel
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(f"{GRAPH_API_BASE}/{pid}/feed",
                                      params={"access_token": test_token, "fields": "id", "limit": 1})
                if resp.status_code == 200:
                    posts = resp.json().get("data", [])
                    if posts:
                        post_id = posts[0]["id"]
            except Exception:
                pass

        if post_id:
            page_results["test_post_id"] = post_id

            # 4d. Post engagement via field expansion
            page_results["post_engagement"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}",
                {"access_token": test_token,
                 "fields": "likes.summary(true),comments.summary(true),reactions.summary(total_count),shares"},
            )

            # 4e. Comments edge
            page_results["post_comments"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/comments",
                {"access_token": test_token,
                 "fields": "id,message,created_time,like_count", "limit": 5},
            )

            # 4f. Reactions edge
            page_results["post_reactions"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/reactions",
                {"access_token": test_token, "limit": 0, "summary": "total_count"},
            )

            # 4g. Meme tests avec USER token (profil)
            page_results["user_token_feed"] = safe_get(
                f"{GRAPH_API_BASE}/{pid}/feed",
                {"access_token": user_token, "fields": "id,message,shares", "limit": 2},
            )
            page_results["user_token_feed_engagement"] = safe_get(
                f"{GRAPH_API_BASE}/{pid}/feed",
                {"access_token": user_token,
                 "fields": "id,likes.summary(true),comments.summary(true),reactions.summary(total_count),shares",
                 "limit": 2},
            )
            page_results["user_token_post_engagement"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}",
                {"access_token": user_token,
                 "fields": "likes.summary(true),comments.summary(true),reactions.summary(total_count),shares"},
            )
            page_results["user_token_comments"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/comments",
                {"access_token": user_token,
                 "fields": "id,message,created_time,like_count", "limit": 5},
            )
        else:
            page_results["note"] = "Aucun post trouve - tests post/engagement non effectues"

        results[section] = page_results

    # ── 5. Test pages fraiches non stockees en DB ──
    stored_page_ids = {a.account_id for a in page_accounts}
    for fp_id, fp_data in fresh_pages.items():
        if fp_id in stored_page_ids:
            continue  # Deja teste ci-dessus
        section = f"fresh_page_{fp_data['name'].replace(' ', '_')}"
        fp_results = {"fb_id": fp_id, "name": fp_data["name"], "tasks": fp_data.get("tasks", []),
                      "note": "Page dans /me/accounts mais PAS en DB"}
        fresh_tok = fp_data["access_token"]

        fp_results["feed_basic"] = safe_get(
            f"{GRAPH_API_BASE}/{fp_id}/feed",
            {"access_token": fresh_tok, "fields": "id,message,shares", "limit": 2},
        )
        fp_results["feed_engagement"] = safe_get(
            f"{GRAPH_API_BASE}/{fp_id}/feed",
            {"access_token": fresh_tok,
             "fields": "id,likes.summary(true),comments.summary(true),reactions.summary(total_count),shares",
             "limit": 2},
        )

        # Post test
        post_id = None
        if fp_results["feed_basic"].get("status") == "OK":
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(f"{GRAPH_API_BASE}/{fp_id}/feed",
                                      params={"access_token": fresh_tok, "fields": "id", "limit": 1})
                if resp.status_code == 200:
                    posts = resp.json().get("data", [])
                    if posts:
                        post_id = posts[0]["id"]
            except Exception:
                pass

        if post_id:
            fp_results["post_engagement"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}",
                {"access_token": fresh_tok,
                 "fields": "likes.summary(true),comments.summary(true),reactions.summary(total_count),shares"},
            )
            fp_results["post_comments"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/comments",
                {"access_token": fresh_tok,
                 "fields": "id,message,created_time,like_count", "limit": 5},
            )

        results[section] = fp_results

    # ── 6. Recommandations ──
    recommendations = []
    # Verifier permissions user token
    user_perms_res = results.get("user_token_permissions", {})
    if user_perms_res.get("status") == "OK":
        sample = user_perms_res.get("sample", "")
        if "pages_read_engagement" not in sample:
            recommendations.append(
                "CRITIQUE: Le token user N'A PAS la permission 'pages_read_engagement'. "
                "Allez sur Meta Developer Portal > Votre App > Facebook Login for Business > "
                f"Configuration (config_id) et ajoutez 'pages_read_engagement' + 'pages_read_user_content'. "
                "Puis reconnectez le compte Facebook dans l'app."
            )
        if "pages_read_user_content" not in sample:
            recommendations.append(
                "IMPORTANT: Permission 'pages_read_user_content' manquante — necessaire pour lire les commentaires."
            )
    else:
        recommendations.append(f"Impossible de verifier les permissions du user token: {user_perms_res}")

    if not fresh_pages:
        recommendations.append("ALERTE: /me/accounts ne retourne aucune page. L'utilisateur n'a pas de page accessible.")
    else:
        for pa in page_accounts:
            if pa.account_id not in fresh_pages:
                recommendations.append(
                    f"Page '{pa.account_name}' (id {pa.account_id}) n'est PAS dans /me/accounts. "
                    "L'utilisateur connecte n'a pas acces a cette page. "
                    "Connectez-vous avec un compte Facebook qui est admin/editeur de cette page."
                )

    results["recommendations"] = recommendations

    return results

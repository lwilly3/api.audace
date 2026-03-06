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

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import logging
import threading

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
    get_reactions_breakdown,
    get_follower_trend,
    get_video_performance,
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
    ReactionsBreakdownResponse,
    FollowerTrendResponse,
    VideoPerformanceResponse,
    GenerateFromUrlRequest,
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
# SYNCHRONISATION FACEBOOK (BACKGROUND TASK)
# ════════════════════════════════════════════════════════════════

@router.post("/accounts/{account_id}/sync")
def sync_account(
    account_id: int,
    force: bool = Query(False, description="Force la re-synchronisation complete des metriques"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Lancer la synchronisation Facebook en arrière-plan.

    Retourne immédiatement un task_id pour suivre la progression
    via GET /social/sync/status/{task_id}.
    """
    from app.services import sync_tasks
    from app.db.database import SessionLocal

    sync_tasks.cleanup()

    task_id = sync_tasks.create(label=f"sync-account-{account_id}")

    def _run():
        session = SessionLocal()
        try:
            def progress(msg, pct):
                sync_tasks.update(task_id, progress=msg, percent=pct)

            result = sync_facebook_account(session, account_id, force=force, on_progress=progress)
            sync_tasks.complete(task_id, result)
        except Exception as e:
            sync_tasks.fail(task_id, str(e))
        finally:
            session.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    log_action(db, current_user.id, "sync", "social_accounts", account_id)
    return {"task_id": task_id, "status": "running", "message": "Synchronisation lancée en arrière-plan"}


@router.post("/sync")
def sync_all(
    force: bool = Query(False, description="Force la re-synchronisation complete des metriques"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Synchroniser tous les comptes Facebook en arrière-plan.

    Retourne immédiatement un task_id pour suivre la progression.
    """
    from app.services import sync_tasks
    from app.db.database import SessionLocal

    sync_tasks.cleanup()

    task_id = sync_tasks.create(label="sync-all")

    def _run():
        session = SessionLocal()
        try:
            def progress(msg, pct):
                sync_tasks.update(task_id, progress=msg, percent=pct)

            result = sync_all_facebook_accounts(session, force=force, on_progress=progress)
            sync_tasks.complete(task_id, result)
        except Exception as e:
            sync_tasks.fail(task_id, str(e))
        finally:
            session.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    log_action(db, current_user.id, "sync_all", "social_accounts", 0)
    return {"task_id": task_id, "status": "running", "message": "Synchronisation lancée en arrière-plan"}


@router.get("/sync/status/{task_id}")
def sync_status(
    task_id: str,
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Vérifier le statut d'une tâche de synchronisation.

    Retourne le pourcentage de progression, le message courant,
    et le résultat final quand la tâche est terminée.
    """
    from app.services import sync_tasks

    task = sync_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return task


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
# GENERATION IA DEPUIS URL
# ════════════════════════════════════════════════════════════════

@router.post("/generate-from-url")
def generate_from_url(
    body: GenerateFromUrlRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Generer un post Facebook a partir d'une URL d'article.

    1. Telecharge le contenu HTML de l'URL
    2. Extrait le texte brut
    3. Envoie a Mistral Small pour generation
    4. Retourne le texte genere

    Le contenu genere est une suggestion — l'utilisateur peut le modifier
    avant de publier.
    """
    from app.services.ai_service import fetch_article_text, generate_post_from_article

    article_text = fetch_article_text(body.url)
    generated_content = generate_post_from_article(article_text, body.url, body.mode, body.custom_instructions)

    log_action(db, current_user.id, "ai_generate", "social_posts", 0)

    return {
        "generated_content": generated_content,
        "source_url": body.url,
    }


# ════════════════════════════════════════════════════════════════
# INBOX — COMMENTAIRES
# ════════════════════════════════════════════════════════════════

@router.get("/comments", response_model=list[SocialCommentResponse])
def list_comments(
    response: Response,
    post_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None, description="Date debut ISO 8601 (ex: 2025-01-01)"),
    date_to: Optional[str] = Query(None, description="Date fin ISO 8601"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max de commentaires"),
    offset: int = Query(0, ge=0, description="Decalage pour pagination"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Lister les commentaires (inbox) avec pagination et filtrage par date."""
    parsed_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_to = datetime.fromisoformat(date_to) if date_to else None

    comments, total = get_social_comments(
        db, post_id, platform, is_read, parsed_from, parsed_to, limit, offset
    )
    # Enrichir avec le nom du compte
    for comment in comments:
        try:
            acc = get_social_account_by_id(db, comment.account_id)
            comment.account_name = acc.account_name
        except Exception:
            comment.account_name = None
    response.headers["X-Total-Count"] = str(total)
    return comments


@router.post("/comments/{comment_id}/reply", response_model=SocialCommentResponse)
def reply_to_comment(
    comment_id: int,
    body: ReplyToCommentRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Répondre à un commentaire — envoie la réponse sur Facebook puis sauvegarde en BDD."""
    parent = get_comment_by_id(db, comment_id)
    from app.models.model_social import SocialComment as SocialCommentModel
    import secrets

    # Recuperer le compte (page) pour obtenir le page access token
    page_account = get_social_account_by_id(db, parent.account_id)

    fb_reply_id = None

    # Envoyer sur Facebook si c'est un commentaire Facebook avec un vrai ID
    if (
        parent.platform == "facebook"
        and page_account.access_token
        and parent.platform_comment_id
        and not parent.platform_comment_id.startswith("reply_")
    ):
        try:
            from app.services.social_facebook import reply_to_facebook_comment
            fb_result = reply_to_facebook_comment(
                page_access_token=page_account.access_token,
                comment_id=parent.platform_comment_id,
                message=body.content,
            )
            fb_reply_id = fb_result.get("id", "")
            print(f"[REPLY] Reponse envoyee sur Facebook: {fb_reply_id}", flush=True)
        except HTTPException as e:
            print(f"[REPLY] Erreur envoi Facebook: {e.detail}", flush=True)
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Impossible d'envoyer la reponse sur Facebook: {e.detail}"
            )

    # Sauvegarder en BDD avec le vrai ID Facebook ou un ID local
    reply = SocialCommentModel(
        platform_comment_id=fb_reply_id if fb_reply_id else f"reply_{secrets.token_hex(8)}",
        post_id=parent.post_id,
        account_id=parent.account_id,
        platform=parent.platform,
        author_name=page_account.account_name or "Radio Manager",
        author_platform_id=page_account.account_id or "self",
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
    """Liker un commentaire — envoie le like sur Facebook puis met à jour en BDD."""
    comment = get_comment_by_id(db, comment_id)

    # Envoyer le like sur Facebook
    if (
        comment.platform == "facebook"
        and comment.platform_comment_id
        and not comment.platform_comment_id.startswith("reply_")
    ):
        page_account = get_social_account_by_id(db, comment.account_id)
        if page_account.access_token:
            try:
                from app.services.social_facebook import like_facebook_comment
                like_facebook_comment(
                    page_access_token=page_account.access_token,
                    comment_id=comment.platform_comment_id,
                )
                print(f"[LIKE] Like envoye sur Facebook: {comment.platform_comment_id}", flush=True)
            except HTTPException as e:
                print(f"[LIKE] Erreur envoi Facebook: {e.detail}", flush=True)
                # On continue quand meme pour mettre a jour localement

    comment.likes_count += 1
    db.commit()
    return {"success": True}


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Supprimer un commentaire — supprime sur Facebook si possible, puis en BDD."""
    comment = get_comment_by_id(db, comment_id)

    # Supprimer sur Facebook (uniquement pour les reponses faites par la page)
    if (
        comment.platform == "facebook"
        and comment.platform_comment_id
        and not comment.platform_comment_id.startswith("reply_")
    ):
        page_account = get_social_account_by_id(db, comment.account_id)
        if page_account.access_token:
            try:
                from app.services.social_facebook import delete_facebook_comment
                delete_facebook_comment(
                    page_access_token=page_account.access_token,
                    comment_id=comment.platform_comment_id,
                )
                print(f"[DELETE] Commentaire supprime sur Facebook: {comment.platform_comment_id}", flush=True)
            except Exception as e:
                print(f"[DELETE] Erreur suppression Facebook (continue localement): {e}", flush=True)

    result = delete_social_comment(db, comment_id)
    log_action(db, current_user.id, "delete", "social_comments", comment_id)
    return {"success": True, "cascade": result}


@router.post("/comments/{comment_id}/hide")
def hide_comment_route(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Masquer un commentaire — masque sur Facebook puis en BDD."""
    comment = get_comment_by_id(db, comment_id)

    # Masquer sur Facebook
    if (
        comment.platform == "facebook"
        and comment.platform_comment_id
        and not comment.platform_comment_id.startswith("reply_")
    ):
        page_account = get_social_account_by_id(db, comment.account_id)
        if page_account.access_token:
            try:
                from app.services.social_facebook import hide_facebook_comment
                hide_facebook_comment(
                    page_access_token=page_account.access_token,
                    comment_id=comment.platform_comment_id,
                    hide=True,
                )
                print(f"[HIDE] Commentaire masque sur Facebook: {comment.platform_comment_id}", flush=True)
            except Exception as e:
                print(f"[HIDE] Erreur masquage Facebook (continue localement): {e}", flush=True)

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
    """Repondre dans une conversation — envoie le message via l'API Facebook."""
    conversation = get_conversation_by_id(db, conversation_id)

    # Recuperer le compte social pour le page access token
    account = get_social_account_by_id(db, conversation.account_id)

    # Trouver le PSID du destinataire (premier message inbound)
    from app.models.model_social import SocialMessage as SocialMessageModel
    recipient_msg = (
        db.query(SocialMessageModel)
        .filter(
            SocialMessageModel.conversation_id == conversation_id,
            SocialMessageModel.direction == "inbound",
            SocialMessageModel.is_deleted == False,
        )
        .order_by(SocialMessageModel.created_at.asc())
        .first()
    )

    # Envoyer via l'API Facebook si c'est un compte Facebook
    fb_message_id = None
    if account and conversation.platform == "facebook" and recipient_msg:
        try:
            from app.services.social_facebook import send_facebook_message
            result = send_facebook_message(
                page_id=account.account_id,
                recipient_psid=recipient_msg.sender_platform_id,
                message_text=body.content,
                page_access_token=account.access_token,
            )
            fb_message_id = result.get("message_id")
        except Exception as e:
            logger.warning(f"Echec envoi message Facebook: {e}")
            # On continue quand meme pour sauvegarder localement

    import secrets
    message = SocialMessageModel(
        conversation_id=conversation_id,
        platform_message_id=fb_message_id or f"msg_{secrets.token_hex(8)}",
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
    # Mettre a jour la conversation
    from datetime import datetime, timezone
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, current_user.id, "reply", "social_messages", conversation_id)
    return {"success": True, "sent_to_platform": fb_message_id is not None}


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


@router.post("/storage/cleanup-orphans")
def cleanup_storage_orphans(
    dry_run: bool = Query(True, description="Apercu sans suppression (True par defaut)"),
    prefix: str = Query("social/", description="Prefix Firebase Storage a scanner"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Detecter et supprimer les fichiers orphelins dans Firebase Storage.

    Compare les fichiers presents dans le bucket (sous le prefix donne)
    avec les media_urls references par les posts actifs en base.
    Les fichiers non references sont consideres comme orphelins.

    - dry_run=True (defaut) : retourne la liste des orphelins sans suppression
    - dry_run=False : supprime les fichiers orphelins

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

    # Collecter toutes les media_urls des posts actifs (non soft-deleted)
    from app.models.model_social import SocialPost

    posts_with_media = db.query(SocialPost.media_urls).filter(
        SocialPost.is_deleted == False,
        SocialPost.media_urls != None,
    ).all()

    all_media_urls: list[str] = []
    for (media_urls,) in posts_with_media:
        if media_urls:
            all_media_urls.extend(media_urls)

    from app.services.firebase_cleanup import cleanup_orphan_files
    result = cleanup_orphan_files(
        db_media_urls=all_media_urls,
        prefix=prefix,
        dry_run=dry_run,
    )

    action = "storage_cleanup_preview" if dry_run else "storage_cleanup_execute"
    log_action(db, current_user.id, action, "firebase_storage", 0)

    return result


# ════════════════════════════════════════════════════════════════
# SCHEDULER (TÂCHES PÉRIODIQUES)
# ════════════════════════════════════════════════════════════════

@router.get("/scheduler/settings")
def get_scheduler_settings(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Récupérer les paramètres du scheduler (auto-sync, auto-optimize).
    Inclut le statut courant et les dernières exécutions.
    """
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )
    from app.services.social_scheduler import scheduler
    return scheduler.get_settings()


@router.put("/scheduler/settings")
def update_scheduler_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Mettre à jour les paramètres du scheduler.

    Paramètres acceptés :
    - auto_sync_enabled (bool)
    - auto_sync_interval_minutes (int: 5, 15, 30, 60, 120, 360, 720)
    - auto_sync_force (bool)
    - auto_optimize_enabled (bool)
    - auto_optimize_interval_hours (int: 6, 12, 24, 48, 168)
    - auto_optimize_purge_days (int: 7, 30, 90)
    """
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )
    from app.services.social_scheduler import scheduler
    result = scheduler.update_settings(settings)
    log_action(db, current_user.id, "update", "social_scheduler", 0)
    return result


@router.post("/scheduler/trigger/sync")
def trigger_scheduler_sync(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Déclencher manuellement une sync via le scheduler (exécution immédiate)."""
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )
    from app.services.social_scheduler import scheduler
    settings = scheduler.get_settings()
    force = settings.get("auto_sync_force", False)

    # Lancer dans un thread séparé
    def _run():
        scheduler._run_sync(force)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log_action(db, current_user.id, "trigger_sync", "social_scheduler", 0)
    return {"message": "Synchronisation déclenchée"}


@router.post("/scheduler/trigger/optimize")
def trigger_scheduler_optimize(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Déclencher manuellement une optimisation via le scheduler."""
    perms = db.query(UserPermissions).filter(
        UserPermissions.user_id == current_user.id
    ).first()
    if not perms or not perms.social_manage_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'social_manage_accounts' requise"
        )
    from app.services.social_scheduler import scheduler
    settings = scheduler.get_settings()
    purge_days = settings.get("auto_optimize_purge_days", 30)

    def _run():
        scheduler._run_optimize(purge_days)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log_action(db, current_user.id, "trigger_optimize", "social_scheduler", 0)
    return {"message": "Optimisation déclenchée"}


# ════════════════════════════════════════════════════════════════
# STATISTIQUES
# ════════════════════════════════════════════════════════════════

@router.get("/analytics/overview", response_model=SocialAnalyticsOverviewResponse)
def analytics_overview(
    period: str = Query("30d", description="Période : 7d, 30d, 90d, 12m"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer les stats"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Vue d'ensemble des statistiques d'engagement."""
    return get_analytics_overview(db, period, account_id=account_id)


@router.get("/analytics/platforms", response_model=list[PlatformStatsResponse])
def analytics_platforms(
    period: str = Query("30d"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer les stats"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Statistiques ventilées par plateforme."""
    return get_platform_stats(db, period, account_id=account_id)


@router.get("/analytics/best-times", response_model=list[BestTimeSlotResponse])
def analytics_best_times(
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer les stats"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Meilleurs horaires de publication."""
    return get_best_times(db, account_id=account_id)


@router.get("/analytics/engagement", response_model=list[TimeSeriesPointResponse])
def analytics_engagement(
    period: str = Query("30d"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer les stats"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Série temporelle de l'engagement."""
    return get_engagement_time_series(db, period, account_id=account_id)


@router.get("/analytics/reactions", response_model=ReactionsBreakdownResponse)
def analytics_reactions(
    period: str = Query("30d", description="Période : 7d, 30d, 90d, 12m"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Repartition des reactions par type (like, love, wow, haha, sorry, anger)."""
    return get_reactions_breakdown(db, period, account_id=account_id)


@router.get("/analytics/followers", response_model=FollowerTrendResponse)
def analytics_followers(
    period: str = Query("30d", description="Période : 7d, 30d, 90d, 12m"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Tendance des abonnes avec serie temporelle."""
    return get_follower_trend(db, period, account_id=account_id)


@router.get("/analytics/video", response_model=VideoPerformanceResponse)
def analytics_video(
    period: str = Query("30d", description="Période : 7d, 30d, 90d, 12m"),
    account_id: Optional[int] = Query(None, description="ID du compte pour filtrer"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Performance video de la page."""
    return get_video_performance(db, period, account_id=account_id)


# ════════════════════════════════════════════════════════════════
# VERIFICATION DES PERMISSIONS FACEBOOK
# ════════════════════════════════════════════════════════════════

@router.get("/accounts/permissions-check")
def check_facebook_permissions(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Verifie les permissions Facebook du token utilisateur.
    Retourne les permissions accordees, manquantes, et les pages accessibles.
    Utilise par le frontend pour afficher des alertes de configuration.
    """
    import httpx

    GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

    profile = (
        db.query(SocialAccount)
        .filter(SocialAccount.platform == "facebook", SocialAccount.account_type == "profile", SocialAccount.is_active == True)
        .first()
    )
    if not profile or not profile.access_token:
        return {
            "status": "no_profile",
            "message": "Aucun compte Facebook n'est connecte. Connectez un compte dans Parametres > Comptes sociaux.",
            "permissions": [], "missing_permissions": [], "pages": [],
        }

    user_token = profile.access_token
    result = {
        "status": "ok",
        "profile_name": profile.account_name,
        "permissions": [],
        "missing_permissions": [],
        "pages": [],
        "issues": [],
    }

    # Permissions requises pour l'engagement et les commentaires
    required_permissions = {
        "pages_read_engagement": "Lire les likes, commentaires, reactions, et le feed des pages",
        "pages_read_user_content": "Lire les commentaires des visiteurs sur les pages",
        "pages_show_list": "Lister les pages gerees par l'utilisateur",
        "pages_manage_posts": "Publier et gerer les publications sur les pages",
        "read_insights": "Lire les statistiques des pages (impressions, clics, portee)",
    }

    # Verifier les permissions
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{GRAPH_API_BASE}/me/permissions", params={"access_token": user_token})
        if resp.status_code == 200:
            perms = resp.json().get("data", [])
            granted = {p["permission"] for p in perms if p["status"] == "granted"}
            result["permissions"] = sorted(granted)

            for perm, description in required_permissions.items():
                if perm not in granted:
                    result["missing_permissions"].append({"permission": perm, "description": description})

            if result["missing_permissions"]:
                result["status"] = "missing_permissions"
                result["issues"].append(
                    "Des permissions Facebook sont manquantes. "
                    "Allez sur Meta Developer Portal > Votre App > Facebook Login for Business > "
                    "Configuration, ajoutez les permissions manquantes, puis reconnectez le compte."
                )
        else:
            result["status"] = "token_error"
            result["issues"].append(f"Impossible de verifier les permissions (HTTP {resp.status_code}). Le token est peut-etre expire.")
    except Exception as e:
        result["status"] = "error"
        result["issues"].append(f"Erreur lors de la verification: {str(e)}")

    # Verifier les pages accessibles
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{GRAPH_API_BASE}/me/accounts", params={
                "access_token": user_token, "fields": "id,name", "limit": 50})
        if resp.status_code == 200:
            pages = resp.json().get("data", [])
            result["pages"] = [{"id": p["id"], "name": p["name"]} for p in pages]

            # Comparer avec les pages en DB
            db_pages = (
                db.query(SocialAccount)
                .filter(SocialAccount.platform == "facebook", SocialAccount.account_type == "page", SocialAccount.is_active == True)
                .all()
            )
            accessible_ids = {p["id"] for p in pages}
            for db_page in db_pages:
                if db_page.account_id not in accessible_ids:
                    result["issues"].append(
                        f"La page '{db_page.account_name}' n'est plus accessible. "
                        "L'utilisateur connecte n'a peut-etre plus les droits admin/editeur sur cette page."
                    )
    except Exception:
        pass

    return result


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

    GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
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

            # 4g. INSIGHTS (impressions, clicks, reach) avec period=lifetime
            page_results["post_insights_impressions"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/insights",
                {"access_token": test_token,
                 "metric": "post_impressions,post_impressions_unique",
                 "period": "lifetime"},
            )
            page_results["post_insights_clicks"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/insights",
                {"access_token": test_token,
                 "metric": "post_clicks",
                 "period": "lifetime"},
            )
            page_results["post_insights_consumptions"] = safe_get(
                f"{GRAPH_API_BASE}/{post_id}/insights",
                {"access_token": test_token,
                 "metric": "post_consumptions",
                 "period": "lifetime"},
            )

            # 4h. Meme tests avec USER token (profil)
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
        if "read_insights" not in sample:
            recommendations.append(
                "CRITIQUE: Permission 'read_insights' manquante — necessaire pour les impressions, clics et portee. "
                "Reconnectez le compte Facebook pour obtenir cette permission."
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


@router.get("/debug/test-insights-metrics")
def debug_test_insights_metrics(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Teste tous les noms de metriques Insights possibles pour trouver
    lesquels sont valides sur la version actuelle de la Graph API.
    """
    import httpx

    GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

    # Trouver une page avec un post
    all_accounts = (
        db.query(SocialAccount)
        .filter(SocialAccount.platform == "facebook", SocialAccount.is_active == True)
        .all()
    )
    profile = next((a for a in all_accounts if a.account_type == "profile"), None)
    page_accounts = [a for a in all_accounts if a.account_type == "page"]

    if not profile:
        return {"error": "Aucun profil Facebook"}

    # Obtenir un token frais via /me/accounts
    fresh_pages = {}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{GRAPH_API_BASE}/me/accounts", params={
                "access_token": profile.access_token,
                "fields": "id,name,access_token",
                "limit": 50,
            })
        if resp.status_code == 200:
            for p in resp.json().get("data", []):
                fresh_pages[p["id"]] = p
    except Exception as e:
        return {"error": f"Impossible d'obtenir les pages: {e}"}

    # Trouver un post sur la premiere page disponible
    results = {"pages_found": len(fresh_pages), "tests": {}}

    for page_acc in page_accounts:
        pid = page_acc.account_id
        fresh = fresh_pages.get(pid)
        if not fresh:
            continue

        token = fresh["access_token"]

        # Trouver un post
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{GRAPH_API_BASE}/{pid}/feed", params={
                    "access_token": token, "fields": "id", "limit": 1,
                })
            if resp.status_code != 200:
                continue
            posts = resp.json().get("data", [])
            if not posts:
                continue
            post_id = posts[0]["id"]
        except Exception:
            continue

        results["page"] = fresh["name"]
        results["post_id"] = post_id

        # Tester chaque metrique individuellement
        ALL_METRICS = [
            "post_impressions",
            "post_impressions_unique",
            "post_impressions_organic",
            "post_impressions_organic_unique",
            "post_impressions_paid",
            "post_impressions_paid_unique",
            "post_impressions_fan",
            "post_impressions_fan_unique",
            "post_impressions_viral",
            "post_impressions_viral_unique",
            "post_clicks",
            "post_clicks_unique",
            "post_clicks_by_type",
            "post_clicks_by_type_unique",
            "post_consumptions",
            "post_consumptions_unique",
            "post_consumptions_by_type",
            "post_engaged_users",
            "post_engaged_fan",
            "post_negative_feedback",
            "post_negative_feedback_unique",
            "post_negative_feedback_by_type",
            "post_activity_by_action_type",
            "post_reactions_by_type_total",
            "post_video_views",
            "post_video_views_organic",
            "post_video_views_paid",
        ]

        with httpx.Client(timeout=10.0) as client:
            for metric in ALL_METRICS:
                try:
                    resp = client.get(f"{GRAPH_API_BASE}/{post_id}/insights", params={
                        "access_token": token,
                        "metric": metric,
                        "period": "lifetime",
                    })
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        if data:
                            vals = data[0].get("values", [])
                            value = vals[0].get("value", "?") if vals else "?"
                            results["tests"][metric] = {"status": "OK", "value": value}
                        else:
                            results["tests"][metric] = {"status": "OK_EMPTY", "value": None}
                    else:
                        err = resp.json().get("error", {}).get("message", resp.text[:100])
                        results["tests"][metric] = {"status": f"HTTP_{resp.status_code}", "error": err[:150]}
                except Exception as e:
                    results["tests"][metric] = {"status": "ERROR", "error": str(e)[:100]}

        # Aussi tester SANS le parametre metric (tous les metrics)
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{GRAPH_API_BASE}/{post_id}/insights", params={
                    "access_token": token,
                    "period": "lifetime",
                })
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                results["all_metrics_no_filter"] = {
                    "status": "OK",
                    "count": len(data),
                    "names": [d["name"] for d in data],
                }
            else:
                results["all_metrics_no_filter"] = {"status": f"HTTP_{resp.status_code}"}
        except Exception as e:
            results["all_metrics_no_filter"] = {"status": "ERROR", "error": str(e)[:100]}

        break  # On teste une seule page

    return results

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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action
from app.db.crud.crud_social import (
    # Comptes
    get_social_accounts,
    get_social_account_by_id,
    disconnect_social_account,
    check_account_token_status,
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
    Initier la connexion OAuth pour une plateforme.
    
    Retourne l'URL de redirection vers la page d'autorisation
    de la plateforme sociale.
    
    TODO: Implémenter le flux OAuth réel pour chaque plateforme.
    """
    # TODO: Implémenter l'OAuth réel (Facebook Graph API, Instagram Basic Display, etc.)
    # Pour l'instant, retourner un placeholder
    import secrets
    state = secrets.token_urlsafe(32)

    oauth_urls = {
        "facebook": f"https://www.facebook.com/v18.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT&state={state}&scope=pages_manage_posts,pages_read_engagement",
        "instagram": f"https://api.instagram.com/oauth/authorize?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT&state={state}&scope=user_profile,user_media",
        "linkedin": f"https://www.linkedin.com/oauth/v2/authorization?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT&state={state}&scope=w_member_social",
        "twitter": f"https://twitter.com/i/oauth2/authorize?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT&state={state}&scope=tweet.read%20tweet.write%20users.read",
    }

    redirect_url = oauth_urls.get(platform, f"https://oauth.example.com/{platform}?state={state}")

    log_action(db, current_user.id, "oauth_init", "social_accounts", 0)

    return OAuthRedirectResponse(redirect_url=redirect_url, state=state)


@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Déconnecter un compte social."""
    result = disconnect_social_account(db, account_id)
    log_action(db, current_user.id, "disconnect", "social_accounts", account_id)
    return {"success": result}


@router.get("/accounts/{account_id}/status", response_model=SocialAccountStatusResponse)
def account_status(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """Vérifier le statut du token OAuth d'un compte."""
    return check_account_token_status(db, account_id)


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
    # Enrichir avec le nom de l'auteur
    for post in posts:
        from app.models import User
        user = db.query(User).filter(User.id == post.created_by).first()
        post.created_by_name = f"{user.name} {user.family_name}" if user else None
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
    """Supprimer une publication (soft delete)."""
    result = delete_social_post(db, post_id)
    log_action(db, current_user.id, "delete", "social_posts", post_id)
    return {"success": result}


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
    """Supprimer un commentaire."""
    result = delete_social_comment(db, comment_id)
    log_action(db, current_user.id, "delete", "social_comments", comment_id)
    return {"success": result}


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

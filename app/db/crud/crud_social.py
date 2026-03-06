"""
Opérations CRUD pour le module Social.

Gère les accès base de données pour les comptes sociaux,
publications, commentaires, conversations et messages.
Inclut les fonctions de synchronisation avec Facebook Graph API.
"""

import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func, desc, and_
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable

from app.models.model_social import (
    SocialAccount, SocialPost, SocialPostResult,
    SocialComment, SocialConversation, SocialMessage,
    SocialPageInsight,
)
from app.schemas.schema_social import (
    SocialPostCreate, SocialPostUpdate,
)

logger = logging.getLogger("hapson-api")


def _get_sync_settings() -> dict:
    """Recuperer les limites configurables depuis le scheduler."""
    try:
        from app.services.social_scheduler import scheduler
        return scheduler.get_settings()
    except Exception:
        return {
            "sync_posts_limit": 100,
            "sync_insights_days": 93,
            "sync_comments_per_post": 100,
            "analytics_best_times_limit": 20,
            "analytics_top_hashtags_limit": 10,
        }


# ════════════════════════════════════════════════════════════════
# COMPTES SOCIAUX
# ════════════════════════════════════════════════════════════════

def get_social_accounts(db: Session) -> list[SocialAccount]:
    """Récupérer tous les comptes sociaux actifs (non supprimés)."""
    return (
        db.query(SocialAccount)
        .filter(SocialAccount.is_deleted == False)
        .order_by(SocialAccount.platform, SocialAccount.account_name)
        .all()
    )


def get_social_account_by_id(db: Session, account_id: int) -> SocialAccount:
    """Récupérer un compte social par ID."""
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.id == account_id, SocialAccount.is_deleted == False)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compte social #{account_id} introuvable"
        )
    return account


def disconnect_social_account(db: Session, account_id: int) -> dict:
    """
    Soft delete d'un compte social avec cascade sur toutes les données liées.

    Supprime (soft) : le compte, ses page-accounts enfants,
    les PostResults, Comments, Conversations et Messages associés.
    Retourne un résumé des suppressions effectuées.
    """
    account = get_social_account_by_id(db, account_id)
    now = datetime.now(timezone.utc)
    stats = {
        "accounts_deleted": 0,
        "posts_deleted": 0,
        "post_results_deleted": 0,
        "comments_deleted": 0,
        "conversations_deleted": 0,
        "messages_deleted": 0,
    }

    def _soft_delete_account_data(acc: SocialAccount):
        """Cascade soft-delete sur toutes les données d'un compte."""
        # 1. PostResults liés à ce compte
        results = db.query(SocialPostResult).filter(
            SocialPostResult.account_id == acc.id,
            SocialPostResult.is_deleted == False,
        ).all()
        for r in results:
            r.is_deleted = True
            r.deleted_at = now
            stats["post_results_deleted"] += 1

        # 2. Commentaires liés à ce compte
        comments = db.query(SocialComment).filter(
            SocialComment.account_id == acc.id,
            SocialComment.is_deleted == False,
        ).all()
        for c in comments:
            c.is_deleted = True
            c.deleted_at = now
            stats["comments_deleted"] += 1

        # 3. Conversations + leurs messages
        conversations = db.query(SocialConversation).filter(
            SocialConversation.account_id == acc.id,
            SocialConversation.is_deleted == False,
        ).all()
        for conv in conversations:
            msgs = db.query(SocialMessage).filter(
                SocialMessage.conversation_id == conv.id,
                SocialMessage.is_deleted == False,
            ).all()
            for m in msgs:
                m.is_deleted = True
                m.deleted_at = now
                stats["messages_deleted"] += 1
            conv.is_deleted = True
            conv.deleted_at = now
            stats["conversations_deleted"] += 1

        # 4. Marquer le compte lui-même
        acc.is_deleted = True
        acc.deleted_at = now
        acc.is_active = False
        stats["accounts_deleted"] += 1

    # Si c'est un profil, supprimer aussi les page-accounts enfants
    if account.account_type == "profile":
        child_pages = db.query(SocialAccount).filter(
            SocialAccount.connected_by == account.connected_by,
            SocialAccount.platform == account.platform,
            SocialAccount.account_type == "page",
            SocialAccount.is_deleted == False,
        ).all()
        for page_acc in child_pages:
            _soft_delete_account_data(page_acc)

    # Supprimer les données du compte principal
    _soft_delete_account_data(account)

    # 5. Soft-delete les SocialPost qui n'ont plus AUCUN result actif
    #    (posts devenus orphelins après suppression des results)
    db.flush()  # S'assurer que les results sont bien marqués
    orphan_posts = (
        db.query(SocialPost)
        .filter(
            SocialPost.is_deleted == False,
            ~SocialPost.id.in_(
                db.query(SocialPostResult.post_id)
                .filter(SocialPostResult.is_deleted == False)
                .distinct()
            )
        )
        .all()
    )
    for p in orphan_posts:
        p.is_deleted = True
        p.deleted_at = now
        stats["posts_deleted"] += 1

    db.commit()
    logger.info(f"[DELETE] Compte #{account_id} supprimé avec cascade: {stats}")
    return stats


def check_account_token_status(db: Session, account_id: int) -> dict:
    """Vérifier la validité du token OAuth d'un compte."""
    account = get_social_account_by_id(db, account_id)
    now = datetime.now(timezone.utc)
    valid = True
    if account.token_expires_at:
        valid = account.token_expires_at > now
    return {
        "valid": valid,
        "expires_at": account.token_expires_at,
    }


def upsert_social_account_from_oauth(
    db: Session,
    platform: str,
    platform_user_id: str,
    account_name: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expires_at: Optional[datetime],
    avatar_url: Optional[str],
    connected_by: int,
) -> SocialAccount:
    """
    Creer ou mettre a jour un SocialAccount depuis les donnees OAuth.

    Si un compte avec le meme platform + account_id + connected_by existe
    (non supprime), met a jour ses tokens. Sinon, cree un nouveau record.
    """
    try:
        existing = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.platform == platform,
                SocialAccount.account_id == platform_user_id,
                SocialAccount.connected_by == connected_by,
                SocialAccount.is_deleted == False,
            )
            .first()
        )

        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.token_expires_at = token_expires_at
            existing.account_name = account_name
            existing.avatar_url = avatar_url
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        new_account = SocialAccount(
            platform=platform,
            account_name=account_name,
            account_id=platform_user_id,
            account_type="profile",
            avatar_url=avatar_url,
            profile_picture=avatar_url,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            connected_by=connected_by,
            is_active=True,
            permissions=[],
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la sauvegarde du compte social: {str(e)}"
        )


# ════════════════════════════════════════════════════════════════
# PUBLICATIONS
# ════════════════════════════════════════════════════════════════

def get_social_posts(
    db: Session,
    status_filter: Optional[str] = None,
    platform: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
) -> list[SocialPost]:
    """
    Récupérer les posts avec filtres optionnels.

    Exclut automatiquement les posts qui n'ont aucun result actif
    (par ex. après déconnexion d'un compte).
    """
    query = (
        db.query(SocialPost)
        .options(joinedload(SocialPost.results))
        .filter(SocialPost.is_deleted == False)
    )

    if status_filter:
        query = query.filter(SocialPost.status == status_filter)
    if platform:
        query = query.filter(SocialPost.platforms.any(platform))
    if search:
        query = query.filter(SocialPost.content.ilike(f"%{search}%"))
    if date_from:
        query = query.filter(SocialPost.created_at >= date_from)
    if date_to:
        query = query.filter(SocialPost.created_at <= date_to)

    posts = query.order_by(desc(SocialPost.created_at)).all()

    # Filtrer côté Python : exclure les results soft-deleted
    # et les posts qui n'ont plus aucun result actif (sauf drafts/scheduled)
    for post in posts:
        post.results = [r for r in post.results if not r.is_deleted]

    return [
        p for p in posts
        if p.results or p.status in ("draft", "scheduled")
    ]


def get_social_post_by_id(db: Session, post_id: int) -> SocialPost:
    """Récupérer un post par ID avec ses résultats actifs."""
    post = (
        db.query(SocialPost)
        .options(joinedload(SocialPost.results))
        .filter(SocialPost.id == post_id, SocialPost.is_deleted == False)
        .first()
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication #{post_id} introuvable"
        )
    # Exclure les results soft-deleted
    post.results = [r for r in post.results if not r.is_deleted]
    return post


def create_social_post(db: Session, post_data: SocialPostCreate, user_id: int) -> SocialPost:
    """Créer un nouveau post."""
    new_post = SocialPost(
        content=post_data.content,
        media_urls=post_data.media_urls,
        link_url=post_data.link_url,
        hashtags=post_data.hashtags,
        platforms=post_data.platforms,
        target_accounts=post_data.target_accounts,
        status="scheduled" if post_data.scheduled_at else "draft",
        scheduled_at=post_data.scheduled_at,
        created_by=user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def update_social_post(db: Session, post_id: int, post_data: SocialPostUpdate) -> SocialPost:
    """Mettre à jour un post existant."""
    post = get_social_post_by_id(db, post_id)

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier un post déjà publié"
        )

    update_dict = post_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


def delete_social_post(db: Session, post_id: int) -> dict:
    """
    Soft delete d'un post avec cascade sur ses résultats.

    Supprime (soft) le post et tous les SocialPostResult associés.
    """
    post = get_social_post_by_id(db, post_id)
    now = datetime.now(timezone.utc)
    stats = {"post_results_deleted": 0}

    # Cascade : supprimer les PostResults
    results = db.query(SocialPostResult).filter(
        SocialPostResult.post_id == post.id,
        SocialPostResult.is_deleted == False,
    ).all()
    for r in results:
        r.is_deleted = True
        r.deleted_at = now
        stats["post_results_deleted"] += 1

    post.is_deleted = True
    post.deleted_at = now
    db.commit()
    return stats


def publish_social_post(db: Session, post_id: int) -> SocialPost:
    """
    Publier un post sur les plateformes cibles.

    Pour chaque compte cible sur Facebook :
    1. Recupere le page access token via /me/accounts
    2. Publie sur la page via Graph API
    3. Cree un SocialPostResult avec le platform_post_id

    Pour les plateformes non-Facebook, simule le succes (TODO).

    Utilise un UPDATE atomique pour eviter les doublons quand
    plusieurs workers Gunicorn traitent le meme post planifie.
    """
    from app.services.social_facebook import publish_to_page

    # Transition atomique : seul le premier worker a reussir cet UPDATE continue.
    # Les autres workers verront updated == 0 et abandonneront.
    updated = db.query(SocialPost).filter(
        SocialPost.id == post_id,
        SocialPost.is_deleted == False,
        SocialPost.status.in_(["draft", "scheduled"]),
    ).update({"status": "publishing"}, synchronize_session="fetch")
    db.commit()

    if updated == 0:
        # Verifier si le post existe et son statut actuel
        post = db.query(SocialPost).filter(
            SocialPost.id == post_id, SocialPost.is_deleted == False
        ).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publication #{post_id} introuvable"
            )
        if post.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce post est déjà publié"
            )
        # Status est "publishing" ou "error" — un autre worker l'a deja pris
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Publication déjà en cours par un autre processus"
        )

    post = get_social_post_by_id(db, post_id)
    has_error = False
    now = datetime.now(timezone.utc)

    # Recuperer les comptes cibles
    target_account_ids = post.target_accounts or []

    # Si aucun compte cible specifie, trouver tous les comptes pour les plateformes
    if not target_account_ids:
        accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.platform.in_(post.platforms),
                SocialAccount.is_active == True,
                SocialAccount.is_deleted == False,
            )
            .all()
        )
    else:
        accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.id.in_([int(a) for a in target_account_ids if a.isdigit()]),
                SocialAccount.is_active == True,
                SocialAccount.is_deleted == False,
            )
            .all()
        )

    for account in accounts:
        result = SocialPostResult(
            post_id=post.id,
            account_id=account.id,
            platform=account.platform,
            status="pending",
        )

        if account.platform == "facebook":
            try:
                # Utiliser directement le page access token stocké en BDD
                # (pas besoin de /me/accounts car le token est déjà un Page token)
                if not account.access_token:
                    result.status = "error"
                    result.error_message = "Aucun access token disponible pour ce compte"
                    has_error = True
                elif not account.account_id:
                    result.status = "error"
                    result.error_message = "Aucun Page ID disponible pour ce compte"
                    has_error = True
                else:
                    fb_result = publish_to_page(
                        page_access_token=account.access_token,
                        page_id=account.account_id,
                        message=post.content,
                        link=post.link_url,
                        media_urls=post.media_urls or [],
                    )
                    result.status = "published"
                    result.platform_post_id = fb_result["id"]
                    result.platform_post_url = fb_result["permalink_url"]
                    result.platform_url = fb_result["permalink_url"]
                    result.published_at = now
            except Exception as e:
                logger.error(f"Erreur publication Facebook: {e}")
                result.status = "error"
                result.error_message = str(e)[:500]
                has_error = True
        else:
            # TODO: Implementer pour Instagram, LinkedIn, Twitter
            result.status = "published"
            result.published_at = now

        db.add(result)

    post.status = "error" if has_error and not any(
        r.status == "published" for r in db.query(SocialPostResult).filter(
            SocialPostResult.post_id == post.id
        ).all()
    ) else "published"
    post.published_at = now
    db.commit()
    db.refresh(post)

    # Nettoyer les fichiers Firebase Storage temporaires apres publication reussie
    if post.status == "published" and post.media_urls:
        try:
            from app.services.firebase_cleanup import cleanup_firebase_urls
            cleaned = cleanup_firebase_urls(post.media_urls)
            logger.info(f"Firebase cleanup: {cleaned} fichier(s) supprime(s) pour post #{post.id}")
        except Exception as e:
            # Le cleanup est best-effort, ne pas bloquer la publication
            logger.warning(f"Firebase cleanup echoue pour post #{post.id}: {e}")

    return post


def schedule_social_post(db: Session, post_id: int, scheduled_at: datetime) -> SocialPost:
    """Planifier un post pour une date future."""
    post = get_social_post_by_id(db, post_id)

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce post est déjà publié"
        )

    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    if scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de planification doit être dans le futur"
        )

    post.scheduled_at = scheduled_at
    post.status = "scheduled"
    db.commit()
    db.refresh(post)
    return post


def get_due_scheduled_posts(db: Session) -> list[SocialPost]:
    """Recuperer les posts planifies dont la date de publication est passee."""
    now = datetime.now(timezone.utc)
    return (
        db.query(SocialPost)
        .filter(
            SocialPost.status == "scheduled",
            SocialPost.scheduled_at != None,
            SocialPost.scheduled_at <= now,
            SocialPost.is_deleted == False,
        )
        .order_by(SocialPost.scheduled_at)
        .all()
    )


# ════════════════════════════════════════════════════════════════
# COMMENTAIRES
# ════════════════════════════════════════════════════════════════

def get_social_comments(
    db: Session,
    post_id: Optional[int] = None,
    platform: Optional[str] = None,
    is_read: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SocialComment], int]:
    """Récupérer les commentaires avec filtres et pagination."""
    query = (
        db.query(SocialComment)
        .filter(SocialComment.is_deleted == False, SocialComment.parent_comment_id == None)
    )

    if post_id:
        query = query.filter(SocialComment.post_id == post_id)
    if platform:
        query = query.filter(SocialComment.platform == platform)
    if is_read is not None:
        query = query.filter(SocialComment.is_read == is_read)
    if date_from:
        query = query.filter(SocialComment.created_at >= date_from)
    if date_to:
        query = query.filter(SocialComment.created_at <= date_to)

    total = query.count()
    comments = query.order_by(desc(SocialComment.created_at)).offset(offset).limit(limit).all()
    return comments, total


def get_comment_by_id(db: Session, comment_id: int) -> SocialComment:
    """Récupérer un commentaire par ID."""
    comment = (
        db.query(SocialComment)
        .filter(SocialComment.id == comment_id, SocialComment.is_deleted == False)
        .first()
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commentaire #{comment_id} introuvable"
        )
    return comment


def mark_comment_read(db: Session, comment_id: int) -> bool:
    """Marquer un commentaire comme lu."""
    comment = get_comment_by_id(db, comment_id)
    comment.is_read = True
    db.commit()
    return True


def hide_comment(db: Session, comment_id: int) -> bool:
    """Masquer un commentaire."""
    comment = get_comment_by_id(db, comment_id)
    comment.is_hidden = True
    db.commit()
    return True


def delete_social_comment(db: Session, comment_id: int) -> dict:
    """
    Soft delete d'un commentaire avec cascade sur ses réponses.

    Supprime (soft) le commentaire et toutes ses réponses (replies).
    """
    comment = get_comment_by_id(db, comment_id)
    now = datetime.now(timezone.utc)
    stats = {"replies_deleted": 0}

    # Cascade : supprimer les réponses récursivement
    def _soft_delete_replies(parent_id: int):
        replies = db.query(SocialComment).filter(
            SocialComment.parent_comment_id == parent_id,
            SocialComment.is_deleted == False,
        ).all()
        for reply in replies:
            _soft_delete_replies(reply.id)
            reply.is_deleted = True
            reply.deleted_at = now
            stats["replies_deleted"] += 1

    _soft_delete_replies(comment.id)
    comment.is_deleted = True
    comment.deleted_at = now
    db.commit()
    return stats


# ════════════════════════════════════════════════════════════════
# CONVERSATIONS / MESSAGES
# ════════════════════════════════════════════════════════════════

def get_conversations(db: Session, platform: Optional[str] = None) -> list[SocialConversation]:
    """Récupérer les conversations avec dernier message."""
    query = (
        db.query(SocialConversation)
        .options(joinedload(SocialConversation.messages))
        .filter(SocialConversation.is_deleted == False)
    )

    if platform:
        query = query.filter(SocialConversation.platform == platform)

    return query.order_by(desc(SocialConversation.last_message_at)).all()


def get_conversation_by_id(db: Session, conversation_id: int) -> SocialConversation:
    """Récupérer une conversation par ID avec ses messages."""
    conversation = (
        db.query(SocialConversation)
        .options(joinedload(SocialConversation.messages))
        .filter(SocialConversation.id == conversation_id, SocialConversation.is_deleted == False)
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation #{conversation_id} introuvable"
        )
    return conversation


# ════════════════════════════════════════════════════════════════
# STATISTIQUES
# ════════════════════════════════════════════════════════════════

def get_analytics_overview(db: Session, period: str = "30d", account_id: Optional[int] = None) -> dict:
    """Calculer les statistiques d'ensemble pour la période donnée.
    Si account_id est fourni, filtre les stats pour ce compte uniquement.
    """
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)

    # Filtre de base pour les posts liés au compte (via SocialPostResult)
    if account_id:
        post_ids_for_account = db.query(SocialPostResult.post_id).filter(
            SocialPostResult.account_id == account_id
        ).distinct().subquery()

    # Posts stats
    post_base = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    )
    if account_id:
        post_base = post_base.filter(SocialPost.id.in_(post_ids_for_account))
    total_posts = post_base.scalar() or 0

    pub_base = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "published", SocialPost.created_at >= cutoff
    )
    if account_id:
        pub_base = pub_base.filter(SocialPost.id.in_(post_ids_for_account))
    total_published = pub_base.scalar() or 0

    sched_base = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "scheduled"
    )
    if account_id:
        sched_base = sched_base.filter(SocialPost.id.in_(post_ids_for_account))
    total_scheduled = sched_base.scalar() or 0

    draft_base = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "draft"
    )
    if account_id:
        draft_base = draft_base.filter(SocialPost.id.in_(post_ids_for_account))
    total_drafts = draft_base.scalar() or 0

    # Engagement metrics (from results)
    metrics_q = db.query(
        func.coalesce(func.sum(SocialPostResult.impressions), 0),
        func.coalesce(func.sum(SocialPostResult.clicks), 0),
        func.coalesce(func.sum(SocialPostResult.likes), 0),
        func.coalesce(func.sum(SocialPostResult.shares), 0),
        func.coalesce(func.sum(SocialPostResult.comments), 0),
    ).join(SocialPost, SocialPostResult.post_id == SocialPost.id).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    )
    if account_id:
        metrics_q = metrics_q.filter(SocialPostResult.account_id == account_id)
    metrics = metrics_q.first()

    impressions = metrics[0] if metrics else 0
    clicks = metrics[1] if metrics else 0
    likes = metrics[2] if metrics else 0
    shares = metrics[3] if metrics else 0
    comments_count = metrics[4] if metrics else 0
    total_engagements = clicks + likes + shares + comments_count

    # Previous period engagement metrics (for trend calculation)
    prev_metrics_q = db.query(
        func.coalesce(func.sum(SocialPostResult.impressions), 0),
        func.coalesce(func.sum(SocialPostResult.clicks), 0),
        func.coalesce(func.sum(SocialPostResult.likes), 0),
        func.coalesce(func.sum(SocialPostResult.shares), 0),
        func.coalesce(func.sum(SocialPostResult.comments), 0),
    ).join(SocialPost, SocialPostResult.post_id == SocialPost.id).filter(
        SocialPost.is_deleted == False,
        SocialPost.created_at >= prev_cutoff,
        SocialPost.created_at < cutoff,
    )
    if account_id:
        prev_metrics_q = prev_metrics_q.filter(SocialPostResult.account_id == account_id)
    prev_metrics = prev_metrics_q.first()

    prev_impressions = prev_metrics[0] if prev_metrics else 0
    prev_clicks = prev_metrics[1] if prev_metrics else 0
    prev_likes = prev_metrics[2] if prev_metrics else 0
    prev_shares = prev_metrics[3] if prev_metrics else 0
    prev_comments = prev_metrics[4] if prev_metrics else 0
    prev_engagements = prev_clicks + prev_likes + prev_shares + prev_comments

    def _pct_change(current: float, previous: float) -> float:
        """Calcul du pourcentage de variation entre deux periodes."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    # Followers
    followers_q = db.query(func.coalesce(func.sum(SocialAccount.followers_count), 0)).filter(
        SocialAccount.is_deleted == False, SocialAccount.is_active == True
    )
    if account_id:
        followers_q = followers_q.filter(SocialAccount.id == account_id)
    followers_total = followers_q.scalar() or 0

    # Avg engagement rate
    avg_engagement = 0.0
    if impressions > 0:
        avg_engagement = round((total_engagements / impressions) * 100, 2)

    prev_engagement_rate = 0.0
    if prev_impressions > 0:
        prev_engagement_rate = round((prev_engagements / prev_impressions) * 100, 2)

    # Top hashtags
    hashtags_q = db.query(SocialPost.hashtags).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    )
    if account_id:
        hashtags_q = hashtags_q.filter(SocialPost.id.in_(post_ids_for_account))
    all_hashtags = hashtags_q.all()
    hashtag_count: dict[str, int] = {}
    for (tags,) in all_hashtags:
        if tags:
            for tag in tags:
                hashtag_count[tag] = hashtag_count.get(tag, 0) + 1
    _settings = _get_sync_settings()
    top_hashtags = sorted(hashtag_count, key=hashtag_count.get, reverse=True)[:_settings.get("analytics_top_hashtags_limit", 10)]

    # Top platforms
    platforms_q = db.query(SocialPost.platforms).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    )
    if account_id:
        platforms_q = platforms_q.filter(SocialPost.id.in_(post_ids_for_account))
    all_platforms = platforms_q.all()
    platform_count: dict[str, int] = {}
    for (plats,) in all_platforms:
        if plats:
            for p in plats:
                platform_count[p] = platform_count.get(p, 0) + 1
    top_platforms = sorted(platform_count, key=platform_count.get, reverse=True)

    # Followers growth depuis SocialPageInsight
    followers_growth = 0
    try:
        insights_q = db.query(
            func.coalesce(func.sum(SocialPageInsight.page_daily_follows), 0),
            func.coalesce(func.sum(SocialPageInsight.page_daily_unfollows), 0),
        ).filter(
            SocialPageInsight.date >= cutoff.date(),
        )
        if account_id:
            insights_q = insights_q.filter(SocialPageInsight.account_id == account_id)
        growth_data = insights_q.first()
        if growth_data:
            followers_growth = (growth_data[0] or 0) - (growth_data[1] or 0)
    except Exception:
        pass  # Table peut ne pas encore exister

    return {
        "total_posts": total_posts,
        "total_published": total_published,
        "total_scheduled": total_scheduled,
        "total_drafts": total_drafts,
        "total_impressions": impressions,
        "total_clicks": clicks,
        "total_likes": likes,
        "total_shares": shares,
        "total_comments": comments_count,
        "total_reach": impressions,  # Simplification : reach ≈ impressions
        "avg_engagement_rate": avg_engagement,
        "followers_total": followers_total,
        "followers_growth": followers_growth,
        "impressions_change": _pct_change(impressions, prev_impressions),
        "engagements_change": _pct_change(total_engagements, prev_engagements),
        "reach_change": _pct_change(impressions, prev_impressions),
        "engagement_rate_change": _pct_change(avg_engagement, prev_engagement_rate),
        "total_engagements": total_engagements,
        "top_hashtags": top_hashtags,
        "top_platforms": top_platforms,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
    }


def get_platform_stats(db: Session, period: str = "30d", account_id: Optional[int] = None) -> list[dict]:
    """Statistiques ventilées par plateforme.
    Si account_id est fourni, filtre les stats pour ce compte uniquement.
    """
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_q = (
        db.query(
            SocialPostResult.platform,
            func.count(SocialPostResult.id).label("posts_count"),
            func.coalesce(func.sum(SocialPostResult.impressions), 0).label("impressions"),
            func.coalesce(func.sum(SocialPostResult.clicks), 0).label("clicks"),
            func.coalesce(func.sum(SocialPostResult.likes), 0).label("likes"),
            func.coalesce(func.sum(SocialPostResult.shares), 0).label("shares"),
            func.coalesce(func.sum(SocialPostResult.comments), 0).label("comments"),
        )
        .join(SocialPost, SocialPostResult.post_id == SocialPost.id)
        .filter(SocialPost.is_deleted == False, SocialPost.created_at >= cutoff)
    )
    if account_id:
        base_q = base_q.filter(SocialPostResult.account_id == account_id)
    results = base_q.group_by(SocialPostResult.platform).all()

    stats = []
    for r in results:
        engagements = r.clicks + r.likes + r.shares + r.comments
        engagement_rate = round((engagements / r.impressions) * 100, 2) if r.impressions > 0 else 0.0

        # Followers pour cette plateforme
        followers_q = db.query(func.coalesce(func.sum(SocialAccount.followers_count), 0)).filter(
            SocialAccount.platform == r.platform,
            SocialAccount.is_deleted == False,
            SocialAccount.is_active == True,
        )
        if account_id:
            followers_q = followers_q.filter(SocialAccount.id == account_id)
        followers = followers_q.scalar() or 0

        stats.append({
            "platform": r.platform,
            "posts_count": r.posts_count,
            "impressions": r.impressions,
            "engagements": engagements,
            "clicks": r.clicks,
            "likes": r.likes,
            "shares": r.shares,
            "comments": r.comments,
            "engagement_rate": engagement_rate,
            "followers": followers,
            "followers_growth": 0,
        })

    return stats


def get_best_times(db: Session, account_id: Optional[int] = None) -> list[dict]:
    """Calculer les meilleurs horaires de publication basés sur l'engagement."""
    # Requête sur les posts publiés avec leurs résultats
    base_q = (
        db.query(
            SocialPostResult.platform,
            func.extract("dow", SocialPost.published_at).label("dow"),
            func.extract("hour", SocialPost.published_at).label("hour"),
            func.avg(SocialPostResult.engagement_rate).label("avg_eng"),
            func.count(SocialPostResult.id).label("count"),
        )
        .join(SocialPost, SocialPostResult.post_id == SocialPost.id)
        .filter(
            SocialPost.is_deleted == False,
            SocialPost.published_at != None,
        )
    )
    if account_id:
        base_q = base_q.filter(SocialPostResult.account_id == account_id)
    results = (
        base_q
        .group_by(SocialPostResult.platform, "dow", "hour")
        .order_by(desc("avg_eng"))
        .limit(_get_sync_settings().get("analytics_best_times_limit", 20))
        .all()
    )

    day_names = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
    slots = []
    for r in results:
        dow = int(r.dow) if r.dow is not None else 0
        avg_eng = float(r.avg_eng) if r.avg_eng else 0.0
        score = "high" if avg_eng >= 5 else "medium" if avg_eng >= 2 else "low"
        slots.append({
            "platform": r.platform,
            "day_of_week": dow,
            "day_name": day_names[dow] if dow < len(day_names) else "Inconnu",
            "hour": int(r.hour) if r.hour is not None else 0,
            "avg_engagement": avg_eng,
            "engagement_score": avg_eng,
            "posts_count": r.count,
            "score": score,
        })

    return slots


def get_engagement_time_series(db: Session, period: str = "30d", account_id: Optional[int] = None) -> list[dict]:
    """Série temporelle de l'engagement par jour."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_q = (
        db.query(
            func.date(SocialPost.published_at).label("date"),
            func.coalesce(func.sum(SocialPostResult.impressions), 0).label("impressions"),
            func.coalesce(func.sum(SocialPostResult.clicks), 0).label("clicks"),
            func.coalesce(func.sum(SocialPostResult.likes), 0).label("likes"),
            func.coalesce(func.sum(SocialPostResult.shares), 0).label("shares"),
            func.coalesce(func.sum(SocialPostResult.comments), 0).label("comments"),
        )
        .join(SocialPost, SocialPostResult.post_id == SocialPost.id)
        .filter(
            SocialPost.is_deleted == False,
            SocialPost.published_at != None,
            SocialPost.published_at >= cutoff,
        )
    )
    if account_id:
        base_q = base_q.filter(SocialPostResult.account_id == account_id)
    results = (
        base_q
        .group_by(func.date(SocialPost.published_at))
        .order_by("date")
        .all()
    )

    series = []
    for r in results:
        total = r.clicks + r.likes + r.shares + r.comments
        eng_rate = round((total / r.impressions) * 100, 2) if r.impressions > 0 else 0.0
        series.append({
            "date": str(r.date),
            "impressions": r.impressions,
            "clicks": r.clicks,
            "likes": r.likes,
            "shares": r.shares,
            "comments": r.comments,
            "engagement_rate": eng_rate,
        })

    return series


# ════════════════════════════════════════════════════════════════
# SYNCHRONISATION FACEBOOK
# ════════════════════════════════════════════════════════════════

def _ensure_page_account(
    db: Session,
    page: dict,
    connected_by: int,
) -> SocialAccount:
    """
    S'assurer qu'un SocialAccount existe pour une page Facebook.
    Deduplication par (platform='facebook', account_id=page_id, connected_by).

    Returns:
        Le SocialAccount de la page (cree ou mis a jour)
    """
    page_id = page["id"]
    page_name = page.get("name", "Page Facebook")
    page_token = page.get("access_token", "")
    picture_url = page.get("picture_url")
    followers = page.get("followers_count", 0)

    existing = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.platform == "facebook",
            SocialAccount.account_id == page_id,
            SocialAccount.connected_by == connected_by,
            SocialAccount.is_deleted == False,
        )
        .first()
    )

    if existing:
        # Mettre a jour le token et les infos
        existing.access_token = page_token
        existing.account_name = page_name
        existing.account_type = "page"
        existing.is_active = True
        if picture_url:
            existing.avatar_url = picture_url
            existing.profile_picture = picture_url
        if followers:
            existing.followers_count = followers
        existing.profile_url = f"https://www.facebook.com/{page_id}"
        return existing

    # Creer un nouveau SocialAccount pour cette page
    new_account = SocialAccount(
        platform="facebook",
        account_name=page_name,
        account_id=page_id,
        account_type="page",
        avatar_url=picture_url,
        profile_picture=picture_url,
        profile_url=f"https://www.facebook.com/{page_id}",
        followers_count=followers,
        access_token=page_token,
        connected_by=connected_by,
        is_active=True,
        permissions=[],
    )
    db.add(new_account)
    db.flush()  # Pour obtenir l'ID
    logger.info(f"[SYNC] Nouveau SocialAccount cree pour la page '{page_name}' (FB ID: {page_id})")
    print(f"[SYNC] Nouveau SocialAccount #{new_account.id} pour page '{page_name}'", flush=True)
    return new_account


def _sync_page_posts(
    db: Session,
    page_account: SocialAccount,
    page_token: str,
    page_id: str,
    limit: int = 100,
    on_progress: Optional[Callable] = None,
) -> dict:
    """
    Synchroniser les posts et commentaires d'une seule page Facebook.

    Ne remplace JAMAIS une valeur non-nulle par 0 si l'API ne fournit
    pas de donnees fiables (evite d'ecraser des metriques deja collectees).

    Returns:
        dict avec {posts_synced, posts_new, comments_synced, comments_new}
    """
    from app.services.social_facebook import (
        get_page_posts,
        get_post_comments,
        get_post_reactions_count,
        get_post_insights,
        parse_facebook_datetime,
    )

    stats = {"posts_synced": 0, "posts_new": 0, "comments_synced": 0, "comments_new": 0}
    _cfg = _get_sync_settings()
    comments_limit = min(_cfg.get("sync_comments_per_post", 100), 100)

    fb_posts = get_page_posts(page_token, page_id, limit=limit)
    total_posts = len(fb_posts)
    print(f"[SYNC] Page '{page_account.account_name}' ({page_id}): {total_posts} post(s)", flush=True)

    for idx, fb_post in enumerate(fb_posts):
        platform_post_id = fb_post["platform_post_id"]
        if not platform_post_id:
            continue

        # Verifier si ce post existe deja (via SocialPostResult.platform_post_id)
        existing_result = (
            db.query(SocialPostResult)
            .filter(
                SocialPostResult.platform_post_id == platform_post_id,
                SocialPostResult.account_id == page_account.id,
            )
            .first()
        )

        if existing_result:
            # Mettre a jour les metriques du post existant
            # Strategie : ne JAMAIS remplacer une valeur > 0 par 0
            # (evite d'ecraser des donnees valides quand les permissions manquent)

            new_likes = 0
            new_comments = 0
            api_success = False

            # Priorite 1 : likes/comments du feed (inline summary)
            feed_likes = fb_post.get("likes_count", 0)
            feed_comments = fb_post.get("comments_count", 0)

            if feed_likes > 0 or feed_comments > 0:
                new_likes = feed_likes
                new_comments = feed_comments
                api_success = True
            else:
                # Priorite 2 : appel separe get_post_reactions_count
                try:
                    reactions = get_post_reactions_count(page_token, platform_post_id)
                    r_likes = reactions.get("likes", 0)
                    r_comments = reactions.get("comments", 0)
                    if r_likes > 0 or r_comments > 0:
                        new_likes = r_likes
                        new_comments = r_comments
                        api_success = True
                except Exception as e:
                    logger.warning(f"Erreur metriques post {platform_post_id}: {e}")
                    print(f"[SYNC] Erreur metriques {platform_post_id}: {e}", flush=True)

            # Appliquer : ne remplace que si on a de meilleures donnees
            if api_success:
                existing_result.likes = new_likes
                existing_result.comments = new_comments
            # sinon on garde les valeurs precedentes

            # Shares : toujours mis a jour (vient du feed basique, fiable)
            new_shares = fb_post.get("shares_count", 0)
            if new_shares > 0 or existing_result.shares == 0:
                existing_result.shares = new_shares

            # Impressions/clicks : récupérer via Insights API
            insights = get_post_insights(page_token, platform_post_id)
            new_impressions = insights.get("impressions", 0)
            new_clicks = insights.get("clicks", 0)
            if new_impressions > 0:
                existing_result.impressions = new_impressions
            if new_clicks > 0:
                existing_result.clicks = new_clicks

            total_eng = existing_result.likes + existing_result.comments + existing_result.shares + existing_result.clicks
            if existing_result.impressions > 0:
                existing_result.engagement_rate = round((total_eng / existing_result.impressions) * 100, 2)

            post_obj = (
                db.query(SocialPost)
                .filter(SocialPost.id == existing_result.post_id)
                .first()
            )
            stats["posts_synced"] += 1
        else:
            # Creer un nouveau SocialPost + SocialPostResult
            published_at = parse_facebook_datetime(fb_post.get("created_time", ""))

            post_obj = SocialPost(
                content=fb_post.get("message", "") or "(Pas de texte)",
                media_urls=fb_post.get("media_urls", []),
                link_url=fb_post.get("permalink_url"),
                hashtags=[],
                platforms=["facebook"],
                target_accounts=[str(page_account.id)],
                status="published",
                published_at=published_at,
                created_at=published_at,
                created_by=page_account.connected_by,
            )
            db.add(post_obj)
            db.flush()

            # Utiliser les likes/comments du feed en priorite
            feed_likes = fb_post.get("likes_count", 0)
            feed_comments = fb_post.get("comments_count", 0)

            if feed_likes > 0 or feed_comments > 0:
                likes_count = feed_likes
                comments_count = feed_comments
            else:
                try:
                    reactions = get_post_reactions_count(page_token, platform_post_id)
                    likes_count = reactions.get("likes", 0)
                    comments_count = reactions.get("comments", 0)
                except Exception as e:
                    logger.warning(f"Erreur reactions nouveau post {platform_post_id}: {e}")
                    likes_count = 0
                    comments_count = 0

            # Récupérer les insights (impressions, clics) via Insights API
            new_insights = get_post_insights(page_token, platform_post_id)

            result_obj = SocialPostResult(
                post_id=post_obj.id,
                account_id=page_account.id,
                platform="facebook",
                status="published",
                platform_post_id=platform_post_id,
                platform_post_url=fb_post.get("permalink_url", ""),
                platform_url=fb_post.get("permalink_url", ""),
                published_at=published_at,
                impressions=new_insights.get("impressions", 0),
                clicks=new_insights.get("clicks", 0),
                likes=likes_count,
                shares=fb_post.get("shares_count", 0),
                comments=comments_count,
            )
            total_eng = result_obj.likes + result_obj.comments + result_obj.shares + result_obj.clicks
            if result_obj.impressions > 0:
                result_obj.engagement_rate = round((total_eng / result_obj.impressions) * 100, 2)

            db.add(result_obj)
            stats["posts_new"] += 1
            stats["posts_synced"] += 1

        # Synchroniser les commentaires de ce post
        # Utilise les commentaires inline du feed si disponibles (evite le N+1)
        if post_obj:
            try:
                inline_comments = fb_post.get("inline_comments", [])
                if inline_comments:
                    # Commentaires deja inclus dans la reponse du feed (0 appel API)
                    fb_comments = inline_comments
                    print(f"[SYNC] Post {platform_post_id}: {len(fb_comments)} commentaire(s) inline", flush=True)
                else:
                    # Fallback : appel API individuel (champs basiques sans inline)
                    fb_comments = get_post_comments(page_token, platform_post_id, limit=comments_limit)
                    print(f"[SYNC] Post {platform_post_id}: {len(fb_comments)} commentaire(s) via API", flush=True)

                for fb_comment in fb_comments:
                    comment_stats = _sync_single_comment(
                        db, fb_comment, post_obj, page_account, parent_comment_id=None
                    )
                    stats["comments_synced"] += comment_stats["synced"]
                    stats["comments_new"] += comment_stats["new"]

                    for reply in fb_comment.get("replies", []):
                        parent_db = (
                            db.query(SocialComment)
                            .filter(SocialComment.platform_comment_id == fb_comment["platform_comment_id"])
                            .first()
                        )
                        if parent_db:
                            reply_stats = _sync_single_comment(
                                db, reply, post_obj, page_account, parent_comment_id=parent_db.id
                            )
                            stats["comments_synced"] += reply_stats["synced"]
                            stats["comments_new"] += reply_stats["new"]
            except Exception as e:
                logger.warning(f"Erreur sync commentaires pour {platform_post_id}: {e}")
                print(f"[SYNC] ERREUR commentaires {platform_post_id}: {type(e).__name__}: {e}", flush=True)

        # Reporter la progression
        if on_progress and total_posts > 0:
            pct = int(((idx + 1) / total_posts) * 100)
            on_progress(f"{idx + 1}/{total_posts} posts", pct)

    return stats


def _sync_page_insights(
    db: Session,
    page_account: SocialAccount,
    page_token: str,
    page_id: str,
) -> dict:
    """
    Synchroniser les insights page-level quotidiens pour une page Facebook.

    Recupere les 93 derniers jours de metriques via /{page_id}/insights
    et fait un upsert par (account_id, date).

    Returns:
        dict avec {days_synced, days_new}
    """
    from app.services.social_facebook import get_page_level_insights

    stats = {"days_synced": 0, "days_new": 0}

    # Recuperer les N derniers jours (max 93 autorise par Facebook pour period=day)
    _cfg = _get_sync_settings()
    insights_days = min(_cfg.get("sync_insights_days", 93), 93)
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=insights_days)).strftime("%Y-%m-%d")
    until = now.strftime("%Y-%m-%d")

    try:
        days_data = get_page_level_insights(page_token, page_id, since, until)
    except Exception as e:
        logger.warning(f"[SYNC] Erreur page insights {page_id}: {e}")
        print(f"[SYNC] Erreur page insights {page_id}: {e}", flush=True)
        return stats

    if not days_data:
        return stats

    # Pre-fetch existing dates pour tracker nouveaux vs mis a jour
    existing_dates = set(
        row[0] for row in db.query(SocialPageInsight.date).filter(
            SocialPageInsight.account_id == page_account.id,
        ).all()
    )

    latest_follows = 0

    # Colonnes de metriques a upsert
    metric_columns = [
        "page_impressions_unique", "page_posts_impressions",
        "page_posts_impressions_unique", "page_posts_impressions_organic",
        "page_posts_impressions_paid", "page_post_engagements",
        "page_views_total", "page_follows", "page_daily_follows",
        "page_daily_unfollows", "reactions_like", "reactions_love",
        "reactions_wow", "reactions_haha", "reactions_sorry",
        "reactions_anger", "page_video_views", "page_video_view_time",
    ]

    for day in days_data:
        day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()

        values = {
            "account_id": page_account.id,
            "date": day_date,
        }
        for col in metric_columns:
            values[col] = day.get(col, 0)

        # Upsert atomique : INSERT ... ON CONFLICT DO UPDATE
        stmt = pg_insert(SocialPageInsight).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_page_insight_account_date",
            set_={col: stmt.excluded[col] for col in metric_columns},
        )
        db.execute(stmt)

        stats["days_synced"] += 1
        if day_date not in existing_dates:
            stats["days_new"] += 1

        # Garder le dernier page_follows pour mettre a jour le compte
        follows = day.get("page_follows", 0)
        if follows > 0:
            latest_follows = follows

    # Mettre a jour followers_count du SocialAccount avec le dernier page_follows
    if latest_follows > 0:
        page_account.followers_count = latest_follows

    db.flush()
    print(
        f"[SYNC] Page insights '{page_account.account_name}': "
        f"{stats['days_synced']} jours ({stats['days_new']} nouveaux)",
        flush=True,
    )
    return stats


def sync_facebook_account(db: Session, account_id: int, force: bool = False, on_progress: Optional[Callable] = None) -> dict:
    """
    Synchroniser les posts et commentaires Facebook pour un compte.

    Architecture multi-pages :
    - Utilise le user access token pour appeler /me/accounts
    - Pour CHAQUE page trouvee, cree/met a jour un SocialAccount dedie
    - Synchronise les posts de chaque page independamment
    - Deduplication par (platform, page_id, connected_by) → pas de doublons

    Args:
        force: Si True, synchronise davantage de posts (100 au lieu de 50)
               pour rattraper les metriques manquantes.

    Returns:
        dict avec les compteurs globaux
    """
    from app.services.social_facebook import get_facebook_pages

    account = get_social_account_by_id(db, account_id)

    if account.platform != "facebook":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La synchronisation n'est supportee que pour Facebook"
        )

    if not account.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'acces manquant. Reconnectez le compte."
        )

    stats = {
        "posts_synced": 0,
        "posts_new": 0,
        "comments_synced": 0,
        "comments_new": 0,
        "pages_synced": 0,
        "insights_days_synced": 0,
        "insights_days_new": 0,
    }

    print(f"[SYNC] Compte #{account_id}: debut sync, type={account.account_type}, id={account.account_id}, force={force}", flush=True)

    # Recuperer les pages Facebook (utilise le user token)
    pages = get_facebook_pages(account.access_token)
    if not pages:
        print(f"[SYNC] Aucune page trouvee pour le compte #{account_id}", flush=True)
        return stats

    print(f"[SYNC] {len(pages)} page(s) trouvee(s): {[p['name'] for p in pages]}", flush=True)

    # Si ce compte est de type 'page', ne syncer que cette page specifique
    # Si c'est un profil, syncer TOUTES les pages
    if account.account_type == "page":
        # Compte page : syncer uniquement cette page
        target = None
        for p in pages:
            if p["id"] == account.account_id:
                target = p
                break
        if target:
            pages_to_sync = [target]
        else:
            # Page non trouvee dans /me/accounts, elle n'est peut-etre plus geree
            logger.warning(f"[SYNC] Page {account.account_id} non trouvee dans /me/accounts")
            pages_to_sync = []
    else:
        # Compte profil : syncer TOUTES les pages
        pages_to_sync = pages

    for page_idx, page in enumerate(pages_to_sync):
        page_id = page["id"]
        page_token = page.get("access_token", "")
        if not page_token:
            logger.warning(f"[SYNC] Pas de token pour la page {page['name']} ({page_id})")
            continue

        # Reporter progression par page
        if on_progress:
            on_progress(f"Page {page_idx + 1}/{len(pages_to_sync)}: {page['name']}", int((page_idx / max(len(pages_to_sync), 1)) * 100))

        # Creer ou mettre a jour le SocialAccount pour cette page
        page_account = _ensure_page_account(db, page, account.connected_by)

        # Syncer les posts de cette page
        _cfg = _get_sync_settings()
        sync_limit = min(_cfg.get("sync_posts_limit", 100), 100)  # plafond API FB = 100

        def _page_progress(msg: str, pct: int):
            if on_progress:
                base = int((page_idx / max(len(pages_to_sync), 1)) * 100)
                page_share = int(100 / max(len(pages_to_sync), 1))
                on_progress(f"{page['name']}: {msg}", base + int(pct * page_share / 100))

        try:
            page_stats = _sync_page_posts(db, page_account, page_token, page_id, limit=sync_limit, on_progress=_page_progress)
            stats["posts_synced"] += page_stats["posts_synced"]
            stats["posts_new"] += page_stats["posts_new"]
            stats["comments_synced"] += page_stats["comments_synced"]
            stats["comments_new"] += page_stats["comments_new"]
            stats["pages_synced"] += 1

            # Syncer les insights page-level (impressions, followers, reactions, video)
            try:
                insight_stats = _sync_page_insights(db, page_account, page_token, page_id)
                stats["insights_days_synced"] += insight_stats["days_synced"]
                stats["insights_days_new"] += insight_stats["days_new"]
            except Exception as e:
                logger.warning(f"[SYNC] Erreur insights page '{page['name']}': {e}")
                print(f"[SYNC] ERREUR insights '{page['name']}': {e}", flush=True)

        except Exception as e:
            logger.error(f"[SYNC] Erreur sync page '{page['name']}' ({page_id}): {e}")
            print(f"[SYNC] ERREUR page '{page['name']}': {e}", flush=True)

    db.commit()

    print(
        f"[SYNC] Terminee: {stats['pages_synced']} pages, "
        f"{stats['posts_synced']} posts ({stats['posts_new']} nouveaux), "
        f"{stats['comments_synced']} commentaires ({stats['comments_new']} nouveaux), "
        f"{stats['insights_days_synced']} jours insights ({stats['insights_days_new']} nouveaux)",
        flush=True,
    )
    logger.info(f"[SYNC] Compte #{account_id} terminee: {stats}")
    return stats


def _sync_single_comment(
    db: Session,
    fb_comment: dict,
    post_obj: SocialPost,
    account: SocialAccount,
    parent_comment_id: Optional[int] = None,
) -> dict:
    """
    Synchroniser un seul commentaire Facebook vers la BDD.

    Returns:
        {"synced": 1, "new": 0 ou 1}
    """
    from app.services.social_facebook import parse_facebook_datetime

    platform_comment_id = fb_comment.get("platform_comment_id", "")
    if not platform_comment_id:
        return {"synced": 0, "new": 0}

    existing = (
        db.query(SocialComment)
        .filter(SocialComment.platform_comment_id == platform_comment_id)
        .first()
    )

    if existing:
        # Mettre a jour le compteur de likes
        existing.likes_count = fb_comment.get("like_count", 0)
        # Mettre a jour le nom d'auteur si on a maintenant le vrai nom
        new_name = fb_comment.get("author_name", "")
        if new_name and new_name != "Utilisateur Facebook" and existing.author_name != new_name:
            existing.author_name = new_name
        new_platform_id = fb_comment.get("author_platform_id", "")
        if new_platform_id and new_platform_id != "unknown" and existing.author_platform_id != new_platform_id:
            existing.author_platform_id = new_platform_id
        return {"synced": 1, "new": 0}

    # Creer un nouveau commentaire
    new_comment = SocialComment(
        platform_comment_id=platform_comment_id,
        post_id=post_obj.id,
        post_content=post_obj.content[:200] if post_obj.content else None,
        account_id=account.id,
        platform="facebook",
        author_name=fb_comment.get("author_name", "Utilisateur Facebook"),
        author_avatar=None,
        author_platform_id=fb_comment.get("author_platform_id", "unknown"),
        content=fb_comment.get("message", ""),
        parent_comment_id=parent_comment_id,
        is_read=False,
        is_hidden=False,
        likes_count=fb_comment.get("like_count", 0),
        created_at=parse_facebook_datetime(fb_comment.get("created_time", "")),
    )
    db.add(new_comment)
    db.flush()  # Pour les replies qui referencent ce commentaire
    return {"synced": 1, "new": 1}


def sync_all_facebook_accounts(db: Session, force: bool = False, on_progress: Optional[Callable] = None) -> dict:
    """
    Synchroniser tous les comptes Facebook actifs.

    Ne synce que les comptes de type 'profile' (comptes utilisateur OAuth).
    Les comptes de type 'page' sont crees/mis a jour automatiquement
    par sync_facebook_account() a partir du profil parent.

    Returns:
        dict avec les totaux et le detail par compte
    """
    # Recuperer les comptes profil (ou ceux qui n'ont pas encore ete types)
    # Les comptes 'page' sont synces automatiquement via leur profil parent
    accounts = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.platform == "facebook",
            SocialAccount.is_active == True,
            SocialAccount.is_deleted == False,
            SocialAccount.account_type.in_(["profile", "business"]),
        )
        .all()
    )

    # Si aucun profil trouve, chercher TOUS les comptes (migration: anciens comptes)
    if not accounts:
        accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.platform == "facebook",
                SocialAccount.is_active == True,
                SocialAccount.is_deleted == False,
            )
            .all()
        )
        if accounts:
            print(f"[SYNC ALL] Aucun profil FB, fallback sur {len(accounts)} compte(s)", flush=True)

    print(f"[SYNC ALL] {len(accounts)} compte(s) Facebook a synchroniser", flush=True)
    logger.info(f"[SYNC ALL] {len(accounts)} compte(s) Facebook a synchroniser")

    total_stats = {
        "accounts_synced": 0,
        "posts_synced": 0,
        "posts_new": 0,
        "comments_synced": 0,
        "comments_new": 0,
        "pages_synced": 0,
        "errors": [],
    }

    for acct_idx, account in enumerate(accounts):
        try:
            if on_progress:
                on_progress(f"Compte {acct_idx + 1}/{len(accounts)}", int((acct_idx / max(len(accounts), 1)) * 100))
            account_stats = sync_facebook_account(db, account.id, force=force, on_progress=on_progress)
            total_stats["accounts_synced"] += 1
            total_stats["posts_synced"] += account_stats["posts_synced"]
            total_stats["posts_new"] += account_stats["posts_new"]
            total_stats["comments_synced"] += account_stats["comments_synced"]
            total_stats["comments_new"] += account_stats["comments_new"]
            total_stats["pages_synced"] += account_stats.get("pages_synced", 0)
        except Exception as e:
            logger.error(f"Erreur sync compte #{account.id}: {e}")
            print(f"[SYNC ALL] ERREUR compte #{account.id}: {e}", flush=True)
            total_stats["errors"].append({
                "account_id": account.id,
                "error": str(e)[:200],
            })

    return total_stats


# ════════════════════════════════════════════════════════════════
# NETTOYAGE & OPTIMISATION BASE DE DONNÉES
# ════════════════════════════════════════════════════════════════

def get_database_stats(db: Session) -> dict:
    """
    Statistiques de la base de données sociale.

    Retourne les compteurs actifs, soft-deletés et orphelins
    pour chaque table du module social.
    """
    now = datetime.now(timezone.utc)

    # --- Comptes ---
    accounts_active = db.query(func.count(SocialAccount.id)).filter(
        SocialAccount.is_deleted == False
    ).scalar() or 0
    accounts_deleted = db.query(func.count(SocialAccount.id)).filter(
        SocialAccount.is_deleted == True
    ).scalar() or 0

    # --- Posts ---
    posts_active = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False
    ).scalar() or 0
    posts_deleted = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == True
    ).scalar() or 0
    # Orphelins : posts publiés sans aucun result actif
    posts_orphaned = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False,
        SocialPost.status.notin_(["draft", "scheduled"]),
        ~SocialPost.id.in_(
            db.query(SocialPostResult.post_id)
            .filter(SocialPostResult.is_deleted == False)
            .distinct()
        )
    ).scalar() or 0

    # --- PostResults ---
    results_active = db.query(func.count(SocialPostResult.id)).filter(
        SocialPostResult.is_deleted == False
    ).scalar() or 0
    results_deleted = db.query(func.count(SocialPostResult.id)).filter(
        SocialPostResult.is_deleted == True
    ).scalar() or 0
    # Orphelins : results liés à un compte supprimé mais eux-mêmes non supprimés
    results_orphaned_account = db.query(func.count(SocialPostResult.id)).filter(
        SocialPostResult.is_deleted == False,
        SocialPostResult.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).scalar() or 0
    # Orphelins : results liés à un post supprimé mais eux-mêmes non supprimés
    results_orphaned_post = db.query(func.count(SocialPostResult.id)).filter(
        SocialPostResult.is_deleted == False,
        SocialPostResult.post_id.in_(
            db.query(SocialPost.id).filter(SocialPost.is_deleted == True)
        )
    ).scalar() or 0

    # --- Commentaires ---
    comments_active = db.query(func.count(SocialComment.id)).filter(
        SocialComment.is_deleted == False
    ).scalar() or 0
    comments_deleted = db.query(func.count(SocialComment.id)).filter(
        SocialComment.is_deleted == True
    ).scalar() or 0
    # Orphelins : commentaires liés à un compte supprimé
    comments_orphaned = db.query(func.count(SocialComment.id)).filter(
        SocialComment.is_deleted == False,
        SocialComment.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).scalar() or 0

    # --- Conversations ---
    conversations_active = db.query(func.count(SocialConversation.id)).filter(
        SocialConversation.is_deleted == False
    ).scalar() or 0
    conversations_deleted = db.query(func.count(SocialConversation.id)).filter(
        SocialConversation.is_deleted == True
    ).scalar() or 0
    conversations_orphaned = db.query(func.count(SocialConversation.id)).filter(
        SocialConversation.is_deleted == False,
        SocialConversation.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).scalar() or 0

    # --- Messages ---
    messages_active = db.query(func.count(SocialMessage.id)).filter(
        SocialMessage.is_deleted == False
    ).scalar() or 0
    messages_deleted = db.query(func.count(SocialMessage.id)).filter(
        SocialMessage.is_deleted == True
    ).scalar() or 0
    messages_orphaned = db.query(func.count(SocialMessage.id)).filter(
        SocialMessage.is_deleted == False,
        SocialMessage.conversation_id.in_(
            db.query(SocialConversation.id).filter(SocialConversation.is_deleted == True)
        )
    ).scalar() or 0

    total_orphans = (
        posts_orphaned
        + results_orphaned_account + results_orphaned_post
        + comments_orphaned + conversations_orphaned + messages_orphaned
    )

    return {
        "accounts": {"active": accounts_active, "deleted": accounts_deleted},
        "posts": {"active": posts_active, "deleted": posts_deleted, "orphaned": posts_orphaned},
        "post_results": {
            "active": results_active,
            "deleted": results_deleted,
            "orphaned_account": results_orphaned_account,
            "orphaned_post": results_orphaned_post,
        },
        "comments": {"active": comments_active, "deleted": comments_deleted, "orphaned": comments_orphaned},
        "conversations": {"active": conversations_active, "deleted": conversations_deleted, "orphaned": conversations_orphaned},
        "messages": {"active": messages_active, "deleted": messages_deleted, "orphaned": messages_orphaned},
        "total_records": (
            accounts_active + accounts_deleted
            + posts_active + posts_deleted
            + results_active + results_deleted
            + comments_active + comments_deleted
            + conversations_active + conversations_deleted
            + messages_active + messages_deleted
        ),
        "total_orphans": total_orphans,
        "total_soft_deleted": (
            accounts_deleted + posts_deleted + results_deleted
            + comments_deleted + conversations_deleted + messages_deleted
        ),
    }


def cleanup_database(db: Session, hard_delete_days: int = 30) -> dict:
    """
    Nettoyer la base de données du module social.

    Effectue 3 opérations :
    1. Soft-delete les orphelins (données liées à des comptes/posts supprimés)
    2. Hard-delete les enregistrements soft-deleted depuis plus de `hard_delete_days` jours
    3. Retourne les statistiques du nettoyage

    Args:
        db: Session SQLAlchemy
        hard_delete_days: Nombre de jours après soft-delete pour le hard-delete (0 = pas de hard-delete)
    """
    now = datetime.now(timezone.utc)
    stats = {
        "orphans_cleaned": {
            "posts": 0,
            "post_results": 0,
            "comments": 0,
            "conversations": 0,
            "messages": 0,
        },
        "hard_deleted": {
            "accounts": 0,
            "posts": 0,
            "post_results": 0,
            "comments": 0,
            "conversations": 0,
            "messages": 0,
        },
    }

    # ── Étape 1 : Soft-delete les orphelins ──

    # Posts publiés sans aucun result actif
    orphan_posts = db.query(SocialPost).filter(
        SocialPost.is_deleted == False,
        SocialPost.status.notin_(["draft", "scheduled"]),
        ~SocialPost.id.in_(
            db.query(SocialPostResult.post_id)
            .filter(SocialPostResult.is_deleted == False)
            .distinct()
        )
    ).all()
    for p in orphan_posts:
        p.is_deleted = True
        p.deleted_at = now
        stats["orphans_cleaned"]["posts"] += 1

    # PostResults liés à un compte supprimé
    orphan_results_acc = db.query(SocialPostResult).filter(
        SocialPostResult.is_deleted == False,
        SocialPostResult.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).all()
    for r in orphan_results_acc:
        r.is_deleted = True
        r.deleted_at = now
        stats["orphans_cleaned"]["post_results"] += 1

    # PostResults liés à un post supprimé
    orphan_results_post = db.query(SocialPostResult).filter(
        SocialPostResult.is_deleted == False,
        SocialPostResult.post_id.in_(
            db.query(SocialPost.id).filter(SocialPost.is_deleted == True)
        )
    ).all()
    for r in orphan_results_post:
        r.is_deleted = True
        r.deleted_at = now
        stats["orphans_cleaned"]["post_results"] += 1

    # Commentaires liés à un compte supprimé
    orphan_comments = db.query(SocialComment).filter(
        SocialComment.is_deleted == False,
        SocialComment.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).all()
    for c in orphan_comments:
        c.is_deleted = True
        c.deleted_at = now
        stats["orphans_cleaned"]["comments"] += 1

    # Conversations liées à un compte supprimé
    orphan_convs = db.query(SocialConversation).filter(
        SocialConversation.is_deleted == False,
        SocialConversation.account_id.in_(
            db.query(SocialAccount.id).filter(SocialAccount.is_deleted == True)
        )
    ).all()
    for conv in orphan_convs:
        conv.is_deleted = True
        conv.deleted_at = now
        stats["orphans_cleaned"]["conversations"] += 1

    # Messages liés à une conversation supprimée
    orphan_msgs = db.query(SocialMessage).filter(
        SocialMessage.is_deleted == False,
        SocialMessage.conversation_id.in_(
            db.query(SocialConversation.id).filter(SocialConversation.is_deleted == True)
        )
    ).all()
    for m in orphan_msgs:
        m.is_deleted = True
        m.deleted_at = now
        stats["orphans_cleaned"]["messages"] += 1

    db.flush()

    # ── Étape 2 : Hard-delete les anciens soft-deleted ──

    if hard_delete_days >= 0:
        # 0 = purger TOUT immédiatement, >0 = purger les enregistrements plus vieux que X jours
        # -1 = pas de purge (orphelins uniquement)

        # Ordre important : enfants d'abord, parents ensuite (FK constraints)

        def _build_delete_filter(Model):
            """Construire le filtre de suppression selon hard_delete_days."""
            base = db.query(Model).filter(
                Model.is_deleted == True,
            )
            if hard_delete_days > 0:
                cutoff = now - timedelta(days=hard_delete_days)
                base = base.filter(
                    Model.deleted_at != None,
                    Model.deleted_at < cutoff,
                )
            return base

        # Messages
        n = _build_delete_filter(SocialMessage).delete(synchronize_session="fetch")
        stats["hard_deleted"]["messages"] = n

        # Conversations
        n = _build_delete_filter(SocialConversation).delete(synchronize_session="fetch")
        stats["hard_deleted"]["conversations"] = n

        # Commentaires (replies d'abord via parent_comment_id)
        n_replies = db.query(SocialComment).filter(
            SocialComment.is_deleted == True,
            SocialComment.parent_comment_id != None,
        )
        if hard_delete_days > 0:
            cutoff = now - timedelta(days=hard_delete_days)
            n_replies = n_replies.filter(
                SocialComment.deleted_at != None,
                SocialComment.deleted_at < cutoff,
            )
        n_replies = n_replies.delete(synchronize_session="fetch")
        # Puis les commentaires racine
        n_root = _build_delete_filter(SocialComment).delete(synchronize_session="fetch")
        stats["hard_deleted"]["comments"] = n_replies + n_root

        # PostResults
        n = _build_delete_filter(SocialPostResult).delete(synchronize_session="fetch")
        stats["hard_deleted"]["post_results"] = n

        # Posts
        n = _build_delete_filter(SocialPost).delete(synchronize_session="fetch")
        stats["hard_deleted"]["posts"] = n

        # Comptes
        n = _build_delete_filter(SocialAccount).delete(synchronize_session="fetch")
        stats["hard_deleted"]["accounts"] = n

    db.commit()

    total_orphans = sum(stats["orphans_cleaned"].values())
    total_hard = sum(stats["hard_deleted"].values())
    logger.info(
        f"[CLEANUP] Nettoyage terminé: {total_orphans} orphelins nettoyés, "
        f"{total_hard} enregistrements purgés (>{hard_delete_days}j)"
    )

    return stats


def purge_published_data(db: Session) -> dict:
    """
    Purger toutes les donnees publiees du module social (hard-delete).

    Supprime definitivement les messages, conversations, commentaires,
    insights, resultats de publication et posts publies/erreur.
    Preserve les comptes OAuth, les brouillons et les posts planifies.

    Ordre de suppression (respect des FK) :
    1. SocialMessage (tous)
    2. SocialConversation (tous)
    3. SocialComment (replies d'abord, puis racines)
    4. SocialPageInsight (tous)
    5. SocialPostResult (tous)
    6. SocialPost ou status NOT IN ('draft', 'scheduled')

    Returns:
        dict avec le nombre d'enregistrements supprimes par table
    """
    stats = {
        "messages": 0,
        "conversations": 0,
        "comments": 0,
        "insights": 0,
        "post_results": 0,
        "posts": 0,
    }

    # 1. Messages (tous)
    stats["messages"] = db.query(SocialMessage).delete(synchronize_session="fetch")

    # 2. Conversations (tous)
    stats["conversations"] = db.query(SocialConversation).delete(synchronize_session="fetch")

    # 3. Commentaires (replies d'abord via parent_comment_id, puis racines)
    stats["comments"] = db.query(SocialComment).filter(
        SocialComment.parent_comment_id != None,
    ).delete(synchronize_session="fetch")
    stats["comments"] += db.query(SocialComment).delete(synchronize_session="fetch")

    # 4. Page Insights (tous)
    stats["insights"] = db.query(SocialPageInsight).delete(synchronize_session="fetch")

    # 5. PostResults (tous)
    stats["post_results"] = db.query(SocialPostResult).delete(synchronize_session="fetch")

    # 6. Posts publies/erreur (pas draft/scheduled)
    stats["posts"] = db.query(SocialPost).filter(
        SocialPost.status.notin_(["draft", "scheduled"]),
    ).delete(synchronize_session="fetch")

    db.commit()

    total = sum(stats.values())
    logger.info(f"[PURGE] Donnees publiees purgees: {total} enregistrements ({stats})")
    return stats


# ════════════════════════════════════════════════════════════════
# ANALYTICS — REACTIONS, FOLLOWERS, VIDEO (depuis SocialPageInsight)
# ════════════════════════════════════════════════════════════════

def get_reactions_breakdown(db: Session, period: str = "30d", account_id: Optional[int] = None) -> dict:
    """Repartition des reactions par type depuis les insights page."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_q = db.query(
        func.coalesce(func.sum(SocialPageInsight.reactions_like), 0),
        func.coalesce(func.sum(SocialPageInsight.reactions_love), 0),
        func.coalesce(func.sum(SocialPageInsight.reactions_wow), 0),
        func.coalesce(func.sum(SocialPageInsight.reactions_haha), 0),
        func.coalesce(func.sum(SocialPageInsight.reactions_sorry), 0),
        func.coalesce(func.sum(SocialPageInsight.reactions_anger), 0),
    ).filter(
        SocialPageInsight.date >= cutoff.date(),
    )
    if account_id:
        base_q = base_q.filter(SocialPageInsight.account_id == account_id)

    row = base_q.first()
    like = row[0] if row else 0
    love = row[1] if row else 0
    wow = row[2] if row else 0
    haha = row[3] if row else 0
    sorry = row[4] if row else 0
    anger = row[5] if row else 0

    return {
        "like": like,
        "love": love,
        "wow": wow,
        "haha": haha,
        "sorry": sorry,
        "anger": anger,
        "total": like + love + wow + haha + sorry + anger,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
    }


def get_follower_trend(db: Session, period: str = "30d", account_id: Optional[int] = None) -> dict:
    """Serie temporelle des abonnes depuis les insights page."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_q = db.query(
        SocialPageInsight.date,
        func.coalesce(func.sum(SocialPageInsight.page_follows), 0),
        func.coalesce(func.sum(SocialPageInsight.page_daily_follows), 0),
        func.coalesce(func.sum(SocialPageInsight.page_daily_unfollows), 0),
    ).filter(
        SocialPageInsight.date >= cutoff.date(),
    )
    if account_id:
        base_q = base_q.filter(SocialPageInsight.account_id == account_id)

    rows = (
        base_q
        .group_by(SocialPageInsight.date)
        .order_by(SocialPageInsight.date)
        .all()
    )

    trend = []
    total_new = 0
    total_unfollows = 0
    latest_total = 0
    for row in rows:
        new_f = row[2] or 0
        unf = row[3] or 0
        total_new += new_f
        total_unfollows += unf
        latest_total = row[1] or 0
        trend.append({
            "date": str(row[0]),
            "total_followers": latest_total,
            "new_followers": new_f,
            "unfollows": unf,
            "net_change": new_f - unf,
        })

    # Fallback : si pas d'insights, utiliser followers_count des comptes
    if not trend:
        followers_q = db.query(func.coalesce(func.sum(SocialAccount.followers_count), 0)).filter(
            SocialAccount.is_deleted == False, SocialAccount.is_active == True
        )
        if account_id:
            followers_q = followers_q.filter(SocialAccount.id == account_id)
        latest_total = followers_q.scalar() or 0

    return {
        "current_total": latest_total,
        "net_change_period": total_new - total_unfollows,
        "trend": trend,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
    }


def get_video_performance(db: Session, period: str = "30d", account_id: Optional[int] = None) -> dict:
    """Performance video agregee depuis les insights page."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_q = db.query(
        func.coalesce(func.sum(SocialPageInsight.page_video_views), 0),
        func.coalesce(func.sum(SocialPageInsight.page_video_view_time), 0),
    ).filter(
        SocialPageInsight.date >= cutoff.date(),
    )
    if account_id:
        base_q = base_q.filter(SocialPageInsight.account_id == account_id)

    row = base_q.first()
    total_views = row[0] if row else 0
    total_view_time_ms = row[1] if row else 0

    avg_view_time_seconds = 0.0
    if total_views > 0:
        avg_view_time_seconds = round((total_view_time_ms / 1000) / total_views, 1)

    return {
        "total_views": total_views,
        "total_view_time_ms": total_view_time_ms,
        "avg_view_time_seconds": avg_view_time_seconds,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
    }

"""
Opérations CRUD pour le module Social.

Gère les accès base de données pour les comptes sociaux,
publications, commentaires, conversations et messages.
Inclut les fonctions de synchronisation avec Facebook Graph API.
"""

import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models.model_social import (
    SocialAccount, SocialPost, SocialPostResult,
    SocialComment, SocialConversation, SocialMessage,
)
from app.schemas.schema_social import (
    SocialPostCreate, SocialPostUpdate,
)

logger = logging.getLogger("hapson-api")


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


def disconnect_social_account(db: Session, account_id: int) -> bool:
    """Soft delete d'un compte social."""
    account = get_social_account_by_id(db, account_id)
    account.is_deleted = True
    account.deleted_at = datetime.now(timezone.utc)
    account.is_active = False
    db.commit()
    return True


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
    """Récupérer les posts avec filtres optionnels."""
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

    return query.order_by(desc(SocialPost.created_at)).all()


def get_social_post_by_id(db: Session, post_id: int) -> SocialPost:
    """Récupérer un post par ID avec ses résultats."""
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


def delete_social_post(db: Session, post_id: int) -> bool:
    """Soft delete d'un post."""
    post = get_social_post_by_id(db, post_id)
    post.is_deleted = True
    post.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def publish_social_post(db: Session, post_id: int) -> SocialPost:
    """
    Publier un post sur les plateformes cibles.

    Pour chaque compte cible sur Facebook :
    1. Recupere le page access token via /me/accounts
    2. Publie sur la page via Graph API
    3. Cree un SocialPostResult avec le platform_post_id

    Pour les plateformes non-Facebook, simule le succes (TODO).
    """
    from app.services.social_facebook import get_facebook_pages, publish_to_page

    post = get_social_post_by_id(db, post_id)

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce post est déjà publié"
        )

    post.status = "publishing"
    db.commit()
    db.refresh(post)

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
                # Recuperer les pages Facebook avec le user token
                pages = get_facebook_pages(account.access_token)
                if not pages:
                    result.status = "error"
                    result.error_message = "Aucune page Facebook trouvee"
                    has_error = True
                else:
                    # Publier sur la premiere page (ou celle qui correspond a account_id)
                    target_page = None
                    for page in pages:
                        if page["id"] == account.account_id:
                            target_page = page
                            break
                    if not target_page:
                        target_page = pages[0]

                    fb_result = publish_to_page(
                        page_access_token=target_page["access_token"],
                        page_id=target_page["id"],
                        message=post.content,
                        link=post.link_url,
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

    return post


def schedule_social_post(db: Session, post_id: int, scheduled_at: datetime) -> SocialPost:
    """Planifier un post pour une date future."""
    post = get_social_post_by_id(db, post_id)

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce post est déjà publié"
        )

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


# ════════════════════════════════════════════════════════════════
# COMMENTAIRES
# ════════════════════════════════════════════════════════════════

def get_social_comments(
    db: Session,
    post_id: Optional[int] = None,
    platform: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> list[SocialComment]:
    """Récupérer les commentaires avec filtres."""
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

    return query.order_by(desc(SocialComment.created_at)).all()


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


def delete_social_comment(db: Session, comment_id: int) -> bool:
    """Soft delete d'un commentaire."""
    comment = get_comment_by_id(db, comment_id)
    comment.is_deleted = True
    comment.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


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

def get_analytics_overview(db: Session, period: str = "30d") -> dict:
    """Calculer les statistiques d'ensemble pour la période donnée."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)

    # Posts stats
    total_posts = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    ).scalar() or 0

    total_published = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "published", SocialPost.created_at >= cutoff
    ).scalar() or 0

    total_scheduled = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "scheduled"
    ).scalar() or 0

    total_drafts = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_deleted == False, SocialPost.status == "draft"
    ).scalar() or 0

    # Engagement metrics (from results)
    metrics = db.query(
        func.coalesce(func.sum(SocialPostResult.impressions), 0),
        func.coalesce(func.sum(SocialPostResult.clicks), 0),
        func.coalesce(func.sum(SocialPostResult.likes), 0),
        func.coalesce(func.sum(SocialPostResult.shares), 0),
        func.coalesce(func.sum(SocialPostResult.comments), 0),
    ).join(SocialPost, SocialPostResult.post_id == SocialPost.id).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    ).first()

    impressions = metrics[0] if metrics else 0
    clicks = metrics[1] if metrics else 0
    likes = metrics[2] if metrics else 0
    shares = metrics[3] if metrics else 0
    comments_count = metrics[4] if metrics else 0
    total_engagements = clicks + likes + shares + comments_count

    # Followers
    followers_total = db.query(func.coalesce(func.sum(SocialAccount.followers_count), 0)).filter(
        SocialAccount.is_deleted == False, SocialAccount.is_active == True
    ).scalar() or 0

    # Avg engagement rate
    avg_engagement = 0.0
    if impressions > 0:
        avg_engagement = round((total_engagements / impressions) * 100, 2)

    # Top hashtags
    all_hashtags = db.query(SocialPost.hashtags).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    ).all()
    hashtag_count: dict[str, int] = {}
    for (tags,) in all_hashtags:
        if tags:
            for tag in tags:
                hashtag_count[tag] = hashtag_count.get(tag, 0) + 1
    top_hashtags = sorted(hashtag_count, key=hashtag_count.get, reverse=True)[:10]

    # Top platforms
    all_platforms = db.query(SocialPost.platforms).filter(
        SocialPost.is_deleted == False, SocialPost.created_at >= cutoff
    ).all()
    platform_count: dict[str, int] = {}
    for (plats,) in all_platforms:
        if plats:
            for p in plats:
                platform_count[p] = platform_count.get(p, 0) + 1
    top_platforms = sorted(platform_count, key=platform_count.get, reverse=True)

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
        "followers_growth": 0,  # TODO: calcul historique
        "impressions_change": 0.0,
        "engagements_change": 0.0,
        "reach_change": 0.0,
        "engagement_rate_change": 0.0,
        "total_engagements": total_engagements,
        "top_hashtags": top_hashtags,
        "top_platforms": top_platforms,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
    }


def get_platform_stats(db: Session, period: str = "30d") -> list[dict]:
    """Statistiques ventilées par plateforme."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
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
        .group_by(SocialPostResult.platform)
        .all()
    )

    stats = []
    for r in results:
        engagements = r.clicks + r.likes + r.shares + r.comments
        engagement_rate = round((engagements / r.impressions) * 100, 2) if r.impressions > 0 else 0.0

        # Followers pour cette plateforme
        followers = db.query(func.coalesce(func.sum(SocialAccount.followers_count), 0)).filter(
            SocialAccount.platform == r.platform,
            SocialAccount.is_deleted == False,
            SocialAccount.is_active == True,
        ).scalar() or 0

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


def get_best_times(db: Session) -> list[dict]:
    """Calculer les meilleurs horaires de publication basés sur l'engagement."""
    # Requête sur les posts publiés avec leurs résultats
    results = (
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
        .group_by(SocialPostResult.platform, "dow", "hour")
        .order_by(desc("avg_eng"))
        .limit(20)
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


def get_engagement_time_series(db: Session, period: str = "30d") -> list[dict]:
    """Série temporelle de l'engagement par jour."""
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
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

def sync_facebook_account(db: Session, account_id: int) -> dict:
    """
    Synchroniser les posts et commentaires Facebook pour un compte.

    Processus :
    1. Recuperer le page access token via /me/accounts
    2. Mettre a jour les infos du compte (page_id, avatar, followers)
    3. Importer les posts de la page
    4. Pour chaque post, importer les commentaires
    5. Mettre a jour les metriques d'engagement

    Returns:
        dict avec les compteurs : {posts_synced, comments_synced, posts_new, comments_new}
    """
    from app.services.social_facebook import (
        get_facebook_pages,
        get_page_posts,
        get_post_comments,
        get_post_reactions_count,
        parse_facebook_datetime,
    )

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
    }

    # 0. DIAGNOSTIC — verifier les permissions du token
    from app.services.social_facebook import debug_token_permissions
    debug_token_permissions(account.access_token)

    # 1. Recuperer les pages Facebook
    print(f"[SYNC] Compte #{account_id}: debut sync, platform={account.platform}, account_id={account.account_id}", flush=True)
    logger.info(f"[SYNC] Compte #{account_id}: debut sync, platform={account.platform}, account_id={account.account_id}")
    pages = get_facebook_pages(account.access_token)
    if not pages:
        print(f"[SYNC] Aucune page Facebook trouvee pour le compte #{account_id}", flush=True)
        logger.warning(f"[SYNC] Aucune page Facebook trouvee pour le compte #{account_id}")
        return stats

    logger.info(f"[SYNC] Compte #{account_id}: {len(pages)} page(s) trouvee(s) -> {[p['name'] for p in pages]}")
    print(f"[SYNC] Compte #{account_id}: {len(pages)} page(s) -> {[p['name'] for p in pages]}", flush=True)

    # Trouver la page correspondante au compte, ou utiliser la premiere
    target_page = None
    for page in pages:
        if page["id"] == account.account_id:
            target_page = page
            break
    if not target_page:
        # Si le account_id stocke est le user ID, prendre la premiere page
        target_page = pages[0]
        # Mettre a jour le account_id avec le page_id
        account.account_id = target_page["id"]
        account.account_name = target_page["name"]
        logger.info(f"[SYNC] account_id mis a jour: {account.account_id} -> {target_page['id']} ({target_page['name']})")

    page_token = target_page["access_token"]
    page_id = target_page["id"]
    logger.info(f"[SYNC] Page cible: {target_page['name']} (ID: {page_id})")

    # Mettre a jour les infos du compte
    if target_page.get("picture_url"):
        account.avatar_url = target_page["picture_url"]
        account.profile_picture = target_page["picture_url"]
    if target_page.get("followers_count"):
        account.followers_count = target_page["followers_count"]
    account.account_type = "page"
    account.profile_url = f"https://www.facebook.com/{page_id}"
    db.commit()

    # 2. Recuperer les posts de la page
    fb_posts = get_page_posts(page_token, page_id, limit=50)
    logger.info(f"[SYNC] Page {page_id}: {len(fb_posts)} post(s) recupere(s) depuis Facebook")
    print(f"[SYNC] Page {page_id}: {len(fb_posts)} post(s) recupere(s)", flush=True)

    for fb_post in fb_posts:
        platform_post_id = fb_post["platform_post_id"]
        if not platform_post_id:
            continue

        # Verifier si ce post existe deja (via SocialPostResult.platform_post_id)
        existing_result = (
            db.query(SocialPostResult)
            .filter(
                SocialPostResult.platform_post_id == platform_post_id,
                SocialPostResult.account_id == account.id,
            )
            .first()
        )

        if existing_result:
            # Mettre a jour les metriques du post existant
            try:
                reactions = get_post_reactions_count(page_token, platform_post_id)
                existing_result.likes = reactions.get("likes", 0)
                existing_result.comments = reactions.get("comments", 0)
                existing_result.shares = fb_post.get("shares_count", 0)
                existing_result.impressions = fb_post.get("impressions", 0)
                existing_result.clicks = fb_post.get("clicks", 0)
                total_eng = existing_result.likes + existing_result.comments + existing_result.shares + existing_result.clicks
                if existing_result.impressions > 0:
                    existing_result.engagement_rate = round((total_eng / existing_result.impressions) * 100, 2)
            except Exception as e:
                logger.warning(f"Erreur mise a jour metriques post {platform_post_id}: {e}")

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
                target_accounts=[str(account.id)],
                status="published",
                published_at=published_at,
                created_at=published_at,
                created_by=account.connected_by,
            )
            db.add(post_obj)
            db.flush()  # Pour obtenir post_obj.id

            # Recuperer les reactions/likes
            try:
                reactions = get_post_reactions_count(page_token, platform_post_id)
                likes_count = reactions.get("likes", 0)
                comments_count = reactions.get("comments", 0)
            except Exception:
                likes_count = 0
                comments_count = 0

            result_obj = SocialPostResult(
                post_id=post_obj.id,
                account_id=account.id,
                platform="facebook",
                status="published",
                platform_post_id=platform_post_id,
                platform_post_url=fb_post.get("permalink_url", ""),
                platform_url=fb_post.get("permalink_url", ""),
                published_at=published_at,
                impressions=fb_post.get("impressions", 0),
                clicks=fb_post.get("clicks", 0),
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

        # 3. Synchroniser les commentaires de ce post
        if post_obj:
            try:
                fb_comments = get_post_comments(page_token, platform_post_id, limit=100)
                for fb_comment in fb_comments:
                    comment_stats = _sync_single_comment(
                        db, fb_comment, post_obj, account, parent_comment_id=None
                    )
                    stats["comments_synced"] += comment_stats["synced"]
                    stats["comments_new"] += comment_stats["new"]

                    # Sync replies
                    for reply in fb_comment.get("replies", []):
                        # On doit d'abord trouver le parent comment dans la BDD
                        parent_db = (
                            db.query(SocialComment)
                            .filter(
                                SocialComment.platform_comment_id == fb_comment["platform_comment_id"]
                            )
                            .first()
                        )
                        if parent_db:
                            reply_stats = _sync_single_comment(
                                db, reply, post_obj, account, parent_comment_id=parent_db.id
                            )
                            stats["comments_synced"] += reply_stats["synced"]
                            stats["comments_new"] += reply_stats["new"]
            except Exception as e:
                logger.warning(f"Erreur sync commentaires pour {platform_post_id}: {e}")

    db.commit()
    logger.info(
        f"Sync Facebook #{account_id} terminee: "
        f"{stats['posts_synced']} posts ({stats['posts_new']} new), "
        f"{stats['comments_synced']} comments ({stats['comments_new']} new)"
    )
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


def sync_all_facebook_accounts(db: Session) -> dict:
    """
    Synchroniser tous les comptes Facebook actifs.

    Returns:
        dict avec les totaux et le detail par compte
    """
    accounts = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.platform == "facebook",
            SocialAccount.is_active == True,
            SocialAccount.is_deleted == False,
        )
        .all()
    )

    logger.info(f"[SYNC ALL] {len(accounts)} compte(s) Facebook actif(s) a synchroniser")
    print(f"[SYNC ALL] {len(accounts)} compte(s) Facebook actif(s) a synchroniser", flush=True)

    total_stats = {
        "accounts_synced": 0,
        "posts_synced": 0,
        "posts_new": 0,
        "comments_synced": 0,
        "comments_new": 0,
        "errors": [],
    }

    for account in accounts:
        try:
            account_stats = sync_facebook_account(db, account.id)
            total_stats["accounts_synced"] += 1
            total_stats["posts_synced"] += account_stats["posts_synced"]
            total_stats["posts_new"] += account_stats["posts_new"]
            total_stats["comments_synced"] += account_stats["comments_synced"]
            total_stats["comments_new"] += account_stats["comments_new"]
        except Exception as e:
            logger.error(f"Erreur sync compte #{account.id}: {e}")
            print(f"[SYNC ALL] ERREUR compte #{account.id}: {e}", flush=True)
            total_stats["errors"].append({
                "account_id": account.id,
                "error": str(e)[:200],
            })

    return total_stats

"""
Opérations CRUD pour le module Social.

Gère les accès base de données pour les comptes sociaux,
publications, commentaires, conversations et messages.
"""

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
    """Marquer un post pour publication immédiate."""
    post = get_social_post_by_id(db, post_id)

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce post est déjà publié"
        )

    post.status = "publishing"
    post.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)

    # TODO: Déclencher la publication réelle via les APIs des plateformes
    # Pour l'instant on simule le succès
    post.status = "published"
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

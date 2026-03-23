from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func as sa_func
from fastapi import HTTPException
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_subscription import InventorySubscription
from app.models.model_inventory_settings import InventoryConfigOption
from app.models.model_inventory_company import InventoryCompany
from app.schemas.schema_inventory_subscription import (
    SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate,
    SubscriptionListResponse, SubscriptionAlertResponse,
)


# ════════════════════════════════════════════════════════════════
# HELPER : enrichir la reponse avec les noms des relations
# ════════════════════════════════════════════════════════════════

def _build_subscription_response(sub: InventorySubscription) -> SubscriptionResponse:
    """Construit un SubscriptionResponse enrichi des noms issus des relations."""
    resp = SubscriptionResponse.model_validate(sub)
    resp.category_name = sub.category.name if sub.category else None
    resp.company_name = sub.company.name if sub.company else None
    return resp


def _eager_load_query(db: Session):
    """Retourne une query avec les relations pre-chargees."""
    return db.query(InventorySubscription).options(
        joinedload(InventorySubscription.category),
        joinedload(InventorySubscription.company),
    )


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

def create_subscription(
    db: Session,
    data: SubscriptionCreate,
    user_id: int,
    user_name: str,
) -> SubscriptionResponse:
    try:
        subscription = InventorySubscription(
            name=data.name,
            description=data.description,
            reference=data.reference,
            category_id=data.category_id,
            provider_name=data.provider_name,
            provider_website=data.provider_website,
            provider_contact_email=data.provider_contact_email,
            provider_contact_phone=data.provider_contact_phone,
            provider_account_number=data.provider_account_number,
            cost_amount=data.cost_amount,
            cost_currency=data.cost_currency,
            billing_cycle=data.billing_cycle,
            next_billing_date=data.next_billing_date,
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_type=data.renewal_type,
            auto_renew_period_months=data.auto_renew_period_months,
            status=data.status,
            company_id=data.company_id,
            notes=data.notes,
            login_url=data.login_url,
            created_by=user_id,
            created_by_name=user_name,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Eager-load relationships for response
        subscription = _eager_load_query(db).filter(
            InventorySubscription.id == subscription.id
        ).first()

        return _build_subscription_response(subscription)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation abonnement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# LIST (pagination, filtres, tri, recherche)
# ════════════════════════════════════════════════════════════════

def get_subscription_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    renewal_type: str | None = None,
    company_id: int | None = None,
    is_archived: bool = False,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> SubscriptionListResponse:
    try:
        query = _eager_load_query(db).filter(
            InventorySubscription.is_deleted == False,
            InventorySubscription.is_archived == is_archived,
        )

        # Filtres
        if category_id is not None:
            query = query.filter(InventorySubscription.category_id == category_id)
        if status is not None:
            query = query.filter(InventorySubscription.status == status)
        if renewal_type is not None:
            query = query.filter(InventorySubscription.renewal_type == renewal_type)
        if company_id is not None:
            query = query.filter(InventorySubscription.company_id == company_id)

        # Recherche texte (ILIKE)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    InventorySubscription.name.ilike(search_pattern),
                    InventorySubscription.reference.ilike(search_pattern),
                    InventorySubscription.description.ilike(search_pattern),
                    InventorySubscription.provider_name.ilike(search_pattern),
                    InventorySubscription.notes.ilike(search_pattern),
                )
            )

        # Compter le total AVANT pagination
        count_query = db.query(sa_func.count(InventorySubscription.id)).filter(
            InventorySubscription.is_deleted == False,
            InventorySubscription.is_archived == is_archived,
        )
        if category_id is not None:
            count_query = count_query.filter(InventorySubscription.category_id == category_id)
        if status is not None:
            count_query = count_query.filter(InventorySubscription.status == status)
        if renewal_type is not None:
            count_query = count_query.filter(InventorySubscription.renewal_type == renewal_type)
        if company_id is not None:
            count_query = count_query.filter(InventorySubscription.company_id == company_id)
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.filter(
                or_(
                    InventorySubscription.name.ilike(search_pattern),
                    InventorySubscription.reference.ilike(search_pattern),
                    InventorySubscription.description.ilike(search_pattern),
                    InventorySubscription.provider_name.ilike(search_pattern),
                    InventorySubscription.notes.ilike(search_pattern),
                )
            )
        total = count_query.scalar()

        # Tri
        allowed_sort_fields = {
            "created_at": InventorySubscription.created_at,
            "name": InventorySubscription.name,
            "start_date": InventorySubscription.start_date,
            "end_date": InventorySubscription.end_date,
            "cost_amount": InventorySubscription.cost_amount,
            "status": InventorySubscription.status,
            "provider_name": InventorySubscription.provider_name,
            "updated_at": InventorySubscription.updated_at,
        }
        sort_column = allowed_sort_fields.get(sort_by, InventorySubscription.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * page_size
        subscription_list = query.offset(offset).limit(page_size).all()

        items = [_build_subscription_response(sub) for sub in subscription_list]
        return SubscriptionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation abonnements: {str(e)}")


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

def get_subscription_by_id(db: Session, subscription_id: int) -> SubscriptionResponse:
    subscription = _eager_load_query(db).filter(
        InventorySubscription.id == subscription_id,
        InventorySubscription.is_deleted == False,
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Abonnement non trouve")
    return _build_subscription_response(subscription)


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

def update_subscription(
    db: Session,
    subscription_id: int,
    data: SubscriptionUpdate,
    user_id: int,
) -> SubscriptionResponse:
    try:
        subscription = _eager_load_query(db).filter(
            InventorySubscription.id == subscription_id,
            InventorySubscription.is_deleted == False,
        ).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouve")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)
        subscription.updated_by = user_id

        db.commit()
        db.refresh(subscription)

        # Recharger les relations
        subscription = _eager_load_query(db).filter(
            InventorySubscription.id == subscription_id
        ).first()

        return _build_subscription_response(subscription)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour abonnement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# ARCHIVE / RESTORE
# ════════════════════════════════════════════════════════════════

def archive_subscription(db: Session, subscription_id: int, reason: str | None, user_id: int) -> SubscriptionResponse:
    try:
        subscription = db.query(InventorySubscription).filter(
            InventorySubscription.id == subscription_id,
            InventorySubscription.is_deleted == False,
        ).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouve")

        subscription.is_archived = True
        subscription.archived_at = datetime.now(timezone.utc)
        subscription.archived_reason = reason
        subscription.updated_by = user_id
        db.commit()
        db.refresh(subscription)

        # Recharger les relations
        subscription = _eager_load_query(db).filter(
            InventorySubscription.id == subscription_id
        ).first()

        return _build_subscription_response(subscription)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur archivage abonnement: {str(e)}")


def restore_subscription(db: Session, subscription_id: int, user_id: int) -> SubscriptionResponse:
    try:
        subscription = db.query(InventorySubscription).filter(
            InventorySubscription.id == subscription_id,
            InventorySubscription.is_deleted == False,
        ).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouve")

        subscription.is_archived = False
        subscription.archived_at = None
        subscription.archived_reason = None
        subscription.updated_by = user_id
        db.commit()
        db.refresh(subscription)

        subscription = _eager_load_query(db).filter(
            InventorySubscription.id == subscription_id
        ).first()

        return _build_subscription_response(subscription)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur restauration abonnement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# DELETE (hard delete)
# ════════════════════════════════════════════════════════════════

def delete_subscription(db: Session, subscription_id: int) -> bool:
    try:
        subscription = db.query(InventorySubscription).filter(
            InventorySubscription.id == subscription_id,
        ).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouve")
        db.delete(subscription)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression abonnement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# ALERTS (expiring / expired subscriptions)
# ════════════════════════════════════════════════════════════════

def get_subscription_alerts(db: Session, days: int = 30) -> SubscriptionAlertResponse:
    """
    Retourne les abonnements expires et ceux qui expirent bientot.

    - expired: end_date < aujourd'hui (et statut encore 'active')
    - expiring_soon: end_date dans les 7 prochains jours
    - expiring_warning: end_date dans les `days` prochains jours (apres les 7j)
    """
    try:
        today = date.today()
        soon_date = today + timedelta(days=7)
        warning_date = today + timedelta(days=days)

        # Base query : actifs, non archives, non supprimes, avec une date de fin
        base_filter = [
            InventorySubscription.is_deleted == False,
            InventorySubscription.is_archived == False,
            InventorySubscription.status == 'active',
            InventorySubscription.end_date.isnot(None),
        ]

        # Expires
        expired_query = _eager_load_query(db).filter(
            *base_filter,
            InventorySubscription.end_date < today,
        ).all()

        # Expirant dans 7 jours
        expiring_soon_query = _eager_load_query(db).filter(
            *base_filter,
            InventorySubscription.end_date >= today,
            InventorySubscription.end_date <= soon_date,
        ).all()

        # Expirant dans les `days` jours (hors les 7 premiers jours)
        expiring_warning_query = _eager_load_query(db).filter(
            *base_filter,
            InventorySubscription.end_date > soon_date,
            InventorySubscription.end_date <= warning_date,
        ).all()

        expired = [_build_subscription_response(s) for s in expired_query]
        expiring_soon = [_build_subscription_response(s) for s in expiring_soon_query]
        expiring_warning = [_build_subscription_response(s) for s in expiring_warning_query]

        return SubscriptionAlertResponse(
            expired=expired,
            expiring_soon=expiring_soon,
            expiring_warning=expiring_warning,
            total_alerts=len(expired) + len(expiring_soon) + len(expiring_warning),
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation alertes abonnements: {str(e)}")

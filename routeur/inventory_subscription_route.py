from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_subscription import (
    create_subscription, get_subscription_list, get_subscription_by_id,
    update_subscription, archive_subscription, restore_subscription,
    delete_subscription, get_subscription_alerts,
)
from app.schemas.schema_inventory_subscription import (
    SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate,
    SubscriptionListResponse, SubscriptionArchiveBody, SubscriptionAlertResponse,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-subscriptions"]
)


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION LIST
# ════════════════════════════════════════════════════════════════

@router.get("/subscriptions/", response_model=SubscriptionListResponse)
def get_subscription_list_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    status: str | None = Query(None),
    renewal_type: str | None = Query(None),
    company_id: int | None = Query(None),
    is_archived: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_subscription_list(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status=status,
        renewal_type=renewal_type,
        company_id=company_id,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ════════════════════════════════════════════════════════════════
# ALERTS (expiring / expired)
# ════════════════════════════════════════════════════════════════

@router.get("/subscriptions/alerts", response_model=SubscriptionAlertResponse)
def get_subscription_alerts_route(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_subscription_alerts(db, days)


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_subscription_by_id(db, subscription_id)


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

@router.post("/subscriptions/", response_model=SubscriptionResponse)
def create_subscription_route(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_subscription(db, data, current_user.id, current_user.username)
    log_action(db, current_user.id, "create", "inventory_subscription", result.id)
    return result


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription_route(
    subscription_id: int,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_subscription(db, subscription_id, data, current_user.id)
    log_action(db, current_user.id, "update", "inventory_subscription", subscription_id)
    return result


# ════════════════════════════════════════════════════════════════
# ARCHIVE / RESTORE
# ════════════════════════════════════════════════════════════════

@router.put("/subscriptions/{subscription_id}/archive", response_model=SubscriptionResponse)
def archive_subscription_route(
    subscription_id: int,
    body: SubscriptionArchiveBody,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = archive_subscription(db, subscription_id, body.reason, current_user.id)
    log_action(db, current_user.id, "archive", "inventory_subscription", subscription_id)
    return result


@router.put("/subscriptions/{subscription_id}/restore", response_model=SubscriptionResponse)
def restore_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = restore_subscription(db, subscription_id, current_user.id)
    log_action(db, current_user.id, "restore", "inventory_subscription", subscription_id)
    return result


# ════════════════════════════════════════════════════════════════
# DELETE
# ════════════════════════════════════════════════════════════════

@router.delete("/subscriptions/{subscription_id}", response_model=bool)
def delete_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = delete_subscription(db, subscription_id)
    log_action(db, current_user.id, "delete", "inventory_subscription", subscription_id)
    return result

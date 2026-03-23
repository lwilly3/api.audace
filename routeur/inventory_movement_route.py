from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_movement import (
    create_movement, get_movement_list, get_pending_movements,
    get_equipment_movements, approve_movement, reject_movement,
)
from app.schemas.schema_inventory_movement import (
    MovementCreate, MovementResponse, MovementListResponse,
    MovementApproveBody, MovementRejectBody,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-movements"]
)


# ════════════════════════════════════════════════════════════════
# MOVEMENT LIST (filtres + pagination)
# ════════════════════════════════════════════════════════════════

@router.get("/movements/", response_model=MovementListResponse)
def get_movement_list_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    equipment_id: int | None = Query(None),
    movement_category: str | None = Query(None),
    status: str | None = Query(None),
    from_company_id: int | None = Query(None),
    to_company_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("date"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_movement_list(
        db,
        page=page,
        page_size=page_size,
        equipment_id=equipment_id,
        movement_category=movement_category,
        status=status,
        from_company_id=from_company_id,
        to_company_id=to_company_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ════════════════════════════════════════════════════════════════
# PENDING MOVEMENTS (en attente d'approbation)
# ════════════════════════════════════════════════════════════════

@router.get("/movements/pending", response_model=MovementListResponse)
def get_pending_movements_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_pending_movements(db, page=page, page_size=page_size)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT MOVEMENTS (mouvements d'un equipement)
# ════════════════════════════════════════════════════════════════

@router.get("/movements/equipment/{equipment_id}", response_model=MovementListResponse)
def get_equipment_movements_route(
    equipment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_equipment_movements(db, equipment_id, page=page, page_size=page_size)


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

@router.post("/movements/", response_model=MovementResponse)
def create_movement_route(
    data: MovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_movement(db, data, current_user.id, current_user.username)
    log_action(db, current_user.id, "create", "inventory_movements", result.id)
    return result


# ════════════════════════════════════════════════════════════════
# APPROVE
# ════════════════════════════════════════════════════════════════

@router.put("/movements/{movement_id}/approve", response_model=MovementResponse)
def approve_movement_route(
    movement_id: int,
    body: MovementApproveBody,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = approve_movement(db, movement_id, current_user.id, current_user.username)
    log_action(db, current_user.id, "approve", "inventory_movements", movement_id)
    return result


# ════════════════════════════════════════════════════════════════
# REJECT
# ════════════════════════════════════════════════════════════════

@router.put("/movements/{movement_id}/reject", response_model=MovementResponse)
def reject_movement_route(
    movement_id: int,
    body: MovementRejectBody,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = reject_movement(db, movement_id, current_user.id, current_user.username, body.reason)
    log_action(db, current_user.id, "reject", "inventory_movements", movement_id)
    return result

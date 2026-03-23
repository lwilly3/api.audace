from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_maintenance import (
    create_maintenance, get_maintenance_list, get_maintenance_by_equipment,
    get_maintenance_by_id, update_maintenance, get_upcoming_maintenance,
    delete_maintenance,
)
from app.schemas.schema_inventory_maintenance import (
    MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate,
    MaintenanceListResponse,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-maintenance"]
)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE LIST (pagination, filtres)
# ════════════════════════════════════════════════════════════════

@router.get("/maintenance/", response_model=MaintenanceListResponse)
def get_maintenance_list_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    equipment_id: int | None = Query(None),
    status: str | None = Query(None),
    maintenance_type: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_maintenance_list(
        db,
        page=page,
        page_size=page_size,
        equipment_id=equipment_id,
        status=status,
        maintenance_type=maintenance_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ════════════════════════════════════════════════════════════════
# UPCOMING MAINTENANCE (planifiees dans les X jours)
# ════════════════════════════════════════════════════════════════

@router.get("/maintenance/upcoming", response_model=list[MaintenanceResponse])
def get_upcoming_maintenance_route(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_upcoming_maintenance(db, days=days)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE BY EQUIPMENT
# ════════════════════════════════════════════════════════════════

@router.get("/maintenance/equipment/{equipment_id}", response_model=list[MaintenanceResponse])
def get_maintenance_by_equipment_route(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_maintenance_by_equipment(db, equipment_id)


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance_route(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_maintenance_by_id(db, maintenance_id)


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

@router.post("/maintenance/", response_model=MaintenanceResponse)
def create_maintenance_route(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_maintenance(db, data, current_user.id, current_user.username)
    log_action(db, current_user.id, "create", "inventory_maintenance", result.id)
    return result


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

@router.put("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance_route(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_maintenance(db, maintenance_id, data, current_user.id)
    log_action(db, current_user.id, "update", "inventory_maintenance", maintenance_id)
    return result


# ════════════════════════════════════════════════════════════════
# DELETE (soft delete)
# ════════════════════════════════════════════════════════════════

@router.delete("/maintenance/{maintenance_id}", response_model=bool)
def delete_maintenance_route(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = delete_maintenance(db, maintenance_id)
    log_action(db, current_user.id, "delete", "inventory_maintenance", maintenance_id)
    return result

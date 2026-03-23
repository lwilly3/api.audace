from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_equipment import (
    create_equipment, get_equipment_list, get_equipment_by_id,
    update_equipment, archive_equipment, restore_equipment, delete_equipment,
    get_inventory_stats, peek_next_reference,
    add_document, delete_document,
)
from app.schemas.schema_inventory_equipment import (
    EquipmentCreate, EquipmentResponse, EquipmentUpdate,
    EquipmentListResponse, InventoryStatsResponse, NextReferenceResponse,
    DocumentCreate, DocumentResponse, ArchiveBody,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-equipment"]
)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT LIST
# ════════════════════════════════════════════════════════════════

@router.get("/equipment/", response_model=EquipmentListResponse)
def get_equipment_list_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    status_id: int | None = Query(None),
    condition_id: int | None = Query(None),
    company_id: int | None = Query(None),
    site_id: int | None = Query(None),
    room_id: int | None = Query(None),
    is_archived: bool = Query(False),
    is_consumable: bool | None = Query(None),
    low_stock: bool | None = Query(None),
    assigned_to_user_id: int | None = Query(None),
    is_assigned: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_equipment_list(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status_id=status_id,
        condition_id=condition_id,
        company_id=company_id,
        site_id=site_id,
        room_id=room_id,
        is_archived=is_archived,
        is_consumable=is_consumable,
        low_stock=low_stock,
        assigned_to_user_id=assigned_to_user_id,
        is_assigned=is_assigned,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ════════════════════════════════════════════════════════════════
# STATS
# ════════════════════════════════════════════════════════════════

@router.get("/equipment/stats", response_model=InventoryStatsResponse)
def get_inventory_stats_route(
    company_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_inventory_stats(db, company_id)


# ════════════════════════════════════════════════════════════════
# NEXT REFERENCE
# ════════════════════════════════════════════════════════════════

@router.get("/equipment/next-reference", response_model=NextReferenceResponse)
def get_next_reference_route(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    ref = peek_next_reference(db)
    return NextReferenceResponse(reference=ref)


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_route(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_equipment_by_id(db, equipment_id)


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

@router.post("/equipment/", response_model=EquipmentResponse)
def create_equipment_route(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_equipment(db, data, current_user.id, current_user.username)
    log_action(db, current_user.id, "create", "inventory_equipment", result.id)
    return result


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment_route(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_equipment(db, equipment_id, data, current_user.id)
    log_action(db, current_user.id, "update", "inventory_equipment", equipment_id)
    return result


# ════════════════════════════════════════════════════════════════
# ARCHIVE / RESTORE
# ════════════════════════════════════════════════════════════════

@router.put("/equipment/{equipment_id}/archive", response_model=EquipmentResponse)
def archive_equipment_route(
    equipment_id: int,
    body: ArchiveBody,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = archive_equipment(db, equipment_id, body.reason, current_user.id)
    log_action(db, current_user.id, "archive", "inventory_equipment", equipment_id)
    return result


@router.put("/equipment/{equipment_id}/restore", response_model=EquipmentResponse)
def restore_equipment_route(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = restore_equipment(db, equipment_id, current_user.id)
    log_action(db, current_user.id, "restore", "inventory_equipment", equipment_id)
    return result


# ════════════════════════════════════════════════════════════════
# DELETE
# ════════════════════════════════════════════════════════════════

@router.delete("/equipment/{equipment_id}", response_model=bool)
def delete_equipment_route(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = delete_equipment(db, equipment_id)
    log_action(db, current_user.id, "delete", "inventory_equipment", equipment_id)
    return result


# ════════════════════════════════════════════════════════════════
# DOCUMENTS
# ════════════════════════════════════════════════════════════════

@router.post("/equipment/{equipment_id}/documents", response_model=DocumentResponse)
def add_document_route(
    equipment_id: int,
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = add_document(db, equipment_id, data, current_user.id, current_user.username)
    log_action(db, current_user.id, "create", "inventory_documents", result.id)
    return result


@router.delete("/equipment/{equipment_id}/documents/{document_id}", response_model=bool)
def delete_document_route(
    equipment_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = delete_document(db, document_id)
    log_action(db, current_user.id, "delete", "inventory_documents", document_id)
    return result

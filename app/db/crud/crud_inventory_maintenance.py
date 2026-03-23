from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_maintenance import InventoryMaintenance
from app.models.model_inventory_equipment import InventoryEquipment
from app.schemas.schema_inventory_maintenance import (
    MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate,
    MaintenanceListResponse,
)


# ════════════════════════════════════════════════════════════════
# HELPER : enrichir la response avec les noms de l'equipement
# ════════════════════════════════════════════════════════════════

def _build_maintenance_response(m: InventoryMaintenance) -> MaintenanceResponse:
    """Construit un MaintenanceResponse enrichi des noms de l'equipement."""
    resp = MaintenanceResponse.model_validate(m)
    if m.equipment:
        resp.equipment_name = m.equipment.name
        resp.equipment_reference = m.equipment.reference
    return resp


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

def create_maintenance(
    db: Session,
    data: MaintenanceCreate,
    user_id: int,
    user_name: str,
) -> MaintenanceResponse:
    try:
        # Verifier que l'equipement existe
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == data.equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        maintenance = InventoryMaintenance(
            equipment_id=data.equipment_id,
            type=data.type,
            title=data.title,
            description=data.description,
            scheduled_date=data.scheduled_date,
            start_date=data.start_date,
            end_date=data.end_date,
            estimated_duration=data.estimated_duration,
            actual_duration=data.actual_duration,
            performer_type=data.performer_type,
            performer_user_id=data.performer_user_id,
            performer_user_name=data.performer_user_name,
            performer_company=data.performer_company,
            performer_contact=data.performer_contact,
            cost_labor=data.cost_labor,
            cost_parts=data.cost_parts,
            cost_other=data.cost_other,
            cost_total=data.cost_total,
            cost_currency=data.cost_currency,
            parts_used_json=data.parts_used_json,
            status=data.status,
            result=data.result,
            findings=data.findings,
            recommendations=data.recommendations,
            next_maintenance_date=data.next_maintenance_date,
            attachments_json=data.attachments_json,
            created_by=user_id,
            created_by_name=user_name,
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)

        # Eager-load equipment relationship for response
        maintenance = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(InventoryMaintenance.id == maintenance.id).first()

        return _build_maintenance_response(maintenance)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation maintenance: {str(e)}")


# ════════════════════════════════════════════════════════════════
# LIST (pagination, filtres)
# ════════════════════════════════════════════════════════════════

def get_maintenance_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    equipment_id: int | None = None,
    status: str | None = None,
    maintenance_type: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> MaintenanceListResponse:
    try:
        query = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(
            InventoryMaintenance.is_deleted == False,
        )

        if equipment_id is not None:
            query = query.filter(InventoryMaintenance.equipment_id == equipment_id)
        if status is not None:
            query = query.filter(InventoryMaintenance.status == status)
        if maintenance_type is not None:
            query = query.filter(InventoryMaintenance.type == maintenance_type)

        # Count
        count_query = db.query(sa_func.count(InventoryMaintenance.id)).filter(
            InventoryMaintenance.is_deleted == False,
        )
        if equipment_id is not None:
            count_query = count_query.filter(InventoryMaintenance.equipment_id == equipment_id)
        if status is not None:
            count_query = count_query.filter(InventoryMaintenance.status == status)
        if maintenance_type is not None:
            count_query = count_query.filter(InventoryMaintenance.type == maintenance_type)
        total = count_query.scalar()

        # Tri
        allowed_sort_fields = {
            "created_at": InventoryMaintenance.created_at,
            "scheduled_date": InventoryMaintenance.scheduled_date,
            "start_date": InventoryMaintenance.start_date,
            "end_date": InventoryMaintenance.end_date,
            "title": InventoryMaintenance.title,
            "status": InventoryMaintenance.status,
            "type": InventoryMaintenance.type,
            "cost_total": InventoryMaintenance.cost_total,
            "updated_at": InventoryMaintenance.updated_at,
        }
        sort_column = allowed_sort_fields.get(sort_by, InventoryMaintenance.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return MaintenanceListResponse(
            items=[_build_maintenance_response(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation maintenances: {str(e)}")


# ════════════════════════════════════════════════════════════════
# GET BY EQUIPMENT ID (toutes les maintenances d'un equipement)
# ════════════════════════════════════════════════════════════════

def get_maintenance_by_equipment(
    db: Session,
    equipment_id: int,
) -> list[MaintenanceResponse]:
    try:
        items = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(
            InventoryMaintenance.equipment_id == equipment_id,
            InventoryMaintenance.is_deleted == False,
        ).order_by(InventoryMaintenance.created_at.desc()).all()

        return [_build_maintenance_response(m) for m in items]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation maintenances equipement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

def get_maintenance_by_id(db: Session, maintenance_id: int) -> MaintenanceResponse:
    maintenance = db.query(InventoryMaintenance).options(
        joinedload(InventoryMaintenance.equipment),
    ).filter(
        InventoryMaintenance.id == maintenance_id,
        InventoryMaintenance.is_deleted == False,
    ).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Enregistrement de maintenance non trouve")
    return _build_maintenance_response(maintenance)


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

def update_maintenance(
    db: Session,
    maintenance_id: int,
    data: MaintenanceUpdate,
    user_id: int,
) -> MaintenanceResponse:
    try:
        maintenance = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(
            InventoryMaintenance.id == maintenance_id,
            InventoryMaintenance.is_deleted == False,
        ).first()
        if not maintenance:
            raise HTTPException(status_code=404, detail="Enregistrement de maintenance non trouve")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(maintenance, field, value)

        db.commit()
        db.refresh(maintenance)

        # Recharger la relation
        maintenance = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(InventoryMaintenance.id == maintenance_id).first()

        return _build_maintenance_response(maintenance)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour maintenance: {str(e)}")


# ════════════════════════════════════════════════════════════════
# UPCOMING MAINTENANCE (maintenances planifiees dans les X jours)
# ════════════════════════════════════════════════════════════════

def get_upcoming_maintenance(
    db: Session,
    days: int = 30,
) -> list[MaintenanceResponse]:
    """
    Retourne les maintenances planifiees (status=scheduled) dont la date
    prevue est dans les `days` prochains jours.
    """
    try:
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=days)

        items = db.query(InventoryMaintenance).options(
            joinedload(InventoryMaintenance.equipment),
        ).filter(
            InventoryMaintenance.is_deleted == False,
            InventoryMaintenance.status == 'scheduled',
            InventoryMaintenance.scheduled_date.isnot(None),
            InventoryMaintenance.scheduled_date >= now,
            InventoryMaintenance.scheduled_date <= deadline,
        ).order_by(InventoryMaintenance.scheduled_date.asc()).all()

        return [_build_maintenance_response(m) for m in items]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation maintenances a venir: {str(e)}")


# ════════════════════════════════════════════════════════════════
# DELETE (soft delete)
# ════════════════════════════════════════════════════════════════

def delete_maintenance(db: Session, maintenance_id: int) -> bool:
    try:
        maintenance = db.query(InventoryMaintenance).filter(
            InventoryMaintenance.id == maintenance_id,
        ).first()
        if not maintenance:
            raise HTTPException(status_code=404, detail="Enregistrement de maintenance non trouve")

        maintenance.is_deleted = True
        maintenance.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression maintenance: {str(e)}")

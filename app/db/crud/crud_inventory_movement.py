from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func as sa_func
from fastapi import HTTPException, status
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_movement import InventoryMovement
from app.models.model_inventory_equipment import InventoryEquipment
from app.models.model_inventory_settings import InventoryConfigOption
from app.models.model_inventory_company import InventoryCompany
from app.models.model_inventory_site import InventorySite
from app.models.model_inventory_room import InventoryRoom
from app.schemas.schema_inventory_movement import (
    MovementCreate, MovementResponse, MovementListResponse,
)


# ════════════════════════════════════════════════════════════════
# HELPER : enrichir la response avec les noms des relations
# ════════════════════════════════════════════════════════════════

def _build_movement_response(mv: InventoryMovement) -> MovementResponse:
    """Construit un MovementResponse enrichi des noms issus des relations."""
    resp = MovementResponse.model_validate(mv)
    # Equipment
    if mv.equipment:
        resp.equipment_name = mv.equipment.name
        resp.equipment_reference = mv.equipment.reference
    # Movement type
    if mv.movement_type:
        resp.movement_type_name = mv.movement_type.name
    # From location names
    if mv.from_company:
        resp.from_company_name = mv.from_company.name
    if mv.from_site:
        resp.from_site_name = mv.from_site.name
    if mv.from_room:
        resp.from_room_name = mv.from_room.name
    # To location names
    if mv.to_company:
        resp.to_company_name = mv.to_company.name
    if mv.to_site:
        resp.to_site_name = mv.to_site.name
    if mv.to_room:
        resp.to_room_name = mv.to_room.name
    return resp


def _eager_load_movement(db: Session, movement_id: int) -> InventoryMovement:
    """Charge un mouvement avec toutes ses relations."""
    mv = db.query(InventoryMovement).options(
        joinedload(InventoryMovement.equipment),
        joinedload(InventoryMovement.movement_type),
        joinedload(InventoryMovement.from_company),
        joinedload(InventoryMovement.from_site),
        joinedload(InventoryMovement.from_room),
        joinedload(InventoryMovement.to_company),
        joinedload(InventoryMovement.to_site),
        joinedload(InventoryMovement.to_room),
    ).filter(
        InventoryMovement.id == movement_id,
        InventoryMovement.is_deleted == False,
    ).first()
    return mv


def _apply_movement_to_equipment(db: Session, mv: InventoryMovement) -> None:
    """
    Met a jour atomiquement la localisation et/ou l'affectation de l'equipement
    en fonction des donnees du mouvement. Remplace le writeBatch de Firestore.
    """
    equipment = db.query(InventoryEquipment).filter(
        InventoryEquipment.id == mv.equipment_id,
        InventoryEquipment.is_deleted == False,
    ).with_for_update().first()
    if not equipment:
        return

    # Mettre a jour la localisation si une destination est definie
    if mv.to_company_id is not None:
        equipment.company_id = mv.to_company_id
    if mv.to_site_id is not None:
        equipment.site_id = mv.to_site_id
    # room peut etre mis a null explicitement
    equipment.room_id = mv.to_room_id
    equipment.specific_location = mv.to_specific_location

    # Mettre a jour l'affectation utilisateur selon la categorie de mouvement
    assignment_categories = {
        'assignment', 'loan', 'mission_checkout', 'company_loan',
    }
    return_categories = {
        'return', 'loan_return', 'mission_checkin', 'company_loan_return',
    }

    if mv.movement_category in assignment_categories:
        if mv.to_user_id is not None:
            equipment.assigned_user_id = mv.to_user_id
            equipment.assigned_user_name = mv.to_user_name
            equipment.assigned_at = datetime.now(timezone.utc)
            equipment.assigned_by = mv.created_by
            equipment.expected_return_date = mv.expected_return_date
    elif mv.movement_category in return_categories:
        equipment.assigned_user_id = None
        equipment.assigned_user_name = None
        equipment.assigned_user_email = None
        equipment.assigned_at = None
        equipment.assigned_by = None
        equipment.expected_return_date = None
        equipment.assignment_notes = None

    db.flush()


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

def create_movement(
    db: Session,
    data: MovementCreate,
    user_id: int,
    user_name: str,
) -> MovementResponse:
    """
    Cree un mouvement d'equipement.

    Si requires_approval est False, le mouvement est immediatement 'completed'
    et la localisation/affectation de l'equipement est mise a jour dans la meme
    transaction (equivalent du writeBatch Firestore).

    Si requires_approval est True, le mouvement reste en 'pending' jusqu'a
    approbation.
    """
    try:
        # Verifier que l'equipement existe
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == data.equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        # Determiner le statut initial
        initial_status = 'pending' if data.requires_approval else 'completed'

        movement = InventoryMovement(
            equipment_id=data.equipment_id,
            movement_type_id=data.movement_type_id,
            movement_category=data.movement_category,
            mission_id=data.mission_id,
            mission_title=data.mission_title,
            mission_type=data.mission_type,
            from_company_id=data.from_company_id,
            from_site_id=data.from_site_id,
            from_room_id=data.from_room_id,
            from_user_id=data.from_user_id,
            from_user_name=data.from_user_name,
            from_specific_location=data.from_specific_location,
            to_company_id=data.to_company_id,
            to_site_id=data.to_site_id,
            to_room_id=data.to_room_id,
            to_user_id=data.to_user_id,
            to_user_name=data.to_user_name,
            to_specific_location=data.to_specific_location,
            to_external_location=data.to_external_location,
            date=data.date,
            expected_return_date=data.expected_return_date,
            reason=data.reason,
            notes=data.notes,
            status=initial_status,
            requires_approval=data.requires_approval,
            return_condition_json=data.return_condition_json,
            attachments_json=data.attachments_json,
            signature_url=data.signature_url,
            created_by=user_id,
            created_by_name=user_name,
        )
        db.add(movement)
        db.flush()

        # Si pas d'approbation requise, appliquer immediatement a l'equipement
        if not data.requires_approval:
            _apply_movement_to_equipment(db, movement)

        db.commit()
        db.refresh(movement)

        loaded = _eager_load_movement(db, movement.id)
        return _build_movement_response(loaded)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation mouvement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# LIST (pagination, filtres, tri)
# ════════════════════════════════════════════════════════════════

def get_movement_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    equipment_id: int | None = None,
    movement_category: str | None = None,
    status: str | None = None,
    from_company_id: int | None = None,
    to_company_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    sort_by: str = "date",
    sort_dir: str = "desc",
) -> MovementListResponse:
    try:
        query = db.query(InventoryMovement).options(
            joinedload(InventoryMovement.equipment),
            joinedload(InventoryMovement.movement_type),
            joinedload(InventoryMovement.from_company),
            joinedload(InventoryMovement.from_site),
            joinedload(InventoryMovement.from_room),
            joinedload(InventoryMovement.to_company),
            joinedload(InventoryMovement.to_site),
            joinedload(InventoryMovement.to_room),
        ).filter(
            InventoryMovement.is_deleted == False,
        )

        # Filtres
        if equipment_id is not None:
            query = query.filter(InventoryMovement.equipment_id == equipment_id)
        if movement_category is not None:
            query = query.filter(InventoryMovement.movement_category == movement_category)
        if status is not None:
            query = query.filter(InventoryMovement.status == status)
        if from_company_id is not None:
            query = query.filter(InventoryMovement.from_company_id == from_company_id)
        if to_company_id is not None:
            query = query.filter(InventoryMovement.to_company_id == to_company_id)
        if date_from is not None:
            query = query.filter(InventoryMovement.date >= date_from)
        if date_to is not None:
            query = query.filter(InventoryMovement.date <= date_to)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    InventoryMovement.reason.ilike(search_pattern),
                    InventoryMovement.notes.ilike(search_pattern),
                    InventoryMovement.from_user_name.ilike(search_pattern),
                    InventoryMovement.to_user_name.ilike(search_pattern),
                )
            )

        # Count
        count_query = db.query(sa_func.count(InventoryMovement.id)).filter(
            InventoryMovement.is_deleted == False,
        )
        if equipment_id is not None:
            count_query = count_query.filter(InventoryMovement.equipment_id == equipment_id)
        if movement_category is not None:
            count_query = count_query.filter(InventoryMovement.movement_category == movement_category)
        if status is not None:
            count_query = count_query.filter(InventoryMovement.status == status)
        if from_company_id is not None:
            count_query = count_query.filter(InventoryMovement.from_company_id == from_company_id)
        if to_company_id is not None:
            count_query = count_query.filter(InventoryMovement.to_company_id == to_company_id)
        if date_from is not None:
            count_query = count_query.filter(InventoryMovement.date >= date_from)
        if date_to is not None:
            count_query = count_query.filter(InventoryMovement.date <= date_to)
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.filter(
                or_(
                    InventoryMovement.reason.ilike(search_pattern),
                    InventoryMovement.notes.ilike(search_pattern),
                    InventoryMovement.from_user_name.ilike(search_pattern),
                    InventoryMovement.to_user_name.ilike(search_pattern),
                )
            )
        total = count_query.scalar()

        # Tri
        allowed_sort_fields = {
            "date": InventoryMovement.date,
            "created_at": InventoryMovement.created_at,
            "status": InventoryMovement.status,
            "movement_category": InventoryMovement.movement_category,
        }
        sort_column = allowed_sort_fields.get(sort_by, InventoryMovement.date)
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * page_size
        movements = query.offset(offset).limit(page_size).all()

        items = [_build_movement_response(mv) for mv in movements]
        return MovementListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation mouvements: {str(e)}")


# ════════════════════════════════════════════════════════════════
# PENDING MOVEMENTS
# ════════════════════════════════════════════════════════════════

def get_pending_movements(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> MovementListResponse:
    """Retourne les mouvements en attente d'approbation."""
    return get_movement_list(
        db,
        page=page,
        page_size=page_size,
        status="pending",
        sort_by="created_at",
        sort_dir="asc",
    )


# ════════════════════════════════════════════════════════════════
# EQUIPMENT MOVEMENTS
# ════════════════════════════════════════════════════════════════

def get_equipment_movements(
    db: Session,
    equipment_id: int,
    page: int = 1,
    page_size: int = 50,
) -> MovementListResponse:
    """Retourne les mouvements d'un equipement specifique."""
    return get_movement_list(
        db,
        page=page,
        page_size=page_size,
        equipment_id=equipment_id,
        sort_by="date",
        sort_dir="desc",
    )


# ════════════════════════════════════════════════════════════════
# APPROVE
# ════════════════════════════════════════════════════════════════

def approve_movement(
    db: Session,
    movement_id: int,
    user_id: int,
    user_name: str,
) -> MovementResponse:
    """
    Approuve un mouvement en attente.

    Passe le statut a 'completed' et applique les modifications
    de localisation/affectation a l'equipement de maniere atomique.
    """
    try:
        movement = db.query(InventoryMovement).filter(
            InventoryMovement.id == movement_id,
            InventoryMovement.is_deleted == False,
        ).first()
        if not movement:
            raise HTTPException(status_code=404, detail="Mouvement non trouve")
        if movement.status != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Impossible d'approuver un mouvement en statut '{movement.status}'"
            )

        movement.status = 'completed'
        movement.approved_by = user_id
        movement.approved_by_name = user_name
        movement.approved_at = datetime.now(timezone.utc)

        # Appliquer les modifications a l'equipement
        _apply_movement_to_equipment(db, movement)

        db.commit()
        db.refresh(movement)

        loaded = _eager_load_movement(db, movement.id)
        return _build_movement_response(loaded)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur approbation mouvement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# REJECT
# ════════════════════════════════════════════════════════════════

def reject_movement(
    db: Session,
    movement_id: int,
    user_id: int,
    user_name: str,
    reason: str,
) -> MovementResponse:
    """
    Rejette un mouvement en attente.
    L'equipement n'est PAS modifie.
    """
    try:
        movement = db.query(InventoryMovement).filter(
            InventoryMovement.id == movement_id,
            InventoryMovement.is_deleted == False,
        ).first()
        if not movement:
            raise HTTPException(status_code=404, detail="Mouvement non trouve")
        if movement.status != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de rejeter un mouvement en statut '{movement.status}'"
            )

        movement.status = 'rejected'
        movement.approved_by = user_id
        movement.approved_by_name = user_name
        movement.approved_at = datetime.now(timezone.utc)
        movement.rejection_reason = reason

        db.commit()
        db.refresh(movement)

        loaded = _eager_load_movement(db, movement.id)
        return _build_movement_response(loaded)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur rejet mouvement: {str(e)}")

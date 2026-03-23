from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func as sa_func, case
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_equipment import InventoryEquipment
from app.models.model_inventory_document import InventoryDocument
from app.models.model_inventory_settings import InventoryConfigOption, InventoryGlobalSettings
from app.models.model_inventory_company import InventoryCompany
from app.models.model_inventory_site import InventorySite
from app.models.model_inventory_room import InventoryRoom
from app.schemas.schema_inventory_equipment import (
    EquipmentCreate, EquipmentResponse, EquipmentUpdate, EquipmentBrief,
    EquipmentListResponse, DocumentCreate, DocumentResponse,
    InventoryStatsResponse, NextReferenceResponse,
)


# ════════════════════════════════════════════════════════════════
# REFERENCE AUTO-INCREMENT
# ════════════════════════════════════════════════════════════════

def get_next_reference(db: Session) -> str:
    """
    Genere la prochaine reference au format 'INV-XXXX' de maniere atomique.

    Utilise SELECT FOR UPDATE sur le parametre global reference_counter
    pour garantir l'unicite meme en cas d'acces concurrent.
    """
    try:
        # Recuperer le prefixe
        prefix_setting = db.query(InventoryGlobalSettings).filter(
            InventoryGlobalSettings.key == "reference_prefix"
        ).first()
        prefix = prefix_setting.value if prefix_setting else "INV"

        # Recuperer et incrementer le compteur de maniere atomique
        counter_setting = db.query(InventoryGlobalSettings).filter(
            InventoryGlobalSettings.key == "reference_counter"
        ).with_for_update().first()

        if not counter_setting:
            raise HTTPException(
                status_code=500,
                detail="Parametre reference_counter introuvable. Lancez l'initialisation des parametres."
            )

        new_counter = int(counter_setting.value) + 1
        counter_setting.value = str(new_counter)
        db.flush()

        return f"{prefix}-{new_counter:04d}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur generation reference: {str(e)}")


def peek_next_reference(db: Session) -> str:
    """
    Retourne la prochaine reference SANS incrementer le compteur.
    Utile pour l'affichage dans le formulaire de creation.
    """
    try:
        prefix_setting = db.query(InventoryGlobalSettings).filter(
            InventoryGlobalSettings.key == "reference_prefix"
        ).first()
        prefix = prefix_setting.value if prefix_setting else "INV"

        counter_setting = db.query(InventoryGlobalSettings).filter(
            InventoryGlobalSettings.key == "reference_counter"
        ).first()
        current = int(counter_setting.value) if counter_setting else 0

        return f"{prefix}-{current + 1:04d}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture reference: {str(e)}")


# ════════════════════════════════════════════════════════════════
# HELPER : enrichir la response avec les noms des relations
# ════════════════════════════════════════════════════════════════

def _build_equipment_response(eq: InventoryEquipment, include_documents: bool = False) -> EquipmentResponse:
    """Construit un EquipmentResponse enrichi des noms issus des relations."""
    resp = EquipmentResponse.model_validate(eq)
    resp.category_name = eq.category.name if eq.category else None
    resp.status_name = eq.status.name if eq.status else None
    resp.status_color = eq.status.color if eq.status else None
    resp.condition_name = eq.condition.name if eq.condition else None
    resp.company_name = eq.company.name if eq.company else None
    resp.site_name = eq.site.name if eq.site else None
    resp.room_name = eq.room.name if eq.room else None
    if include_documents and eq.documents:
        resp.documents = [
            DocumentResponse.model_validate(doc)
            for doc in eq.documents
            if not doc.is_deleted
        ]
    else:
        resp.documents = []
    return resp


def _build_equipment_brief(eq: InventoryEquipment) -> EquipmentBrief:
    """Construit un EquipmentBrief enrichi des noms issus des relations."""
    brief = EquipmentBrief.model_validate(eq)
    brief.category_name = eq.category.name if eq.category else None
    brief.status_name = eq.status.name if eq.status else None
    brief.status_color = eq.status.color if eq.status else None
    brief.condition_name = eq.condition.name if eq.condition else None
    brief.company_name = eq.company.name if eq.company else None
    brief.site_name = eq.site.name if eq.site else None
    brief.room_name = eq.room.name if eq.room else None
    return brief


# ════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════

def create_equipment(
    db: Session,
    data: EquipmentCreate,
    user_id: int,
    user_name: str,
) -> EquipmentResponse:
    try:
        # Generer la reference si absente
        reference = data.reference
        if not reference:
            reference = get_next_reference(db)

        equipment = InventoryEquipment(
            name=data.name,
            reference=reference,
            serial_number=data.serial_number,
            barcode=data.barcode,
            category_id=data.category_id,
            subcategory=data.subcategory,
            brand=data.brand,
            model_name=data.model_name,
            manufacturer=data.manufacturer,
            status_id=data.status_id,
            condition_id=data.condition_id,
            company_id=data.company_id,
            site_id=data.site_id,
            room_id=data.room_id,
            specific_location=data.specific_location,
            assigned_user_id=data.assigned_user_id,
            assigned_user_name=data.assigned_user_name,
            assigned_user_email=data.assigned_user_email,
            assigned_at=datetime.now(timezone.utc) if data.assigned_user_id else None,
            assigned_by=user_id if data.assigned_user_id else None,
            expected_return_date=data.expected_return_date,
            assignment_notes=data.assignment_notes,
            acquisition_date=data.acquisition_date,
            acquisition_type=data.acquisition_type,
            purchase_price=data.purchase_price,
            current_value=data.current_value,
            supplier=data.supplier,
            invoice_number=data.invoice_number,
            invoice_url=data.invoice_url,
            warranty_start_date=data.warranty_start_date,
            warranty_end_date=data.warranty_end_date,
            warranty_provider=data.warranty_provider,
            warranty_contract_number=data.warranty_contract_number,
            warranty_notes=data.warranty_notes,
            config_settings_json=data.config_settings_json,
            config_notes=data.config_notes,
            firmware_version=data.firmware_version,
            software_version=data.software_version,
            description=data.description,
            notes=data.notes,
            manual_url=data.manual_url,
            photos_json=data.photos_json if data.photos_json else [],
            specifications_json=data.specifications_json,
            is_consumable=data.is_consumable,
            quantity=data.quantity,
            min_quantity=data.min_quantity,
            unit=data.unit,
            created_by=user_id,
            created_by_name=user_name,
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)

        # Eager-load relationships for response
        equipment = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(InventoryEquipment.id == equipment.id).first()

        return _build_equipment_response(equipment)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation equipement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# LIST (pagination, filtres, tri, recherche)
# ════════════════════════════════════════════════════════════════

def get_equipment_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    category_id: int | None = None,
    status_id: int | None = None,
    condition_id: int | None = None,
    company_id: int | None = None,
    site_id: int | None = None,
    room_id: int | None = None,
    is_archived: bool = False,
    is_consumable: bool | None = None,
    low_stock: bool | None = None,
    assigned_to_user_id: int | None = None,
    is_assigned: bool | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> EquipmentListResponse:
    try:
        query = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(
            InventoryEquipment.is_deleted == False,
            InventoryEquipment.is_archived == is_archived,
        )

        # Filtres
        if category_id is not None:
            query = query.filter(InventoryEquipment.category_id == category_id)
        if status_id is not None:
            query = query.filter(InventoryEquipment.status_id == status_id)
        if condition_id is not None:
            query = query.filter(InventoryEquipment.condition_id == condition_id)
        if company_id is not None:
            query = query.filter(InventoryEquipment.company_id == company_id)
        if site_id is not None:
            query = query.filter(InventoryEquipment.site_id == site_id)
        if room_id is not None:
            query = query.filter(InventoryEquipment.room_id == room_id)
        if is_consumable is not None:
            query = query.filter(InventoryEquipment.is_consumable == is_consumable)
        if assigned_to_user_id is not None:
            query = query.filter(InventoryEquipment.assigned_user_id == assigned_to_user_id)
        if is_assigned is True:
            query = query.filter(InventoryEquipment.assigned_user_id.isnot(None))
        elif is_assigned is False:
            query = query.filter(InventoryEquipment.assigned_user_id.is_(None))
        if low_stock is True:
            query = query.filter(
                InventoryEquipment.is_consumable == True,
                InventoryEquipment.quantity.isnot(None),
                InventoryEquipment.min_quantity.isnot(None),
                InventoryEquipment.quantity <= InventoryEquipment.min_quantity,
            )

        # Recherche texte (ILIKE)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    InventoryEquipment.name.ilike(search_pattern),
                    InventoryEquipment.reference.ilike(search_pattern),
                    InventoryEquipment.serial_number.ilike(search_pattern),
                    InventoryEquipment.brand.ilike(search_pattern),
                    InventoryEquipment.model_name.ilike(search_pattern),
                    InventoryEquipment.barcode.ilike(search_pattern),
                )
            )

        # Compter le total AVANT pagination (sur la requete filtree sans joinedload)
        count_query = db.query(sa_func.count(InventoryEquipment.id)).filter(
            InventoryEquipment.is_deleted == False,
            InventoryEquipment.is_archived == is_archived,
        )
        # Reproduire les memes filtres pour le count
        if category_id is not None:
            count_query = count_query.filter(InventoryEquipment.category_id == category_id)
        if status_id is not None:
            count_query = count_query.filter(InventoryEquipment.status_id == status_id)
        if condition_id is not None:
            count_query = count_query.filter(InventoryEquipment.condition_id == condition_id)
        if company_id is not None:
            count_query = count_query.filter(InventoryEquipment.company_id == company_id)
        if site_id is not None:
            count_query = count_query.filter(InventoryEquipment.site_id == site_id)
        if room_id is not None:
            count_query = count_query.filter(InventoryEquipment.room_id == room_id)
        if is_consumable is not None:
            count_query = count_query.filter(InventoryEquipment.is_consumable == is_consumable)
        if assigned_to_user_id is not None:
            count_query = count_query.filter(InventoryEquipment.assigned_user_id == assigned_to_user_id)
        if is_assigned is True:
            count_query = count_query.filter(InventoryEquipment.assigned_user_id.isnot(None))
        elif is_assigned is False:
            count_query = count_query.filter(InventoryEquipment.assigned_user_id.is_(None))
        if low_stock is True:
            count_query = count_query.filter(
                InventoryEquipment.is_consumable == True,
                InventoryEquipment.quantity.isnot(None),
                InventoryEquipment.min_quantity.isnot(None),
                InventoryEquipment.quantity <= InventoryEquipment.min_quantity,
            )
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.filter(
                or_(
                    InventoryEquipment.name.ilike(search_pattern),
                    InventoryEquipment.reference.ilike(search_pattern),
                    InventoryEquipment.serial_number.ilike(search_pattern),
                    InventoryEquipment.brand.ilike(search_pattern),
                    InventoryEquipment.model_name.ilike(search_pattern),
                    InventoryEquipment.barcode.ilike(search_pattern),
                )
            )
        total = count_query.scalar()

        # Tri
        allowed_sort_fields = {
            "created_at": InventoryEquipment.created_at,
            "name": InventoryEquipment.name,
            "reference": InventoryEquipment.reference,
            "brand": InventoryEquipment.brand,
            "model_name": InventoryEquipment.model_name,
            "acquisition_date": InventoryEquipment.acquisition_date,
            "purchase_price": InventoryEquipment.purchase_price,
            "quantity": InventoryEquipment.quantity,
            "updated_at": InventoryEquipment.updated_at,
        }
        sort_column = allowed_sort_fields.get(sort_by, InventoryEquipment.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * page_size
        equipment_list = query.offset(offset).limit(page_size).all()

        items = [_build_equipment_brief(eq) for eq in equipment_list]
        return EquipmentListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation equipements: {str(e)}")


# ════════════════════════════════════════════════════════════════
# GET BY ID
# ════════════════════════════════════════════════════════════════

def get_equipment_by_id(db: Session, equipment_id: int) -> EquipmentResponse:
    equipment = db.query(InventoryEquipment).options(
        joinedload(InventoryEquipment.category),
        joinedload(InventoryEquipment.status),
        joinedload(InventoryEquipment.condition),
        joinedload(InventoryEquipment.company),
        joinedload(InventoryEquipment.site),
        joinedload(InventoryEquipment.room),
        joinedload(InventoryEquipment.documents),
    ).filter(
        InventoryEquipment.id == equipment_id,
        InventoryEquipment.is_deleted == False,
    ).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipement non trouve")
    return _build_equipment_response(equipment, include_documents=True)


# ════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════

def update_equipment(
    db: Session,
    equipment_id: int,
    data: EquipmentUpdate,
    user_id: int,
) -> EquipmentResponse:
    try:
        equipment = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(
            InventoryEquipment.id == equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)
        equipment.updated_by = user_id

        db.commit()
        db.refresh(equipment)

        # Recharger les relations
        equipment = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(InventoryEquipment.id == equipment_id).first()

        return _build_equipment_response(equipment)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour equipement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# ARCHIVE / RESTORE
# ════════════════════════════════════════════════════════════════

def archive_equipment(db: Session, equipment_id: int, reason: str | None, user_id: int) -> EquipmentResponse:
    try:
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        equipment.is_archived = True
        equipment.archived_at = datetime.now(timezone.utc)
        equipment.archived_reason = reason
        equipment.updated_by = user_id
        db.commit()
        db.refresh(equipment)

        # Recharger les relations
        equipment = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(InventoryEquipment.id == equipment_id).first()

        return _build_equipment_response(equipment)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur archivage equipement: {str(e)}")


def restore_equipment(db: Session, equipment_id: int, user_id: int) -> EquipmentResponse:
    try:
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        equipment.is_archived = False
        equipment.archived_at = None
        equipment.archived_reason = None
        equipment.updated_by = user_id
        db.commit()
        db.refresh(equipment)

        equipment = db.query(InventoryEquipment).options(
            joinedload(InventoryEquipment.category),
            joinedload(InventoryEquipment.status),
            joinedload(InventoryEquipment.condition),
            joinedload(InventoryEquipment.company),
            joinedload(InventoryEquipment.site),
            joinedload(InventoryEquipment.room),
        ).filter(InventoryEquipment.id == equipment_id).first()

        return _build_equipment_response(equipment)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur restauration equipement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# DELETE (hard delete)
# ════════════════════════════════════════════════════════════════

def delete_equipment(db: Session, equipment_id: int) -> bool:
    try:
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == equipment_id,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")
        db.delete(equipment)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression equipement: {str(e)}")


# ════════════════════════════════════════════════════════════════
# STATS
# ════════════════════════════════════════════════════════════════

def get_inventory_stats(db: Session, company_id: int | None = None) -> InventoryStatsResponse:
    """Retourne des statistiques agregees sur l'inventaire."""
    try:
        base_filter = [
            InventoryEquipment.is_deleted == False,
            InventoryEquipment.is_archived == False,
        ]
        if company_id is not None:
            base_filter.append(InventoryEquipment.company_id == company_id)

        # Total count
        total_count = db.query(sa_func.count(InventoryEquipment.id)).filter(
            *base_filter
        ).scalar() or 0

        # Par statut
        status_rows = db.query(
            InventoryConfigOption.id,
            InventoryConfigOption.name,
            InventoryConfigOption.color,
            sa_func.count(InventoryEquipment.id).label("count"),
        ).join(
            InventoryEquipment, InventoryEquipment.status_id == InventoryConfigOption.id
        ).filter(
            *base_filter
        ).group_by(
            InventoryConfigOption.id, InventoryConfigOption.name, InventoryConfigOption.color
        ).all()
        by_status = [
            {"id": row.id, "name": row.name, "color": row.color, "count": row.count}
            for row in status_rows
        ]

        # Par categorie
        category_rows = db.query(
            InventoryConfigOption.id,
            InventoryConfigOption.name,
            sa_func.count(InventoryEquipment.id).label("count"),
        ).join(
            InventoryEquipment, InventoryEquipment.category_id == InventoryConfigOption.id
        ).filter(
            *base_filter
        ).group_by(
            InventoryConfigOption.id, InventoryConfigOption.name
        ).all()
        by_category = [
            {"id": row.id, "name": row.name, "count": row.count}
            for row in category_rows
        ]

        # Par entreprise
        company_rows = db.query(
            InventoryCompany.id,
            InventoryCompany.name,
            sa_func.count(InventoryEquipment.id).label("count"),
        ).join(
            InventoryEquipment, InventoryEquipment.company_id == InventoryCompany.id
        ).filter(
            *base_filter
        ).group_by(
            InventoryCompany.id, InventoryCompany.name
        ).all()
        by_company = [
            {"id": row.id, "name": row.name, "count": row.count}
            for row in company_rows
        ]

        # Valeur totale
        total_value = db.query(
            sa_func.coalesce(sa_func.sum(InventoryEquipment.current_value), 0.0)
        ).filter(*base_filter).scalar() or 0.0

        # Consommables en stock bas
        low_stock_count = db.query(sa_func.count(InventoryEquipment.id)).filter(
            *base_filter,
            InventoryEquipment.is_consumable == True,
            InventoryEquipment.quantity.isnot(None),
            InventoryEquipment.min_quantity.isnot(None),
            InventoryEquipment.quantity <= InventoryEquipment.min_quantity,
        ).scalar() or 0

        # Retours en retard
        now = datetime.now(timezone.utc)
        overdue_returns_count = db.query(sa_func.count(InventoryEquipment.id)).filter(
            *base_filter,
            InventoryEquipment.assigned_user_id.isnot(None),
            InventoryEquipment.expected_return_date.isnot(None),
            InventoryEquipment.expected_return_date < now,
        ).scalar() or 0

        return InventoryStatsResponse(
            total_count=total_count,
            by_status=by_status,
            by_category=by_category,
            by_company=by_company,
            total_value=float(total_value),
            low_stock_count=low_stock_count,
            overdue_returns_count=overdue_returns_count,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation statistiques: {str(e)}")


# ════════════════════════════════════════════════════════════════
# DOCUMENTS
# ════════════════════════════════════════════════════════════════

def add_document(
    db: Session,
    equipment_id: int,
    data: DocumentCreate,
    user_id: int,
    user_name: str,
) -> DocumentResponse:
    try:
        # Verifier que l'equipement existe
        equipment = db.query(InventoryEquipment).filter(
            InventoryEquipment.id == equipment_id,
            InventoryEquipment.is_deleted == False,
        ).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipement non trouve")

        document = InventoryDocument(
            equipment_id=equipment_id,
            file_name=data.file_name,
            display_name=data.display_name,
            description=data.description,
            document_type=data.document_type,
            mime_type=data.mime_type,
            file_size=data.file_size,
            storage_url=data.storage_url,
            storage_path=data.storage_path,
            thumbnail_url=data.thumbnail_url,
            access_level=data.access_level,
            version=data.version,
            is_latest=data.is_latest,
            previous_version_id=data.previous_version_id,
            tags_json=data.tags_json,
            language=data.language,
            expires_at=data.expires_at,
            uploaded_by=user_id,
            uploaded_by_name=user_name,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return DocumentResponse.model_validate(document)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur ajout document: {str(e)}")


def delete_document(db: Session, document_id: int) -> bool:
    try:
        document = db.query(InventoryDocument).filter(
            InventoryDocument.id == document_id,
        ).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouve")
        db.delete(document)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression document: {str(e)}")

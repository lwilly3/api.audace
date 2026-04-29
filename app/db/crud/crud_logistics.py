"""
CRUD operations pour le module Logistique.

Gestion des véhicules, chauffeurs, équipes et paramètres.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func as sa_func
from fastapi import HTTPException, status
from datetime import datetime, timezone
from decimal import Decimal

from app.models.model_logistics_vehicle import LogisticsVehicle
from app.models.model_logistics_vehicle_extras import LogisticsVehicleCompartment, LogisticsVehicleAssociation
from app.models.model_logistics_driver_team import LogisticsDriver, LogisticsTeam, LogisticsMechanic, LogisticsInvitation
from app.models.model_logistics_operations import LogisticsMission, LogisticsMissionCheckpoint, LogisticsFuelLog, LogisticsMaintenance
from app.models.model_logistics_settings import LogisticsConfigOption, LogisticsGlobalSettings
from app.models.model_inventory_company import InventoryCompany
from app.models.model_user import User
from app.models.model_user_permissions import UserPermissions
from app.schemas.schema_logistics import (
    VehicleCreate, VehicleResponse, VehicleUpdate, VehicleListResponse,
    CompartmentCreate, CompartmentUpdate, CompartmentResponse,
    VehicleAssociationCreate, VehicleAssociationUpdate, VehicleAssociationResponse,
    DriverCreate, DriverResponse, DriverUpdate, DriverListResponse,
    TeamCreate, TeamResponse, TeamUpdate, TeamListResponse, TeamDetailResponse,
    ConfigOptionCreate, ConfigOptionUpdate, ConfigOptionResponse,
    NextReferenceResponse, LogisticsDashboardStats, LogisticsDashboardResponse,
    AlertSummary,
    MissionCreate, MissionResponse, MissionUpdate, MissionListResponse,
    MissionCompleteRequest, MissionRejectRequest,
    CheckpointCreate, CheckpointResponse,
    FuelLogCreate, FuelLogResponse, FuelLogUpdate, FuelLogListResponse,
    FuelAlertResponse, FuelAlertListResponse,
    DriverUserCreate, DriverUserResponse, DriverUserListResponse,
    MechanicCreate, MechanicUpdate, MechanicResponse, MechanicListResponse, MechanicSummary,
    InviteCreateRequest, InviteResponse, InviteValidateResponse, InviteAcceptRequest, LinkUserRequest,
    MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse, MaintenanceListResponse,
)
from typing import Optional, List
import uuid
from datetime import timedelta


# ════════════════════════════════════════════════════════════════
# UTILS: REFERENCE AUTO-INCREMENT
# ════════════════════════════════════════════════════════════════

def get_next_vehicle_reference(db: Session) -> str:
    """Génère la prochaine référence véhicule au format 'LOG-XXXX'."""
    try:
        prefix_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_prefix_vehicle"
        ).with_for_update().first()

        if not prefix_setting:
            raise HTTPException(
                status_code=500,
                detail="Paramètre reference_prefix_vehicle introuvable."
            )

        prefix = prefix_setting.value

        counter_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_counter_vehicle"
        ).with_for_update().first()

        if not counter_setting:
            raise HTTPException(
                status_code=500,
                detail="Paramètre reference_counter_vehicle introuvable."
            )

        new_counter = int(counter_setting.value) + 1
        counter_setting.value = str(new_counter)
        db.flush()

        return f"{prefix}-{new_counter:04d}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération référence: {str(e)}")


def peek_next_vehicle_reference(db: Session) -> str:
    """Retourne la prochaine référence SANS l'incrémenter."""
    try:
        prefix_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_prefix_vehicle"
        ).first()
        prefix = prefix_setting.value if prefix_setting else "LOG"

        counter_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_counter_vehicle"
        ).first()
        current = int(counter_setting.value) if counter_setting else 0

        return f"{prefix}-{current + 1:04d}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture référence: {str(e)}")


# ════════════════════════════════════════════════════════════════
# VEHICULES: CRUD
# ════════════════════════════════════════════════════════════════

def create_vehicle(
    db: Session,
    data: VehicleCreate,
    user_id: int,
    user_name: str
) -> VehicleResponse:
    """Créer un nouveau véhicule."""
    internal_ref = get_next_vehicle_reference(db)
    
    vehicle = LogisticsVehicle(
        registration_number=data.registration_number,
        internal_reference=internal_ref,
        vehicle_role=data.vehicle_role,
        segment=data.segment,
        type_id=data.type_id,
        brand=data.brand,
        model=data.model,
        year=data.year,
        vin=data.vin,
        capacity_value=data.capacity_value,
        capacity_unit=data.capacity_unit,
        fuel_type_id=data.fuel_type_id,
        status_id=data.status_id,
        company_id=data.company_id,
        base_site_id=data.base_site_id,
        acquisition_date=data.acquisition_date,
        acquisition_cost=data.acquisition_cost,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


def get_vehicles(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    segment: Optional[str] = None,
    vehicle_role: Optional[str] = None,
    status_id: Optional[int] = None,
    is_archived: bool = False,
) -> VehicleListResponse:
    """Récupérer la liste des véhicules avec filtrage."""
    query = db.query(LogisticsVehicle).filter(LogisticsVehicle.is_deleted == False)

    if not is_archived:
        query = query.filter(LogisticsVehicle.is_archived == False)

    if search:
        query = query.filter(or_(
            LogisticsVehicle.registration_number.ilike(f"%{search}%"),
            LogisticsVehicle.internal_reference.ilike(f"%{search}%"),
            LogisticsVehicle.brand.ilike(f"%{search}%"),
            LogisticsVehicle.model.ilike(f"%{search}%"),
        ))

    if company_id:
        query = query.filter(LogisticsVehicle.company_id == company_id)

    if segment:
        query = query.filter(LogisticsVehicle.segment == segment)

    if vehicle_role:
        query = query.filter(LogisticsVehicle.vehicle_role == vehicle_role)

    if status_id:
        query = query.filter(LogisticsVehicle.status_id == status_id)

    total = query.count()
    offset = (page - 1) * page_size

    vehicles = query.offset(offset).limit(page_size).all()

    return VehicleListResponse(
        items=[VehicleResponse.model_validate(v) for v in vehicles],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_vehicle(db: Session, vehicle_id: int) -> VehicleResponse:
    """Récupérer un véhicule par ID."""
    vehicle = db.query(LogisticsVehicle).filter(
        LogisticsVehicle.id == vehicle_id,
        LogisticsVehicle.is_deleted == False,
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Véhicule non trouvé."
        )

    return VehicleResponse.model_validate(vehicle)


def update_vehicle(
    db: Session,
    vehicle_id: int,
    data: VehicleUpdate,
    user_id: int,
) -> VehicleResponse:
    """Modifier un véhicule."""
    vehicle = db.query(LogisticsVehicle).filter(
        LogisticsVehicle.id == vehicle_id,
        LogisticsVehicle.is_deleted == False,
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Véhicule non trouvé."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)

    vehicle.updated_by = user_id
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


def archive_vehicle(db: Session, vehicle_id: int) -> VehicleResponse:
    """Archiver un véhicule."""
    vehicle = db.query(LogisticsVehicle).filter(
        LogisticsVehicle.id == vehicle_id,
        LogisticsVehicle.is_deleted == False,
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Véhicule non trouvé."
        )

    vehicle.is_archived = True
    vehicle.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


def delete_vehicle(db: Session, vehicle_id: int) -> bool:
    """Soft-delete un véhicule."""
    vehicle = db.query(LogisticsVehicle).filter(
        LogisticsVehicle.id == vehicle_id,
        LogisticsVehicle.is_deleted == False,
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Véhicule non trouvé."
        )

    vehicle.is_deleted = True
    vehicle.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# COMPARTIMENTS CITERNE
# ════════════════════════════════════════════════════════════════

def _get_vehicle_or_404(db: Session, vehicle_id: int) -> LogisticsVehicle:
    v = db.query(LogisticsVehicle).filter(
        LogisticsVehicle.id == vehicle_id,
        LogisticsVehicle.is_deleted == False,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé.")
    return v


def get_compartments(db: Session, vehicle_id: int) -> list[CompartmentResponse]:
    """Retourne tous les compartiments d'un véhicule triés par numéro."""
    _get_vehicle_or_404(db, vehicle_id)
    rows = (
        db.query(LogisticsVehicleCompartment)
        .filter(LogisticsVehicleCompartment.vehicle_id == vehicle_id)
        .order_by(LogisticsVehicleCompartment.compartment_no)
        .all()
    )
    return [CompartmentResponse.model_validate(r) for r in rows]


def create_compartment(
    db: Session, vehicle_id: int, data: CompartmentCreate
) -> CompartmentResponse:
    """Ajoute un compartiment à un véhicule citerne."""
    _get_vehicle_or_404(db, vehicle_id)
    # Vérifier l'unicité du numéro de compartiment
    existing = db.query(LogisticsVehicleCompartment).filter(
        LogisticsVehicleCompartment.vehicle_id == vehicle_id,
        LogisticsVehicleCompartment.compartment_no == data.compartment_no,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Compartiment n°{data.compartment_no} déjà existant pour ce véhicule.",
        )
    comp = LogisticsVehicleCompartment(vehicle_id=vehicle_id, **data.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return CompartmentResponse.model_validate(comp)


def update_compartment(
    db: Session, vehicle_id: int, compartment_id: int, data: CompartmentUpdate
) -> CompartmentResponse:
    """Modifie un compartiment."""
    comp = db.query(LogisticsVehicleCompartment).filter(
        LogisticsVehicleCompartment.id == compartment_id,
        LogisticsVehicleCompartment.vehicle_id == vehicle_id,
    ).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Compartiment non trouvé.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(comp, field, value)
    db.commit()
    db.refresh(comp)
    return CompartmentResponse.model_validate(comp)


def delete_compartment(db: Session, vehicle_id: int, compartment_id: int) -> bool:
    """Supprime définitivement un compartiment."""
    comp = db.query(LogisticsVehicleCompartment).filter(
        LogisticsVehicleCompartment.id == compartment_id,
        LogisticsVehicleCompartment.vehicle_id == vehicle_id,
    ).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Compartiment non trouvé.")
    db.delete(comp)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# ASSOCIATIONS TRACTEUR ↔ REMORQUE
# ════════════════════════════════════════════════════════════════

def _build_association_response(assoc: LogisticsVehicleAssociation) -> VehicleAssociationResponse:
    return VehicleAssociationResponse(
        id=assoc.id,
        tractor_id=assoc.tractor_id,
        trailer_id=assoc.trailer_id,
        company_id=assoc.company_id,
        is_default=assoc.is_default,
        is_active=assoc.is_active,
        notes=assoc.notes,
        tractor_registration=assoc.tractor.registration_number if assoc.tractor else None,
        trailer_registration=assoc.trailer.registration_number if assoc.trailer else None,
        created_at=assoc.created_at,
    )


def get_vehicle_associations(
    db: Session,
    vehicle_id: int,
    active_only: bool = True,
) -> list[VehicleAssociationResponse]:
    """Associations où ce véhicule est tracteur ou remorque."""
    _get_vehicle_or_404(db, vehicle_id)
    query = db.query(LogisticsVehicleAssociation).filter(
        or_(
            LogisticsVehicleAssociation.tractor_id == vehicle_id,
            LogisticsVehicleAssociation.trailer_id == vehicle_id,
        )
    )
    if active_only:
        query = query.filter(LogisticsVehicleAssociation.is_active == True)
    return [_build_association_response(a) for a in query.all()]


def get_associations_by_company(
    db: Session,
    company_id: int,
    active_only: bool = True,
) -> list[VehicleAssociationResponse]:
    """Toutes les associations d'une entreprise."""
    query = db.query(LogisticsVehicleAssociation).filter(
        LogisticsVehicleAssociation.company_id == company_id
    )
    if active_only:
        query = query.filter(LogisticsVehicleAssociation.is_active == True)
    return [_build_association_response(a) for a in query.all()]


def create_vehicle_association(
    db: Session, data: VehicleAssociationCreate, user_id: int
) -> VehicleAssociationResponse:
    """Crée un couple tracteur ↔ remorque."""
    # Valider que les deux véhicules existent
    tractor = _get_vehicle_or_404(db, data.tractor_id)
    trailer = _get_vehicle_or_404(db, data.trailer_id)

    if tractor.vehicle_role != 'tracteur':
        raise HTTPException(status_code=422, detail="Le véhicule tracteur doit avoir le rôle 'tracteur'.")
    if trailer.vehicle_role != 'remorque':
        raise HTTPException(status_code=422, detail="Le véhicule remorque doit avoir le rôle 'remorque'.")

    # Si is_default=True, désactiver l'ancienne association par défaut pour ce tracteur et cette remorque
    if data.is_default:
        db.query(LogisticsVehicleAssociation).filter(
            LogisticsVehicleAssociation.tractor_id == data.tractor_id,
            LogisticsVehicleAssociation.is_default == True,
        ).update({'is_default': False})
        db.query(LogisticsVehicleAssociation).filter(
            LogisticsVehicleAssociation.trailer_id == data.trailer_id,
            LogisticsVehicleAssociation.is_default == True,
        ).update({'is_default': False})

    assoc = LogisticsVehicleAssociation(
        tractor_id=data.tractor_id,
        trailer_id=data.trailer_id,
        company_id=data.company_id,
        is_default=data.is_default,
        is_active=True,
        notes=data.notes,
        created_by=user_id,
    )
    db.add(assoc)
    db.commit()
    db.refresh(assoc)
    return _build_association_response(assoc)


def update_vehicle_association(
    db: Session, association_id: int, data: VehicleAssociationUpdate
) -> VehicleAssociationResponse:
    """Modifie une association."""
    assoc = db.query(LogisticsVehicleAssociation).filter(
        LogisticsVehicleAssociation.id == association_id
    ).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="Association non trouvée.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assoc, field, value)
    db.commit()
    db.refresh(assoc)
    return _build_association_response(assoc)


def delete_vehicle_association(db: Session, association_id: int) -> bool:
    """Supprime définitivement une association."""
    assoc = db.query(LogisticsVehicleAssociation).filter(
        LogisticsVehicleAssociation.id == association_id
    ).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="Association non trouvée.")
    db.delete(assoc)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# CHAUFFEURS: CRUD
# ════════════════════════════════════════════════════════════════

def create_driver(
    db: Session,
    data: DriverCreate,
    user_id: int,
    user_name: str
) -> DriverResponse:
    """Créer un nouveau chauffeur."""
    driver = LogisticsDriver(
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        phone=data.phone,
        email=data.email,
        company_id=data.company_id,
        license_types_json=data.license_types_json or [],
        license_expiry=data.license_expiry,
        adr_certificate_expiry=data.adr_certificate_expiry,
        hire_date=data.hire_date,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


def get_drivers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    company_id: Optional[int] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
) -> DriverListResponse:
    """Récupérer la liste des chauffeurs."""
    query = db.query(LogisticsDriver).filter(LogisticsDriver.is_deleted == False)

    if company_id:
        query = query.filter(LogisticsDriver.company_id == company_id)

    if role:
        query = query.filter(LogisticsDriver.role == role)

    if status:
        query = query.filter(LogisticsDriver.status == status)

    total = query.count()
    offset = (page - 1) * page_size

    drivers = query.offset(offset).limit(page_size).all()

    return DriverListResponse(
        items=[DriverResponse.model_validate(d) for d in drivers],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_driver(db: Session, driver_id: int) -> DriverResponse:
    """Récupérer un chauffeur par ID."""
    driver = db.query(LogisticsDriver).filter(
        LogisticsDriver.id == driver_id,
        LogisticsDriver.is_deleted == False,
    ).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chauffeur non trouvé."
        )

    return DriverResponse.model_validate(driver)


def update_driver(
    db: Session,
    driver_id: int,
    data: DriverUpdate,
    user_id: int,
) -> DriverResponse:
    """Modifier un chauffeur."""
    driver = db.query(LogisticsDriver).filter(
        LogisticsDriver.id == driver_id,
        LogisticsDriver.is_deleted == False,
    ).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chauffeur non trouvé."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)

    driver.updated_by = user_id
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


def delete_driver(db: Session, driver_id: int) -> bool:
    """Soft-delete un chauffeur."""
    driver = db.query(LogisticsDriver).filter(
        LogisticsDriver.id == driver_id,
        LogisticsDriver.is_deleted == False,
    ).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chauffeur non trouvé."
        )

    driver.is_deleted = True
    driver.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# ÉQUIPES: CRUD
# ════════════════════════════════════════════════════════════════

def create_team(
    db: Session,
    data: TeamCreate,
    user_id: int,
    user_name: str
) -> TeamResponse:
    """Créer une nouvelle équipe."""
    team = LogisticsTeam(
        name=data.name,
        code=data.code,
        leader_id=data.leader_id,
        company_id=data.company_id,
        preferred_segment=data.preferred_segment,
        default_vehicle_id=data.default_vehicle_id,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return TeamResponse.model_validate(team)


def get_teams(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
) -> TeamListResponse:
    """Récupérer la liste des équipes."""
    query = db.query(LogisticsTeam).filter(LogisticsTeam.is_deleted == False)

    if company_id:
        query = query.filter(LogisticsTeam.company_id == company_id)

    if status:
        query = query.filter(LogisticsTeam.status == status)

    total = query.count()
    offset = (page - 1) * page_size

    teams = query.offset(offset).limit(page_size).all()

    return TeamListResponse(
        items=[TeamResponse.model_validate(t) for t in teams],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_team(db: Session, team_id: int) -> TeamDetailResponse:
    """Récupérer une équipe par ID avec ses membres."""
    team = db.query(LogisticsTeam).filter(
        LogisticsTeam.id == team_id,
        LogisticsTeam.is_deleted == False,
    ).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Équipe non trouvée."
        )

    members = db.query(LogisticsDriver).filter(
        LogisticsDriver.team_id == team_id,
        LogisticsDriver.is_deleted == False,
    ).all()

    response = TeamDetailResponse.model_validate(team)
    response.members = [DriverResponse.model_validate(m) for m in members]
    return response


def update_team(
    db: Session,
    team_id: int,
    data: TeamUpdate,
    user_id: int,
) -> TeamResponse:
    """Modifier une équipe."""
    team = db.query(LogisticsTeam).filter(
        LogisticsTeam.id == team_id,
        LogisticsTeam.is_deleted == False,
    ).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Équipe non trouvée."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)

    team.updated_by = user_id
    db.commit()
    db.refresh(team)
    return TeamResponse.model_validate(team)


def delete_team(db: Session, team_id: int) -> bool:
    """Soft-delete une équipe."""
    team = db.query(LogisticsTeam).filter(
        LogisticsTeam.id == team_id,
        LogisticsTeam.is_deleted == False,
    ).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Équipe non trouvée."
        )

    team.is_deleted = True
    team.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# DASHBOARD & STATS
# ════════════════════════════════════════════════════════════════

def get_logistics_dashboard(db: Session, company_id: Optional[int] = None) -> LogisticsDashboardResponse:
    """Récupérer les statistiques du dashboard logistique."""
    vehicle_query = db.query(LogisticsVehicle).filter(LogisticsVehicle.is_deleted == False)
    driver_query = db.query(LogisticsDriver).filter(LogisticsDriver.is_deleted == False)
    team_query = db.query(LogisticsTeam).filter(LogisticsTeam.is_deleted == False)
    mission_query = db.query(LogisticsMission).filter(LogisticsMission.is_deleted == False)
    maintenance_query = db.query(LogisticsMaintenance).filter(LogisticsMaintenance.is_deleted == False)

    if company_id:
        vehicle_query = vehicle_query.filter(LogisticsVehicle.company_id == company_id)
        driver_query = driver_query.filter(LogisticsDriver.company_id == company_id)
        team_query = team_query.filter(LogisticsTeam.company_id == company_id)
        mission_query = mission_query.join(
            LogisticsVehicle, LogisticsMission.vehicle_id == LogisticsVehicle.id
        ).filter(LogisticsVehicle.company_id == company_id)
        maintenance_query = maintenance_query.join(
            LogisticsVehicle, LogisticsMaintenance.vehicle_id == LogisticsVehicle.id
        ).filter(LogisticsVehicle.company_id == company_id)

    total_vehicles = vehicle_query.count()
    vehicles_active = vehicle_query.filter(LogisticsVehicle.is_archived == False).count()
    total_drivers = driver_query.count()
    total_teams = team_query.count()
    missions_in_progress = mission_query.filter(LogisticsMission.status == 'in_progress').count()
    vehicles_in_maintenance = maintenance_query.filter(LogisticsMaintenance.status == 'in_progress').count()
    open_breakdowns_count = maintenance_query.filter(
        LogisticsMaintenance.status.in_(["scheduled", "in_progress"]),
        LogisticsMaintenance.category == "corrective",
    ).count()

    stats = LogisticsDashboardStats(
        total_vehicles=total_vehicles,
        vehicles_active=vehicles_active,
        total_drivers=total_drivers,
        total_teams=total_teams,
        missions_in_progress=missions_in_progress,
        vehicles_in_maintenance=vehicles_in_maintenance,
        open_breakdowns_count=open_breakdowns_count,
        alerts_count=open_breakdowns_count,
    )

    alerts = [
        AlertSummary(type="documents_expiring", count=0, description="Documents expirant bientôt"),
        AlertSummary(type="maintenance_due", count=open_breakdowns_count, description="Pannes ouvertes"),
    ]

    return LogisticsDashboardResponse(stats=stats, alerts=alerts)


# ════════════════════════════════════════════════════════════════
# MISSIONS: REFERENCE AUTO-INCREMENT
# ════════════════════════════════════════════════════════════════

def get_next_mission_reference(db: Session) -> str:
    """Génère la prochaine référence mission au format 'MIS-XXXX'."""
    try:
        prefix_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_prefix_mission"
        ).with_for_update().first()

        if not prefix_setting:
            raise HTTPException(
                status_code=500,
                detail="Paramètre reference_prefix_mission introuvable."
            )

        prefix = prefix_setting.value

        counter_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_counter_mission"
        ).with_for_update().first()

        if not counter_setting:
            raise HTTPException(
                status_code=500,
                detail="Paramètre reference_counter_mission introuvable."
            )

        new_counter = int(counter_setting.value) + 1
        counter_setting.value = str(new_counter)
        db.flush()

        return f"{prefix}-{new_counter:04d}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération référence mission: {str(e)}")


def peek_next_mission_reference(db: Session) -> str:
    """Retourne la prochaine référence mission SANS l'incrémenter."""
    try:
        prefix_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_prefix_mission"
        ).first()
        prefix = prefix_setting.value if prefix_setting else "MIS"

        counter_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_counter_mission"
        ).first()
        current = int(counter_setting.value) if counter_setting else 0

        return f"{prefix}-{current + 1:04d}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture référence mission: {str(e)}")


# ════════════════════════════════════════════════════════════════
# MISSIONS: CRUD
# ════════════════════════════════════════════════════════════════

def create_mission(
    db: Session,
    data: MissionCreate,
    user_id: int,
    user_name: str
) -> MissionResponse:
    """Créer une nouvelle mission."""
    reference = get_next_mission_reference(db)

    mission = LogisticsMission(
        reference=reference,
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id,
        co_driver_id=data.co_driver_id,
        team_id=data.team_id,
        segment=data.segment,
        client_name=data.client_name,
        client_reference=data.client_reference,
        departure_location=data.departure_location,
        departure_lat=data.departure_lat,
        departure_lng=data.departure_lng,
        arrival_location=data.arrival_location,
        arrival_lat=data.arrival_lat,
        arrival_lng=data.arrival_lng,
        distance_planned_km=data.distance_planned_km,
        mileage_start=data.mileage_start,
        planned_date=data.planned_date,
        status='planned',
        cargo_type_id=data.cargo_type_id,
        cargo_description=data.cargo_description,
        cargo_loaded_qty=data.cargo_loaded_qty,
        cargo_unit=data.cargo_unit,
        wood_species=data.wood_species,
        log_count=data.log_count,
        product_name=data.product_name,
        depotage_cert_number=data.depotage_cert_number,
        tank_calibrated=data.tank_calibrated,
        container_count=data.container_count,
        fill_rate_percent=data.fill_rate_percent,
        revenue=data.revenue,
        toll_cost=data.toll_cost,
        other_costs=data.other_costs,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def get_missions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    segment: Optional[str] = None,
    status: Optional[str] = None,
    driver_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
) -> MissionListResponse:
    """Récupérer la liste des missions avec filtrage."""
    query = db.query(LogisticsMission).filter(LogisticsMission.is_deleted == False)

    if segment:
        query = query.filter(LogisticsMission.segment == segment)

    if status:
        query = query.filter(LogisticsMission.status == status)

    if driver_id:
        query = query.filter(
            or_(LogisticsMission.driver_id == driver_id, LogisticsMission.co_driver_id == driver_id)
        )

    if vehicle_id:
        query = query.filter(LogisticsMission.vehicle_id == vehicle_id)

    if date_from:
        query = query.filter(LogisticsMission.planned_date >= date_from)

    if date_to:
        query = query.filter(LogisticsMission.planned_date <= date_to)

    if search:
        query = query.filter(or_(
            LogisticsMission.reference.ilike(f"%{search}%"),
            LogisticsMission.client_name.ilike(f"%{search}%"),
            LogisticsMission.departure_location.ilike(f"%{search}%"),
            LogisticsMission.arrival_location.ilike(f"%{search}%"),
        ))

    if company_id:
        query = query.join(LogisticsVehicle, LogisticsMission.vehicle_id == LogisticsVehicle.id).filter(
            LogisticsVehicle.company_id == company_id
        )

    total = query.count()
    offset = (page - 1) * page_size

    missions = query.order_by(LogisticsMission.planned_date.desc()).offset(offset).limit(page_size).all()

    return MissionListResponse(
        items=[MissionResponse.model_validate(m) for m in missions],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_mission(db: Session, mission_id: int) -> MissionResponse:
    """Récupérer une mission par ID."""
    mission = db.query(LogisticsMission).filter(
        LogisticsMission.id == mission_id,
        LogisticsMission.is_deleted == False,
    ).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée."
        )

    return MissionResponse.model_validate(mission)


def update_mission(
    db: Session,
    mission_id: int,
    data: MissionUpdate,
    user_id: int,
) -> MissionResponse:
    """Modifier une mission."""
    mission = db.query(LogisticsMission).filter(
        LogisticsMission.id == mission_id,
        LogisticsMission.is_deleted == False,
    ).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mission, field, value)

    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def delete_mission(db: Session, mission_id: int) -> bool:
    """Soft-delete une mission."""
    mission = db.query(LogisticsMission).filter(
        LogisticsMission.id == mission_id,
        LogisticsMission.is_deleted == False,
    ).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée."
        )

    mission.is_deleted = True
    mission.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def get_driver_missions(
    db: Session,
    driver_id: int,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> MissionListResponse:
    """Récupérer les missions d'un chauffeur (Mes Missions)."""
    query = db.query(LogisticsMission).filter(
        LogisticsMission.is_deleted == False,
        or_(LogisticsMission.driver_id == driver_id, LogisticsMission.co_driver_id == driver_id)
    )

    if status_filter:
        query = query.filter(LogisticsMission.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size

    missions = query.order_by(LogisticsMission.planned_date.desc()).offset(offset).limit(page_size).all()

    return MissionListResponse(
        items=[MissionResponse.model_validate(m) for m in missions],
        total=total,
        page=page,
        page_size=page_size,
    )


# ════════════════════════════════════════════════════════════════
# MISSIONS: WORKFLOW
# ════════════════════════════════════════════════════════════════

def _get_mission_for_update(db: Session, mission_id: int) -> LogisticsMission:
    """Helper: récupérer une mission pour modification ou 404."""
    mission = db.query(LogisticsMission).filter(
        LogisticsMission.id == mission_id,
        LogisticsMission.is_deleted == False,
    ).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée."
        )
    return mission


def start_mission(db: Session, mission_id: int, user_id: int) -> MissionResponse:
    """Démarrer une mission : planned → in_progress."""
    mission = _get_mission_for_update(db, mission_id)

    if mission.status != 'planned':
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de démarrer une mission au statut '{mission.status}'. Statut requis: 'planned'."
        )

    mission.status = 'in_progress'
    mission.actual_departure = datetime.now(timezone.utc)
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def complete_mission(
    db: Session,
    mission_id: int,
    data: MissionCompleteRequest,
    user_id: int,
) -> MissionResponse:
    """Terminer une mission : in_progress → completed."""
    mission = _get_mission_for_update(db, mission_id)

    if mission.status != 'in_progress':
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de terminer une mission au statut '{mission.status}'. Statut requis: 'in_progress'."
        )

    mission.status = 'completed'
    mission.actual_arrival = datetime.now(timezone.utc)
    mission.mileage_end = data.mileage_end
    mission.distance_actual_km = data.distance_actual_km
    mission.cargo_unloaded_qty = data.cargo_unloaded_qty
    mission.cargo_loss_qty = data.cargo_loss_qty
    mission.cargo_loss_reason = data.cargo_loss_reason
    if data.return_empty is not None:
        mission.return_empty = data.return_empty
    if data.notes:
        mission.notes = data.notes
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def cancel_mission(db: Session, mission_id: int, user_id: int) -> MissionResponse:
    """Annuler une mission : planned|in_progress → cancelled."""
    mission = _get_mission_for_update(db, mission_id)

    if mission.status not in ('planned', 'in_progress'):
        raise HTTPException(
            status_code=400,
            detail=f"Impossible d'annuler une mission au statut '{mission.status}'."
        )

    mission.status = 'cancelled'
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def submit_mission(db: Session, mission_id: int, user_id: int) -> MissionResponse:
    """Soumettre une mission pour validation : completed + submitted_at = now."""
    mission = _get_mission_for_update(db, mission_id)

    if mission.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de soumettre une mission au statut '{mission.status}'. Statut requis: 'completed'."
        )

    mission.submitted_by = user_id
    mission.submitted_at = datetime.now(timezone.utc)
    mission.rejection_reason = None
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def approve_mission(db: Session, mission_id: int, user_id: int) -> MissionResponse:
    """Approuver une mission soumise."""
    mission = _get_mission_for_update(db, mission_id)

    if not mission.submitted_at:
        raise HTTPException(
            status_code=400,
            detail="Impossible d'approuver une mission non soumise."
        )

    mission.approved_by = user_id
    mission.approved_at = datetime.now(timezone.utc)
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


def reject_mission(
    db: Session,
    mission_id: int,
    data: MissionRejectRequest,
    user_id: int,
) -> MissionResponse:
    """Rejeter une mission soumise."""
    mission = _get_mission_for_update(db, mission_id)

    if not mission.submitted_at:
        raise HTTPException(
            status_code=400,
            detail="Impossible de rejeter une mission non soumise."
        )

    mission.rejection_reason = data.rejection_reason
    mission.submitted_at = None
    mission.submitted_by = None
    mission.updated_by = user_id
    db.commit()
    db.refresh(mission)
    return MissionResponse.model_validate(mission)


# ════════════════════════════════════════════════════════════════
# CHECKPOINTS: CRUD
# ════════════════════════════════════════════════════════════════

def add_checkpoint(
    db: Session,
    mission_id: int,
    data: CheckpointCreate,
) -> CheckpointResponse:
    """Ajouter un checkpoint à une mission."""
    mission = db.query(LogisticsMission).filter(
        LogisticsMission.id == mission_id,
        LogisticsMission.is_deleted == False,
    ).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée."
        )

    checkpoint = LogisticsMissionCheckpoint(
        mission_id=mission_id,
        checkpoint_type=data.checkpoint_type,
        location_name=data.location_name,
        lat=data.lat,
        lng=data.lng,
        arrived_at=data.arrived_at,
        departed_at=data.departed_at,
        wait_time_minutes=data.wait_time_minutes,
        cargo_quantity=data.cargo_quantity,
        cargo_unit=data.cargo_unit,
        mileage_at=data.mileage_at,
        photos_json=data.photos_json or [],
        notes=data.notes,
    )
    db.add(checkpoint)
    db.commit()
    db.refresh(checkpoint)
    return CheckpointResponse.model_validate(checkpoint)


def get_mission_checkpoints(
    db: Session,
    mission_id: int,
) -> List[CheckpointResponse]:
    """Récupérer les checkpoints d'une mission, ordonnés par arrived_at."""
    checkpoints = db.query(LogisticsMissionCheckpoint).filter(
        LogisticsMissionCheckpoint.mission_id == mission_id,
        LogisticsMissionCheckpoint.is_deleted == False,
    ).order_by(LogisticsMissionCheckpoint.arrived_at).all()

    return [CheckpointResponse.model_validate(c) for c in checkpoints]


def delete_checkpoint(db: Session, checkpoint_id: int) -> bool:
    """Supprimer un checkpoint (soft delete)."""
    checkpoint = db.query(LogisticsMissionCheckpoint).filter(
        LogisticsMissionCheckpoint.id == checkpoint_id,
        LogisticsMissionCheckpoint.is_deleted == False,
    ).first()

    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint non trouvé."
        )

    checkpoint.is_deleted = True
    checkpoint.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ════════════════════════════════════════════════════════════════
# CARBURANT (FUEL LOGS): CRUD
# ════════════════════════════════════════════════════════════════

def create_fuel_log(
    db: Session,
    data: FuelLogCreate,
    user_id: int,
    user_name: str,
) -> FuelLogResponse:
    """Créer un log de carburant."""
    fuel_log = LogisticsFuelLog(
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id,
        mission_id=data.mission_id,
        date=data.date,
        station_name=data.station_name,
        fuel_type=data.fuel_type,
        quantity_liters=data.quantity_liters,
        unit_price=data.unit_price,
        total_cost=data.total_cost,
        mileage_at=data.mileage_at,
        is_full_tank=data.is_full_tank,
        receipt_url=data.receipt_url,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(fuel_log)
    db.commit()
    db.refresh(fuel_log)
    return FuelLogResponse.model_validate(fuel_log)


def get_fuel_logs(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    mission_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> FuelLogListResponse:
    """Récupérer les logs de carburant avec filtrage."""
    query = db.query(LogisticsFuelLog).filter(LogisticsFuelLog.is_deleted == False)

    if vehicle_id:
        query = query.filter(LogisticsFuelLog.vehicle_id == vehicle_id)

    if driver_id:
        query = query.filter(LogisticsFuelLog.driver_id == driver_id)

    if mission_id:
        query = query.filter(LogisticsFuelLog.mission_id == mission_id)

    if date_from:
        query = query.filter(LogisticsFuelLog.date >= date_from)

    if date_to:
        query = query.filter(LogisticsFuelLog.date <= date_to)

    total = query.count()
    offset = (page - 1) * page_size

    logs = query.order_by(LogisticsFuelLog.date.desc()).offset(offset).limit(page_size).all()

    return FuelLogListResponse(
        items=[FuelLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_fuel_log(db: Session, fuel_log_id: int) -> FuelLogResponse:
    """Récupérer un log de carburant par ID."""
    fuel_log = db.query(LogisticsFuelLog).filter(
        LogisticsFuelLog.id == fuel_log_id,
        LogisticsFuelLog.is_deleted == False,
    ).first()

    if not fuel_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log carburant non trouvé."
        )

    return FuelLogResponse.model_validate(fuel_log)


def update_fuel_log(
    db: Session,
    fuel_log_id: int,
    data: FuelLogUpdate,
    user_id: int,
) -> FuelLogResponse:
    """Modifier un log de carburant."""
    fuel_log = db.query(LogisticsFuelLog).filter(
        LogisticsFuelLog.id == fuel_log_id,
        LogisticsFuelLog.is_deleted == False,
    ).first()

    if not fuel_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log carburant non trouvé."
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fuel_log, field, value)

    fuel_log.updated_by = user_id
    db.commit()
    db.refresh(fuel_log)
    return FuelLogResponse.model_validate(fuel_log)


def delete_fuel_log(db: Session, fuel_log_id: int) -> bool:
    """Soft-delete un log de carburant."""
    fuel_log = db.query(LogisticsFuelLog).filter(
        LogisticsFuelLog.id == fuel_log_id,
        LogisticsFuelLog.is_deleted == False,
    ).first()

    if not fuel_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log carburant non trouvé."
        )

    fuel_log.is_deleted = True
    fuel_log.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def get_vehicle_fuel_logs(
    db: Session,
    vehicle_id: int,
    page: int = 1,
    page_size: int = 20,
) -> FuelLogListResponse:
    """Raccourci: logs carburant d'un véhicule."""
    return get_fuel_logs(db, page=page, page_size=page_size, vehicle_id=vehicle_id)


def get_fuel_alerts(
    db: Session,
    company_id: Optional[int] = None,
) -> FuelAlertListResponse:
    """Alertes surconsommation: comparer conso moyenne vs seuil."""
    threshold_setting = db.query(LogisticsGlobalSettings).filter(
        LogisticsGlobalSettings.key == "fuel_consumption_alert_threshold"
    ).first()
    threshold = float(threshold_setting.value) if threshold_setting else 8.0

    query = db.query(
        LogisticsFuelLog.vehicle_id,
        sa_func.avg(LogisticsFuelLog.consumption_l100km).label('avg_consumption'),
    ).filter(
        LogisticsFuelLog.is_deleted == False,
        LogisticsFuelLog.consumption_l100km != None,
    ).group_by(LogisticsFuelLog.vehicle_id).having(
        sa_func.avg(LogisticsFuelLog.consumption_l100km) > threshold
    )

    results = query.all()

    alerts = []
    for vehicle_id, avg_consumption in results:
        vehicle = db.query(LogisticsVehicle).filter(
            LogisticsVehicle.id == vehicle_id
        ).first()
        if vehicle and (not company_id or vehicle.company_id == company_id):
            alerts.append(FuelAlertResponse(
                vehicle_id=vehicle_id,
                registration_number=vehicle.registration_number,
                avg_consumption=round(float(avg_consumption), 2),
                threshold=threshold,
                alert_type="overconsumption",
            ))

    return FuelAlertListResponse(items=alerts, total=len(alerts))


# ════════════════════════════════════════════════════════════════
# UTILISATEURS CHAUFFEURS (gestion par superviseur)
# ════════════════════════════════════════════════════════════════

# Presets de permissions par profil
DRIVER_PERMISSIONS = {
    "logistics_access_section": True,
    "logistics_view": True,
    "logistics_missions_view_own": True,
    "logistics_missions_submit": True,
    "logistics_missions_add_photos": True,
    "logistics_fuel_create": True,
    "logistics_fuel_view": True,
}

MOTOR_BOY_PERMISSIONS = {
    "logistics_access_section": True,
    "logistics_view": True,
    "logistics_missions_view_own": True,
    "logistics_missions_add_photos": True,
}


def create_driver_user(
    db: Session,
    data: DriverUserCreate,
    creator_id: int,
    creator_name: str,
) -> DriverUserResponse:
    """Créer un utilisateur + fiche chauffeur en une seule opération."""
    from app.utils import utils
    from app.db.crud.crud_users import create_user

    # Vérifier unicité username/email
    existing_user = db.query(User).filter(
        or_(User.username == data.username, User.email == data.email)
    ).first()
    if existing_user:
        if existing_user.username == data.username:
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris.")
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà utilisée.")

    # Valider le rôle
    if data.role not in ("driver", "motor_boy"):
        raise HTTPException(status_code=400, detail="Le rôle doit être 'driver' ou 'motor_boy'.")

    # 1. Hash password
    hashed = utils.hash(data.password)

    # 2. Créer le User (insert + initialize_user_permissions)
    user_data = {
        "username": data.username,
        "email": data.email,
        "password": hashed,
        "name": data.first_name,
        "family_name": data.last_name,
        "phone_number": data.phone or "",
    }
    new_user = create_user(db, user_data)

    # 3. Assigner le rôle "public"
    from routeur.users_route import assign_default_role_to_user
    assign_default_role_to_user(new_user.id, db)

    # 4. Appliquer les permissions logistiques selon le profil
    perms = DRIVER_PERMISSIONS if data.role == "driver" else MOTOR_BOY_PERMISSIONS
    user_perms = db.query(UserPermissions).filter_by(user_id=new_user.id).first()
    if user_perms:
        for key, value in perms.items():
            setattr(user_perms, key, value)
        db.flush()

    # 5. Créer la fiche LogisticsDriver liée au user
    driver = LogisticsDriver(
        user_id=new_user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        phone=data.phone,
        company_id=data.company_id,
        license_types_json=data.license_types_json or [],
        license_expiry=data.license_expiry,
        hire_date=data.hire_date,
        notes=data.notes,
        created_by=creator_id,
        created_by_name=creator_name,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    db.refresh(new_user)

    return DriverUserResponse(
        user_id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        driver_id=driver.id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        role=driver.role,
        company_id=driver.company_id,
        status=driver.status,
        created_at=driver.created_at,
    )


def get_driver_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    company_id: Optional[int] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
) -> DriverUserListResponse:
    """Lister les chauffeurs qui ont un compte utilisateur."""
    query = db.query(LogisticsDriver).filter(
        LogisticsDriver.is_deleted == False,
        LogisticsDriver.user_id != None,
    )

    if company_id:
        query = query.filter(LogisticsDriver.company_id == company_id)

    if role:
        query = query.filter(LogisticsDriver.role == role)

    if search:
        query = query.filter(or_(
            LogisticsDriver.first_name.ilike(f"%{search}%"),
            LogisticsDriver.last_name.ilike(f"%{search}%"),
        ))

    total = query.count()
    offset = (page - 1) * page_size
    drivers = query.order_by(LogisticsDriver.id.desc()).offset(offset).limit(page_size).all()

    items = []
    for driver in drivers:
        user = db.query(User).filter(User.id == driver.user_id).first()
        if user:
            items.append(DriverUserResponse(
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                driver_id=driver.id,
                first_name=driver.first_name,
                last_name=driver.last_name,
                role=driver.role,
                company_id=driver.company_id,
                status=driver.status,
                created_at=driver.created_at,
            ))

    return DriverUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def toggle_driver_user_active(
    db: Session,
    driver_id: int,
) -> DriverUserResponse:
    """Activer/Désactiver le compte utilisateur d'un chauffeur."""
    driver = db.query(LogisticsDriver).filter(
        LogisticsDriver.id == driver_id,
        LogisticsDriver.is_deleted == False,
    ).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé.")

    if not driver.user_id:
        raise HTTPException(status_code=400, detail="Ce chauffeur n'a pas de compte utilisateur.")

    user = db.query(User).filter(User.id == driver.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return DriverUserResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        driver_id=driver.id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        role=driver.role,
        company_id=driver.company_id,
        status=driver.status,
        created_at=driver.created_at,
    )


# ════════════════════════════════════════════════════════════════
# MÉCANICIENS
# ════════════════════════════════════════════════════════════════

def _build_mechanic_response(m: LogisticsMechanic) -> MechanicResponse:
    return MechanicResponse(
        id=m.id,
        user_id=m.user_id,
        has_account=m.user_id is not None,
        first_name=m.first_name,
        last_name=m.last_name,
        full_name=f"{m.first_name} {m.last_name}",
        email=m.email,
        phone=m.phone,
        specialty=m.specialty,
        company_id=m.company_id,
        is_active=m.is_active,
        notes=m.notes,
        created_at=m.created_at,
        created_by=m.created_by,
        created_by_name=m.created_by_name,
    )


def create_mechanic(
    db: Session, data: MechanicCreate, user_id: int, user_name: str
) -> MechanicResponse:
    mechanic = LogisticsMechanic(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        specialty=data.specialty,
        company_id=data.company_id,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(mechanic)
    db.commit()
    db.refresh(mechanic)
    return _build_mechanic_response(mechanic)


def get_mechanics(
    db: Session,
    company_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> MechanicListResponse:
    query = db.query(LogisticsMechanic).filter(LogisticsMechanic.is_deleted == False)
    if company_id:
        query = query.filter(LogisticsMechanic.company_id == company_id)
    if is_active is not None:
        query = query.filter(LogisticsMechanic.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                LogisticsMechanic.first_name.ilike(f"%{search}%"),
                LogisticsMechanic.last_name.ilike(f"%{search}%"),
                LogisticsMechanic.specialty.ilike(f"%{search}%"),
            )
        )
    total = query.count()
    mechanics = query.offset((page - 1) * page_size).limit(page_size).all()
    return MechanicListResponse(
        items=[_build_mechanic_response(m) for m in mechanics],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_mechanic(db: Session, mechanic_id: int) -> MechanicResponse:
    m = db.query(LogisticsMechanic).filter(
        LogisticsMechanic.id == mechanic_id,
        LogisticsMechanic.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mécanicien non trouvé.")
    return _build_mechanic_response(m)


def update_mechanic(
    db: Session, mechanic_id: int, data: MechanicUpdate, user_id: int
) -> MechanicResponse:
    m = db.query(LogisticsMechanic).filter(
        LogisticsMechanic.id == mechanic_id,
        LogisticsMechanic.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mécanicien non trouvé.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    m.updated_by = user_id
    db.commit()
    db.refresh(m)
    return _build_mechanic_response(m)


def delete_mechanic(db: Session, mechanic_id: int) -> bool:
    m = db.query(LogisticsMechanic).filter(
        LogisticsMechanic.id == mechanic_id,
        LogisticsMechanic.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mécanicien non trouvé.")
    m.is_deleted = True
    m.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def link_mechanic_to_user(db: Session, mechanic_id: int, user_id: int) -> MechanicResponse:
    m = db.query(LogisticsMechanic).filter(
        LogisticsMechanic.id == mechanic_id,
        LogisticsMechanic.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mécanicien non trouvé.")
    m.user_id = user_id
    db.commit()
    db.refresh(m)
    return _build_mechanic_response(m)


# ════════════════════════════════════════════════════════════════
# INVITATIONS (Chemin A)
# ════════════════════════════════════════════════════════════════

def create_invitation(
    db: Session,
    entity_type: str,
    entity_id: int,
    email: str,
    created_by: int,
    created_by_name: str,
    base_url: str = "",
) -> InviteResponse:
    # Invalider les invitations précédentes non utilisées pour la même entité
    db.query(LogisticsInvitation).filter(
        LogisticsInvitation.entity_type == entity_type,
        LogisticsInvitation.entity_id == entity_id,
        LogisticsInvitation.used_at == None,
    ).delete(synchronize_session=False)

    token = str(uuid.uuid4()).replace("-", "")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = LogisticsInvitation(
        token=token,
        entity_type=entity_type,
        entity_id=entity_id,
        email=email,
        expires_at=expires_at,
        created_by=created_by,
        created_by_name=created_by_name,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    invite_url = f"{base_url}/invite/accept?token={token}"
    return InviteResponse(
        token=token,
        invite_url=invite_url,
        expires_at=expires_at,
        entity_type=entity_type,
        entity_id=entity_id,
        email=email,
    )


def validate_invitation(db: Session, token: str) -> InviteValidateResponse:
    inv = db.query(LogisticsInvitation).filter(
        LogisticsInvitation.token == token
    ).first()

    if not inv:
        return InviteValidateResponse(is_valid=False)
    if inv.used_at is not None:
        return InviteValidateResponse(is_valid=False)
    if datetime.now(timezone.utc) > inv.expires_at.replace(tzinfo=timezone.utc) if inv.expires_at.tzinfo is None else datetime.now(timezone.utc) > inv.expires_at:
        return InviteValidateResponse(is_valid=False)

    full_name = None
    role = None
    company_name = None

    if inv.entity_type == "driver":
        entity = db.query(LogisticsDriver).filter(
            LogisticsDriver.id == inv.entity_id,
            LogisticsDriver.is_deleted == False,
        ).first()
        if entity:
            full_name = f"{entity.first_name} {entity.last_name}"
            role = entity.role
            if entity.company:
                company_name = entity.company.name
    elif inv.entity_type == "mechanic":
        entity = db.query(LogisticsMechanic).filter(
            LogisticsMechanic.id == inv.entity_id,
            LogisticsMechanic.is_deleted == False,
        ).first()
        if entity:
            full_name = f"{entity.first_name} {entity.last_name}"
            role = entity.specialty or "Mécanicien"
            if entity.company:
                company_name = entity.company.name

    return InviteValidateResponse(
        is_valid=True,
        entity_type=inv.entity_type,
        entity_id=inv.entity_id,
        full_name=full_name,
        role=role,
        company_name=company_name,
        email=inv.email,
        expires_at=inv.expires_at,
    )


def accept_invitation(
    db: Session, token: str, data: InviteAcceptRequest
) -> dict:
    inv = db.query(LogisticsInvitation).filter(
        LogisticsInvitation.token == token
    ).first()
    if not inv or inv.used_at is not None:
        raise HTTPException(status_code=400, detail="Invitation invalide ou déjà utilisée.")

    expires = inv.expires_at.replace(tzinfo=timezone.utc) if inv.expires_at.tzinfo is None else inv.expires_at
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail="Invitation expirée.")

    # Vérifier que le username n'existe pas déjà
    existing_user = db.query(User).filter(
        or_(User.username == data.username, User.email == inv.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur ou email est déjà utilisé.")

    # Créer le compte utilisateur
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(data.password)

    new_user = User(
        username=data.username,
        email=inv.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # Lier l'entité
    if inv.entity_type == "driver":
        entity = db.query(LogisticsDriver).filter(LogisticsDriver.id == inv.entity_id).first()
        if entity:
            entity.user_id = new_user.id
    elif inv.entity_type == "mechanic":
        entity = db.query(LogisticsMechanic).filter(LogisticsMechanic.id == inv.entity_id).first()
        if entity:
            entity.user_id = new_user.id

    # Marquer l'invitation comme utilisée
    inv.used_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Compte créé avec succès."}


# ════════════════════════════════════════════════════════════════
# PANNES / MAINTENANCE — REFERENCE AUTO-INCREMENT
# ════════════════════════════════════════════════════════════════

def get_next_maintenance_reference(db: Session) -> str:
    """Génère la prochaine référence panne au format 'PAN-XXXX'."""
    try:
        prefix_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_prefix_maintenance"
        ).with_for_update().first()
        prefix = prefix_setting.value if prefix_setting else "PAN"

        counter_setting = db.query(LogisticsGlobalSettings).filter(
            LogisticsGlobalSettings.key == "reference_counter_maintenance"
        ).with_for_update().first()

        if not counter_setting:
            # Créer le compteur s'il n'existe pas
            counter_setting = LogisticsGlobalSettings(
                key="reference_counter_maintenance",
                value="0",
                value_type="int",
                description="Compteur référence fiches de panne",
            )
            if not prefix_setting:
                db.add(LogisticsGlobalSettings(
                    key="reference_prefix_maintenance",
                    value="PAN",
                    value_type="string",
                    description="Préfixe référence fiches de panne",
                ))
            db.add(counter_setting)
            db.flush()

        new_counter = int(counter_setting.value) + 1
        counter_setting.value = str(new_counter)
        db.flush()
        return f"{prefix}-{new_counter:04d}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération référence: {str(e)}")


def peek_next_maintenance_reference(db: Session) -> str:
    prefix_setting = db.query(LogisticsGlobalSettings).filter(
        LogisticsGlobalSettings.key == "reference_prefix_maintenance"
    ).first()
    prefix = prefix_setting.value if prefix_setting else "PAN"

    counter_setting = db.query(LogisticsGlobalSettings).filter(
        LogisticsGlobalSettings.key == "reference_counter_maintenance"
    ).first()
    current = int(counter_setting.value) if counter_setting else 0
    return f"{prefix}-{current + 1:04d}"


# ════════════════════════════════════════════════════════════════
# PANNES / MAINTENANCE — CRUD
# ════════════════════════════════════════════════════════════════

def _build_maintenance_response(m: LogisticsMaintenance, db: Session) -> MaintenanceResponse:
    vehicle_registration = None
    if m.vehicle:
        vehicle_registration = m.vehicle.registration_number

    driver_name = None
    if m.reported_by_driver:
        driver_name = f"{m.reported_by_driver.first_name} {m.reported_by_driver.last_name}"

    mechanics_details = []
    if m.mechanics_json:
        for mid in m.mechanics_json:
            mech = db.query(LogisticsMechanic).filter(
                LogisticsMechanic.id == mid,
                LogisticsMechanic.is_deleted == False,
            ).first()
            if mech:
                mechanics_details.append(MechanicSummary(
                    id=mech.id,
                    full_name=f"{mech.first_name} {mech.last_name}",
                    specialty=mech.specialty,
                    has_account=mech.user_id is not None,
                ))

    parts = m.parts_used_json or []

    return MaintenanceResponse(
        id=m.id,
        reference=m.reference,
        vehicle_id=m.vehicle_id,
        vehicle_registration=vehicle_registration,
        category=m.category,
        priority=m.priority,
        description=m.description,
        status=m.status,
        scheduled_date=m.scheduled_date,
        started_at=m.started_at,
        completed_at=m.completed_at,
        mileage_start=m.mileage_start,
        mileage_end=m.mileage_end,
        engine_reference=m.engine_reference,
        mechanics_json=m.mechanics_json or [],
        mechanics_details=mechanics_details,
        reported_by_driver_id=m.reported_by_driver_id,
        reported_by_driver_name=driver_name,
        operations_manager=m.operations_manager,
        parts_used_json=parts,
        labor_cost=m.labor_cost,
        parts_cost=m.parts_cost,
        external_cost=m.external_cost,
        total_cost=m.total_cost,
        notes=m.notes,
        created_at=m.created_at,
        created_by=m.created_by,
        created_by_name=m.created_by_name,
        updated_at=m.updated_at,
    )


def create_maintenance(
    db: Session, data: MaintenanceCreate, user_id: int, user_name: str
) -> MaintenanceResponse:
    reference = get_next_maintenance_reference(db)

    parts_json = [p.model_dump() for p in data.parts_used_json] if data.parts_used_json else []

    # Calcul total_cost
    labor = data.labor_cost or Decimal("0")
    parts = data.parts_cost or Decimal("0")
    external = data.external_cost or Decimal("0")
    total = labor + parts + external

    maintenance = LogisticsMaintenance(
        reference=reference,
        vehicle_id=data.vehicle_id,
        category=data.category,
        priority=data.priority,
        description=data.description,
        status="scheduled",
        scheduled_date=data.scheduled_date,
        mileage_start=data.mileage_start,
        mileage_end=data.mileage_end,
        engine_reference=data.engine_reference,
        mechanics_json=data.mechanics_json or [],
        reported_by_driver_id=data.reported_by_driver_id,
        operations_manager=data.operations_manager,
        parts_used_json=parts_json,
        labor_cost=labor,
        parts_cost=parts,
        external_cost=external,
        total_cost=total,
        notes=data.notes,
        created_by=user_id,
        created_by_name=user_name,
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return _build_maintenance_response(maintenance, db)


def get_maintenances(
    db: Session,
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    company_id: Optional[int] = None,
    priority: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> MaintenanceListResponse:
    query = db.query(LogisticsMaintenance).filter(LogisticsMaintenance.is_deleted == False)

    if vehicle_id:
        query = query.filter(LogisticsMaintenance.vehicle_id == vehicle_id)
    if status:
        query = query.filter(LogisticsMaintenance.status == status)
    if category:
        query = query.filter(LogisticsMaintenance.category == category)
    if priority:
        query = query.filter(LogisticsMaintenance.priority == priority)
    if company_id:
        query = query.join(LogisticsVehicle, LogisticsMaintenance.vehicle_id == LogisticsVehicle.id
                           ).filter(LogisticsVehicle.company_id == company_id)
    if search:
        query = query.filter(
            or_(
                LogisticsMaintenance.reference.ilike(f"%{search}%"),
                LogisticsMaintenance.description.ilike(f"%{search}%"),
                LogisticsMaintenance.operations_manager.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    items = query.order_by(LogisticsMaintenance.scheduled_date.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return MaintenanceListResponse(
        items=[_build_maintenance_response(m, db) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_maintenance(db: Session, maintenance_id: int) -> MaintenanceResponse:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")
    return _build_maintenance_response(m, db)


def update_maintenance(
    db: Session, maintenance_id: int, data: MaintenanceUpdate, user_id: int
) -> MaintenanceResponse:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")

    update_data = data.model_dump(exclude_unset=True)

    if "parts_used_json" in update_data and update_data["parts_used_json"] is not None:
        update_data["parts_used_json"] = [
            p.model_dump() if hasattr(p, "model_dump") else p
            for p in update_data["parts_used_json"]
        ]

    for field, value in update_data.items():
        setattr(m, field, value)

    # Recalculer total_cost
    m.total_cost = (m.labor_cost or Decimal("0")) + (m.parts_cost or Decimal("0")) + (m.external_cost or Decimal("0"))
    m.updated_by = user_id
    db.commit()
    db.refresh(m)
    return _build_maintenance_response(m, db)


def delete_maintenance(db: Session, maintenance_id: int) -> bool:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")
    m.is_deleted = True
    m.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def start_maintenance(db: Session, maintenance_id: int, user_id: int) -> MaintenanceResponse:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")
    if m.status != "scheduled":
        raise HTTPException(status_code=400, detail=f"Impossible de démarrer une fiche au statut '{m.status}'.")
    m.status = "in_progress"
    m.started_at = datetime.now(timezone.utc)
    m.updated_by = user_id
    db.commit()
    db.refresh(m)
    return _build_maintenance_response(m, db)


def close_maintenance(db: Session, maintenance_id: int, user_id: int, notes: Optional[str] = None) -> MaintenanceResponse:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")
    if m.status not in ("scheduled", "in_progress"):
        raise HTTPException(status_code=400, detail=f"Impossible de clôturer une fiche au statut '{m.status}'.")
    m.status = "completed"
    m.completed_at = datetime.now(timezone.utc)
    if notes:
        m.notes = (m.notes or "") + f"\n[Clôture] {notes}"
    m.updated_by = user_id
    db.commit()
    db.refresh(m)
    return _build_maintenance_response(m, db)


def cancel_maintenance(db: Session, maintenance_id: int, user_id: int, notes: Optional[str] = None) -> MaintenanceResponse:
    m = db.query(LogisticsMaintenance).filter(
        LogisticsMaintenance.id == maintenance_id,
        LogisticsMaintenance.is_deleted == False,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Fiche de panne non trouvée.")
    if m.status == "completed":
        raise HTTPException(status_code=400, detail="Impossible d'annuler une fiche déjà clôturée.")
    m.status = "cancelled"
    if notes:
        m.notes = (m.notes or "") + f"\n[Annulation] {notes}"
    m.updated_by = user_id
    db.commit()
    db.refresh(m)
    return _build_maintenance_response(m, db)

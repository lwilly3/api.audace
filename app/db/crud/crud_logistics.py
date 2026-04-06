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
from app.models.model_logistics_driver_team import LogisticsDriver, LogisticsTeam
from app.models.model_logistics_settings import LogisticsConfigOption, LogisticsGlobalSettings
from app.models.model_inventory_company import InventoryCompany
from app.schemas.schema_logistics import (
    VehicleCreate, VehicleResponse, VehicleUpdate, VehicleListResponse,
    DriverCreate, DriverResponse, DriverUpdate, DriverListResponse,
    TeamCreate, TeamResponse, TeamUpdate, TeamListResponse, TeamDetailResponse,
    ConfigOptionCreate, ConfigOptionUpdate, ConfigOptionResponse,
    NextReferenceResponse, LogisticsDashboardStats, LogisticsDashboardResponse,
    AlertSummary,
)
from typing import Optional, List


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

    if company_id:
        vehicle_query = vehicle_query.filter(LogisticsVehicle.company_id == company_id)
        driver_query = driver_query.filter(LogisticsDriver.company_id == company_id)
        team_query = team_query.filter(LogisticsTeam.company_id == company_id)

    total_vehicles = vehicle_query.count()
    vehicles_active = vehicle_query.filter(LogisticsVehicle.status_id != None).count()  # À affiner
    total_drivers = driver_query.count()
    total_teams = team_query.count()

    stats = LogisticsDashboardStats(
        total_vehicles=total_vehicles,
        vehicles_active=vehicles_active,
        total_drivers=total_drivers,
        total_teams=total_teams,
        missions_in_progress=0,  # À implémenter avec les missions
        vehicles_in_maintenance=0,  # À implémenter avec la maintenance
        alerts_count=0,  # À implémenter
    )

    alerts = [
        AlertSummary(type="documents_expiring", count=0, description="Documents expirant bientôt"),
        AlertSummary(type="maintenance_due", count=0, description="Maintenances prévues"),
    ]

    return LogisticsDashboardResponse(stats=stats, alerts=alerts)

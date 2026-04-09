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
from app.models.model_logistics_operations import LogisticsMission, LogisticsMissionCheckpoint, LogisticsFuelLog
from app.models.model_logistics_settings import LogisticsConfigOption, LogisticsGlobalSettings
from app.models.model_inventory_company import InventoryCompany
from app.models.model_user import User
from app.models.model_user_permissions import UserPermissions
from app.schemas.schema_logistics import (
    VehicleCreate, VehicleResponse, VehicleUpdate, VehicleListResponse,
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
    mission_query = db.query(LogisticsMission).filter(LogisticsMission.is_deleted == False)

    if company_id:
        vehicle_query = vehicle_query.filter(LogisticsVehicle.company_id == company_id)
        driver_query = driver_query.filter(LogisticsDriver.company_id == company_id)
        team_query = team_query.filter(LogisticsTeam.company_id == company_id)
        mission_query = mission_query.join(
            LogisticsVehicle, LogisticsMission.vehicle_id == LogisticsVehicle.id
        ).filter(LogisticsVehicle.company_id == company_id)

    total_vehicles = vehicle_query.count()
    vehicles_active = vehicle_query.filter(LogisticsVehicle.is_archived == False).count()
    total_drivers = driver_query.count()
    total_teams = team_query.count()
    missions_in_progress = mission_query.filter(LogisticsMission.status == 'in_progress').count()

    stats = LogisticsDashboardStats(
        total_vehicles=total_vehicles,
        vehicles_active=vehicles_active,
        total_drivers=total_drivers,
        total_teams=total_teams,
        missions_in_progress=missions_in_progress,
        vehicles_in_maintenance=0,  # À implémenter avec la maintenance CRUD
        alerts_count=0,  # À implémenter
    )

    alerts = [
        AlertSummary(type="documents_expiring", count=0, description="Documents expirant bientôt"),
        AlertSummary(type="maintenance_due", count=0, description="Maintenances prévues"),
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

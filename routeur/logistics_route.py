"""
@fileoverview Logistics Module API Routes
Handles all REST endpoints for fleet management, drivers, teams, missions, fuel, maintenance, tires, documents.
Implements authorization checks and request validation via Pydantic schemas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from core.auth import oauth2
from app.db.database import get_db
from app.db.crud.crud_logistics import (
    get_next_vehicle_reference,
    peek_next_vehicle_reference,
    create_vehicle,
    get_vehicles,
    get_vehicle,
    update_vehicle,
    archive_vehicle,
    delete_vehicle,
    get_compartments,
    create_compartment,
    update_compartment,
    delete_compartment,
    get_vehicle_associations,
    get_associations_by_company,
    create_vehicle_association,
    update_vehicle_association,
    delete_vehicle_association,
    create_driver,
    get_drivers,
    get_driver,
    update_driver,
    delete_driver,
    create_team,
    get_teams,
    get_team,
    update_team,
    delete_team,
    get_logistics_dashboard,
    get_next_mission_reference,
    peek_next_mission_reference,
    create_mission,
    get_missions,
    get_mission,
    update_mission,
    delete_mission,
    get_driver_missions,
    start_mission,
    complete_mission,
    cancel_mission,
    submit_mission,
    approve_mission,
    reject_mission,
    add_checkpoint,
    get_mission_checkpoints,
    delete_checkpoint,
    create_fuel_log,
    get_fuel_logs,
    get_fuel_log,
    update_fuel_log,
    delete_fuel_log,
    get_vehicle_fuel_logs,
    get_fuel_alerts,
    create_driver_user,
    get_driver_users,
    toggle_driver_user_active,
    create_mechanic,
    get_mechanics,
    get_mechanic,
    update_mechanic,
    delete_mechanic,
    link_mechanic_to_user,
    create_invitation,
    validate_invitation,
    accept_invitation,
    get_next_maintenance_reference,
    peek_next_maintenance_reference,
    create_maintenance,
    get_maintenances,
    get_maintenance,
    update_maintenance,
    delete_maintenance,
    start_maintenance,
    close_maintenance,
    cancel_maintenance,
)
from app.models.model_user import User
from app.schemas.schema_logistics import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleListResponse,
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverListResponse,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamDetailResponse,
    TeamListResponse,
    NextReferenceResponse,
    LogisticsDashboardResponse,
    MissionCreate,
    MissionUpdate,
    MissionResponse,
    MissionListResponse,
    MissionCompleteRequest,
    MissionRejectRequest,
    CheckpointCreate,
    CheckpointResponse,
    FuelLogCreate,
    FuelLogUpdate,
    FuelLogResponse,
    FuelLogListResponse,
    FuelAlertListResponse,
    DriverUserCreate,
    DriverUserResponse,
    DriverUserListResponse,
    MechanicCreate,
    MechanicUpdate,
    MechanicResponse,
    MechanicListResponse,
    InviteCreateRequest,
    InviteResponse,
    InviteValidateResponse,
    InviteAcceptRequest,
    LinkUserRequest,
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceListResponse,
    MaintenanceStatusUpdate,
    CompartmentCreate,
    CompartmentUpdate,
    CompartmentResponse,
    VehicleAssociationCreate,
    VehicleAssociationUpdate,
    VehicleAssociationResponse,
)

router = APIRouter(prefix="/logistics", tags=["logistics"])


# ============================================================================
# VEHICLES ENDPOINTS
# ============================================================================

@router.get("/vehicles/reference/peek", response_model=NextReferenceResponse)
def peek_vehicle_reference(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Preview next vehicle reference without incrementing counter."""
    if not current_user.permissions.logistics_view:
        raise HTTPException(status_code=403, detail="Access denied")

    next_ref = peek_next_vehicle_reference(db)
    return NextReferenceResponse(next_reference=next_ref)


@router.get("/vehicles/reference/next", response_model=NextReferenceResponse)
def get_vehicle_reference(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get and increment the next vehicle reference."""
    if not current_user.permissions.logistics_view:
        raise HTTPException(status_code=403, detail="Access denied")

    next_ref = get_next_vehicle_reference(db)
    return NextReferenceResponse(next_reference=next_ref)


@router.post("/vehicles", response_model=VehicleResponse)
def create_vehicle_endpoint(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a new vehicle."""
    if not current_user.permissions.logistics_vehicles_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    vehicle = create_vehicle(db, vehicle_data, current_user.id, current_user.username)
    return VehicleResponse.from_orm(vehicle)


@router.get("/vehicles", response_model=VehicleListResponse)
def list_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: int = Query(None),
    search: str = Query(None),
    segment: str = Query(None),
    status: str = Query(None),
    vehicle_role: str = Query(None),
    is_archived: bool = Query(False),
):
    """List vehicles with filtering and pagination."""
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Enforce company scoping unless user can view all
    if not current_user.permissions.logistics_view_all_companies:
        # User can only see vehicles from their company (assume company_id in user context)
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    result = get_vehicles(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        company_id=company_id,
        search=search,
        segment=segment,
        vehicle_role=vehicle_role,
        status_id=None,
        is_archived=is_archived,
    )
    return result


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle_endpoint(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get a specific vehicle by ID."""
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse.from_orm(vehicle)


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle_endpoint(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a vehicle."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    vehicle = update_vehicle(db, vehicle_id, vehicle_data, current_user.id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse.from_orm(vehicle)


@router.post("/vehicles/{vehicle_id}/archive", response_model=VehicleResponse)
def archive_vehicle_endpoint(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Archive a vehicle (soft archive, not deleted)."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    vehicle = archive_vehicle(db, vehicle_id, current_user.id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse.from_orm(vehicle)


@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle_endpoint(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a vehicle (soft delete)."""
    if not current_user.permissions.logistics_vehicles_delete:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_vehicle(db, vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": "Vehicle deleted successfully"}


# ============================================================================
# VEHICLE COMPARTMENTS ENDPOINTS
# ============================================================================

@router.get("/vehicles/{vehicle_id}/compartments", response_model=list[CompartmentResponse])
def list_compartments(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """List all compartments for a vehicle (applicable to porteur_citerne and remorque)."""
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_compartments(db, vehicle_id)


@router.post("/vehicles/{vehicle_id}/compartments", response_model=CompartmentResponse, status_code=201)
def create_compartment_endpoint(
    vehicle_id: int,
    data: CompartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Add a compartment to a tanker vehicle."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return create_compartment(db, vehicle_id, data)


@router.put("/vehicles/{vehicle_id}/compartments/{compartment_id}", response_model=CompartmentResponse)
def update_compartment_endpoint(
    vehicle_id: int,
    compartment_id: int,
    data: CompartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a vehicle compartment."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    comp = update_compartment(db, compartment_id, data)
    if not comp:
        raise HTTPException(status_code=404, detail="Compartment not found")
    return comp


@router.delete("/vehicles/{vehicle_id}/compartments/{compartment_id}")
def delete_compartment_endpoint(
    vehicle_id: int,
    compartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a vehicle compartment."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    success = delete_compartment(db, compartment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Compartment not found")
    return {"message": "Compartment deleted successfully"}


# ============================================================================
# VEHICLE ASSOCIATIONS (TRACTOR ↔ TRAILER) ENDPOINTS
# ============================================================================

@router.get("/vehicles/{vehicle_id}/associations", response_model=list[VehicleAssociationResponse])
def list_vehicle_associations(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """List all tractor↔trailer associations for a vehicle."""
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_vehicle_associations(db, vehicle_id)


@router.get("/vehicle-associations", response_model=list[VehicleAssociationResponse])
def list_associations_by_company(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """List all tractor↔trailer associations for a company."""
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_associations_by_company(db, company_id)


@router.post("/vehicle-associations", response_model=VehicleAssociationResponse, status_code=201)
def create_association_endpoint(
    data: VehicleAssociationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a tractor↔trailer association."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        return create_vehicle_association(db, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/vehicle-associations/{association_id}", response_model=VehicleAssociationResponse)
def update_association_endpoint(
    association_id: int,
    data: VehicleAssociationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a tractor↔trailer association."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    assoc = update_vehicle_association(db, association_id, data)
    if not assoc:
        raise HTTPException(status_code=404, detail="Association not found")
    return assoc


@router.delete("/vehicle-associations/{association_id}")
def delete_association_endpoint(
    association_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a tractor↔trailer association."""
    if not current_user.permissions.logistics_vehicles_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    success = delete_vehicle_association(db, association_id)
    if not success:
        raise HTTPException(status_code=404, detail="Association not found")
    return {"message": "Association deleted successfully"}

@router.post("/drivers", response_model=DriverResponse)
def create_driver_endpoint(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a new driver."""
    if not current_user.permissions.logistics_drivers_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    driver = create_driver(db, driver_data, current_user.id, current_user.username)
    return DriverResponse.from_orm(driver)


@router.get("/drivers", response_model=DriverListResponse)
def list_drivers(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: int = Query(None),
    role: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
):
    """List drivers with filtering and pagination."""
    if not current_user.permissions.logistics_drivers_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Enforce company scoping unless user can view all
    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    result = get_drivers(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        company_id=company_id,
        role=role,
        status=status,
    )
    return result


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
def get_driver_endpoint(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get a specific driver by ID."""
    if not current_user.permissions.logistics_drivers_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    driver = get_driver(db, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return DriverResponse.from_orm(driver)


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
def update_driver_endpoint(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a driver."""
    if not current_user.permissions.logistics_drivers_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    driver = update_driver(db, driver_id, driver_data, current_user.id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return DriverResponse.from_orm(driver)


@router.delete("/drivers/{driver_id}")
def delete_driver_endpoint(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a driver (soft delete)."""
    if not current_user.permissions.logistics_drivers_delete:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_driver(db, driver_id)
    if not success:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"message": "Driver deleted successfully"}


# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

@router.post("/teams", response_model=TeamResponse)
def create_team_endpoint(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a new team (binôme or trinôme)."""
    if not current_user.permissions.logistics_teams_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    team = create_team(db, team_data, current_user.id, current_user.username)
    return TeamResponse.from_orm(team)


@router.get("/teams", response_model=TeamListResponse)
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: int = Query(None),
    status: str = Query(None),
    segment: str = Query(None),
):
    """List teams with filtering and pagination."""
    if not current_user.permissions.logistics_teams_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Enforce company scoping unless user can view all
    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    result = get_teams(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        company_id=company_id,
        status=status,
    )
    return result


@router.get("/teams/{team_id}", response_model=TeamDetailResponse)
def get_team_endpoint(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get a specific team by ID with member details."""
    if not current_user.permissions.logistics_teams_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    team = get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamDetailResponse.from_orm(team)


@router.put("/teams/{team_id}", response_model=TeamResponse)
def update_team_endpoint(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a team."""
    if not current_user.permissions.logistics_teams_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    team = update_team(db, team_id, team_data, current_user.id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.from_orm(team)


@router.delete("/teams/{team_id}")
def delete_team_endpoint(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a team (soft delete)."""
    if not current_user.permissions.logistics_teams_delete:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_team(db, team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted successfully"}


# ============================================================================
# DRIVER USER MANAGEMENT ENDPOINTS (gestion par superviseur)
# ============================================================================

@router.post("/users", response_model=DriverUserResponse, status_code=201)
def create_driver_user_endpoint(
    data: DriverUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a user account + driver record in one operation."""
    if not current_user.permissions.logistics_drivers_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    return create_driver_user(db, data, current_user.id, current_user.username)


@router.get("/users", response_model=DriverUserListResponse)
def list_driver_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: int = Query(None),
    role: str = Query(None),
    search: str = Query(None),
):
    """List drivers with user accounts."""
    if not current_user.permissions.logistics_drivers_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    return get_driver_users(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        company_id=company_id,
        role=role,
        search=search,
    )


@router.put("/users/{driver_id}/toggle-active", response_model=DriverUserResponse)
def toggle_driver_active_endpoint(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Activate/deactivate a driver's user account."""
    if not current_user.permissions.logistics_drivers_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return toggle_driver_user_active(db, driver_id)


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=LogisticsDashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    company_id: int = Query(None),
):
    """Get logistics module dashboard statistics and alerts."""
    if not current_user.permissions.logistics_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Enforce company scoping unless user can view all
    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    dashboard = get_logistics_dashboard(db, company_id=company_id)
    return dashboard


# ============================================================================
# MISSIONS ENDPOINTS
# ============================================================================

@router.get("/missions/reference/peek", response_model=NextReferenceResponse)
def peek_mission_reference(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Preview next mission reference without incrementing counter."""
    if not current_user.permissions.logistics_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    next_ref = peek_next_mission_reference(db)
    return NextReferenceResponse(reference=next_ref)


@router.get("/missions/reference/next", response_model=NextReferenceResponse)
def get_mission_reference(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get and increment the next mission reference."""
    if not current_user.permissions.logistics_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    next_ref = get_next_mission_reference(db)
    return NextReferenceResponse(reference=next_ref)


@router.get("/missions/driver/{driver_id}", response_model=MissionListResponse)
def list_driver_missions(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
):
    """List missions for a specific driver (Mes Missions)."""
    if not (current_user.permissions.logistics_missions_view or current_user.permissions.logistics_missions_view_own):
        raise HTTPException(status_code=403, detail="Permission denied")

    result = get_driver_missions(
        db,
        driver_id=driver_id,
        page=(skip // limit) + 1,
        page_size=limit,
        status_filter=status,
    )
    return result


@router.post("/missions", response_model=MissionResponse)
def create_mission_endpoint(
    mission_data: MissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a new mission."""
    if not current_user.permissions.logistics_missions_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    mission = create_mission(db, mission_data, current_user.id, current_user.username)
    return mission


@router.get("/missions", response_model=MissionListResponse)
def list_missions(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    company_id: int = Query(None),
    segment: str = Query(None),
    status: str = Query(None),
    driver_id: int = Query(None),
    vehicle_id: int = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
):
    """List missions with filtering and pagination."""
    if not current_user.permissions.logistics_missions_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    from datetime import datetime as dt
    parsed_date_from = dt.fromisoformat(date_from) if date_from else None
    parsed_date_to = dt.fromisoformat(date_to) if date_to else None

    result = get_missions(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        segment=segment,
        status=status,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        search=search,
        company_id=company_id,
    )
    return result


@router.get("/missions/{mission_id}", response_model=MissionResponse)
def get_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get a specific mission by ID."""
    if not current_user.permissions.logistics_missions_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    return get_mission(db, mission_id)


@router.put("/missions/{mission_id}", response_model=MissionResponse)
def update_mission_endpoint(
    mission_id: int,
    mission_data: MissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a mission."""
    if not current_user.permissions.logistics_missions_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return update_mission(db, mission_id, mission_data, current_user.id)


@router.delete("/missions/{mission_id}")
def delete_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a mission (soft delete)."""
    if not current_user.permissions.logistics_missions_delete:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_mission(db, mission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"message": "Mission deleted successfully"}


@router.put("/missions/{mission_id}/start", response_model=MissionResponse)
def start_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Start a mission: planned → in_progress."""
    if not current_user.permissions.logistics_missions_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return start_mission(db, mission_id, current_user.id)


@router.put("/missions/{mission_id}/complete", response_model=MissionResponse)
def complete_mission_endpoint(
    mission_id: int,
    data: MissionCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Complete a mission: in_progress → completed."""
    if not current_user.permissions.logistics_missions_submit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return complete_mission(db, mission_id, data, current_user.id)


@router.put("/missions/{mission_id}/cancel", response_model=MissionResponse)
def cancel_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Cancel a mission: planned|in_progress → cancelled."""
    if not current_user.permissions.logistics_missions_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return cancel_mission(db, mission_id, current_user.id)


@router.put("/missions/{mission_id}/submit", response_model=MissionResponse)
def submit_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Submit a completed mission for approval."""
    if not current_user.permissions.logistics_missions_submit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return submit_mission(db, mission_id, current_user.id)


@router.put("/missions/{mission_id}/approve", response_model=MissionResponse)
def approve_mission_endpoint(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Approve a submitted mission."""
    if not current_user.permissions.logistics_missions_approve:
        raise HTTPException(status_code=403, detail="Permission denied")

    return approve_mission(db, mission_id, current_user.id)


@router.put("/missions/{mission_id}/reject", response_model=MissionResponse)
def reject_mission_endpoint(
    mission_id: int,
    data: MissionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Reject a submitted mission."""
    if not current_user.permissions.logistics_missions_approve:
        raise HTTPException(status_code=403, detail="Permission denied")

    return reject_mission(db, mission_id, data, current_user.id)


# ============================================================================
# CHECKPOINTS ENDPOINTS
# ============================================================================

@router.post("/missions/{mission_id}/checkpoints", response_model=CheckpointResponse)
def add_checkpoint_endpoint(
    mission_id: int,
    data: CheckpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Add a checkpoint to a mission."""
    if not current_user.permissions.logistics_missions_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return add_checkpoint(db, mission_id, data)


@router.get("/missions/{mission_id}/checkpoints", response_model=list[CheckpointResponse])
def list_mission_checkpoints(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """List checkpoints for a mission."""
    if not current_user.permissions.logistics_missions_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    return get_mission_checkpoints(db, mission_id)


@router.delete("/checkpoints/{checkpoint_id}")
def delete_checkpoint_endpoint(
    checkpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a checkpoint."""
    if not current_user.permissions.logistics_missions_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_checkpoint(db, checkpoint_id)
    if not success:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"message": "Checkpoint deleted successfully"}


# ============================================================================
# FUEL LOGS ENDPOINTS
# ============================================================================

@router.get("/fuel/alerts", response_model=FuelAlertListResponse)
def list_fuel_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    company_id: int = Query(None),
):
    """Get fuel overconsumption alerts."""
    if not current_user.permissions.logistics_fuel_alerts:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not current_user.permissions.logistics_view_all_companies:
        if hasattr(current_user, 'company_id'):
            company_id = current_user.company_id

    return get_fuel_alerts(db, company_id=company_id)


@router.get("/fuel/vehicle/{vehicle_id}", response_model=FuelLogListResponse)
def list_vehicle_fuel_logs(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List fuel logs for a specific vehicle."""
    if not current_user.permissions.logistics_fuel_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    return get_vehicle_fuel_logs(
        db,
        vehicle_id=vehicle_id,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.post("/fuel", response_model=FuelLogResponse)
def create_fuel_log_endpoint(
    fuel_data: FuelLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Create a new fuel log."""
    if not current_user.permissions.logistics_fuel_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    return create_fuel_log(db, fuel_data, current_user.id, current_user.username)


@router.get("/fuel", response_model=FuelLogListResponse)
def list_fuel_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    vehicle_id: int = Query(None),
    driver_id: int = Query(None),
    mission_id: int = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
):
    """List fuel logs with filtering and pagination."""
    if not current_user.permissions.logistics_fuel_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    from datetime import datetime as dt
    parsed_date_from = dt.fromisoformat(date_from) if date_from else None
    parsed_date_to = dt.fromisoformat(date_to) if date_to else None

    return get_fuel_logs(
        db,
        page=(skip // limit) + 1,
        page_size=limit,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        mission_id=mission_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )


@router.get("/fuel/{fuel_id}", response_model=FuelLogResponse)
def get_fuel_log_endpoint(
    fuel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Get a specific fuel log by ID."""
    if not current_user.permissions.logistics_fuel_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    return get_fuel_log(db, fuel_id)


@router.put("/fuel/{fuel_id}", response_model=FuelLogResponse)
def update_fuel_log_endpoint(
    fuel_id: int,
    fuel_data: FuelLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Update a fuel log."""
    if not current_user.permissions.logistics_fuel_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    return update_fuel_log(db, fuel_id, fuel_data, current_user.id)


@router.delete("/fuel/{fuel_id}")
def delete_fuel_log_endpoint(
    fuel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Delete a fuel log (soft delete)."""
    if not current_user.permissions.logistics_fuel_edit:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = delete_fuel_log(db, fuel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fuel log not found")
    return {"message": "Fuel log deleted successfully"}


# ============================================================================
# MÉCANICIENS ENDPOINTS
# ============================================================================

@router.post("/mechanics", response_model=MechanicResponse, status_code=201)
def create_mechanic_endpoint(
    data: MechanicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Créer un mécanicien (peut être sans compte application)."""
    if not current_user.permissions.logistics_mechanics_manage:
        raise HTTPException(status_code=403, detail="Permission denied")
    return create_mechanic(db, data, current_user.id, current_user.username)


@router.get("/mechanics", response_model=MechanicListResponse)
def list_mechanics_endpoint(
    company_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Lister les mécaniciens."""
    if not current_user.permissions.logistics_mechanics_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_mechanics(db, company_id=company_id, is_active=is_active, search=search, page=page, page_size=page_size)


@router.get("/mechanics/{mechanic_id}", response_model=MechanicResponse)
def get_mechanic_endpoint(
    mechanic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Détail d'un mécanicien."""
    if not current_user.permissions.logistics_mechanics_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_mechanic(db, mechanic_id)


@router.put("/mechanics/{mechanic_id}", response_model=MechanicResponse)
def update_mechanic_endpoint(
    mechanic_id: int,
    data: MechanicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Mettre à jour un mécanicien."""
    if not current_user.permissions.logistics_mechanics_manage:
        raise HTTPException(status_code=403, detail="Permission denied")
    return update_mechanic(db, mechanic_id, data, current_user.id)


@router.delete("/mechanics/{mechanic_id}")
def delete_mechanic_endpoint(
    mechanic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Supprimer un mécanicien (soft delete)."""
    if not current_user.permissions.logistics_mechanics_manage:
        raise HTTPException(status_code=403, detail="Permission denied")
    delete_mechanic(db, mechanic_id)
    return {"message": "Mécanicien supprimé."}


@router.post("/mechanics/{mechanic_id}/invite", response_model=InviteResponse)
def invite_mechanic_endpoint(
    mechanic_id: int,
    data: InviteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Générer un lien d'invitation pour un mécanicien sans compte."""
    if not current_user.permissions.logistics_mechanics_manage:
        raise HTTPException(status_code=403, detail="Permission denied")
    return create_invitation(
        db,
        entity_type="mechanic",
        entity_id=mechanic_id,
        email=data.email,
        created_by=current_user.id,
        created_by_name=current_user.username,
    )


@router.put("/mechanics/{mechanic_id}/link-user", response_model=MechanicResponse)
def link_mechanic_user_endpoint(
    mechanic_id: int,
    data: LinkUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Lier manuellement un mécanicien à un compte existant (admin)."""
    if not current_user.permissions.logistics_mechanics_manage:
        raise HTTPException(status_code=403, detail="Permission denied")
    return link_mechanic_to_user(db, mechanic_id, data.user_id)


# ============================================================================
# INVITATIONS ENDPOINTS (publics — sans authentification)
# ============================================================================

@router.get("/invite/validate/{token}", response_model=InviteValidateResponse)
def validate_invite_endpoint(token: str, db: Session = Depends(get_db)):
    """Valider un token d'invitation et récupérer les infos du profil."""
    return validate_invitation(db, token)


@router.post("/invite/accept/{token}")
def accept_invite_endpoint(
    token: str,
    data: InviteAcceptRequest,
    db: Session = Depends(get_db),
):
    """Accepter une invitation : créer le compte et lier le profil."""
    return accept_invitation(db, token, data)


# Invitation depuis un profil chauffeur existant
@router.post("/drivers/{driver_id}/invite", response_model=InviteResponse)
def invite_driver_endpoint(
    driver_id: int,
    data: InviteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Générer un lien d'invitation pour un chauffeur sans compte."""
    if not current_user.permissions.logistics_drivers_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return create_invitation(
        db,
        entity_type="driver",
        entity_id=driver_id,
        email=data.email,
        created_by=current_user.id,
        created_by_name=current_user.username,
    )


# ============================================================================
# PANNES / MAINTENANCE ENDPOINTS
# ============================================================================

@router.get("/maintenance/reference/peek", response_model=NextReferenceResponse)
def peek_maintenance_reference_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Aperçu de la prochaine référence PAN-XXXX sans l'incrémenter."""
    reference = peek_next_maintenance_reference(db)
    return NextReferenceResponse(reference=reference)


@router.get("/maintenance/reference/next", response_model=NextReferenceResponse)
def next_maintenance_reference_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Réserver la prochaine référence PAN-XXXX (incrémente le compteur)."""
    reference = get_next_maintenance_reference(db)
    return NextReferenceResponse(reference=reference)


@router.post("/maintenance", response_model=MaintenanceResponse, status_code=201)
def create_maintenance_endpoint(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Créer une nouvelle fiche de panne."""
    if not current_user.permissions.logistics_maintenance_create:
        raise HTTPException(status_code=403, detail="Permission denied")
    return create_maintenance(db, data, current_user.id, current_user.username)


@router.get("/maintenance", response_model=MaintenanceListResponse)
def list_maintenance_endpoint(
    vehicle_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Lister les fiches de panne avec filtres."""
    if not current_user.permissions.logistics_maintenance_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_maintenances(
        db, vehicle_id=vehicle_id, status=status, category=category,
        company_id=company_id, priority=priority, search=search,
        page=page, page_size=page_size,
    )


@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance_endpoint(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Détail d'une fiche de panne."""
    if not current_user.permissions.logistics_maintenance_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    return get_maintenance(db, maintenance_id)


@router.put("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance_endpoint(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Mettre à jour une fiche de panne."""
    if not current_user.permissions.logistics_maintenance_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return update_maintenance(db, maintenance_id, data, current_user.id)


@router.delete("/maintenance/{maintenance_id}")
def delete_maintenance_endpoint(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Supprimer une fiche de panne (soft delete)."""
    if not current_user.permissions.logistics_maintenance_delete:
        raise HTTPException(status_code=403, detail="Permission denied")
    delete_maintenance(db, maintenance_id)
    return {"message": "Fiche de panne supprimée."}


@router.put("/maintenance/{maintenance_id}/start", response_model=MaintenanceResponse)
def start_maintenance_endpoint(
    maintenance_id: int,
    data: MaintenanceStatusUpdate = MaintenanceStatusUpdate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Démarrer une intervention (scheduled → in_progress)."""
    if not current_user.permissions.logistics_maintenance_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return start_maintenance(db, maintenance_id, current_user.id)


@router.put("/maintenance/{maintenance_id}/close", response_model=MaintenanceResponse)
def close_maintenance_endpoint(
    maintenance_id: int,
    data: MaintenanceStatusUpdate = MaintenanceStatusUpdate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Clôturer une intervention (→ completed)."""
    if not current_user.permissions.logistics_maintenance_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return close_maintenance(db, maintenance_id, current_user.id, data.notes)


@router.put("/maintenance/{maintenance_id}/cancel", response_model=MaintenanceResponse)
def cancel_maintenance_endpoint(
    maintenance_id: int,
    data: MaintenanceStatusUpdate = MaintenanceStatusUpdate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    """Annuler une intervention (→ cancelled)."""
    if not current_user.permissions.logistics_maintenance_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    return cancel_maintenance(db, maintenance_id, current_user.id, data.notes)

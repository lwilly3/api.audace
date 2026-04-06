"""
@fileoverview Logistics Module API Routes
Handles all REST endpoints for fleet management, drivers, teams, missions, fuel, maintenance, tires, documents.
Implements authorization checks and request validation via Pydantic schemas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
        skip=skip,
        limit=limit,
        company_id=company_id,
        search=search,
        segment=segment,
        status=status,
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
# DRIVERS ENDPOINTS
# ============================================================================

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
        skip=skip,
        limit=limit,
        company_id=company_id,
        role=role,
        status=status,
        search=search,
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
        skip=skip,
        limit=limit,
        company_id=company_id,
        status=status,
        segment=segment,
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

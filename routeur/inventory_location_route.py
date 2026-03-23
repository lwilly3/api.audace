from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_locations import (
    create_company, get_companies, get_company_by_id, update_company, soft_delete_company,
    create_site, get_sites, get_site_by_id, update_site, soft_delete_site,
    create_room, get_rooms, get_room_by_id, update_room, soft_delete_room,
    get_location_tree,
)
from app.schemas.schema_inventory_locations import (
    CompanyCreate, CompanyResponse, CompanyUpdate,
    SiteCreate, SiteResponse, SiteUpdate,
    RoomCreate, RoomResponse, RoomUpdate,
    CompanyWithSites,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-locations"]
)


# ════════════════════════════════════════════════════════════════
# COMPANIES
# ════════════════════════════════════════════════════════════════

@router.post("/companies/", response_model=CompanyResponse)
def create_company_route(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_company(db, data)
    log_action(db, current_user.id, "create", "inventory_companies", result.id)
    return result


@router.get("/companies/", response_model=list[CompanyResponse])
def get_companies_route(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_companies(db, include_inactive)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company_route(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_company_by_id(db, company_id)


@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company_route(
    company_id: int,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_company(db, company_id, data)
    log_action(db, current_user.id, "update", "inventory_companies", company_id)
    return result


@router.delete("/companies/{company_id}", response_model=bool)
def delete_company_route(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = soft_delete_company(db, company_id)
    log_action(db, current_user.id, "soft_delete", "inventory_companies", company_id)
    return result


# ════════════════════════════════════════════════════════════════
# SITES
# ════════════════════════════════════════════════════════════════

@router.post("/sites/", response_model=SiteResponse)
def create_site_route(
    data: SiteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_site(db, data)
    log_action(db, current_user.id, "create", "inventory_sites", result.id)
    return result


@router.get("/sites/", response_model=list[SiteResponse])
def get_sites_route(
    company_id: int | None = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_sites(db, company_id, include_inactive)


@router.get("/sites/{site_id}", response_model=SiteResponse)
def get_site_route(
    site_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_site_by_id(db, site_id)


@router.put("/sites/{site_id}", response_model=SiteResponse)
def update_site_route(
    site_id: int,
    data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_site(db, site_id, data)
    log_action(db, current_user.id, "update", "inventory_sites", site_id)
    return result


@router.delete("/sites/{site_id}", response_model=bool)
def delete_site_route(
    site_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = soft_delete_site(db, site_id)
    log_action(db, current_user.id, "soft_delete", "inventory_sites", site_id)
    return result


# ════════════════════════════════════════════════════════════════
# ROOMS
# ════════════════════════════════════════════════════════════════

@router.post("/rooms/", response_model=RoomResponse)
def create_room_route(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_room(db, data)
    log_action(db, current_user.id, "create", "inventory_rooms", result.id)
    return result


@router.get("/rooms/", response_model=list[RoomResponse])
def get_rooms_route(
    site_id: int | None = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_rooms(db, site_id, include_inactive)


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room_route(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_room_by_id(db, room_id)


@router.put("/rooms/{room_id}", response_model=RoomResponse)
def update_room_route(
    room_id: int,
    data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_room(db, room_id, data)
    log_action(db, current_user.id, "update", "inventory_rooms", room_id)
    return result


@router.delete("/rooms/{room_id}", response_model=bool)
def delete_room_route(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = soft_delete_room(db, room_id)
    log_action(db, current_user.id, "soft_delete", "inventory_rooms", room_id)
    return result


# ════════════════════════════════════════════════════════════════
# LOCATION TREE
# ════════════════════════════════════════════════════════════════

@router.get("/locations/tree", response_model=list[CompanyWithSites])
def get_location_tree_route(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_location_tree(db)

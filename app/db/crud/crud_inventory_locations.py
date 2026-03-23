from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_company import InventoryCompany
from app.models.model_inventory_site import InventorySite
from app.models.model_inventory_room import InventoryRoom
from app.schemas.schema_inventory_locations import (
    CompanyCreate, CompanyResponse, CompanyUpdate,
    SiteCreate, SiteResponse, SiteUpdate,
    RoomCreate, RoomResponse, RoomUpdate,
    CompanyWithSites, SiteWithRooms, RoomBrief,
)


# ════════════════════════════════════════════════════════════════
# COMPANY CRUD
# ════════════════════════════════════════════════════════════════

def create_company(db: Session, data: CompanyCreate) -> CompanyResponse:
    try:
        company = InventoryCompany(
            name=data.name,
            code=data.code,
            type=data.type,
            description=data.description,
            address=data.address,
            phone=data.phone,
            email=data.email,
            logo_url=data.logo_url,
            can_share_equipment=data.can_share_equipment,
            can_borrow_equipment=data.can_borrow_equipment,
            requires_approval_to_lend=data.requires_approval_to_lend,
            requires_approval_to_borrow=data.requires_approval_to_borrow,
            parent_company_id=data.parent_company_id,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return CompanyResponse.model_validate(company)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation entreprise: {str(e)}")


def get_companies(db: Session, include_inactive: bool = False) -> list[CompanyResponse]:
    try:
        query = db.query(InventoryCompany).filter(InventoryCompany.is_deleted == False)
        if not include_inactive:
            query = query.filter(InventoryCompany.is_active == True)
        companies = query.order_by(InventoryCompany.name).all()
        return [CompanyResponse.model_validate(c) for c in companies]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation entreprises: {str(e)}")


def get_company_by_id(db: Session, company_id: int) -> CompanyResponse:
    company = db.query(InventoryCompany).filter(
        InventoryCompany.id == company_id,
        InventoryCompany.is_deleted == False
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvee")
    return CompanyResponse.model_validate(company)


def update_company(db: Session, company_id: int, data: CompanyUpdate) -> CompanyResponse:
    try:
        company = db.query(InventoryCompany).filter(
            InventoryCompany.id == company_id,
            InventoryCompany.is_deleted == False
        ).first()
        if not company:
            raise HTTPException(status_code=404, detail="Entreprise non trouvee")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        db.commit()
        db.refresh(company)
        return CompanyResponse.model_validate(company)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour entreprise: {str(e)}")


def soft_delete_company(db: Session, company_id: int) -> bool:
    try:
        company = db.query(InventoryCompany).filter(InventoryCompany.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Entreprise non trouvee")
        company.is_deleted = True
        company.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression entreprise: {str(e)}")


# ════════════════════════════════════════════════════════════════
# SITE CRUD
# ════════════════════════════════════════════════════════════════

def create_site(db: Session, data: SiteCreate) -> SiteResponse:
    try:
        # Verifier que l'entreprise existe
        company = db.query(InventoryCompany).filter(
            InventoryCompany.id == data.company_id,
            InventoryCompany.is_deleted == False
        ).first()
        if not company:
            raise HTTPException(status_code=404, detail="Entreprise non trouvee")

        site = InventorySite(
            company_id=data.company_id,
            name=data.name,
            code=data.code,
            type=data.type,
            address_street=data.address_street,
            address_city=data.address_city,
            address_postal_code=data.address_postal_code,
            address_country=data.address_country,
            latitude=data.latitude,
            longitude=data.longitude,
            phone=data.phone,
            email=data.email,
            manager_user_id=data.manager_user_id,
            manager_user_name=data.manager_user_name,
        )
        db.add(site)
        db.commit()
        db.refresh(site)

        response = SiteResponse.model_validate(site)
        response.company_name = company.name
        return response
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation site: {str(e)}")


def get_sites(db: Session, company_id: int | None = None, include_inactive: bool = False) -> list[SiteResponse]:
    try:
        query = db.query(InventorySite).options(
            joinedload(InventorySite.company)
        ).filter(InventorySite.is_deleted == False)

        if company_id is not None:
            query = query.filter(InventorySite.company_id == company_id)
        if not include_inactive:
            query = query.filter(InventorySite.is_active == True)

        sites = query.order_by(InventorySite.name).all()
        result = []
        for site in sites:
            resp = SiteResponse.model_validate(site)
            resp.company_name = site.company.name if site.company else None
            result.append(resp)
        return result
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation sites: {str(e)}")


def get_site_by_id(db: Session, site_id: int) -> SiteResponse:
    site = db.query(InventorySite).options(
        joinedload(InventorySite.company)
    ).filter(
        InventorySite.id == site_id,
        InventorySite.is_deleted == False
    ).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouve")
    resp = SiteResponse.model_validate(site)
    resp.company_name = site.company.name if site.company else None
    return resp


def update_site(db: Session, site_id: int, data: SiteUpdate) -> SiteResponse:
    try:
        site = db.query(InventorySite).options(
            joinedload(InventorySite.company)
        ).filter(
            InventorySite.id == site_id,
            InventorySite.is_deleted == False
        ).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouve")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(site, field, value)

        db.commit()
        db.refresh(site)
        resp = SiteResponse.model_validate(site)
        resp.company_name = site.company.name if site.company else None
        return resp
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour site: {str(e)}")


def soft_delete_site(db: Session, site_id: int) -> bool:
    try:
        site = db.query(InventorySite).filter(InventorySite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouve")
        site.is_deleted = True
        site.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression site: {str(e)}")


# ════════════════════════════════════════════════════════════════
# ROOM CRUD
# ════════════════════════════════════════════════════════════════

def create_room(db: Session, data: RoomCreate) -> RoomResponse:
    try:
        site = db.query(InventorySite).options(
            joinedload(InventorySite.company)
        ).filter(
            InventorySite.id == data.site_id,
            InventorySite.is_deleted == False
        ).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouve")

        room = InventoryRoom(
            site_id=data.site_id,
            name=data.name,
            code=data.code,
            type=data.type,
            floor=data.floor,
            building=data.building,
            capacity=data.capacity,
            description=data.description,
        )
        db.add(room)
        db.commit()
        db.refresh(room)

        resp = RoomResponse.model_validate(room)
        resp.site_name = site.name
        resp.company_id = site.company_id
        return resp
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation local: {str(e)}")


def get_rooms(db: Session, site_id: int | None = None, include_inactive: bool = False) -> list[RoomResponse]:
    try:
        query = db.query(InventoryRoom).options(
            joinedload(InventoryRoom.site).joinedload(InventorySite.company)
        ).filter(InventoryRoom.is_deleted == False)

        if site_id is not None:
            query = query.filter(InventoryRoom.site_id == site_id)
        if not include_inactive:
            query = query.filter(InventoryRoom.is_active == True)

        rooms = query.order_by(InventoryRoom.name).all()
        result = []
        for room in rooms:
            resp = RoomResponse.model_validate(room)
            resp.site_name = room.site.name if room.site else None
            resp.company_id = room.site.company_id if room.site else None
            result.append(resp)
        return result
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation locaux: {str(e)}")


def get_room_by_id(db: Session, room_id: int) -> RoomResponse:
    room = db.query(InventoryRoom).options(
        joinedload(InventoryRoom.site)
    ).filter(
        InventoryRoom.id == room_id,
        InventoryRoom.is_deleted == False
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Local non trouve")
    resp = RoomResponse.model_validate(room)
    resp.site_name = room.site.name if room.site else None
    resp.company_id = room.site.company_id if room.site else None
    return resp


def update_room(db: Session, room_id: int, data: RoomUpdate) -> RoomResponse:
    try:
        room = db.query(InventoryRoom).options(
            joinedload(InventoryRoom.site)
        ).filter(
            InventoryRoom.id == room_id,
            InventoryRoom.is_deleted == False
        ).first()
        if not room:
            raise HTTPException(status_code=404, detail="Local non trouve")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)

        db.commit()
        db.refresh(room)
        resp = RoomResponse.model_validate(room)
        resp.site_name = room.site.name if room.site else None
        resp.company_id = room.site.company_id if room.site else None
        return resp
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour local: {str(e)}")


def soft_delete_room(db: Session, room_id: int) -> bool:
    try:
        room = db.query(InventoryRoom).filter(InventoryRoom.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Local non trouve")
        room.is_deleted = True
        room.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression local: {str(e)}")


# ════════════════════════════════════════════════════════════════
# LOCATION TREE
# ════════════════════════════════════════════════════════════════

def get_location_tree(db: Session) -> list[CompanyWithSites]:
    """Retourne la hierarchie complete : entreprises > sites > locaux."""
    try:
        companies = db.query(InventoryCompany).options(
            joinedload(InventoryCompany.sites).joinedload(InventorySite.rooms)
        ).filter(
            InventoryCompany.is_deleted == False,
            InventoryCompany.is_active == True,
        ).order_by(InventoryCompany.name).all()

        result = []
        for company in companies:
            sites_data = []
            for site in sorted(company.sites, key=lambda s: s.name):
                if site.is_deleted or not site.is_active:
                    continue
                rooms_data = [
                    RoomBrief(
                        id=room.id,
                        name=room.name,
                        code=room.code,
                        type=room.type,
                        is_active=room.is_active,
                    )
                    for room in sorted(site.rooms, key=lambda r: r.name)
                    if not room.is_deleted and room.is_active
                ]
                sites_data.append(SiteWithRooms(
                    id=site.id,
                    name=site.name,
                    code=site.code,
                    type=site.type,
                    is_active=site.is_active,
                    rooms=rooms_data,
                ))
            result.append(CompanyWithSites(
                id=company.id,
                name=company.name,
                code=company.code,
                type=company.type,
                is_active=company.is_active,
                sites=sites_data,
            ))
        return result
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation arbre localisations: {str(e)}")

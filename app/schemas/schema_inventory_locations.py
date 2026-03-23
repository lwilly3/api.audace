from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ════════════════════════════════════════════════════════════════
# COMPANY
# ════════════════════════════════════════════════════════════════

class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Nom de l'entreprise")
    code: str = Field(..., max_length=10, description="Code unique")
    type: str = Field(..., max_length=50, description="Type d'activite")
    description: Optional[str] = Field(None, description="Description")
    address: Optional[str] = Field(None, description="Adresse")
    phone: Optional[str] = Field(None, max_length=50, description="Telephone")
    email: Optional[str] = Field(None, max_length=255, description="Email")
    logo_url: Optional[str] = Field(None, description="URL du logo")
    can_share_equipment: bool = Field(True, description="Peut partager du materiel")
    can_borrow_equipment: bool = Field(True, description="Peut emprunter du materiel")
    requires_approval_to_lend: bool = Field(True, description="Approbation requise pour preter")
    requires_approval_to_borrow: bool = Field(True, description="Approbation requise pour emprunter")
    parent_company_id: Optional[int] = Field(None, description="ID entreprise parente")

    model_config = ConfigDict(from_attributes=True)


class CompanyResponse(BaseModel):
    id: int
    name: str
    code: str
    type: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    can_share_equipment: bool
    can_borrow_equipment: bool
    requires_approval_to_lend: bool
    requires_approval_to_borrow: bool
    parent_company_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=10)
    type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    can_share_equipment: Optional[bool] = None
    can_borrow_equipment: Optional[bool] = None
    requires_approval_to_lend: Optional[bool] = None
    requires_approval_to_borrow: Optional[bool] = None
    parent_company_id: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# SITE
# ════════════════════════════════════════════════════════════════

class SiteCreate(BaseModel):
    company_id: int = Field(..., description="ID de l'entreprise")
    name: str = Field(..., max_length=255, description="Nom du site")
    code: str = Field(..., max_length=20, description="Code unique par entreprise")
    type: str = Field(..., max_length=50, description="Type de site")
    address_street: Optional[str] = Field(None, description="Rue")
    address_city: Optional[str] = Field(None, max_length=255, description="Ville")
    address_postal_code: Optional[str] = Field(None, max_length=20, description="Code postal")
    address_country: Optional[str] = Field(None, max_length=100, description="Pays")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    phone: Optional[str] = Field(None, max_length=50, description="Telephone")
    email: Optional[str] = Field(None, max_length=255, description="Email")
    manager_user_id: Optional[int] = Field(None, description="ID du responsable")
    manager_user_name: Optional[str] = Field(None, max_length=255, description="Nom du responsable")

    model_config = ConfigDict(from_attributes=True)


class SiteResponse(BaseModel):
    id: int
    company_id: int
    company_name: Optional[str] = None
    name: str
    code: str
    type: str
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_user_id: Optional[int] = None
    manager_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class SiteUpdate(BaseModel):
    company_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=20)
    type: Optional[str] = Field(None, max_length=50)
    address_street: Optional[str] = None
    address_city: Optional[str] = Field(None, max_length=255)
    address_postal_code: Optional[str] = Field(None, max_length=20)
    address_country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    manager_user_id: Optional[int] = None
    manager_user_name: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# ROOM
# ════════════════════════════════════════════════════════════════

class RoomCreate(BaseModel):
    site_id: int = Field(..., description="ID du site")
    name: str = Field(..., max_length=255, description="Nom du local")
    code: str = Field(..., max_length=20, description="Code")
    type: str = Field(..., max_length=50, description="Type de local")
    floor: Optional[str] = Field(None, max_length=50, description="Etage")
    building: Optional[str] = Field(None, max_length=255, description="Batiment")
    capacity: Optional[int] = Field(None, description="Capacite")
    description: Optional[str] = Field(None, description="Description")

    model_config = ConfigDict(from_attributes=True)


class RoomResponse(BaseModel):
    id: int
    site_id: int
    site_name: Optional[str] = None
    company_id: Optional[int] = None
    name: str
    code: str
    type: str
    floor: Optional[str] = None
    building: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    site_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=20)
    type: Optional[str] = Field(None, max_length=50)
    floor: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=255)
    capacity: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# LOCATION TREE (hierarchie complete)
# ════════════════════════════════════════════════════════════════

class RoomBrief(BaseModel):
    id: int
    name: str
    code: str
    type: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SiteWithRooms(BaseModel):
    id: int
    name: str
    code: str
    type: str
    is_active: bool
    rooms: list[RoomBrief] = []

    model_config = ConfigDict(from_attributes=True)


class CompanyWithSites(BaseModel):
    id: int
    name: str
    code: str
    type: str
    is_active: bool
    sites: list[SiteWithRooms] = []

    model_config = ConfigDict(from_attributes=True)

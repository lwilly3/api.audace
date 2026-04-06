"""
Schémas Pydantic pour le module Logistique.

Validation et sérialisation des données pour l'API REST.
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List


# ════════════════════════════════════════════════════════════════
# VEHICULES
# ════════════════════════════════════════════════════════════════

class VehicleBase(BaseModel):
    registration_number: str
    segment: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    capacity_value: Optional[Decimal] = None
    capacity_unit: Optional[str] = None
    company_id: int
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    internal_reference: Optional[str] = None
    type_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    status_id: int
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = None
    base_site_id: Optional[int] = None


class VehicleUpdate(BaseModel):
    registration_number: Optional[str] = None
    segment: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity_value: Optional[Decimal] = None
    capacity_unit: Optional[str] = None
    status_id: Optional[int] = None
    mileage_counter: Optional[int] = None
    current_driver_id: Optional[int] = None
    notes: Optional[str] = None


class VehicleResponse(VehicleBase):
    id: int
    internal_reference: Optional[str]
    status_id: int
    status_name: Optional[str]
    mileage_counter: int
    is_archived: bool
    created_at: datetime
    created_by: int
    created_by_name: str

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    items: List[VehicleResponse]
    total: int
    page: int
    page_size: int


class NextReferenceResponse(BaseModel):
    reference: str


# ════════════════════════════════════════════════════════════════
# CHAUFFEURS
# ════════════════════════════════════════════════════════════════

class DriverBase(BaseModel):
    first_name: str
    last_name: str
    role: str = "driver"
    phone: Optional[str] = None
    email: Optional[str] = None
    company_id: int


class DriverCreate(DriverBase):
    license_types_json: Optional[List[str]] = None
    license_expiry: Optional[date] = None
    adr_certificate_expiry: Optional[date] = None
    hire_date: Optional[date] = None
    notes: Optional[str] = None


class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_types_json: Optional[List[str]] = None
    license_expiry: Optional[date] = None
    adr_certificate_expiry: Optional[date] = None
    status: Optional[str] = None
    assigned_vehicle_id: Optional[int] = None
    team_id: Optional[int] = None
    notes: Optional[str] = None


class DriverResponse(DriverBase):
    id: int
    status: str
    assigned_vehicle_id: Optional[int]
    team_id: Optional[int]
    license_types_json: Optional[List[str]]
    license_expiry: Optional[date]
    is_archived: bool
    created_at: datetime
    created_by: int
    created_by_name: str

    class Config:
        from_attributes = True


class DriverListResponse(BaseModel):
    items: List[DriverResponse]
    total: int
    page: int
    page_size: int


# ════════════════════════════════════════════════════════════════
# ÉQUIPES
# ════════════════════════════════════════════════════════════════

class TeamBase(BaseModel):
    name: str
    leader_id: int
    company_id: int
    preferred_segment: Optional[str] = None
    default_vehicle_id: Optional[int] = None


class TeamCreate(TeamBase):
    code: Optional[str] = None
    notes: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    leader_id: Optional[int] = None
    preferred_segment: Optional[str] = None
    default_vehicle_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TeamResponse(TeamBase):
    id: int
    code: Optional[str]
    status: str
    is_deleted: bool
    created_at: datetime
    created_by: int
    created_by_name: str

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    members: List[DriverResponse] = []


class TeamListResponse(BaseModel):
    items: List[TeamResponse]
    total: int
    page: int
    page_size: int


# ════════════════════════════════════════════════════════════════
# OPTIONS CONFIGURABLES
# ════════════════════════════════════════════════════════════════

class ConfigOptionCreate(BaseModel):
    list_type: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True


class ConfigOptionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ConfigOptionResponse(BaseModel):
    id: int
    list_type: str
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    is_default: bool
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# PARAMÈTRES GLOBAUX
# ════════════════════════════════════════════════════════════════

class GlobalSettingsUpdate(BaseModel):
    entries: dict[str, str]


class GlobalSettingsResponse(BaseModel):
    settings: dict[str, str]


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════

class LogisticsDashboardStats(BaseModel):
    total_vehicles: int
    vehicles_active: int
    total_drivers: int
    total_teams: int
    missions_in_progress: int
    vehicles_in_maintenance: int
    alerts_count: int


class AlertSummary(BaseModel):
    type: str
    count: int
    description: str


class LogisticsDashboardResponse(BaseModel):
    stats: LogisticsDashboardStats
    alerts: List[AlertSummary]

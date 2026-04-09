"""
Schémas Pydantic pour le module Logistique.

Validation et sérialisation des données pour l'API REST.
"""
from pydantic import BaseModel, Field, EmailStr
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

# ════════════════════════════════════════════════════════════════
# MISSIONS
# ════════════════════════════════════════════════════════════════

class MissionBase(BaseModel):
    vehicle_id: int
    driver_id: int
    segment: str
    departure_location: str
    arrival_location: str
    planned_date: datetime


class MissionCreate(MissionBase):
    co_driver_id: Optional[int] = None
    team_id: Optional[int] = None
    client_name: Optional[str] = None
    client_reference: Optional[str] = None
    departure_lat: Optional[float] = None
    departure_lng: Optional[float] = None
    arrival_lat: Optional[float] = None
    arrival_lng: Optional[float] = None
    distance_planned_km: Optional[float] = None
    mileage_start: Optional[int] = None
    cargo_type_id: Optional[int] = None
    cargo_description: Optional[str] = None
    cargo_loaded_qty: Optional[Decimal] = None
    cargo_unit: Optional[str] = None
    # Grumier
    wood_species: Optional[str] = None
    log_count: Optional[int] = None
    # Citerne
    product_name: Optional[str] = None
    depotage_cert_number: Optional[str] = None
    tank_calibrated: Optional[bool] = None
    # Plateau
    container_count: Optional[int] = None
    fill_rate_percent: Optional[Decimal] = None
    # Financier
    revenue: Optional[Decimal] = None
    toll_cost: Optional[Decimal] = None
    other_costs: Optional[Decimal] = None
    notes: Optional[str] = None


class MissionUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    co_driver_id: Optional[int] = None
    team_id: Optional[int] = None
    segment: Optional[str] = None
    client_name: Optional[str] = None
    client_reference: Optional[str] = None
    departure_location: Optional[str] = None
    departure_lat: Optional[float] = None
    departure_lng: Optional[float] = None
    arrival_location: Optional[str] = None
    arrival_lat: Optional[float] = None
    arrival_lng: Optional[float] = None
    distance_planned_km: Optional[float] = None
    planned_date: Optional[datetime] = None
    mileage_start: Optional[int] = None
    cargo_type_id: Optional[int] = None
    cargo_description: Optional[str] = None
    cargo_loaded_qty: Optional[Decimal] = None
    cargo_unit: Optional[str] = None
    wood_species: Optional[str] = None
    log_count: Optional[int] = None
    product_name: Optional[str] = None
    depotage_cert_number: Optional[str] = None
    tank_calibrated: Optional[bool] = None
    container_count: Optional[int] = None
    fill_rate_percent: Optional[Decimal] = None
    revenue: Optional[Decimal] = None
    toll_cost: Optional[Decimal] = None
    other_costs: Optional[Decimal] = None
    notes: Optional[str] = None


class MissionResponse(MissionBase):
    id: int
    reference: str
    co_driver_id: Optional[int]
    team_id: Optional[int]
    status: str
    client_name: Optional[str]
    client_reference: Optional[str]
    departure_lat: Optional[float]
    departure_lng: Optional[float]
    arrival_lat: Optional[float]
    arrival_lng: Optional[float]
    distance_planned_km: Optional[float]
    distance_actual_km: Optional[float]
    mileage_start: Optional[int]
    mileage_end: Optional[int]
    actual_departure: Optional[datetime]
    actual_arrival: Optional[datetime]
    return_empty: bool
    cargo_type_id: Optional[int]
    cargo_description: Optional[str]
    cargo_loaded_qty: Optional[Decimal]
    cargo_unloaded_qty: Optional[Decimal]
    cargo_unit: Optional[str]
    cargo_loss_qty: Optional[Decimal]
    cargo_loss_reason: Optional[str]
    wood_species: Optional[str]
    log_count: Optional[int]
    product_name: Optional[str]
    depotage_cert_number: Optional[str]
    tank_calibrated: Optional[bool]
    container_count: Optional[int]
    fill_rate_percent: Optional[Decimal]
    revenue: Optional[Decimal]
    fuel_cost: Optional[Decimal]
    toll_cost: Optional[Decimal]
    other_costs: Optional[Decimal]
    total_cost: Optional[Decimal]
    submitted_by: Optional[int]
    submitted_at: Optional[datetime]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    photos_json: Optional[list]
    notes: Optional[str]
    created_at: datetime
    created_by: int
    created_by_name: str
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MissionListResponse(BaseModel):
    items: List[MissionResponse]
    total: int
    page: int
    page_size: int


class MissionCompleteRequest(BaseModel):
    mileage_end: int
    distance_actual_km: Optional[float] = None
    cargo_unloaded_qty: Optional[Decimal] = None
    cargo_loss_qty: Optional[Decimal] = None
    cargo_loss_reason: Optional[str] = None
    return_empty: Optional[bool] = None
    notes: Optional[str] = None


class MissionRejectRequest(BaseModel):
    rejection_reason: str


# ════════════════════════════════════════════════════════════════
# CHECKPOINTS
# ════════════════════════════════════════════════════════════════

class CheckpointCreate(BaseModel):
    checkpoint_type: str
    location_name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    arrived_at: datetime
    departed_at: Optional[datetime] = None
    wait_time_minutes: Optional[int] = None
    cargo_quantity: Optional[Decimal] = None
    cargo_unit: Optional[str] = None
    mileage_at: Optional[int] = None
    photos_json: Optional[list] = None
    notes: Optional[str] = None


class CheckpointResponse(BaseModel):
    id: int
    mission_id: int
    checkpoint_type: str
    location_name: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    arrived_at: datetime
    departed_at: Optional[datetime]
    wait_time_minutes: Optional[int]
    cargo_quantity: Optional[Decimal]
    cargo_unit: Optional[str]
    mileage_at: Optional[int]
    photos_json: Optional[list]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════════
# CARBURANT (FUEL LOGS)
# ════════════════════════════════════════════════════════════════

class FuelLogBase(BaseModel):
    vehicle_id: int
    date: datetime
    quantity_liters: Decimal
    total_cost: Decimal
    mileage_at: int


class FuelLogCreate(FuelLogBase):
    driver_id: Optional[int] = None
    mission_id: Optional[int] = None
    station_name: Optional[str] = None
    fuel_type: Optional[str] = None
    unit_price: Optional[Decimal] = None
    is_full_tank: bool = True
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class FuelLogUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    mission_id: Optional[int] = None
    date: Optional[datetime] = None
    station_name: Optional[str] = None
    fuel_type: Optional[str] = None
    quantity_liters: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    mileage_at: Optional[int] = None
    is_full_tank: Optional[bool] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class FuelLogResponse(FuelLogBase):
    id: int
    driver_id: Optional[int]
    mission_id: Optional[int]
    station_name: Optional[str]
    fuel_type: Optional[str]
    unit_price: Optional[Decimal]
    consumption_l100km: Optional[Decimal]
    is_full_tank: bool
    receipt_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    created_by: int
    created_by_name: str
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FuelLogListResponse(BaseModel):
    items: List[FuelLogResponse]
    total: int
    page: int
    page_size: int


class FuelAlertResponse(BaseModel):
    vehicle_id: int
    registration_number: str
    avg_consumption: float
    threshold: float
    alert_type: str


class FuelAlertListResponse(BaseModel):
    items: List[FuelAlertResponse]
    total: int


# ════════════════════════════════════════════════════════════════
# UTILISATEURS CHAUFFEURS (gestion par superviseur)
# ════════════════════════════════════════════════════════════════

class DriverUserCreate(BaseModel):
    """Création combinée User + LogisticsDriver."""
    # Compte utilisateur
    username: str
    email: EmailStr
    password: str
    # Fiche chauffeur
    first_name: str
    last_name: str
    role: str = "driver"  # "driver" ou "motor_boy"
    phone: Optional[str] = None
    company_id: int
    license_types_json: Optional[List[str]] = None
    license_expiry: Optional[date] = None
    hire_date: Optional[date] = None
    notes: Optional[str] = None


class DriverUserResponse(BaseModel):
    """Réponse combinée User + LogisticsDriver."""
    # User info
    user_id: int
    username: str
    email: str
    is_active: bool
    # Driver info
    driver_id: int
    first_name: str
    last_name: str
    role: str
    company_id: int
    status: str
    created_at: datetime


class DriverUserListResponse(BaseModel):
    items: List[DriverUserResponse]
    total: int
    page: int
    page_size: int
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

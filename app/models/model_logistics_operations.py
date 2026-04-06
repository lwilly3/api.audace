from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, Float, JSON, DECIMAL,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class LogisticsMission(BaseModel):
    """
    Mission / Voyage du module Logistique.

    Représente un trajet avec véhicule, équipe, cargo, localisation, documents
    et workflow de validation.
    """
    __tablename__ = 'logistics_missions'

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(20), unique=True, nullable=False, index=True)
    
    # Ressources
    vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('logistics_teams.id'), nullable=True)
    driver_id = Column(Integer, ForeignKey('logistics_drivers.id'), nullable=False)
    co_driver_id = Column(Integer, ForeignKey('logistics_drivers.id'), nullable=True)
    
    # Classification
    segment = Column(String(20), nullable=False, index=True)
    
    # Client et références
    client_name = Column(String(255), nullable=True)
    client_reference = Column(String(100), nullable=True)
    
    # Itinéraire
    departure_location = Column(String(255), nullable=False)
    departure_lat = Column(Float, nullable=True)
    departure_lng = Column(Float, nullable=True)
    arrival_location = Column(String(255), nullable=False)
    arrival_lat = Column(Float, nullable=True)
    arrival_lng = Column(Float, nullable=True)
    distance_planned_km = Column(Float, nullable=True)
    distance_actual_km = Column(Float, nullable=True)
    
    # Compteurs
    mileage_start = Column(Integer, nullable=True)
    mileage_end = Column(Integer, nullable=True)
    
    # Planification
    planned_date = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_departure = Column(DateTime(timezone=True), nullable=True)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)
    
    # Statut
    status = Column(String(20), default='planned', index=True)  # planned, in_progress, completed, cancelled
    return_empty = Column(Boolean, default=False)
    
    # Cargo
    cargo_type_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=True)
    cargo_description = Column(Text, nullable=True)
    cargo_loaded_qty = Column(DECIMAL(12, 3), nullable=True)
    cargo_unloaded_qty = Column(DECIMAL(12, 3), nullable=True)
    cargo_unit = Column(String(20), nullable=True)
    cargo_loss_qty = Column(DECIMAL(12, 3), nullable=True)
    cargo_loss_reason = Column(Text, nullable=True)
    
    # Données spécifiques segment
    wood_species = Column(String(100), nullable=True)  # grumier
    log_count = Column(Integer, nullable=True)
    product_name = Column(String(100), nullable=True)  # citerne
    depotage_cert_number = Column(String(50), nullable=True)
    tank_calibrated = Column(Boolean, nullable=True)
    container_count = Column(Integer, nullable=True)  # plateau
    fill_rate_percent = Column(DECIMAL(5, 2), nullable=True)
    
    # Financier
    revenue = Column(DECIMAL(12, 2), nullable=True)
    fuel_cost = Column(DECIMAL(10, 2), nullable=True)
    toll_cost = Column(DECIMAL(10, 2), nullable=True)
    other_costs = Column(DECIMAL(10, 2), nullable=True)
    total_cost = Column(DECIMAL(12, 2), nullable=True)
    
    # Validation
    submitted_by = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Médias
    attachments_json = Column(JSON, default=[])
    photos_json = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    vehicle = relationship('LogisticsVehicle', foreign_keys=[vehicle_id], back_populates='missions')
    team = relationship('LogisticsTeam', foreign_keys=[team_id], back_populates='missions')
    driver = relationship('LogisticsDriver', foreign_keys=[driver_id], back_populates='missions_as_driver')
    co_driver = relationship('LogisticsDriver', foreign_keys=[co_driver_id], back_populates='missions_as_co_driver')
    cargo_type = relationship('LogisticsConfigOption', foreign_keys=[cargo_type_id])
    checkpoints = relationship('LogisticsMissionCheckpoint', back_populates='mission', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_mission_vehicle_date', 'vehicle_id', 'planned_date'),
        Index('ix_mission_driver', 'driver_id'),
        Index('ix_mission_status', 'status'),
        Index('ix_mission_segment', 'segment'),
    )


class LogisticsMissionCheckpoint(BaseModel):
    """
    Point de passage / checkpoint d'une mission.

    Représente un chargement, déchargement, arrêt, etc. sur le trajet.
    """
    __tablename__ = 'logistics_mission_checkpoints'

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey('logistics_missions.id', ondelete='CASCADE'), nullable=False)
    
    # Informations
    checkpoint_type = Column(String(20), nullable=False)  # departure, loading, unloading, stop, arrival
    location_name = Column(String(255), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Timestamps
    arrived_at = Column(DateTime(timezone=True), nullable=False)
    departed_at = Column(DateTime(timezone=True), nullable=True)
    wait_time_minutes = Column(Integer, nullable=True)
    
    # Cargo
    cargo_quantity = Column(DECIMAL(12, 3), nullable=True)
    cargo_unit = Column(String(20), nullable=True)
    mileage_at = Column(Integer, nullable=True)
    
    # Médias
    photos_json = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    mission = relationship('LogisticsMission', foreign_keys=[mission_id], back_populates='checkpoints')

    __table_args__ = (
        Index('ix_checkpoint_mission', 'mission_id'),
    )


class LogisticsFuelLog(BaseModel):
    """
    Log de carburant / Ravitaillement du module Logistique.
    """
    __tablename__ = 'logistics_fuel_logs'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('logistics_drivers.id'), nullable=True)
    mission_id = Column(Integer, ForeignKey('logistics_missions.id'), nullable=True)
    
    # Informations
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    station_name = Column(String(255), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    quantity_liters = Column(DECIMAL(8, 2), nullable=False)
    unit_price = Column(DECIMAL(8, 2), nullable=True)
    total_cost = Column(DECIMAL(10, 2), nullable=False)
    
    # Compteur
    mileage_at = Column(Integer, nullable=False)
    consumption_l100km = Column(DECIMAL(6, 2), nullable=True)
    is_full_tank = Column(Boolean, default=True)
    
    # Médias
    receipt_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    vehicle = relationship('LogisticsVehicle', foreign_keys=[vehicle_id], back_populates='fuel_logs')
    driver = relationship('LogisticsDriver', foreign_keys=[driver_id], back_populates='fuel_logs')
    mission = relationship('LogisticsMission', foreign_keys=[mission_id])

    __table_args__ = (
        Index('ix_fuel_vehicle_date', 'vehicle_id', 'date'),
        Index('ix_fuel_mission', 'mission_id'),
    )


class LogisticsMaintenance(BaseModel):
    """
    Maintenance / Entretien du module Logistique.
    """
    __tablename__ = 'logistics_maintenance'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=False)
    maintenance_type_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=True)
    
    # Classification
    category = Column(String(20), nullable=False)  # preventive, corrective, inspection
    description = Column(Text, nullable=False)
    
    # Statut
    status = Column(String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    scheduled_date = Column(Date, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Kilométrage
    mileage_at = Column(Integer, nullable=True)
    next_maintenance_km = Column(Integer, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    
    # Prestataire
    performed_by_name = Column(String(255), nullable=True)
    performed_by_type = Column(String(20), nullable=True)  # internal, external
    
    # Coûts
    labor_cost = Column(DECIMAL(10, 2), default=0)
    parts_cost = Column(DECIMAL(10, 2), default=0)
    external_cost = Column(DECIMAL(10, 2), default=0)
    total_cost = Column(DECIMAL(12, 2), default=0)
    
    # Détails
    parts_used_json = Column(JSON, default=[])
    attachments_json = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    vehicle = relationship('LogisticsVehicle', foreign_keys=[vehicle_id], back_populates='maintenance_records')
    maintenance_type = relationship('LogisticsConfigOption', foreign_keys=[maintenance_type_id])

    __table_args__ = (
        Index('ix_logi_maintenance_vehicle_date', 'vehicle_id', 'scheduled_date'),
        Index('ix_logi_maintenance_status', 'status'),
        Index('ix_logi_maintenance_category', 'category'),
    )


class LogisticsTire(BaseModel):
    """
    Suivi de pneumatique du module Logistique.
    """
    __tablename__ = 'logistics_tires'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=False)
    
    # Position et identification
    position = Column(String(20), nullable=False)  # front_left, etc.
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    # Suivi kilométrage
    installed_at_km = Column(Integer, nullable=False)
    current_km = Column(Integer, nullable=False)
    max_km = Column(Integer, nullable=True)
    
    # Statut
    status = Column(String(20), default='active')  # active, worn, replaced, spare
    installed_at = Column(Date, nullable=False)
    replaced_at = Column(Date, nullable=True)
    cost = Column(DECIMAL(8, 2), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    vehicle = relationship('LogisticsVehicle', foreign_keys=[vehicle_id], back_populates='tires')

    __table_args__ = (
        Index('ix_tire_vehicle_position', 'vehicle_id', 'position'),
        Index('ix_tire_status', 'status'),
    )


class LogisticsDocument(BaseModel):
    """
    Document attaché à une entité du module Logistique (polymorphique).
    """
    __tablename__ = 'logistics_documents'

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)  # vehicle, driver, mission
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Type et stockage
    document_type_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=True)
    name = Column(String(255), nullable=False)
    storage_url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Validité
    expiry_date = Column(Date, nullable=True)
    is_expired = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    
    # Audit
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, nullable=False)
    uploaded_by_name = Column(String(255), nullable=False)

    # Relations
    document_type_option = relationship('LogisticsConfigOption', foreign_keys=[document_type_id])

    __table_args__ = (
        Index('ix_document_entity', 'entity_type', 'entity_id'),
        Index('ix_document_expiry', 'expiry_date'),
    )

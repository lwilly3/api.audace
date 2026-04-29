from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, Float, JSON,
    ForeignKey, Index, func, DECIMAL,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class LogisticsVehicle(BaseModel):
    """
    Véhicule du module Logistique.

    Représente un véhicule de transport (camion citerne, grumier, plateau, etc)
    avec ses informations d'identification, localisation, affectation, acquisition
    et statut.

    vehicle_role discrimine la nature physique de l'engin :
      - porteur_citerne : camion citerne monobloc (cab + citerne fixe intégrée)
      - porteur         : camion porteur classique (benne, fourgon, grumier monobloc…)
      - tracteur        : cab tracteur semi-remorque seul
      - remorque        : remorque seule (citerne, plateau, grumier, bâchée…)
      - leger           : véhicule léger (SUV, berline, pick-up, moto)
    """
    __tablename__ = 'logistics_vehicles'

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(20), unique=True, nullable=False, index=True)
    internal_reference = Column(String(20), unique=True, nullable=True)

    # Rôle physique de l'engin (voir docstring ci-dessus)
    vehicle_role = Column(String(20), nullable=False, default='porteur', server_default='porteur', index=True)

    # Classification
    segment = Column(String(20), nullable=False, index=True)  # petroleum, transport, media…
    type_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=True)
    
    # Informations du véhicule
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    vin = Column(String(50), unique=True, nullable=True)
    
    # Capacité
    capacity_value = Column(DECIMAL(10, 2), nullable=True)
    capacity_unit = Column(String(10), nullable=True)  # litres, m3, tonnes, conteneurs
    
    # État
    fuel_type_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=True)
    fuel_type_raw = Column(String(50), nullable=True)   # stockage direct si pas de config option
    status_id = Column(Integer, ForeignKey('logistics_config_options.id'), nullable=False)
    mileage_counter = Column(Integer, default=0)
    
    # Affectation
    current_driver_id = Column(Integer, ForeignKey('logistics_drivers.id'), nullable=True)
    
    # Localisation
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=False)
    base_site_id = Column(Integer, ForeignKey('inventory_sites.id'), nullable=True)
    
    # Acquisition
    acquisition_date = Column(Date, nullable=True)
    acquisition_cost = Column(DECIMAL(12, 2), nullable=True)
    
    # Médias
    photos_json = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Archivage
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    company = relationship('InventoryCompany', foreign_keys=[company_id])
    base_site = relationship('InventorySite', foreign_keys=[base_site_id])
    current_driver = relationship('LogisticsDriver', foreign_keys=[current_driver_id])
    type_option = relationship('LogisticsConfigOption', foreign_keys=[type_id])
    fuel_type_option = relationship('LogisticsConfigOption', foreign_keys=[fuel_type_id])
    status_option = relationship('LogisticsConfigOption', foreign_keys=[status_id])
    documents = relationship(
        'LogisticsDocument',
        primaryjoin="and_(LogisticsDocument.entity_type=='vehicle', foreign(LogisticsDocument.entity_id)==LogisticsVehicle.id)",
        viewonly=True,
        cascade='none'
    )
    missions = relationship('LogisticsMission', back_populates='vehicle', cascade='all, delete-orphan')
    fuel_logs = relationship('LogisticsFuelLog', back_populates='vehicle', cascade='all, delete-orphan')
    maintenance_records = relationship('LogisticsMaintenance', back_populates='vehicle', cascade='all, delete-orphan')
    tires = relationship('LogisticsTire', back_populates='vehicle', cascade='all, delete-orphan')
    compartments = relationship('LogisticsVehicleCompartment', back_populates='vehicle', cascade='all, delete-orphan', order_by='LogisticsVehicleCompartment.compartment_no')
    # Associations où ce véhicule est le tracteur ou la remorque
    tractor_associations = relationship('LogisticsVehicleAssociation', foreign_keys='LogisticsVehicleAssociation.tractor_id', back_populates='tractor', cascade='all, delete-orphan')
    trailer_associations = relationship('LogisticsVehicleAssociation', foreign_keys='LogisticsVehicleAssociation.trailer_id', back_populates='trailer', cascade='all, delete-orphan')

    @property
    def status_name(self) -> Optional[str]:
        """Nom du statut depuis la relation status_option."""
        return self.status_option.name if self.status_option else None

    @property
    def company_name(self) -> Optional[str]:
        """Nom de l'entreprise depuis la relation company."""
        return self.company.name if self.company else None

    @property
    def fuel_type(self) -> Optional[str]:
        """Type de carburant : config option name en priorite, sinon valeur directe."""
        if self.fuel_type_option:
            return self.fuel_type_option.name
        return self.fuel_type_raw

    @property
    def license_plate(self) -> Optional[str]:
        """Alias de registration_number pour compatibilite frontend."""
        return self.registration_number

    @property
    def reference(self) -> Optional[str]:
        """Alias de internal_reference pour compatibilite frontend."""
        return self.internal_reference

    @property
    def mileage(self) -> int:
        """Alias de mileage_counter pour compatibilite frontend."""
        return self.mileage_counter or 0

    @property
    def capacity_kg(self) -> Optional[float]:
        """Capacite en kg si capacity_unit est 'kg' ou 'tonnes'."""
        if self.capacity_value is None:
            return None
        if self.capacity_unit in ('kg', 'tonnes'):
            return float(self.capacity_value)
        return None

    @property
    def capacity_volume(self) -> Optional[float]:
        """Capacite en volume : retourne capacity_value si l unite n est pas un poids."""
        if self.capacity_value is None:
            return None
        if self.capacity_unit in ('kg', 'tonnes'):
            return None  # c est du poids, pas du volume
        return float(self.capacity_value)

    @property
    def assigned_driver_id(self) -> Optional[int]:
        """ID du chauffeur assigne (current_driver_id)."""
        return self.current_driver_id

    @property
    def assigned_driver_name(self) -> Optional[str]:
        """Nom du chauffeur assigne depuis la relation current_driver."""
        if self.current_driver:
            return f"{self.current_driver.first_name} {self.current_driver.last_name}".strip()
        return None

    __table_args__ = (
        Index('ix_vehicle_company_status', 'company_id', 'status_id'),
        Index('ix_vehicle_segment', 'segment'),
        Index('ix_vehicle_is_archived', 'is_archived'),
        Index('ix_vehicle_role', 'vehicle_role'),
    )

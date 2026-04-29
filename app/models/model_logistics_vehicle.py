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

    __table_args__ = (
        Index('ix_vehicle_company_status', 'company_id', 'status_id'),
        Index('ix_vehicle_segment', 'segment'),
        Index('ix_vehicle_is_archived', 'is_archived'),
        Index('ix_vehicle_role', 'vehicle_role'),
    )

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, Float, JSON,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryEquipment(BaseModel):
    """
    Equipement du module Inventaire.

    Represente un equipement physique ou consommable avec toutes ses
    informations d'identification, localisation, affectation, acquisition,
    garantie, configuration et documentation.
    """
    __tablename__ = 'inventory_equipment'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    reference = Column(String(50), unique=True, nullable=False, index=True)
    serial_number = Column(String(255), nullable=True, index=True)
    barcode = Column(String(255), nullable=True, index=True)

    # Classification
    category_id = Column(Integer, ForeignKey('inventory_config_options.id'), nullable=False)
    subcategory = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=False)
    model_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)

    # Etat
    status_id = Column(Integer, ForeignKey('inventory_config_options.id'), nullable=False)
    condition_id = Column(Integer, ForeignKey('inventory_config_options.id'), nullable=False)

    # Localisation
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=False)
    site_id = Column(Integer, ForeignKey('inventory_sites.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('inventory_rooms.id'), nullable=True)
    specific_location = Column(String(255), nullable=True)

    # Affectation
    assigned_user_id = Column(Integer, nullable=True)
    assigned_user_name = Column(String(255), nullable=True)
    assigned_user_email = Column(String(255), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    assigned_by = Column(Integer, nullable=True)
    expected_return_date = Column(DateTime(timezone=True), nullable=True)
    assignment_notes = Column(Text, nullable=True)

    # Acquisition
    acquisition_date = Column(Date, nullable=True)
    acquisition_type = Column(String(50), nullable=True)
    purchase_price = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    supplier = Column(String(255), nullable=True)
    invoice_number = Column(String(255), nullable=True)
    invoice_url = Column(Text, nullable=True)

    # Garantie
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    warranty_provider = Column(String(255), nullable=True)
    warranty_contract_number = Column(String(255), nullable=True)
    warranty_notes = Column(Text, nullable=True)

    # Configuration technique
    config_settings_json = Column(JSON, nullable=True)
    config_notes = Column(Text, nullable=True)
    last_configured_at = Column(DateTime(timezone=True), nullable=True)
    last_configured_by = Column(Integer, nullable=True)
    firmware_version = Column(String(100), nullable=True)
    software_version = Column(String(100), nullable=True)

    # Informations complementaires
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    manual_url = Column(Text, nullable=True)
    photos_json = Column(JSON, default=[])
    specifications_json = Column(JSON, nullable=True)

    # Consommables
    is_consumable = Column(Boolean, default=False)
    quantity = Column(Integer, nullable=True)
    min_quantity = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)

    # Archivage
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_reason = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    category = relationship('InventoryConfigOption', foreign_keys=[category_id])
    status = relationship('InventoryConfigOption', foreign_keys=[status_id])
    condition = relationship('InventoryConfigOption', foreign_keys=[condition_id])
    company = relationship('InventoryCompany', foreign_keys=[company_id])
    site = relationship('InventorySite', foreign_keys=[site_id])
    room = relationship('InventoryRoom', foreign_keys=[room_id])
    documents = relationship('InventoryDocument', back_populates='equipment', cascade='all, delete-orphan')
    movements = relationship('InventoryMovement', back_populates='equipment', cascade='all, delete-orphan')
    maintenance_records = relationship('InventoryMaintenance', back_populates='equipment', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_equipment_company_status', 'company_id', 'status_id'),
        Index('ix_equipment_category', 'category_id'),
        Index('ix_equipment_is_archived', 'is_archived'),
    )

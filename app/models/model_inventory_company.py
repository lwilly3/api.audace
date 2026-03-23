from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryCompany(BaseModel):
    __tablename__ = 'inventory_companies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    type = Column(String(50), nullable=False)  # petroleum, transport, media, it_services, holding, other
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    logo_url = Column(Text, nullable=True)

    # Regles de partage d'equipements
    can_share_equipment = Column(Boolean, default=True)
    can_borrow_equipment = Column(Boolean, default=True)
    requires_approval_to_lend = Column(Boolean, default=True)
    requires_approval_to_borrow = Column(Boolean, default=True)

    # Hierarchie
    parent_company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    sites = relationship('InventorySite', back_populates='company', cascade='all, delete-orphan')
    parent = relationship('InventoryCompany', remote_side=[id])

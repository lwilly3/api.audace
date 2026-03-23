from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventorySite(BaseModel):
    __tablename__ = 'inventory_sites'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('inventory_companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)

    # Adresse
    address_street = Column(Text, nullable=True)
    address_city = Column(String(255), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    manager_user_id = Column(Integer, nullable=True)
    manager_user_name = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    company = relationship('InventoryCompany', back_populates='sites')
    rooms = relationship('InventoryRoom', back_populates='site', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_site_company_code'),
    )

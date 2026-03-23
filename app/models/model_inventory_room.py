from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryRoom(BaseModel):
    __tablename__ = 'inventory_rooms'

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey('inventory_sites.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)  # studio, control_room, office, storage, technical, meeting_room, other
    floor = Column(String(50), nullable=True)
    building = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    site = relationship('InventorySite', back_populates='rooms')

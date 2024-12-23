from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base




class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True  # Indique que cette classe ne sera pas une table directe
    is_deleted = Column(Boolean, default=False)  # Marque la ligne comme supprimée
    deleted_at = Column(DateTime, nullable=True)  # Enregistre la date de suppression


class Emission(BaseModel):
    __tablename__ = 'emissions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    synopsis = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    type = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
    frequency = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Relation avec les shows
    # shows = relationship('Show', back_populates='emission', cascade='all, delete-orphan')
 # Relation vers Show (un-à-plusieurs)
    shows = relationship("Show", back_populates="emission", cascade="all, delete-orphan")
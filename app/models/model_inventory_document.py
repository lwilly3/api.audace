from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryDocument(BaseModel):
    """
    Document associe a un equipement.

    Stocke les metadonnees des fichiers (factures, manuels, photos, etc.)
    heberges sur Firebase Storage. Supporte le versionnement de documents.
    """
    __tablename__ = 'inventory_documents'

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(
        Integer,
        ForeignKey('inventory_equipment.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Fichier
    file_name = Column(String(500), nullable=False)
    display_name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)

    # Stockage
    storage_url = Column(Text, nullable=False, comment="Firebase Storage URL")
    storage_path = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    # Acces et versionnement
    access_level = Column(String(50), default='company')
    version = Column(String(50), nullable=True)
    is_latest = Column(Boolean, default=True)
    previous_version_id = Column(Integer, ForeignKey('inventory_documents.id'), nullable=True)

    # Metadonnees
    tags_json = Column(JSON, nullable=True)
    language = Column(String(10), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Audit
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, nullable=False)
    uploaded_by_name = Column(String(255), nullable=False)
    download_count = Column(Integer, default=0)

    # Relations
    equipment = relationship('InventoryEquipment', back_populates='documents')
    previous_version = relationship('InventoryDocument', remote_side=[id])

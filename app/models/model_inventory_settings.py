from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    UniqueConstraint, Index, func,
)
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryConfigOption(BaseModel):
    """
    Options configurables pour le module Inventaire.

    Table unique pour toutes les listes d'options (categories, statuts, types
    de mouvement, etc.), differenciees par le champ `list_type`.
    """
    __tablename__ = 'inventory_config_options'

    id = Column(Integer, primary_key=True, index=True)
    list_type = Column(
        String(50), nullable=False, index=True,
        comment="Type de liste: category, equipment_status, movement_type, "
                "mission_type, condition_state, document_type, service_category",
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True, comment="Code couleur hexadecimal")
    icon = Column(String(50), nullable=True, comment="Nom d'icone Lucide")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True, comment="Donnees supplementaires extensibles")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('list_type', 'name', name='uq_config_option_type_name'),
        Index('ix_config_option_type_active', 'list_type', 'is_active'),
    )


class InventoryGlobalSettings(Base):
    """
    Parametres globaux du module Inventaire (cle-valeur).

    Chaque parametre est stocke sous forme de chaine, le champ `value_type`
    indiquant le type reel pour le parsing cote application.
    """
    __tablename__ = 'inventory_global_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False, comment="Valeur stockee en chaine, parsee selon value_type")
    value_type = Column(
        String(20), nullable=False,
        comment="Type reel: int, bool, string, float",
    )
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

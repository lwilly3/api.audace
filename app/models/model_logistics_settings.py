from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    UniqueConstraint, Index, func,
)
from app.db.database import Base


class LogisticsConfigOption(Base):
    """
    Options configurables pour le module Logistique.

    Table unique pour toutes les listes d'options (segments, statuts de véhicule,
    types de cargo, types de maintenance, types de document, etc),
    différenciées par le champ `list_type`.
    """
    __tablename__ = 'logistics_config_options'

    id = Column(Integer, primary_key=True, index=True)
    list_type = Column(
        String(50), nullable=False, index=True,
        comment="Type de liste: vehicle_segment, vehicle_status, cargo_type, "
                "maintenance_type, document_type, etc.",
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True, comment="Code couleur hexadécimal")
    icon = Column(String(50), nullable=True, comment="Nom d'icône Lucide")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True, comment="Données supplémentaires extensibles")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('list_type', 'name', name='uq_logistics_config_type_name'),
        Index('ix_logistics_config_type_active', 'list_type', 'is_active'),
    )


class LogisticsGlobalSettings(Base):
    """
    Paramètres globaux du module Logistique (clé-valeur).

    Chaque paramètre est stocké sous forme de chaîne, le champ `value_type`
    indiquant le type réel pour le parsing côté application.
    """
    __tablename__ = 'logistics_global_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False, comment="Valeur stockée en chaîne, parsée selon value_type")
    value_type = Column(
        String(20), nullable=False,
        comment="Type réel: int, bool, string, float",
    )
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

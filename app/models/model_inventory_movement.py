from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventoryMovement(BaseModel):
    """
    Mouvement d'equipement du module Inventaire.

    Represente un mouvement (assignation, transfert, pret, mission, maintenance, etc.)
    avec workflow d'approbation optionnel.

    Quand requires_approval est True, le mouvement reste en statut 'pending'
    jusqu'a approbation. Quand approuve (ou si pas d'approbation requise),
    le mouvement passe en 'completed' et la localisation/affectation de
    l'equipement est mise a jour atomiquement.
    """
    __tablename__ = 'inventory_movements'

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(
        Integer,
        ForeignKey('inventory_equipment.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Type de mouvement (FK vers inventory_config_options de type 'movement_type')
    movement_type_id = Column(
        Integer,
        ForeignKey('inventory_config_options.id'),
        nullable=False,
    )
    movement_category = Column(String(50), nullable=False, comment="Categorie fonctionnelle: assignment, return, loan, transfer_site, etc.")

    # Lien mission (optionnel)
    mission_id = Column(Integer, nullable=True)
    mission_title = Column(String(255), nullable=True)
    mission_type = Column(String(50), nullable=True)

    # ── Origine ──
    from_company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=True)
    from_site_id = Column(Integer, ForeignKey('inventory_sites.id'), nullable=True)
    from_room_id = Column(Integer, ForeignKey('inventory_rooms.id'), nullable=True)
    from_user_id = Column(Integer, nullable=True)
    from_user_name = Column(String(255), nullable=True)
    from_specific_location = Column(String(255), nullable=True)

    # ── Destination ──
    to_company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=True)
    to_site_id = Column(Integer, ForeignKey('inventory_sites.id'), nullable=True)
    to_room_id = Column(Integer, ForeignKey('inventory_rooms.id'), nullable=True)
    to_user_id = Column(Integer, nullable=True)
    to_user_name = Column(String(255), nullable=True)
    to_specific_location = Column(String(255), nullable=True)
    to_external_location = Column(Text, nullable=True)

    # ── Details ──
    date = Column(DateTime(timezone=True), nullable=False)
    expected_return_date = Column(DateTime(timezone=True), nullable=True)
    actual_return_date = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    # ── Approbation / Workflow ──
    status = Column(String(20), nullable=False, default='pending', comment="pending, approved, rejected, completed")
    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by = Column(Integer, nullable=True)
    approved_by_name = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # ── Donnees complementaires (JSON) ──
    return_condition_json = Column(JSON, nullable=True, comment="Etat au retour: conditionId, conditionName, notes, issues, photosUrls")
    attachments_json = Column(JSON, nullable=True, comment="Pieces jointes: [{name, url, type}]")
    signature_url = Column(Text, nullable=True)

    # ── Audit ──
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)

    # ── Relations ──
    equipment = relationship('InventoryEquipment', back_populates='movements')
    movement_type = relationship('InventoryConfigOption', foreign_keys=[movement_type_id])
    from_company = relationship('InventoryCompany', foreign_keys=[from_company_id])
    from_site = relationship('InventorySite', foreign_keys=[from_site_id])
    from_room = relationship('InventoryRoom', foreign_keys=[from_room_id])
    to_company = relationship('InventoryCompany', foreign_keys=[to_company_id])
    to_site = relationship('InventorySite', foreign_keys=[to_site_id])
    to_room = relationship('InventoryRoom', foreign_keys=[to_room_id])

    __table_args__ = (
        Index('ix_movement_equipment_date', 'equipment_id', 'date'),
        Index('ix_movement_status', 'status'),
    )

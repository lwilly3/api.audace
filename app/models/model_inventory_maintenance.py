from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.models.model_inventory_equipment import BaseModel


class InventoryMaintenance(BaseModel):
    """
    Enregistrement de maintenance pour un equipement d'inventaire.

    Represente une intervention de maintenance (preventive, corrective,
    inspection, calibration, nettoyage, mise a jour ou autre) avec
    planification, couts, pieces utilisees et resultats.
    """
    __tablename__ = 'inventory_maintenance'

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(
        Integer,
        ForeignKey('inventory_equipment.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Type et description
    type = Column(String(50), nullable=False)  # preventive, corrective, inspection, calibration, cleaning, upgrade, other
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Planification
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # minutes
    actual_duration = Column(Integer, nullable=True)      # minutes

    # Intervenant
    performer_type = Column(String(20), nullable=True)      # internal, external
    performer_user_id = Column(Integer, nullable=True)
    performer_user_name = Column(String(255), nullable=True)
    performer_company = Column(String(255), nullable=True)
    performer_contact = Column(String(255), nullable=True)

    # Couts
    cost_labor = Column(Float, nullable=True)
    cost_parts = Column(Float, nullable=True)
    cost_other = Column(Float, nullable=True)
    cost_total = Column(Float, nullable=True)
    cost_currency = Column(String(10), default='XOF')

    # Pieces utilisees (JSON array of {name, quantity, unitCost})
    parts_used_json = Column(JSON, nullable=True)

    # Statut et resultat
    status = Column(String(20), default='scheduled', nullable=False)  # scheduled, in_progress, completed, cancelled
    result = Column(String(20), nullable=True)   # success, partial, failed
    findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)

    # Documents joints (JSON)
    attachments_json = Column(JSON, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    equipment = relationship('InventoryEquipment', back_populates='maintenance_records')

    __table_args__ = (
        Index('ix_maintenance_equipment_scheduled', 'equipment_id', 'scheduled_date'),
        Index('ix_maintenance_status', 'status'),
    )

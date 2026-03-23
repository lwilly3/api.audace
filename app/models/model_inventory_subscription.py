from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, Float,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class InventorySubscription(BaseModel):
    """
    Abonnement / Service du module Inventaire.

    Represente un abonnement ou service souscrit par l'entreprise
    (licences logicielles, hebergement, maintenance, etc.).
    Entite independante, non liee aux equipements.
    """
    __tablename__ = 'inventory_subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)

    # Classification
    category_id = Column(Integer, ForeignKey('inventory_config_options.id'), nullable=False)

    # Fournisseur
    provider_name = Column(String(255), nullable=False)
    provider_website = Column(Text, nullable=True)
    provider_contact_email = Column(String(255), nullable=True)
    provider_contact_phone = Column(String(50), nullable=True)
    provider_account_number = Column(String(255), nullable=True)

    # Cout
    cost_amount = Column(Float, nullable=False)
    cost_currency = Column(String(10), default='XOF', nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    next_billing_date = Column(Date, nullable=True)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Renouvellement
    renewal_type = Column(String(20), nullable=False)
    auto_renew_period_months = Column(Integer, nullable=True)

    # Statut
    status = Column(String(20), default='active', nullable=False)

    # Entreprise beneficiaire
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    login_url = Column(Text, nullable=True)

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
    company = relationship('InventoryCompany', foreign_keys=[company_id])

    __table_args__ = (
        Index('ix_subscription_status', 'status'),
        Index('ix_subscription_end_date', 'end_date'),
        Index('ix_subscription_company', 'company_id'),
        Index('ix_subscription_is_archived', 'is_archived'),
    )

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, JSON,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class LogisticsDriver(BaseModel):
    """
    Chauffeur ou motor boy du module Logistique.

    Représente un membre d'équipage avec informations d'contact, permis,
    affectations et performances.
    """
    __tablename__ = 'logistics_drivers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Lien vers users (optionnel)
    
    # Identité
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default='driver')  # driver, motor_boy
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Permis et certifications
    license_types_json = Column(JSON, default=[])  # ["C", "CE", "ADR"]
    license_expiry = Column(Date, nullable=True)
    adr_certificate_expiry = Column(Date, nullable=True)
    
    # Affectation
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=False)
    status = Column(String(20), default='available')  # available, on_mission, on_leave, unavailable
    assigned_vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=True)
    team_id = Column(Integer, ForeignKey('logistics_teams.id'), nullable=True)
    
    # Informations
    hire_date = Column(Date, nullable=True)
    photos_json = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Archivage
    is_archived = Column(Boolean, default=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    company = relationship('InventoryCompany', foreign_keys=[company_id])
    assigned_vehicle = relationship('LogisticsVehicle', foreign_keys=[assigned_vehicle_id])
    team = relationship('LogisticsTeam', foreign_keys=[team_id], back_populates='members')
    missions_as_driver = relationship('LogisticsMission', foreign_keys='LogisticsMission.driver_id', back_populates='driver')
    missions_as_co_driver = relationship('LogisticsMission', foreign_keys='LogisticsMission.co_driver_id', back_populates='co_driver')
    fuel_logs = relationship('LogisticsFuelLog', back_populates='driver', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_driver_company_status', 'company_id', 'status'),
        Index('ix_driver_role', 'role'),
        Index('ix_driver_is_archived', 'is_archived'),
    )


class LogisticsTeam(BaseModel):
    """
    Équipe / Équipage du module Logistique.

    Représente un binôme ou trinôme stable composé d'un chef d'équipe (chauffeur),
    d'un motor boy, et éventuellement d'un second chauffeur.
    """
    __tablename__ = 'logistics_teams'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    
    # Chef d'équipe
    leader_id = Column(Integer, ForeignKey('logistics_drivers.id'), nullable=False)
    
    # Affectation
    preferred_segment = Column(String(20), nullable=True)  # grumier, citerne, plateau
    default_vehicle_id = Column(Integer, ForeignKey('logistics_vehicles.id'), nullable=True)
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=False)
    
    # Statut
    status = Column(String(20), default='active')  # active, inactive, dissolved
    dissolved_at = Column(DateTime(timezone=True), nullable=True)
    dissolved_reason = Column(Text, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    leader = relationship('LogisticsDriver', foreign_keys=[leader_id])
    default_vehicle = relationship('LogisticsVehicle', foreign_keys=[default_vehicle_id])
    company = relationship('InventoryCompany', foreign_keys=[company_id])
    members = relationship('LogisticsDriver', foreign_keys=[LogisticsDriver.team_id], back_populates='team')
    missions = relationship('LogisticsMission', back_populates='team', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_team_company_status', 'company_id', 'status'),
        Index('ix_team_leader', 'leader_id'),
    )


class LogisticsMechanic(Base):
    """
    Mécanicien / Technicien du module Logistique.

    Peut exister sans compte applicatif (user_id = null = profil orphelin).
    La liaison au compte se fait via le système d'invitation (Chemin A).
    """
    __tablename__ = 'logistics_mechanics'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # null = sans compte app

    # Identité
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)  # utilisé pour l'invitation
    phone = Column(String(20), nullable=True)
    specialty = Column(String(100), nullable=True)  # mécanicien moteur, électricien, etc.

    # Affectation
    company_id = Column(Integer, ForeignKey('inventory_companies.id'), nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    notes = Column(Text, nullable=True)

    # Suppression douce
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)

    # Relations
    company = relationship('InventoryCompany', foreign_keys=[company_id])

    __table_args__ = (
        Index('ix_logistics_mechanic_company', 'company_id'),
        Index('ix_logistics_mechanic_active', 'is_active'),
    )


class LogisticsInvitation(Base):
    """
    Invitation à créer un compte pour un profil logistique orphelin.

    Chemin A : Admin génère un token → envoie le lien → la personne crée son compte
    → user_id est lié automatiquement au profil driver ou mécanicien.
    """
    __tablename__ = 'logistics_invitations'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)

    # Cible (driver ou mechanic)
    entity_type = Column(String(20), nullable=False)  # 'driver' | 'mechanic'
    entity_id = Column(Integer, nullable=False)

    # Destinataire
    email = Column(String(255), nullable=False)

    # Validité
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)  # null = pas encore utilisé

    # Audit
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_logistics_invitation_entity', 'entity_type', 'entity_id'),
        Index('ix_logistics_invitation_email', 'email'),
    )

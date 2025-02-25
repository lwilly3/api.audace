from sqlalchemy import Column, Integer, String,Text, Boolean, Index,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text



from app.db.database import Base #metadata
# -------------------------
# Table des Utilisateurs
# -------------------------
class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True  # Indique que cette classe ne sera pas une table directe
    is_deleted = Column(Boolean, default=False)  # Marque la ligne comme supprimée
    deleted_at = Column(DateTime, nullable=True)  # Enregistre la date de suppression
    




# Modèle pour la table "users"
class User(BaseModel):
    __tablename__ = "users"  # Nom de la table

    id = Column(Integer, primary_key=True)  # Identifiant unique pour chaque utilisateur
    username = Column(String, nullable=False, unique=True, index=True)  # Nom d'utilisateur unique
    email = Column(String, nullable=False, unique=True, index=True)  # Email unique de l'utilisateur
    password = Column(String, nullable=False)  # Mot de passe de l'utilisateur
    is_active = Column(Boolean, default=True)  # Indique si l'utilisateur est actif
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))  # Date de création
    phone_number = Column(String, nullable=True, index=True)  # Numéro de téléphone de l'utilisateur (optionnel)
    profilePicture = Column(Text, nullable=True)
    # Relations avec d'autres tables
    # roles = relationship('Role', secondary='user_roles', back_populates='users') # Relation avec les rôles via UserRole
    # user_roles = relationship("UserRole", back_populates="user")
    # roles = relationship("Role", secondary="user_roles", back_populates="users")
    # roles = relationship('Role', secondary='user_roles', overlaps="user_roles")
   # Relation many-to-many avec Role via la table d'association 'user_roles'
    roles = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )
    
    # logins = relationship("LoginHistory", back_populates="user")  # Historique des connexions
    # audit_logs = relationship("AuditLog", back_populates="user")  # Journaux des actions effectuées
    # notifications = relationship("Notification", back_populates="user")  # Notifications utilisateur

 # Relation "un-à-plusieurs" avec ArchivedAuditLog
    archived_audit_logs = relationship(
        "ArchivedAuditLog", back_populates="user", cascade="all, delete-orphan"
    )
 # Relation "un-à-plusieurs" avec notifications
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
 # Relation "un-à-plusieurs" avec LoginHistory
    logins = relationship(
        "LoginHistory", back_populates="user", cascade="all, delete-orphan"
    )
 # Relation "un-à-plusieurs" avec AuditLog
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )






# Ajout de la relation presenters
    # presenters = relationship("Presenter", back_populates="user")

    # Relation "un-à-un" avec Presenter   uselist=False : Spécifie qu'il s'agit d'une relation "un-à-un".
    presenter = relationship("Presenter", back_populates="user", uselist=False)

    permissions = relationship("UserPermissions", back_populates="user", uselist=False)
    # Relation avec la table des permissions

    # Relation inverse avec les émissions créées
    created_shows = relationship("Show", back_populates="emission")


    # Index pour accélérer les recherches
    __table_args__ = (
        Index('ix_users_username', 'username'),  # Index pour le champ "username"
        Index('ix_users_email', 'email'),  # Index pour le champ "email"
        Index('ix_users_phone_number', 'phone_number'),  # Index pour le champ "phone_number"
    )

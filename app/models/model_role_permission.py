from sqlalchemy import Column, Integer, ForeignKey,Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.db.database import Base #metadata
# -------------------------
# Table de liaison entre Rôles et Permissions
# -------------------------
# Modèle pour la table intermédiaire "role_permissions" (liaison entre rôles et permissions)
class RolePermission(Base):
    __tablename__ = "role_permissions"  # Nom de la table

    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, index=True)  # Clé étrangère vers "roles"
    permission_id = Column(Integer, ForeignKey('permissions.id'), primary_key=True, index=True)  # Clé étrangère vers "permissions"

    # Relations
    # role = relationship("Role", back_populates="permissions")  # Liaison avec Role
    # permission = relationship("Permission", back_populates="roles")  # Liaison avec Permission

    # Index pour optimiser les requêtes
    __table_args__ = (
        Index('ix_role_permissions_role_id', 'role_id'),  # Index pour "role_id"
        Index('ix_role_permissions_permission_id', 'permission_id'),  # Index pour "permission_id"
    )

# Ce fichier définit la table de liaison entre les rôles et les permissions. 
# Un rôle peut avoir plusieurs permissions, et chaque permission peut être 
# associée à plusieurs rôles. La table de liaison gère cette relation.
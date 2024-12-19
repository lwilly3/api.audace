from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.database import Base #metadata
# -------------------------
# Table pour les Rôles
# -------------------------
class Role(Base):
    __tablename__ = "roles"  # Nom de la table

    id = Column(Integer, primary_key=True)  # Identifiant unique pour chaque rôle
    name = Column(String, nullable=False, unique=True)  # Nom unique du rôle

    # Relations
    # permissions = relationship("RolePermission", back_populates="role")  # Permissions associées via RolePermission
    # users = relationship("UserRole", back_populates="role")  # Utilisateurs associés via UserRole
    permissions = relationship('Permission', secondary='role_permissions', back_populates='roles')
    # users = relationship('User', secondary='user_roles', back_populates='roles')

#  # Relation inverse avec UserRole
#     user_roles = relationship("UserRole", back_populates="role")
#     # users = relationship("User", secondary="user_roles", back_populates="roles")
#     users = relationship('User', secondary='user_roles', overlaps="user_roles")

    # Relation many-to-many avec User via la table d'association 'user_roles'
    users = relationship(
        "User", secondary="user_roles", back_populates="roles"
    )
# Ce fichier définit la table des rôles. Un rôle représente un groupe 
# d'utilisateurs ayant des permissions spécifiques. Par exemple, un rôle
# "admin" peut avoir plus de permissions qu'un rôle "user". Il existe aussi 
# une relation avec la table de liaison des permissions.
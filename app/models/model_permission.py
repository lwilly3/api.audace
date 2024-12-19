from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


from app.db.database import Base #metadata
# -------------------------
# Table pour les Permissions
# -------------------------
class Permission(Base):
    __tablename__ = "permissions"  # Nom de la table

    id = Column(Integer, primary_key=True)  # Identifiant de la permission
    name = Column(String, nullable=False, unique=True)  # Nom unique de la permission (ex : "read", "write")

      # Relation avec les rôles via la table de liaison RolePermission
    # roles = relationship("RolePermission", back_populates="permission")
    roles = relationship('Role', secondary='role_permissions', back_populates='permissions')
   


# Ce fichier définit la table des permissions, 
# qui est utilisée pour attribuer des droits spécifiques aux utilisateurs. 
# Chaque permission a un identifiant unique et un nom.
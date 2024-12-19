from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base




# -------------------------
# Table de liaison entre Utilisateurs et Rôles
# -------------------------

# Modèle pour la table intermédiaire "user_roles" (liaison entre utilisateurs et rôles)
class UserRole(Base):
    __tablename__ = "user_roles"  # Nom de la table

    # user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)  # Clé étrangère vers "users"
    # role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)  # Clé étrangère vers "roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    # Relations
#     user = relationship("User", back_populates="roles")  # Liaison avec User
#     role = relationship("Role", back_populates="users")  # Liaison avec Role
# #    # Relations
#     user = relationship('User', overlaps='roles')
#     role = relationship('Role', overlaps='users')
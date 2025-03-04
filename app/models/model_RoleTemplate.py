from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class RoleTemplate(Base):
    __tablename__ = "role_templates"


    id = Column(Integer, primary_key=True)  # ID comme chaîne (ex. "admin", "presenter")
    name = Column(String, nullable=False, unique=True)  # Nom du modèle (ex. "Administrateur")
    description = Column(String, nullable=True)  # Description du modèle
    permissions = Column(JSON, nullable=False)  # Permissions stockées en JSON (ex. {"can_edit_users": true})
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

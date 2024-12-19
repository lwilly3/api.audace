from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from app.db.database import Base #metadata

# -------------------------
# BaseModel pour Soft Delete
# -------------------------
class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True  # Indique que cette classe ne sera pas une table directe
    is_deleted = Column(Boolean, default=False)  # Marque la ligne comme supprimée
    deleted_at = Column(DateTime, nullable=True)  # Enregistre la date de suppression





# Ce fichier définit une classe de base avec la fonctionnalité 
# de suppression douce (soft delete), permettant de marquer un 
# enregistrement comme supprimé sans le supprimer réellement de la base de données.

# Importation des modules nécessaires
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Text, DateTime,func,Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import zlib
from datetime import datetime
from app.db.database import Base #metadata


# -------------------------
# BaseModel pour Soft Delete
# définit une classe de base avec la fonctionnalité 
# de suppression douce (soft delete), permettant de marquer un 
# enregistrement comme supprimé sans le supprimer réellement de la base de données.
# -------------------------
class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True  # Indique que cette classe ne sera pas une table directe
    is_deleted = Column(Boolean, default=False)  # Marque la ligne comme supprimée
    deleted_at = Column(DateTime, nullable=True)  # Enregistre la date de suppression



# -------------------------
# Modèle pour les Présentateurs (avec Soft Delete)
# -------------------------
# class Presenter(BaseModel):
#     __tablename__ = "presenters"  # Table des présentateurs
#     id = Column(Integer, primary_key=True)  # Identifiant du présentateur
#     name = Column(String, nullable=False)  # Nom du présentateur
#     biography = Column(Text, nullable=True)  # Biographie du présentateur (optionnelle)





class Presenter(BaseModel):
    """
    Modèle représentant un présentateur d'émission.
    Un présentateur peut être associé à plusieurs émissions.
    """
    __tablename__ = "presenters"  # Nom de la table dans la base de données

    id = Column(Integer, primary_key=True)  # Identifiant unique du présentateur
    name = Column(String, nullable=False, index=True)  # Nom du présentateur
    contact_info = Column(String, nullable=True)  # Informations de contact
    biography = Column(Text, nullable=True)  # Biographie ou informations détaillées sur le présentateur
    profilePicture = Column(Text, nullable=True)
    isMainPresenter = Column(Boolean, default=False)  # Indique si le présentateur est le principal 
    
    # Dates de création et de dernière modification
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    users_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relation avec les émissions via la table associative "show_presenters"
    # shows = relationship("Show", secondary="show_presenters", back_populates="presenters")

    # Relation plusieurs-à-plusieurs avec Show via ShowPresenter
    shows = relationship("Show", secondary="show_presenters", back_populates="presenters")
      # Relation avec les émissions via la table "show_presenters"
    # show_presenters = relationship("ShowPresenter", back_populates="presenter", overlaps="shows")
    # user = relationship("User", back_populates="presenters")

      # Relation inverse avec User
    user = relationship("User", back_populates="presenter")


    # Relation avec les émissions via la table associative "show_presenters"
   
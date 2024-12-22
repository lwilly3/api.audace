
from sqlalchemy import Column, Integer, String, Text, DateTime, func,Table, ForeignKey,Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base


class BaseModel(Base):
    """Classe de base avec suppression douce (soft delete)"""
    __abstract__ = True  # Indique que cette classe ne sera pas une table directe
    is_deleted = Column(Boolean, default=False)  # Marque la ligne comme supprimée
    deleted_at = Column(DateTime, nullable=True)  # Enregistre la date de suppression




class Guest(BaseModel):
    """
    Modèle représentant un invité d'une émission ou d'un segment.
    Un invité peut être associé à plusieurs segments.
    """
    __tablename__ = "guests"  # Nom de la table dans la base de données a metre a jour

    id  = Column(Integer, primary_key=True)  #  Identifiant unique de l'invité
    name  = Column(String, nullable=False, index=True)  # Nom de l'invité
    email  = Column(String, nullable=True)  # Email  de l'invite
    phone = Column(String, nullable=True)  # Numéro de téléphone de l'invite 
    role  = Column(String, nullable=True)  # role de l'invite (optionnel)
# role phone email
    contact_info = Column(String, nullable=True, index=True)  # Informations de contact
    biography = Column(Text, nullable=True)  # Biographie ou informations détaillées sur l'invité

    # Dates de création et de dernière modification
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    # # Relation avec les segments via la table associative "segment_guests"
    # segments = relationship("Segment", secondary="segment_guests", back_populates="guests")



    # Relation plusieurs-à-plusieurs avec Segment via SegmentGuest
    segments = relationship("Segment", secondary="segment_guests", back_populates="guests")



















# # Importation des modules nécessaires
# from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Text, DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship, sessionmaker
# import zlib
# from datetime import datetime

# from app.db.database import Base #metadata





# # -------------------------
# # Modèle pour les Invités (avec Soft Delete)
# # -------------------------
# class Guest(Base):
#     __tablename__ = "guests"  # Table des invités
#     id = Column(Integer, primary_key=True)  # Identifiant de l'invité
#     name = Column(String, nullable=False)  # Nom de l'invité 
#     contact_info = Column(String, nullable=False)  # Informations de contact de l'invité
#     is_active = Column(Boolean, default=True)  # Indique si l'invité est actif
#     created_at = Column(DateTime, default=datetime.utcnow)  # Date de création de l'invité
#     details = Column(Text, nullable=True)  # Détails supplémentaires sur l'invité (optionnel)
#     biography = Column(Text, nullable=True)  # Biographie de l'invité (optionnelle)


  
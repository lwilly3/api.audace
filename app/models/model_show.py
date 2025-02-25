from sqlalchemy import Column, Integer, String, Text, DateTime, func, Table, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base



class Show(Base):
    """
    Modèle représentant une émission/programmation de la radio.
    Une émission peut être associée à plusieurs segments et plusieurs présentateurs.
    """
    __tablename__ = "shows"  # Nom de la table dans la base de données

    id = Column(Integer, primary_key=True)  # Identifiant unique de l'émission
    title = Column(String, nullable=False, index=True)  # Titre de l'émission
    type = Column(String, nullable=False, index=True)  # Type d'émission (e.g., actualité, musique, débat)
    broadcast_date = Column(DateTime, nullable=True, index=True)  # Date de diffusion de l'émission
    duration = Column(Integer, nullable=False)  # Durée de l'émission en minutes
    frequency = Column(String, nullable=True)  # Fréquence (e.g., hebdomadaire, mensuelle)
    description = Column(Text, nullable=True)  # Description ou résumé de l'émission
    status = Column(String, default="En préparation", nullable=False, index=True)  # Statut de l'émission

    # Dates de création et de dernière modification (générées automatiquement par le serveur)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    # emission_id = Column(Integer, ForeignKey('emissions.id'))

    # Clé étrangère vers l'utilisateur qui a créé l'émission
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
   
    
    # Clé étrangère vers Emission
    emission_id = Column(Integer, ForeignKey("emissions.id", ondelete="CASCADE"))

    # Relation inverse vers Emission
    emission = relationship("Emission", back_populates="shows")

    presenters = relationship("Presenter", secondary="show_presenters", back_populates="shows")
    segments = relationship("Segment", back_populates="show", cascade="all, delete-orphan")

    # Ajout d'un index composite pour optimiser les recherches par type et statut
    __table_args__ = (
        Index("ix_show_type_status", "type", "status"),
        Index("ix_created_by_status_type", "created_by", "status", "type"),  # Nouvel index composite
        Index("ix_created_by_status_broadcast_date", "created_by", "status", "broadcast_date"),  # Nouvel index composite pour created_by, status et broadcast_date
    )

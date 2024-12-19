# from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Table, Index
# from sqlalchemy.orm import relationship
# from app.db.database import Base



# class Segment(Base):
#     """
#     Modèle représentant un segment d'une émission.
#     Un segment peut être associé à plusieurs invités.
#     """
#     __tablename__ = "segments"  # Nom de la table dans la base de données

#     id = Column(Integer, primary_key=True)  # Identifiant unique du segment
#     title = Column(String, nullable=False, index=True)  # Titre du segment
#     type = Column(String, nullable=False, index=True)  # Type de segment (e.g., interview, reportage)
#     duration = Column(Integer, nullable=False)  # Durée en minutes
#     description = Column(Text, nullable=True)  # Description ou résumé du segment
#     technical_notes = Column(Text, nullable=True)  # Notes techniques pour les techniciens

#     # Clé étrangère pour lier un segment à une émission
#     show_id = Column(Integer, ForeignKey("shows.id"), nullable=False, index=True)
#     show = relationship("Show", back_populates="segments")  # Relation inverse vers Show

#     # Dates de création et de dernière modification
#     created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
#     updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

#     # Relation avec les invités via la table associative "segment_guests"
#     guests = relationship("Guest", secondary="segment_guests", back_populates="segments")

#     # Ajout d'un index composite pour optimiser les recherches
#     __table_args__ = (
#         Index("ix_segment_title_type", "title", "type"),
#     )

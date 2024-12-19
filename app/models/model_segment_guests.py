from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Index
# from sqlalchemy.orm import relationship
from app.db.database import Base

class SegmentGuest(Base):
    """
    Table associative pour lier les invités aux segments.
    Elle permet de gérer la relation plusieurs-à-plusieurs entre les segments et les invités.
    """
    __tablename__ = "segment_guests"
    
    id = Column(Integer, primary_key=True)  # Identifiant unique pour la table associative
    segment_id = Column(Integer, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id", ondelete="CASCADE"), nullable=False)
    # segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False, index=True)  # Clé étrangère vers Segment
    # guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False, index=True)  # Clé étrangère vers Guest
    created_at = Column(DateTime, server_default=func.now(), nullable=False)  # Date de création de la liaison

    # Index pour optimiser les recherches par segment et invité
    # __table_args__ = (
    #     Index("ix_segment_guest_segment_id_guest_id", "segment_id", "guest_id", unique=True),
    # )
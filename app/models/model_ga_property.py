"""
Modele SQLAlchemy pour les proprietes Google Analytics 4 (GA4).

Table : ga_properties — Stocke les proprietes GA4 configurees
pour le suivi web analytics multi-sites.

Chaque propriete correspond a un site web avec son property_id GA4.
Le Service Account doit avoir l'acces "Lecteur" dans GA4 pour chaque propriete.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class GaProperty(Base):
    """Propriete GA4 configuree pour le suivi web analytics."""
    __tablename__ = "ga_properties"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    website_url = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

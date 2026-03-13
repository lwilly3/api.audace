"""
@fileoverview Modele SQLAlchemy pour les appareils de confiance (trusted devices).

Permet aux utilisateurs de marquer un navigateur comme "de confiance" apres
une verification 2FA reussie, evitant de redemander le code OTP pendant 30 jours.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql.expression import func

from app.db.database import Base


class TrustedDevice(Base):
    """Appareil de confiance pour le bypass 2FA."""
    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_token_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hex
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class PublicAlert(Base):
    """
    Modele representant une alerte publique affichee sur le site WordPress.
    Les alertes sont gerees depuis le SaaS RadioManager et affichees
    en bandeau sur le site public.
    """
    __tablename__ = "public_alerts"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), default="info", nullable=False)  # info, warning, urgent
    is_active = Column(Boolean, default=True, nullable=False)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    url = Column(String(500), nullable=True)  # Lien CTA optionnel

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship("User")

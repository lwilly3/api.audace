from sqlalchemy import Column, Integer, String, DateTime, func, Index
from app.db.database import Base


class ListenEvent(Base):
    """
    Modele representant un evenement d'ecoute envoye depuis le site WordPress.
    Table append-only pour les statistiques d'audience.
    """
    __tablename__ = "listen_events"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # play, pause, stop, heartbeat
    duration = Column(Integer, default=0)  # Duree d'ecoute en secondes
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    referrer = Column(String(500), nullable=True)
    page_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_listen_events_session_created", "session_id", "created_at"),
        Index("ix_listen_events_type_created", "event_type", "created_at"),
    )

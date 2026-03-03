from sqlalchemy import Column, Integer, String, Float, DateTime, func, Index
from app.db.database import Base


class NowPlayingTrack(Base):
    """
    Modele representant un morceau en cours de diffusion signale par RadioDJ.
    Chaque changement de piste cree une nouvelle ligne (historique + current = latest row).
    """
    __tablename__ = "now_playing_tracks"

    id = Column(Integer, primary_key=True)
    artist = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration = Column(Float, nullable=True)            # Duree en secondes
    track_type = Column(String(50), nullable=True)     # Type RadioDJ: Music, Jingle, Sweeper...
    cover_url = Column(String(500), nullable=True)     # URL pochette (reserve pour v2)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_now_playing_tracks_started_at", "started_at"),
    )

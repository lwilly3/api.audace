"""
Modeles SQLAlchemy pour la gestion des sauvegardes (Backup Management).

Tables :
- backup_config : configuration singleton (1 seule ligne) pour Google Drive + schedule
- backup_history : historique de chaque tentative de sauvegarde
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, text
from sqlalchemy.sql import func
from app.db.database import Base


class BackupConfig(Base):
    """Configuration singleton pour les sauvegardes Google Drive."""
    __tablename__ = "backup_config"

    id = Column(Integer, primary_key=True, index=True)

    # Google Drive OAuth tokens (chiffres via Fernet, meme cle que TOTP)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Google Drive : dossier cible pour les backups
    google_drive_folder_id = Column(String(255), nullable=True)
    google_drive_folder_name = Column(String(255), nullable=True)

    # Email du compte Google connecte (affichage UI)
    google_email = Column(String(255), nullable=True)

    # Configuration du backup automatique
    auto_backup_enabled = Column(Boolean, default=False, server_default=text('false'))
    auto_backup_hour = Column(Integer, default=3)       # Heure du jour (0-23)
    retention_days = Column(Integer, default=30)          # Nombre de jours de retention

    # Etat de la connexion
    is_connected = Column(Boolean, default=False, server_default=text('false'))
    connected_by = Column(Integer, nullable=True)         # user_id qui a connecte
    connected_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BackupHistory(Base):
    """Historique des sauvegardes (1 ligne par tentative de backup)."""
    __tablename__ = "backup_history"

    id = Column(Integer, primary_key=True, index=True)

    # Metadonnees du fichier
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # Type et statut
    backup_type = Column(String(20), nullable=False, default="manual")    # manual, scheduled
    status = Column(String(20), nullable=False, default="running")        # running, completed, failed
    error_message = Column(Text, nullable=True)

    # Google Drive
    google_drive_file_id = Column(String(255), nullable=True)
    uploaded_to_drive = Column(Boolean, default=False, server_default=text('false'))

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Qui a declenche le backup (null = scheduled)
    triggered_by = Column(Integer, nullable=True)

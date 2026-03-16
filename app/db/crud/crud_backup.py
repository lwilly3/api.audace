"""
CRUD pour la gestion des sauvegardes (Backup Management).

Fonctions d'acces aux tables backup_config et backup_history.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.model_backup import BackupConfig, BackupHistory

logger = logging.getLogger("hapson-api")


# ── BackupConfig (singleton) ───────────────────────────────────

def get_backup_config(db: Session) -> Optional[BackupConfig]:
    """Retourne la configuration unique de backup (ou None)."""
    return db.query(BackupConfig).first()


def upsert_backup_config(db: Session, **fields) -> BackupConfig:
    """
    Cree ou met a jour la configuration de backup.
    Pattern singleton : il n'y a qu'une seule ligne.
    """
    config = db.query(BackupConfig).first()
    if not config:
        config = BackupConfig(**fields)
        db.add(config)
    else:
        for key, value in fields.items():
            if hasattr(config, key):
                setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


# ── BackupHistory ───────────────────────────────────────────────

def create_backup_history(
    db: Session,
    filename: str,
    backup_type: str = "manual",
    triggered_by: Optional[int] = None,
) -> BackupHistory:
    """Cree une nouvelle entree d'historique de backup."""
    entry = BackupHistory(
        filename=filename,
        backup_type=backup_type,
        status="running",
        triggered_by=triggered_by,
        started_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_backup_history(db: Session, backup_id: int, **fields) -> Optional[BackupHistory]:
    """Met a jour une entree d'historique."""
    entry = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
    if not entry:
        return None
    for key, value in fields.items():
        if hasattr(entry, key):
            setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def get_backup_history(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[BackupHistory], int]:
    """Retourne l'historique pagine (plus recents en premier) + total."""
    query = db.query(BackupHistory).order_by(BackupHistory.started_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_backup_by_id(db: Session, backup_id: int) -> Optional[BackupHistory]:
    """Retourne une entree de backup par son ID."""
    return db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()


def get_last_backup(db: Session) -> Optional[BackupHistory]:
    """Retourne le dernier backup (peu importe le statut)."""
    return db.query(BackupHistory).order_by(BackupHistory.started_at.desc()).first()


def get_today_backup(db: Session) -> Optional[BackupHistory]:
    """Retourne le backup du jour (pour eviter les doublons scheduled)."""
    today = datetime.now(timezone.utc).date()
    return (
        db.query(BackupHistory)
        .filter(
            BackupHistory.backup_type == "scheduled",
            BackupHistory.started_at >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc),
        )
        .first()
    )

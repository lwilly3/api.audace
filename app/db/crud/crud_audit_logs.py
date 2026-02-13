from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models import AuditLog, ArchivedAuditLog
from app.schemas.schema_archived_audit_logs import ArchivedAuditLogCreate
from sqlalchemy.exc import SQLAlchemyError

# CRUD pour les logs d'audit actifs
def get_all_audit_logs(db: Session) -> list:
    """Récupérer tous les logs d'audit actifs"""
    try:
        return db.query(AuditLog).all()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des logs d'audit actifs : {str(e)}")

def get_audit_log(db: Session, id: int) -> AuditLog:
    """Récupérer un log d'audit spécifique"""
    try:
        return db.query(AuditLog).filter(AuditLog.id == id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération du log d'audit avec ID {id} : {str(e)}")

def create_audit_log(db: Session, action: str, user_id: Optional[int], details: Optional[str]) -> AuditLog:
    """Créer un log d'audit"""
    try:
        new_log = AuditLog(
            action=action,
            user_id=user_id,
            table_name="example_table",  # Remplacez par la table concernée
            record_id=123,  # Remplacez par l'ID de l'enregistrement concerné
            timestamp=datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except SQLAlchemyError as e:
        db.rollback()  # Annule la transaction en cas d'erreur
        raise Exception(f"Erreur lors de la création du log d'audit : {str(e)}")

def archive_audit_log(db: Session, id: int) -> Optional[ArchivedAuditLog]:
    """Archiver un log d'audit"""
    try:
        log = db.query(AuditLog).filter(AuditLog.id == id).first()
        if log:
            # Archive le log
            archived_log = ArchivedAuditLog(
                user_id=log.user_id,
                action=log.action,
                table_name=log.table_name,
                record_id=log.record_id,
                timestamp=log.timestamp
            )
            db.add(archived_log)

            # Supprimer le log actif
            db.delete(log)
            db.commit()
            db.refresh(archived_log)

            return archived_log
        return None
    except SQLAlchemyError as e:
        db.rollback()  # Annule la transaction en cas d'erreur
        raise Exception(f"Erreur lors de l'archivage du log d'audit avec ID {id} : {str(e)}")

# CRUD pour les logs d'audit archivés
def get_all_archived_audit_logs(db: Session) -> list:
    """Récupérer tous les logs d'audit archivés"""
    try:
        return db.query(ArchivedAuditLog).all()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des logs d'audit archivés : {str(e)}")

def get_archived_audit_log(db: Session, id: int) -> ArchivedAuditLog:
    """Récupérer un log d'audit archivé spécifique"""
    try:
        return db.query(ArchivedAuditLog).filter(ArchivedAuditLog.id == id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération du log d'audit archivé avec ID {id} : {str(e)}")

















# # database.py
# from models import AuditLog
# from datetime import datetime

# # Base de données simulée pour les logs actifs et archivés
# audit_logs_db = {}
# archived_audit_logs_db = {}

# # CRUD pour les logs d'audit actifs
# def get_all_audit_logs() -> list:
#     """Récupérer tous les logs d'audit actifs"""
#     return list(audit_logs_db.values())

# def get_audit_log(id: int) -> Optional[AuditLog]:
#     """Récupérer un log d'audit spécifique"""
#     return audit_logs_db.get(id)

# def create_audit_log(action: str, user_id: Optional[int], details: Optional[str]) -> AuditLog:
#     """Créer un log d'audit"""
#     log_id = len(audit_logs_db) + 1  # Génération d'un nouvel ID
#     new_log = AuditLog(
#         id=log_id,
#         action=action,
#         user_id=user_id,
#         details=details,
#         timestamp=datetime.utcnow(),
#         is_archived=False
#     )
#     audit_logs_db[log_id] = new_log
#     return new_log

# def archive_audit_log(id: int) -> Optional[AuditLog]:
#     """Archiver un log d'audit"""
#     log = audit_logs_db.pop(id, None)
#     if log:
#         log.is_archived = True
#         archived_audit_logs_db[id] = log
#     return log

# # CRUD pour les logs d'audit archivés
# def get_all_archived_audit_logs() -> list:
#     """Récupérer tous les logs d'audit archivés"""
#     return list(archived_audit_logs_db.values())

# def get_archived_audit_log(id: int) -> Optional[AuditLog]:
#     """Récupérer un log d'audit archivé spécifique"""
#     return archived_audit_logs_db.get(id)











# from sqlalchemy.orm import Session
# from app.models import AuditLog
# from app.schemas.schema_audit_logs import AuditLogCreate

# def create_audit_log(db: Session, log: AuditLogCreate):
#     new_log = AuditLog(**log.dict())
#     db.add(new_log)
#     db.commit()
#     db.refresh(new_log)
#     return new_log

# def get_audit_logs(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(AuditLog).offset(skip).limit(limit).all()

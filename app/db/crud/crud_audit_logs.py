from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, timezone
from app.models import AuditLog, ArchivedAuditLog, User
from app.schemas.schema_archived_audit_logs import ArchivedAuditLogCreate
from sqlalchemy.exc import SQLAlchemyError


def _serialize_log_with_username(log: AuditLog) -> dict:
    """Sérialise un log d'audit en incluant le username de l'utilisateur."""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "action": log.action,
        "table_name": log.table_name,
        "record_id": log.record_id,
        "timestamp": log.timestamp,
        "username": log.user.username if log.user else None
    }


# CRUD pour les logs d'audit actifs
def get_all_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Tuple[List[dict], int]:
    """
    Récupérer les logs d'audit actifs avec pagination, filtres et tri.
    
    Returns:
        Tuple[List[dict], int]: (logs sérialisés avec username, total count)
    """
    try:
        query = db.query(AuditLog).options(joinedload(AuditLog.user))
        
        # Filtres
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action is not None:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))
        if table_name is not None:
            query = query.filter(AuditLog.table_name.ilike(f"%{table_name}%"))
        if start_date is not None:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date is not None:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Total avant pagination
        total = query.count()
        
        # Tri par date décroissante + pagination
        logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
        
        return [_serialize_log_with_username(log) for log in logs], total
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des logs d'audit actifs : {str(e)}")

def get_audit_log(db: Session, id: int) -> Optional[dict]:
    """Récupérer un log d'audit spécifique avec username"""
    try:
        log = db.query(AuditLog).options(joinedload(AuditLog.user)).filter(AuditLog.id == id).first()
        if log:
            return _serialize_log_with_username(log)
        return None
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération du log d'audit avec ID {id} : {str(e)}")


def get_audit_log_stats(db: Session) -> dict:
    """
    Récupérer des statistiques sur les logs d'audit.
    Comptage par action, par table, et les 10 dernières actions.
    """
    try:
        total = db.query(func.count(AuditLog.id)).scalar()
        
        # Comptage par action
        action_counts = db.query(
            AuditLog.action, func.count(AuditLog.id)
        ).group_by(AuditLog.action).all()
        actions = {action: count for action, count in action_counts}
        
        # Comptage par table
        table_counts = db.query(
            AuditLog.table_name, func.count(AuditLog.id)
        ).group_by(AuditLog.table_name).all()
        tables = {table: count for table, count in table_counts}
        
        # 10 dernières actions
        recent = db.query(AuditLog).options(
            joinedload(AuditLog.user)
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        return {
            "total_logs": total or 0,
            "actions": actions,
            "tables": tables,
            "recent_activity": [_serialize_log_with_username(log) for log in recent]
        }
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des statistiques : {str(e)}")

def create_audit_log(db: Session, action: str, user_id: Optional[int], details: Optional[str] = None, table_name: str = "unknown", record_id: int = 0) -> AuditLog:
    """Créer un log d'audit"""
    try:
        new_log = AuditLog(
            action=action,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Erreur lors de la création du log d'audit : {str(e)}")


def log_action(db: Session, user_id: int, action: str, table_name: str, record_id: int = 0):
    """
    Fonction utilitaire simplifiée pour enregistrer un audit log.
    Ne lève pas d'exception en cas d'échec (fail-safe).
    
    Args:
        db: Session SQLAlchemy
        user_id: ID de l'utilisateur effectuant l'action
        action: Description de l'action (ex: "create", "update", "delete")
        table_name: Nom de la table concernée
        record_id: ID de l'enregistrement concerné
    """
    try:
        new_log = AuditLog(
            action=action,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(new_log)
        # Empêche l'expiration des autres objets traqués par la session
        old_expire = db.expire_on_commit
        db.expire_on_commit = False
        db.commit()
        db.expire_on_commit = old_expire
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger("audit").warning(f"Échec de l'enregistrement du log d'audit: {e}")

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
def get_all_archived_audit_logs(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
    """Récupérer les logs d'audit archivés avec pagination"""
    try:
        total = db.query(func.count(ArchivedAuditLog.id)).scalar()
        logs = db.query(ArchivedAuditLog).options(
            joinedload(ArchivedAuditLog.user)
        ).order_by(desc(ArchivedAuditLog.timestamp)).offset(skip).limit(limit).all()
        
        serialized = []
        for log in logs:
            serialized.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "timestamp": log.timestamp,
                "username": log.user.username if log.user else None
            })
        return serialized, total or 0
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

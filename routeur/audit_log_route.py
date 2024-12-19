from fastapi import APIRouter, HTTPException,Depends
from typing import List, Optional
from app.db.crud.crud_audit_logs import (
    get_all_audit_logs,
    get_audit_log,
    create_audit_log,
    archive_audit_log,
    get_all_archived_audit_logs,
    get_archived_audit_log
)
from app.schemas import AuditLog, AuditLogBase
from core.auth import oauth2


router = APIRouter(
    prefix="/audit-logs",
    tags=['audit-logs']
)

# Routes pour les logs d'audit
@router.get("/audit-logs", response_model=List[AuditLog])
def get_all_audit_logs_route( current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer tous les logs d'audit actifs.
    """
    return get_all_audit_logs()

@router.get("/audit-logs/{id}", response_model=AuditLog)
def get_audit_log_route(id: int, current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer un log d'audit spécifique.
    """
    log = get_audit_log(id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log

@router.post("/audit-logs", response_model=AuditLog)
def create_audit_log_route(log: AuditLogBase,current_user: int = Depends(oauth2.get_current_user)):
    """
    Créer un nouveau log d'audit.
    """
    new_log = create_audit_log(log.action, log.user_id, log.details)
    return new_log

# Routes pour les logs d'audit archivés
@router.get("/archived-audit-logs", response_model=List[AuditLog])
def get_all_archived_audit_logs_route(current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer tous les logs d'audit archivés.
    """
    return get_all_archived_audit_logs()

@router.get("/archived-audit-logs/{id}", response_model=AuditLog)
def get_archived_audit_log_route(id: int,current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer un log d'audit archivé spécifique.
    """
    log = get_archived_audit_log(id)
    if not log:
        raise HTTPException(status_code=404, detail="Archived audit log not found")
    return log

@router.post("/audit-logs/{id}/archive")
def archive_audit_log_route(id: int,current_user: int = Depends(oauth2.get_current_user)):
    """
    Archiver un log d'audit actif.
    """
    log = archive_audit_log(id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"detail": f"Audit log {id} archived successfully"}












# from fastapi import FastAPI, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# app = FastAPI()

# # Simulated databases
# audit_logs_db = {}  # Active audit logs
# archived_audit_logs_db = {}  # Archived audit logs

# # Models
# class AuditLog(BaseModel):
#     """
#     Modèle pour représenter un log d'audit.
#     """
#     id: int
#     action: str
#     user_id: Optional[int] = None
#     details: Optional[str] = None
#     timestamp: datetime
#     is_archived: bool = False


# # Routes pour l'audit et les logs
# @app.get("/audit-logs", response_model=List[AuditLog])
# def get_all_audit_logs():
#     """
#     Récupérer tous les logs d'audit actifs.
#     """
#     return list(audit_logs_db.values())


# @app.get("/audit-logs/{id}", response_model=AuditLog)
# def get_audit_log(id: int):
#     """
#     Récupérer un log d'audit spécifique.
#     """
#     log = audit_logs_db.get(id)
#     if not log:
#         raise HTTPException(status_code=404, detail="Audit log not found")
#     return log


# @app.post("/audit-logs", response_model=AuditLog)
# def create_audit_log(action: str, user_id: Optional[int] = None, details: Optional[str] = None):
#     """
#     Créer un nouveau log d'audit.
#     """
#     log_id = len(audit_logs_db) + 1
#     new_log = AuditLog(
#         id=log_id,
#         action=action,
#         user_id=user_id,
#         details=details,
#         timestamp=datetime.utcnow(),
#     )
#     audit_logs_db[log_id] = new_log
#     return new_log


# @app.get("/archived-audit-logs", response_model=List[AuditLog])
# def get_all_archived_audit_logs():
#     """
#     Récupérer tous les logs d'audit archivés.
#     """
#     return list(archived_audit_logs_db.values())


# @app.get("/archived-audit-logs/{id}", response_model=AuditLog)
# def get_archived_audit_log(id: int):
#     """
#     Récupérer un log d'audit archivé spécifique.
#     """
#     log = archived_audit_logs_db.get(id)
#     if not log:
#         raise HTTPException(status_code=404, detail="Archived audit log not found")
#     return log


# # Fonction pour archiver un log d'audit
# @app.post("/audit-logs/{id}/archive")
# def archive_audit_log(id: int):
#     """
#     Archiver un log d'audit actif.
#     """
#     log = audit_logs_db.pop(id, None)
#     if not log:
#         raise HTTPException(status_code=404, detail="Audit log not found")
#     log.is_archived = True
#     archived_audit_logs_db[id] = log
#     return {"detail": f"Audit log {id} archived successfully"}

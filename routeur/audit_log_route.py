from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.crud.crud_audit_logs import (
    get_all_audit_logs,
    get_audit_log,
    create_audit_log,
    archive_audit_log,
    get_all_archived_audit_logs,
    get_archived_audit_log
)
from app.schemas import AuditLog, AuditLogBase
from app.db.database import get_db
from core.auth import oauth2


router = APIRouter(
    prefix="/audit-logs",
    tags=['audit-logs']
)

# Routes pour les logs d'audit
@router.get("/audit-logs", response_model=List[AuditLog])
def get_all_audit_logs_route(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer tous les logs d'audit actifs.
    """
    return get_all_audit_logs(db)

@router.get("/audit-logs/{id}", response_model=AuditLog)
def get_audit_log_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer un log d'audit spécifique.
    """
    log = get_audit_log(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log

@router.post("/audit-logs", response_model=AuditLog)
def create_audit_log_route(
    log: AuditLogBase,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Créer un nouveau log d'audit.
    """
    new_log = create_audit_log(db, log.action, log.user_id, log.details)
    return new_log

# Routes pour les logs d'audit archivés
@router.get("/archived-audit-logs", response_model=List[AuditLog])
def get_all_archived_audit_logs_route(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer tous les logs d'audit archivés.
    """
    return get_all_archived_audit_logs(db)

@router.get("/archived-audit-logs/{id}", response_model=AuditLog)
def get_archived_audit_log_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer un log d'audit archivé spécifique.
    """
    log = get_archived_audit_log(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="Archived audit log not found")
    return log

@router.post("/audit-logs/{id}/archive")
def archive_audit_log_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Archiver un log d'audit actif.
    """
    log = archive_audit_log(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"detail": f"Audit log {id} archived successfully"}

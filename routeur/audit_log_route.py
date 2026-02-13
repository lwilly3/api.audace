from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.crud.crud_audit_logs import (
    get_all_audit_logs,
    get_audit_log,
    create_audit_log,
    archive_audit_log,
    get_all_archived_audit_logs,
    get_archived_audit_log,
    get_audit_log_stats
)
from app.schemas import AuditLog, AuditLogBase, AuditLogPaginated, AuditLogStats
from app.db.database import get_db
from core.auth import oauth2


router = APIRouter(
    prefix="/audit-logs",
    tags=['audit-logs']
)


# ===================== LOGS ACTIFS =====================

@router.get("/", response_model=AuditLogPaginated)
def get_all_audit_logs_route(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max d'éléments à retourner"),
    user_id: Optional[int] = Query(None, description="Filtrer par ID utilisateur"),
    action: Optional[str] = Query(None, description="Filtrer par action (create, update, delete, login...)"),
    table_name: Optional[str] = Query(None, description="Filtrer par table (users, shows, emissions...)"),
    start_date: Optional[datetime] = Query(None, description="Date de début (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Date de fin (ISO 8601)"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer les logs d'audit avec pagination et filtres.
    
    Filtres disponibles :
    - **user_id** : ID de l'utilisateur
    - **action** : Type d'action (create, update, delete, login, logout, etc.)
    - **table_name** : Table concernée (users, shows, emissions, etc.)
    - **start_date / end_date** : Plage de dates
    """
    items, total = get_all_audit_logs(
        db, skip=skip, limit=limit,
        user_id=user_id, action=action, table_name=table_name,
        start_date=start_date, end_date=end_date
    )
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats", response_model=AuditLogStats)
def get_audit_stats_route(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer les statistiques des logs d'audit.
    
    Retourne :
    - **total_logs** : Nombre total de logs
    - **actions** : Comptage par type d'action
    - **tables** : Comptage par table
    - **recent_activity** : Les 10 dernières actions
    """
    return get_audit_log_stats(db)


@router.get("/{id}", response_model=AuditLog)
def get_audit_log_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer un log d'audit spécifique par son ID.
    """
    log = get_audit_log(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


@router.post("/", response_model=AuditLog)
def create_audit_log_route(
    log: AuditLogBase,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Créer un nouveau log d'audit manuellement.
    """
    new_log = create_audit_log(
        db, log.action, log.user_id,
        table_name=log.table_name or "manual",
        record_id=log.record_id or 0
    )
    return new_log


# ===================== ARCHIVAGE =====================

@router.post("/{id}/archive")
def archive_audit_log_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Archiver un log d'audit actif (le déplace vers la table des archives).
    """
    log = archive_audit_log(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"detail": f"Audit log {id} archived successfully"}


# ===================== LOGS ARCHIVÉS =====================

@router.get("/archived/all", response_model=AuditLogPaginated)
def get_all_archived_audit_logs_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer les logs d'audit archivés avec pagination.
    """
    items, total = get_all_archived_audit_logs(db, skip=skip, limit=limit)
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }


@router.get("/archived/{id}", response_model=AuditLog)
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

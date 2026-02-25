"""
Routes Scaleway/Dedibox — Consultation des services Dedibox (Online.net).

Prefix: /scaleway
Tags: Scaleway Dedibox Services
Authentification: Bearer token + permissions granulaires

API source : https://api.online.net/api/v1 (Dedibox)
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.models import model_user
from app.models.model_user_permissions import UserPermissions
from app.db.crud.crud_audit_logs import log_action
from app.services.scaleway_client import (
    get_user_info,
    get_servers,
    get_server_detail,
    get_server_status,
    get_hostings,
    get_hosting_detail,
    get_domains,
    get_domain_detail,
    get_failover_ips,
    get_dashboard,
)

logger = logging.getLogger("hapson-api")

router = APIRouter(
    prefix="/scaleway",
    tags=["Scaleway Dedibox Services"]
)


# ════════════════════════════════════════════════════════════════
# HELPERS PERMISSIONS
# ════════════════════════════════════════════════════════════════

def _check_scw_access(db: Session, user_id: int):
    """Verifie que l'utilisateur a acces a la section Scaleway/Dedibox."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.scw_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'scw_access_section' requise pour acceder aux services Dedibox."
        )


def _check_scw_permission(db: Session, user_id: int, permission_name: str):
    """Verifie une permission Scaleway/Dedibox specifique."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.scw_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'scw_access_section' requise pour acceder aux services Dedibox."
        )
    if not getattr(perms, permission_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission_name}' requise pour cette action."
        )


# ════════════════════════════════════════════════════════════════
# ROUTES — COMPTE / UTILISATEUR
# ════════════════════════════════════════════════════════════════

@router.get("/account")
def get_scw_account(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere les informations du compte utilisateur Dedibox."""
    _check_scw_permission(db, current_user.id, "scw_view_account")
    try:
        result = get_user_info()
        log_action(db, current_user.id, "read", "scaleway_account", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du compte Dedibox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — SERVEURS DEDIES
# ════════════════════════════════════════════════════════════════

@router.get("/servers")
def list_scw_servers(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste tous les serveurs dedies Dedibox."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_servers()
        log_action(db, current_user.id, "read", "scaleway_servers", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des serveurs Dedibox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}")
def get_scw_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail d'un serveur dedie."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_server_detail(server_id)
        log_action(db, current_user.id, "read", f"scaleway_server_{server_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du serveur {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/status")
def get_scw_server_status(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le statut hardware d'un serveur (disques, reseau)."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_server_status(server_id)
        log_action(db, current_user.id, "read", f"scaleway_server_status_{server_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du statut du serveur {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — HEBERGEMENTS
# ════════════════════════════════════════════════════════════════

@router.get("/hosting")
def list_scw_hosting(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste tous les hebergements web Dedibox."""
    _check_scw_permission(db, current_user.id, "scw_view_billing")
    try:
        result = get_hostings()
        log_action(db, current_user.id, "read", "scaleway_hosting", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des hebergements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hosting/{hosting_id}")
def get_scw_hosting_detail(
    hosting_id: int,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail d'un hebergement."""
    _check_scw_permission(db, current_user.id, "scw_view_billing")
    try:
        result = get_hosting_detail(hosting_id)
        log_action(db, current_user.id, "read", f"scaleway_hosting_{hosting_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation de l'hebergement {hosting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — DOMAINES
# ════════════════════════════════════════════════════════════════

@router.get("/domains")
def list_scw_domains(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste tous les domaines geres sur Dedibox."""
    _check_scw_permission(db, current_user.id, "scw_view_domains")
    try:
        result = get_domains()
        log_action(db, current_user.id, "read", "scaleway_domains", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des domaines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains/{domain_id}")
def get_scw_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail d'un domaine."""
    _check_scw_permission(db, current_user.id, "scw_view_domains")
    try:
        result = get_domain_detail(domain_id)
        log_action(db, current_user.id, "read", f"scaleway_domain_{domain_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du domaine {domain_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — RESEAU / FAILOVER
# ════════════════════════════════════════════════════════════════

@router.get("/failover")
def list_scw_failover(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste les adresses IP failover."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_failover_ips()
        log_action(db, current_user.id, "read", "scaleway_failover", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des IPs failover: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — DASHBOARD
# ════════════════════════════════════════════════════════════════

@router.get("/dashboard")
def get_scw_dashboard(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le tableau de bord synthetique Dedibox."""
    _check_scw_permission(db, current_user.id, "scw_view_dashboard")
    try:
        result = get_dashboard()
        log_action(db, current_user.id, "read", "scaleway_dashboard", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la generation du dashboard Dedibox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

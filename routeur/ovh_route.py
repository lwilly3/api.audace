import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.models import model_user
from app.models.model_user_permissions import UserPermissions
from app.db.crud.crud_audit_logs import log_action
from app.schemas.schema_ovh import (
    OvhAccountInfo,
    OvhServiceSummary,
    OvhServiceInfo,
    OvhBill,
    OvhDashboard,
)
from app.services.ovh_client import (
    get_account_info,
    get_all_services,
    get_services_by_type,
    get_service_detail,
    get_service_info,
    get_bills,
    get_bill_detail,
    get_services_dashboard,
    SERVICE_TYPE_MAP,
)

logger = logging.getLogger("hapson-api")


router = APIRouter(
    prefix="/ovh",
    tags=["OVH Services"]
)


# --- Helpers permissions ---

def _check_ovh_access(db: Session, user_id: int):
    """Verifie que l'utilisateur a acces a la section OVH."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.ovh_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'ovh_access_section' requise pour acceder au module OVH."
        )


def _check_ovh_permission(db: Session, user_id: int, permission_name: str):
    """Verifie une permission OVH specifique."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.ovh_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'ovh_access_section' requise pour acceder au module OVH."
        )
    if not getattr(perms, permission_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission_name}' requise pour cette action."
        )


# --- Routes ---

@router.get("/account", response_model=OvhAccountInfo)
def get_ovh_account(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere les informations du compte OVH."""
    _check_ovh_permission(db, current_user.id, "ovh_view_account")
    result = get_account_info()
    log_action(db, current_user.id, "read", "ovh_account", 0)
    return result


@router.get("/services")
def get_ovh_services(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere la liste de tous les services OVH avec statut et echeances."""
    _check_ovh_permission(db, current_user.id, "ovh_view_services")
    try:
        result = get_all_services()
        log_action(db, current_user.id, "read", "ovh_services", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des services OVH: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de la recuperation des services OVH: {str(e)}"
        )


@router.get("/services/dashboard")
def get_ovh_dashboard(
    days: int = Query(default=30, ge=1, le=365, description="Nombre de jours pour l'alerte d'expiration"),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """
    Tableau de bord synthetique des services OVH.

    Retourne le nombre total de services, les services par type,
    ceux qui expirent bientot, ceux qui sont expires, et les compteurs
    de services actifs/suspendus.
    """
    _check_ovh_permission(db, current_user.id, "ovh_view_dashboard")
    try:
        result = get_services_dashboard(days_threshold=days)
        log_action(db, current_user.id, "read", "ovh_dashboard", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la construction du dashboard OVH: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de la construction du dashboard OVH: {str(e)}"
        )


@router.get("/services/types")
def get_ovh_service_types(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Retourne la liste des types de services supportes."""
    _check_ovh_access(db, current_user.id)
    return {
        "types": [
            {"key": key, "endpoint": endpoint, "description": desc}
            for key, endpoint, desc in [
                ("dedicated", "/dedicated/server", "Serveurs dedies"),
                ("vps", "/vps", "Serveurs prives virtuels"),
                ("domain", "/domain", "Noms de domaine"),
                ("hosting", "/hosting/web", "Hebergements web"),
                ("cloud", "/cloud/project", "Projets cloud"),
                ("ip", "/ip", "Blocs IP"),
                ("alldom", "/allDom", "Packs domaines"),
            ]
        ]
    }


@router.get("/services/{service_type}")
def get_ovh_services_by_type(
    service_type: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """
    Recupere la liste des services d'un type donne.

    Types valides: dedicated, vps, domain, hosting, cloud, ip, alldom
    """
    _check_ovh_permission(db, current_user.id, "ovh_view_services")
    result = get_services_by_type(service_type)
    log_action(db, current_user.id, "read", f"ovh_services_{service_type}", 0)
    return result


@router.get("/services/{service_type}/{service_name}")
def get_ovh_service_detail(
    service_type: str,
    service_name: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail complet d'un service specifique."""
    _check_ovh_permission(db, current_user.id, "ovh_view_services")
    result = get_service_detail(service_type, service_name)
    log_action(db, current_user.id, "read", f"ovh_service_{service_type}", 0)
    return result


@router.get("/services/{service_type}/{service_name}/status", response_model=OvhServiceInfo)
def get_ovh_service_status(
    service_type: str,
    service_name: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le statut et les informations d'echeance d'un service."""
    _check_ovh_permission(db, current_user.id, "ovh_view_services")
    result = get_service_info(service_type, service_name)
    log_action(db, current_user.id, "read", f"ovh_service_status_{service_type}", 0)
    return result


@router.get("/billing/bills", response_model=list[OvhBill])
def get_ovh_bills(
    count: int = Query(default=20, ge=1, le=100, description="Nombre de factures a recuperer"),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere les dernieres factures OVH."""
    _check_ovh_permission(db, current_user.id, "ovh_view_billing")
    result = get_bills(count=count)
    log_action(db, current_user.id, "read", "ovh_bills", 0)
    return result


@router.get("/billing/bills/{bill_id}", response_model=OvhBill)
def get_ovh_bill_detail(
    bill_id: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail d'une facture specifique."""
    _check_ovh_permission(db, current_user.id, "ovh_view_billing")
    result = get_bill_detail(bill_id)
    log_action(db, current_user.id, "read", "ovh_bill_detail", 0)
    return result

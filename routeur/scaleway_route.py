"""
Routes Scaleway — Consultation des services Scaleway.

Prefix: /scaleway
Tags: Scaleway Services
Authentification: Bearer token + permissions granulaires
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
from app.schemas.schema_scaleway import (
    ScwAccountInfo,
    ScwInstance,
    ScwConsumption,
    ScwInvoice,
    ScwDnsZone,
    ScwDnsRecord,
    ScwDashboard,
)
from app.services.scaleway_client import (
    get_account_info,
    get_all_instances,
    get_instance_detail,
    get_consumption,
    get_invoices,
    get_invoice_download_url,
    get_dns_zones,
    get_dns_zone_records,
    get_dashboard,
)

logger = logging.getLogger("hapson-api")

router = APIRouter(
    prefix="/scaleway",
    tags=["Scaleway Services"]
)


# ════════════════════════════════════════════════════════════════
# HELPERS PERMISSIONS
# ════════════════════════════════════════════════════════════════

def _check_scw_access(db: Session, user_id: int):
    """Verifie que l'utilisateur a acces a la section Scaleway."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.scw_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'scw_access_section' requise pour acceder aux services Scaleway."
        )


def _check_scw_permission(db: Session, user_id: int, permission_name: str):
    """Verifie une permission Scaleway specifique."""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.scw_access_section:
        raise HTTPException(
            status_code=403,
            detail="Permission 'scw_access_section' requise pour acceder aux services Scaleway."
        )
    if not getattr(perms, permission_name, False):
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission_name}' requise pour cette action."
        )


# ════════════════════════════════════════════════════════════════
# ROUTES — COMPTE
# ════════════════════════════════════════════════════════════════

@router.get("/account")
def get_scw_account(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere les informations du compte/organisation Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_account")
    try:
        result = get_account_info()
        log_action(db, current_user.id, "read", "scaleway_account", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du compte Scaleway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — INSTANCES
# ════════════════════════════════════════════════════════════════

@router.get("/instances")
def list_scw_instances(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste toutes les instances Scaleway sur toutes les zones."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_all_instances()
        log_action(db, current_user.id, "read", "scaleway_instances", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des instances Scaleway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{zone}/{server_id}")
def get_scw_instance(
    zone: str,
    server_id: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le detail d'une instance Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_instances")
    try:
        result = get_instance_detail(zone, server_id)
        log_action(db, current_user.id, "read", f"scaleway_instance_{server_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation de l'instance {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — DASHBOARD
# ════════════════════════════════════════════════════════════════

@router.get("/dashboard")
def get_scw_dashboard(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le tableau de bord synthetique Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_dashboard")
    try:
        result = get_dashboard()
        log_action(db, current_user.id, "read", "scaleway_dashboard", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la generation du dashboard Scaleway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — BILLING
# ════════════════════════════════════════════════════════════════

@router.get("/billing/consumption")
def get_scw_consumption(
    billing_period: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}$", description="Periode YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere la consommation Scaleway pour une periode donnee."""
    _check_scw_permission(db, current_user.id, "scw_view_billing")
    try:
        result = get_consumption(billing_period)
        log_action(db, current_user.id, "read", "scaleway_consumption", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation de la consommation Scaleway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billing/invoices")
def list_scw_invoices(
    count: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste les dernieres factures Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_billing")
    try:
        result = get_invoices(count)
        log_action(db, current_user.id, "read", "scaleway_invoices", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des factures Scaleway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billing/invoices/{invoice_id}/download")
def download_scw_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Recupere le lien de telechargement d'une facture Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_billing")
    try:
        result = get_invoice_download_url(invoice_id)
        log_action(db, current_user.id, "read", f"scaleway_invoice_download_{invoice_id}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du telechargement de la facture {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ROUTES — DNS
# ════════════════════════════════════════════════════════════════

@router.get("/dns/zones")
def list_scw_dns_zones(
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste toutes les zones DNS Scaleway."""
    _check_scw_permission(db, current_user.id, "scw_view_domains")
    try:
        result = get_dns_zones()
        log_action(db, current_user.id, "read", "scaleway_dns_zones", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des zones DNS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dns/zones/{dns_zone}/records")
def list_scw_dns_records(
    dns_zone: str,
    record_type: Optional[str] = Query(None, description="Type d'enregistrement (A, AAAA, CNAME, MX, TXT...)"),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste les enregistrements DNS d'une zone."""
    _check_scw_permission(db, current_user.id, "scw_view_domains")
    try:
        result = get_dns_zone_records(dns_zone, record_type)
        log_action(db, current_user.id, "read", f"scaleway_dns_records_{dns_zone}", 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des enregistrements DNS de {dns_zone}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

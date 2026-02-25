"""
Client Scaleway API — Gestion des services Scaleway.

Utilise l'API REST Scaleway (api.scaleway.com) avec authentification par Secret Key.
Supporte : Instances, Billing (consommation + factures), Domains/DNS.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Base URL de l'API Scaleway
SCW_API_BASE = "https://api.scaleway.com"

# Zones disponibles pour les Instances
SCW_ZONES = ["fr-par-1", "fr-par-2", "fr-par-3", "nl-ams-1", "nl-ams-2", "nl-ams-3", "pl-waw-1", "pl-waw-2", "pl-waw-3"]

# Regions pour les APIs regionales
SCW_REGIONS = ["fr-par", "nl-ams", "pl-waw"]


def _get_headers() -> dict:
    """Retourne les headers d'authentification Scaleway."""
    if not settings.SCW_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scaleway API n'est pas configuree. Verifiez SCW_SECRET_KEY dans .env"
        )
    return {
        "X-Auth-Token": settings.SCW_SECRET_KEY,
        "Content-Type": "application/json",
    }


def _scw_get(path: str, params: dict | None = None) -> dict | list:
    """
    Effectue un appel GET a l'API Scaleway avec gestion d'erreurs.

    Args:
        path: Chemin API (ex: /instance/v1/zones/fr-par-1/servers)
        params: Parametres de requete optionnels

    Returns:
        Reponse JSON (dict ou list)
    """
    url = f"{SCW_API_BASE}{path}"
    headers = _get_headers()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Credentials Scaleway invalides. Verifiez SCW_SECRET_KEY."
            )
        elif response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Acces non autorise pour cette ressource Scaleway. Verifiez les permissions IAM."
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ressource Scaleway introuvable: {path}"
            )
        else:
            error_msg = response.text[:200] if response.text else "Erreur inconnue"
            logger.error(f"Erreur API Scaleway ({response.status_code}) {path}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erreur API Scaleway ({response.status_code}): {error_msg}"
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de l'appel Scaleway: {path}"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau Scaleway ({path}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau lors de l'appel Scaleway: {str(e)}"
        )


# ════════════════════════════════════════════════════════════════
# COMPTE / ORGANISATION
# ════════════════════════════════════════════════════════════════

def get_account_info() -> dict:
    """Recupere les informations de l'organisation Scaleway."""
    org_id = settings.SCW_ORGANIZATION_ID
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SCW_ORGANIZATION_ID non configure dans .env"
        )

    result = {
        "organization_id": org_id,
        "projects": [],
    }

    # Lister les projets de l'organisation
    try:
        data = _scw_get("/account/v3/projects", params={"organization_id": org_id, "page_size": 50})
        if isinstance(data, dict) and "projects" in data:
            result["projects"] = data["projects"]
            result["total_projects"] = data.get("total_count", len(data["projects"]))
    except HTTPException:
        logger.warning("Impossible de lister les projets Scaleway")

    return result


# ════════════════════════════════════════════════════════════════
# INSTANCES (Serveurs)
# ════════════════════════════════════════════════════════════════

def get_all_instances() -> list[dict]:
    """
    Recupere toutes les instances sur toutes les zones.
    Enrichit chaque instance avec la zone source.
    """
    instances = []

    for zone in SCW_ZONES:
        try:
            data = _scw_get(f"/instance/v1/zones/{zone}/servers", params={"page_size": 100})
            if isinstance(data, dict) and "servers" in data:
                for server in data["servers"]:
                    server["zone"] = zone
                    instances.append(server)
        except HTTPException:
            logger.debug(f"Aucune instance dans la zone {zone} ou zone inaccessible")
            continue

    # Trier par nom
    instances.sort(key=lambda s: s.get("name", "").lower())
    return instances


def get_instance_detail(zone: str, server_id: str) -> dict:
    """Recupere le detail d'une instance specifique."""
    data = _scw_get(f"/instance/v1/zones/{zone}/servers/{server_id}")
    if isinstance(data, dict) and "server" in data:
        data["server"]["zone"] = zone
        return data["server"]
    return data


def get_instance_volumes(zone: str, server_id: str) -> list[dict]:
    """Recupere les volumes attaches a une instance."""
    try:
        data = _scw_get(f"/instance/v1/zones/{zone}/servers/{server_id}")
        if isinstance(data, dict) and "server" in data:
            vols = data["server"].get("volumes", {})
            result = []
            for key, vol in vols.items():
                vol["slot"] = key
                result.append(vol)
            return result
    except HTTPException:
        pass
    return []


# ════════════════════════════════════════════════════════════════
# BILLING (Consommation + Factures)
# ════════════════════════════════════════════════════════════════

def _format_money(money: dict | None) -> dict | None:
    """Convertit le type Money Scaleway en valeur lisible."""
    if not money:
        return None
    units = money.get("units", 0)
    nanos = money.get("nanos", 0)
    currency = money.get("currency_code", "EUR")
    value = float(units) + float(nanos) / 1_000_000_000
    return {
        "value": round(value, 2),
        "currency_code": currency,
        "text": f"{value:.2f} {currency}",
    }


def get_consumption(billing_period: str | None = None) -> dict:
    """
    Recupere la consommation du compte Scaleway.

    Args:
        billing_period: Periode au format YYYY-MM (optionnel, defaut: mois courant)

    Retourne la consommation globale et par categorie.
    """
    org_id = settings.SCW_ORGANIZATION_ID
    if not org_id:
        raise HTTPException(status_code=503, detail="SCW_ORGANIZATION_ID non configure")

    params = {"organization_id": org_id}
    if billing_period:
        params["billing_period"] = f"{billing_period}-01T00:00:00Z"

    data = _scw_get("/billing/v2beta1/consumptions", params=params)

    result = {
        "billing_period": billing_period or datetime.now().strftime("%Y-%m"),
        "consumptions": [],
        "total": None,
        "updated_at": data.get("updated_at") if isinstance(data, dict) else None,
    }

    if isinstance(data, dict) and "consumptions" in data:
        total_value = 0.0
        currency = "EUR"
        for item in data["consumptions"]:
            formatted = {
                "category": item.get("category_name", "Autre"),
                "product": item.get("product_name"),
                "project_id": item.get("project_id"),
                "value": _format_money(item.get("value")),
            }
            if formatted["value"]:
                total_value += formatted["value"]["value"]
                currency = formatted["value"]["currency_code"]
            result["consumptions"].append(formatted)

        result["total"] = {
            "value": round(total_value, 2),
            "currency_code": currency,
            "text": f"{total_value:.2f} {currency}",
        }

    return result


def get_invoices(count: int = 20) -> list[dict]:
    """
    Recupere les dernieres factures Scaleway.

    Args:
        count: Nombre max de factures a recuperer
    """
    org_id = settings.SCW_ORGANIZATION_ID
    if not org_id:
        raise HTTPException(status_code=503, detail="SCW_ORGANIZATION_ID non configure")

    data = _scw_get(
        "/billing/v2beta1/invoices",
        params={"organization_id": org_id, "page_size": count, "order_by": "start_date_desc"},
    )

    invoices = []
    if isinstance(data, dict) and "invoices" in data:
        for inv in data["invoices"]:
            invoices.append({
                "id": inv.get("id"),
                "organization_id": inv.get("organization_id"),
                "start_date": inv.get("start_date"),
                "stop_date": inv.get("stop_date"),
                "billing_period": inv.get("billing_period"),
                "issued_date": inv.get("issued_date"),
                "due_date": inv.get("due_date"),
                "total_taxed": _format_money(inv.get("total_taxed")),
                "total_untaxed": _format_money(inv.get("total_untaxed")),
                "total_tax": _format_money(inv.get("total_tax")),
                "invoice_type": inv.get("invoice_type"),
                "state": inv.get("state"),
                "number": inv.get("number"),
            })

    return invoices


def get_invoice_download_url(invoice_id: str) -> dict:
    """Recupere le lien de telechargement d'une facture."""
    data = _scw_get(f"/billing/v2beta1/invoices/{invoice_id}/download")
    return data


# ════════════════════════════════════════════════════════════════
# DOMAINS / DNS
# ════════════════════════════════════════════════════════════════

def get_dns_zones() -> list[dict]:
    """Recupere toutes les zones DNS du compte."""
    data = _scw_get("/domain/v2beta1/dns-zones", params={"page_size": 100})

    zones = []
    if isinstance(data, dict) and "dns_zones" in data:
        zones = data["dns_zones"]

    # Trier par domaine
    zones.sort(key=lambda z: z.get("domain", "").lower())
    return zones


def get_dns_zone_records(dns_zone: str, record_type: str | None = None) -> list[dict]:
    """
    Recupere les enregistrements DNS d'une zone.

    Args:
        dns_zone: Nom de la zone DNS (ex: example.com)
        record_type: Type d'enregistrement optionnel (A, AAAA, CNAME, MX, TXT, etc.)
    """
    params = {"page_size": 500}
    if record_type:
        params["type"] = record_type

    data = _scw_get(f"/domain/v2beta1/dns-zones/{dns_zone}/records", params=params)

    records = []
    if isinstance(data, dict) and "records" in data:
        records = data["records"]

    return records


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════

def get_dashboard() -> dict:
    """
    Genere un tableau de bord synthetique des services Scaleway.

    Retourne:
    - total_instances: nombre d'instances
    - instances_by_state: repartition par etat (running, stopped, etc.)
    - instances_by_zone: repartition par zone
    - dns_zones_count: nombre de zones DNS
    - consumption: consommation du mois courant
    """
    result = {
        "total_instances": 0,
        "instances_by_state": {},
        "instances_by_zone": {},
        "running_count": 0,
        "stopped_count": 0,
        "dns_zones_count": 0,
        "consumption": None,
    }

    # Instances
    try:
        instances = get_all_instances()
        result["total_instances"] = len(instances)
        for inst in instances:
            state = inst.get("state", "unknown")
            zone = inst.get("zone", "unknown")
            result["instances_by_state"][state] = result["instances_by_state"].get(state, 0) + 1
            result["instances_by_zone"][zone] = result["instances_by_zone"].get(zone, 0) + 1
        result["running_count"] = result["instances_by_state"].get("running", 0)
        result["stopped_count"] = result["instances_by_state"].get("stopped", 0) + result["instances_by_state"].get("stopped in place", 0)
    except HTTPException:
        logger.warning("Impossible de recuperer les instances Scaleway")

    # DNS Zones
    try:
        zones = get_dns_zones()
        result["dns_zones_count"] = len(zones)
    except HTTPException:
        logger.warning("Impossible de recuperer les zones DNS Scaleway")

    # Consommation du mois courant
    try:
        result["consumption"] = get_consumption()
    except HTTPException:
        logger.warning("Impossible de recuperer la consommation Scaleway")

    return result

"""
Client Dedibox API — Gestion des services Scaleway Dedibox (Online.net).

Utilise l'API REST Online.net (api.online.net/api/v1) avec authentification
par token prive (Bearer token).
Supporte : Serveurs dedies, Hebergements, Domaines, Informations utilisateur.
"""

import logging
from typing import Optional, Union

import httpx
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Base URL de l'API Online.net (Dedibox)
DEDIBOX_API_BASE = "https://api.online.net/api/v1"


def _get_headers() -> dict:
    """Retourne les headers d'authentification Dedibox (Bearer token)."""
    if not settings.SCW_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API Dedibox non configuree. Ajoutez SCW_SECRET_KEY (token prive Online.net) dans .env"
        )
    return {
        "Authorization": f"Bearer {settings.SCW_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def _dedibox_get(path: str, params: Optional[dict] = None) -> Union[dict, list]:
    """
    Effectue un appel GET a l'API Dedibox avec gestion d'erreurs.

    Args:
        path: Chemin API relatif (ex: /server, /user)
        params: Parametres de requete optionnels

    Returns:
        Reponse JSON (dict ou list)
    """
    url = f"{DEDIBOX_API_BASE}{path}"
    headers = _get_headers()

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()

        # Log detaille pour tout code != 200
        error_body = response.text[:500] if response.text else "(corps vide)"
        print(f"[DEDIBOX ERROR] {response.status_code} {path}: {error_body}")
        logger.error(
            f"Dedibox API {response.status_code} {path}: {error_body}"
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Token API Dedibox invalide. Verifiez SCW_SECRET_KEY dans .env."
            )
        elif response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Acces non autorise pour cette ressource Dedibox: {path}"
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ressource Dedibox introuvable: {path}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erreur API Dedibox ({response.status_code}): {error_body[:200]}"
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de l'appel Dedibox: {path}"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau Dedibox ({path}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau lors de l'appel Dedibox: {str(e)}"
        )


# ════════════════════════════════════════════════════════════════
# UTILISATEUR / COMPTE
# ════════════════════════════════════════════════════════════════

def get_user_info() -> dict:
    """Recupere les informations du compte utilisateur Dedibox."""
    data = _dedibox_get("/user")
    return data if isinstance(data, dict) else {}


# ════════════════════════════════════════════════════════════════
# SERVEURS DEDIES
# ════════════════════════════════════════════════════════════════

def get_servers() -> list[dict]:
    """
    Recupere la liste de tous les serveurs dedies.
    L'API retourne un tableau d'objets serveur.
    """
    data = _dedibox_get("/server")
    if isinstance(data, list):
        return data
    return []


def get_server_detail(server_id: int) -> dict:
    """Recupere le detail d'un serveur dedie specifique."""
    data = _dedibox_get(f"/server/{server_id}")
    return data if isinstance(data, dict) else {}


def get_server_status(server_id: int) -> dict:
    """Recupere le statut hardware d'un serveur (disques, reseau, etc.)."""
    try:
        data = _dedibox_get(f"/server/{server_id}/status")
        return data if isinstance(data, dict) else {}
    except HTTPException:
        return {}


# ════════════════════════════════════════════════════════════════
# HEBERGEMENTS
# ════════════════════════════════════════════════════════════════

def get_hostings() -> list[dict]:
    """Recupere la liste de tous les hebergements web."""
    data = _dedibox_get("/hosting")
    if isinstance(data, list):
        return data
    return []


def get_hosting_detail(hosting_id: int) -> dict:
    """Recupere le detail d'un hebergement specifique."""
    data = _dedibox_get(f"/hosting/{hosting_id}")
    return data if isinstance(data, dict) else {}


# ════════════════════════════════════════════════════════════════
# DOMAINES
# ════════════════════════════════════════════════════════════════

def get_domains() -> list[dict]:
    """Recupere la liste de tous les domaines geres."""
    data = _dedibox_get("/domain")
    if isinstance(data, list):
        return data
    return []


def get_domain_detail(domain_id: int) -> dict:
    """Recupere le detail d'un domaine specifique."""
    data = _dedibox_get(f"/domain/{domain_id}")
    return data if isinstance(data, dict) else {}


# ════════════════════════════════════════════════════════════════
# RESEAU / FAILOVER
# ════════════════════════════════════════════════════════════════

def get_failover_ips() -> list[dict]:
    """Recupere les adresses IP failover."""
    data = _dedibox_get("/server/failover")
    if isinstance(data, list):
        return data
    return []


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════

def get_dashboard() -> dict:
    """
    Genere un tableau de bord synthetique des services Dedibox.

    Retourne:
    - total_servers: nombre de serveurs dedies
    - servers_by_status: repartition par statut (active, etc.)
    - total_hostings: nombre d'hebergements
    - total_domains: nombre de domaines
    - failover_ips_count: nombre d'IPs failover
    - user: infos utilisateur
    """
    result = {
        "total_servers": 0,
        "servers_by_status": {},
        "active_count": 0,
        "total_hostings": 0,
        "total_domains": 0,
        "failover_ips_count": 0,
        "user": None,
    }

    # Serveurs
    try:
        servers = get_servers()
        result["total_servers"] = len(servers)
        for srv in servers:
            # Le champ "abuse" ou "status" indique l'etat
            srv_status = "active"
            if isinstance(srv, dict):
                abuse = srv.get("abuse")
                if abuse:
                    srv_status = "abuse"
            result["servers_by_status"][srv_status] = result["servers_by_status"].get(srv_status, 0) + 1
        result["active_count"] = result["servers_by_status"].get("active", 0)
    except HTTPException:
        logger.warning("Impossible de recuperer les serveurs Dedibox")

    # Hebergements
    try:
        hostings = get_hostings()
        result["total_hostings"] = len(hostings)
    except HTTPException:
        logger.warning("Impossible de recuperer les hebergements Dedibox")

    # Domaines
    try:
        domains = get_domains()
        result["total_domains"] = len(domains)
    except HTTPException:
        logger.warning("Impossible de recuperer les domaines Dedibox")

    # IPs failover
    try:
        ips = get_failover_ips()
        result["failover_ips_count"] = len(ips)
    except HTTPException:
        logger.warning("Impossible de recuperer les IPs failover")

    # User info
    try:
        result["user"] = get_user_info()
    except HTTPException:
        logger.warning("Impossible de recuperer les infos utilisateur Dedibox")

    return result

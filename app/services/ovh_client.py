import logging
from datetime import datetime, timedelta
from typing import Optional

import ovh
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Mapping type URL -> endpoint OVH
SERVICE_TYPE_MAP = {
    "dedicated": "/dedicated/server",
    "vps": "/vps",
    "domain": "/domain",
    "hosting": "/hosting/web",
    "cloud": "/cloud/project",
    "ip": "/ip",
    "alldom": "/allDom",
    "email_pro": "/email/pro",
    "email_exchange": "/email/exchange",
    "email_mxplan": "/email/mxplan",
    "email_domain": "/email/domain",
}


def get_ovh_client() -> ovh.Client:
    """Retourne une instance du client OVH. Leve une exception si non configure."""
    if not settings.OVH_APPLICATION_KEY or not settings.OVH_APPLICATION_SECRET or not settings.OVH_CONSUMER_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OVH API n'est pas configuree. Veuillez renseigner les variables OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET et OVH_CONSUMER_KEY."
        )
    try:
        return ovh.Client(
            endpoint=settings.OVH_ENDPOINT,
            application_key=settings.OVH_APPLICATION_KEY,
            application_secret=settings.OVH_APPLICATION_SECRET,
            consumer_key=settings.OVH_CONSUMER_KEY,
        )
    except Exception as e:
        logger.error(f"Erreur lors de la creation du client OVH: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Impossible de se connecter a l'API OVH: {str(e)}"
        )


def _ovh_call(client: ovh.Client, method: str, path: str):
    """Wrapper pour les appels OVH avec gestion d'erreurs."""
    try:
        if method == "GET":
            return client.get(path)
        raise ValueError(f"Methode non supportee: {method}")
    except ovh.exceptions.NotCredential:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Credentials OVH invalides ou permissions insuffisantes."
        )
    except ovh.exceptions.NotGrantedCall:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Acces non autorise pour cette ressource OVH. Verifiez les droits du consumer_key."
        )
    except ovh.exceptions.ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ressource OVH introuvable: {path}"
        )
    except ovh.exceptions.BadParametersError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parametres invalides pour l'appel OVH: {str(e)}"
        )
    except ovh.exceptions.APIError as e:
        logger.error(f"Erreur API OVH ({path}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur API OVH: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erreur inattendue OVH ({path}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur inattendue lors de l'appel OVH: {str(e)}"
        )


def get_account_info() -> dict:
    """Recupere les informations du compte OVH (/me)."""
    client = get_ovh_client()
    return _ovh_call(client, "GET", "/me")


def get_all_services() -> list[dict]:
    """Recupere tous les services avec leurs infos (expiration, statut, displayName) en iterant par type.
    Pour les services Email Pro, ajoute aussi chaque compte email comme un sous-service."""
    client = get_ovh_client()
    services = []

    for svc_type, endpoint in SERVICE_TYPE_MAP.items():
        try:
            names = _ovh_call(client, "GET", endpoint)
            if not isinstance(names, list):
                continue
            for name in names:
                try:
                    # Recuperer les infos de service (expiration, renouvellement, etc.)
                    info = _ovh_call(client, "GET", f"{endpoint}/{name}/serviceInfos")
                    info["serviceType"] = svc_type
                    info["serviceName"] = str(name)

                    # Recuperer le displayName depuis le detail du service
                    try:
                        detail = _ovh_call(client, "GET", f"{endpoint}/{name}")
                        if isinstance(detail, dict) and detail.get("displayName"):
                            info["displayName"] = detail["displayName"]
                    except HTTPException:
                        pass  # displayName est optionnel, on continue sans

                    services.append(info)

                    # Pour Email Pro, ajouter chaque compte email comme sous-service
                    if svc_type == "email_pro":
                        try:
                            account_emails = _ovh_call(client, "GET", f"{endpoint}/{name}/account")
                            if isinstance(account_emails, list):
                                for email_addr in account_emails:
                                    try:
                                        acct = _ovh_call(client, "GET", f"{endpoint}/{name}/account/{email_addr}")
                                        # Mapper les champs du compte vers le format service standard
                                        services.append({
                                            "serviceType": "email_pro_account",
                                            "serviceName": email_addr,
                                            "displayName": acct.get("displayName") or email_addr,
                                            "status": "ok" if acct.get("state") == "ok" else acct.get("state", "unknown"),
                                            "expiration": acct.get("expirationDate"),
                                            "creation": acct.get("creationDate"),
                                            "domain": acct.get("domain"),
                                            "renewPeriod": acct.get("renewPeriod"),
                                            "deleteAtExpiration": acct.get("deleteAtExpiration", False),
                                            "currentUsage": acct.get("currentUsage"),
                                            "quota": acct.get("quota"),
                                            "parentService": str(name),
                                        })
                                    except HTTPException:
                                        logger.warning(f"Impossible de recuperer le compte email: {email_addr}")
                        except HTTPException:
                            logger.warning(f"Impossible de lister les comptes Email Pro de {name}")

                except HTTPException:
                    # Si un service specifique echoue, on ajoute un placeholder
                    logger.warning(f"Impossible de recuperer les infos du service {svc_type}/{name}")
                    services.append({
                        "serviceType": svc_type,
                        "serviceName": str(name),
                        "status": "unknown",
                    })
        except HTTPException as e:
            logger.warning(f"Impossible de lister les services de type {svc_type}: {e.detail}")
            continue

    return services


def get_services_by_type(service_type: str) -> list:
    """Recupere la liste des services d'un type donne."""
    if service_type not in SERVICE_TYPE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de service inconnu: '{service_type}'. Types valides: {', '.join(SERVICE_TYPE_MAP.keys())}"
        )
    client = get_ovh_client()
    endpoint = SERVICE_TYPE_MAP[service_type]
    return _ovh_call(client, "GET", endpoint)


def get_service_detail(service_type: str, service_name: str) -> dict:
    """Recupere le detail d'un service specifique."""
    if service_type not in SERVICE_TYPE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de service inconnu: '{service_type}'. Types valides: {', '.join(SERVICE_TYPE_MAP.keys())}"
        )
    client = get_ovh_client()
    endpoint = SERVICE_TYPE_MAP[service_type]
    return _ovh_call(client, "GET", f"{endpoint}/{service_name}")


def get_service_info(service_type: str, service_name: str) -> dict:
    """Recupere les infos de service (expiration, renouvellement, contacts)."""
    if service_type not in SERVICE_TYPE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de service inconnu: '{service_type}'. Types valides: {', '.join(SERVICE_TYPE_MAP.keys())}"
        )
    client = get_ovh_client()
    endpoint = SERVICE_TYPE_MAP[service_type]
    return _ovh_call(client, "GET", f"{endpoint}/{service_name}/serviceInfos")


def get_email_pro_accounts(service_name: str) -> list[dict]:
    """Recupere les comptes Email Pro d'un service avec details (expiration, renouvellement)."""
    client = get_ovh_client()
    endpoint = SERVICE_TYPE_MAP.get("email_pro")
    if not endpoint:
        raise HTTPException(status_code=500, detail="Type email_pro non configure")

    account_emails = _ovh_call(client, "GET", f"{endpoint}/{service_name}/account")
    if not isinstance(account_emails, list):
        return []

    accounts = []
    for email in account_emails:
        try:
            detail = _ovh_call(client, "GET", f"{endpoint}/{service_name}/account/{email}")
            detail["email"] = email
            accounts.append(detail)
        except HTTPException:
            logger.warning(f"Impossible de recuperer le detail du compte email: {email}")
            accounts.append({"email": email, "state": "unknown"})

    # Trier par date d'expiration
    accounts.sort(key=lambda a: a.get("expirationDate", "") or "", reverse=False)
    return accounts


def get_bills(count: int = 20) -> list[dict]:
    """Recupere les dernieres factures OVH, triees par date decroissante."""
    client = get_ovh_client()
    bill_ids = _ovh_call(client, "GET", "/me/bill")
    # Trier les IDs par ordre decroissant pour prioriser les plus recents
    bill_ids = sorted(bill_ids, reverse=True)
    # Limiter le nombre de factures recuperees
    bill_ids = bill_ids[:count] if len(bill_ids) > count else bill_ids
    bills = []
    for bill_id in bill_ids:
        try:
            detail = _ovh_call(client, "GET", f"/me/bill/{bill_id}")
            bills.append(detail)
        except HTTPException:
            logger.warning(f"Impossible de recuperer la facture {bill_id}")
            continue
    # Tri final par date decroissante (plus recente en premier)
    bills.sort(key=lambda b: b.get("date", ""), reverse=True)
    return bills


def get_bill_detail(bill_id: str) -> dict:
    """Recupere le detail d'une facture specifique."""
    client = get_ovh_client()
    return _ovh_call(client, "GET", f"/me/bill/{bill_id}")


def get_services_dashboard(days_threshold: int = 30) -> dict:
    """
    Construit un tableau de bord synthetique des services OVH.

    Retourne:
    - total_services: nombre total
    - services_by_type: compte par type de service
    - expiring_soon: services expirant dans les N prochains jours
    - expired: services deja expires
    - active: nombre de services actifs
    """
    client = get_ovh_client()
    all_services = get_all_services()

    now = datetime.utcnow()
    threshold = now + timedelta(days=days_threshold)

    dashboard = {
        "total_services": len(all_services),
        "services_by_type": {},
        "expiring_soon": [],
        "expired": [],
        "active_count": 0,
        "suspended_count": 0,
    }

    for svc in all_services:
        # Compter par type (utilise serviceType injecte par get_all_services)
        svc_type = svc.get("serviceType", "unknown")
        dashboard["services_by_type"][svc_type] = dashboard["services_by_type"].get(svc_type, 0) + 1

        # Analyser le statut
        svc_status = svc.get("status", "unknown")
        svc_name = svc.get("serviceName", svc.get("domain", "N/A"))
        if svc_status == "ok":
            dashboard["active_count"] += 1
        elif svc_status in ("expired", "unPaid"):
            dashboard["expired"].append({
                "serviceId": svc.get("serviceId"),
                "resource": svc_name,
                "serviceType": svc_type,
                "status": svc_status,
                "expiration": svc.get("expiration"),
            })
        elif svc_status == "suspended":
            dashboard["suspended_count"] += 1

        # Verifier les expirations proches
        # Les comptes email_pro_account utilisent "expiration" (deja mappe dans get_all_services)
        expiration_str = svc.get("expiration")
        if expiration_str:
            try:
                exp_date = datetime.fromisoformat(expiration_str.replace("Z", "+00:00")).replace(tzinfo=None)
                if now < exp_date <= threshold:
                    dashboard["expiring_soon"].append({
                        "serviceId": svc.get("serviceId"),
                        "resource": svc_name,
                        "serviceType": svc_type,
                        "status": svc_status,
                        "expiration": expiration_str,
                        "days_remaining": (exp_date - now).days,
                    })
            except (ValueError, TypeError):
                pass

    # Trier expiring_soon par date
    dashboard["expiring_soon"].sort(key=lambda x: x.get("days_remaining", 999))

    return dashboard

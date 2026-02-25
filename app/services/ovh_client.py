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

                    # Pour Email Domain, ne garder que ceux qui ont des comptes email
                    if svc_type == "email_domain":
                        try:
                            email_accounts = _ovh_call(client, "GET", f"{endpoint}/{name}/account")
                            if not isinstance(email_accounts, list) or len(email_accounts) == 0:
                                logger.info(f"Email Domain {name} ignore: aucun compte email configure")
                                continue  # Passer au service suivant, ne pas ajouter
                        except HTTPException:
                            logger.info(f"Email Domain {name} ignore: impossible de verifier les comptes")
                            continue

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


def get_account_balance() -> dict:
    """
    Recupere le solde, les dettes et les methodes de paiement du compte OVH.

    Retourne:
    - balance: solde /me/balance (ou null si indisponible)
    - debtAccount: compte de dettes /me/debtAccount (ou null)
    - paymentMethods: liste des methodes de paiement actives
    """
    client = get_ovh_client()
    result = {
        "balance": None,
        "debtAccount": None,
        "paymentMethods": [],
    }

    # Solde du compte
    try:
        result["balance"] = _ovh_call(client, "GET", "/me/balance")
    except HTTPException:
        logger.info("Endpoint /me/balance non disponible")

    # Dettes
    try:
        result["debtAccount"] = _ovh_call(client, "GET", "/me/debtAccount")
    except HTTPException:
        logger.info("Endpoint /me/debtAccount non disponible")

    # Methodes de paiement
    try:
        method_ids = _ovh_call(client, "GET", "/me/payment/method")
        if isinstance(method_ids, list):
            for mid in method_ids[:10]:  # Limiter a 10
                try:
                    detail = _ovh_call(client, "GET", f"/me/payment/method/{mid}")
                    result["paymentMethods"].append(detail)
                except HTTPException:
                    pass
    except HTTPException:
        logger.info("Endpoint /me/payment/method non disponible")

    return result


def get_vps_monitoring(vps_name: str, period: str = "lastday") -> dict:
    """
    Recupere les statistiques de monitoring d'un VPS.

    Args:
        vps_name: Nom du VPS (ex: vps-xxx.vps.ovh.net)
        period: Periode (lastday, lastweek, lastmonth, lastyear)

    Retourne:
    - cpu, mem, net: donnees de monitoring avec timestamps et valeurs
    - ips: liste des IPs du VPS
    - model: infos du modele VPS
    """
    client = get_ovh_client()
    result = {
        "vpsName": vps_name,
        "period": period,
        "cpu": None,
        "mem": None,
        "netRx": None,
        "netTx": None,
        "ips": [],
        "model": None,
    }

    # CPU
    try:
        result["cpu"] = _ovh_call(client, "GET", f"/vps/{vps_name}/monitoring?period={period}&type=cpu:used")
    except HTTPException:
        logger.warning(f"Monitoring CPU non disponible pour {vps_name}")

    # Memoire
    try:
        result["mem"] = _ovh_call(client, "GET", f"/vps/{vps_name}/monitoring?period={period}&type=mem:used")
    except HTTPException:
        logger.warning(f"Monitoring memoire non disponible pour {vps_name}")

    # Reseau entrant
    try:
        result["netRx"] = _ovh_call(client, "GET", f"/vps/{vps_name}/monitoring?period={period}&type=net:rx")
    except HTTPException:
        logger.warning(f"Monitoring reseau RX non disponible pour {vps_name}")

    # Reseau sortant
    try:
        result["netTx"] = _ovh_call(client, "GET", f"/vps/{vps_name}/monitoring?period={period}&type=net:tx")
    except HTTPException:
        logger.warning(f"Monitoring reseau TX non disponible pour {vps_name}")

    # IPs
    try:
        result["ips"] = _ovh_call(client, "GET", f"/vps/{vps_name}/ips")
    except HTTPException:
        pass

    # Modele
    try:
        vps_detail = _ovh_call(client, "GET", f"/vps/{vps_name}")
        if isinstance(vps_detail, dict):
            result["model"] = vps_detail.get("model")
    except HTTPException:
        pass

    return result


def get_active_tasks() -> list[dict]:
    """
    Recupere les taches actives sur tous les services VPS et serveurs dedies.

    Retourne une liste de taches avec type, statut, date, progression.
    """
    client = get_ovh_client()
    tasks = []

    # Taches VPS
    try:
        vps_names = _ovh_call(client, "GET", "/vps")
        if isinstance(vps_names, list):
            for vps_name in vps_names:
                try:
                    task_ids = _ovh_call(client, "GET", f"/vps/{vps_name}/tasks")
                    if isinstance(task_ids, list):
                        for task_id in task_ids[:20]:  # Limiter par VPS
                            try:
                                task = _ovh_call(client, "GET", f"/vps/{vps_name}/tasks/{task_id}")
                                task["resourceName"] = vps_name
                                task["resourceType"] = "vps"
                                tasks.append(task)
                            except HTTPException:
                                pass
                except HTTPException:
                    pass
    except HTTPException:
        logger.warning("Impossible de lister les VPS pour les taches")

    # Taches serveurs dedies
    try:
        server_names = _ovh_call(client, "GET", "/dedicated/server")
        if isinstance(server_names, list):
            for server_name in server_names:
                try:
                    task_ids = _ovh_call(client, "GET", f"/dedicated/server/{server_name}/task")
                    if isinstance(task_ids, list):
                        for task_id in task_ids[:20]:
                            try:
                                task = _ovh_call(client, "GET", f"/dedicated/server/{server_name}/task/{task_id}")
                                task["resourceName"] = server_name
                                task["resourceType"] = "dedicated"
                                tasks.append(task)
                            except HTTPException:
                                pass
                except HTTPException:
                    pass
    except HTTPException:
        logger.warning("Impossible de lister les serveurs pour les taches")

    # Trier par date decroissante (taches recentes en premier)
    tasks.sort(key=lambda t: t.get("startDate", t.get("todoDate", "")), reverse=True)

    return tasks


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

    # Ajouter le solde / dettes
    try:
        balance_info = get_account_balance()
        dashboard["balance"] = balance_info
    except Exception:
        dashboard["balance"] = None

    # Ajouter les taches actives (filtrer uniquement celles en cours)
    try:
        all_tasks = get_active_tasks()
        # Garder uniquement les taches non terminees (doing, todo, init, waitingAck)
        active_tasks = [t for t in all_tasks if t.get("state", t.get("status", "")) in ("doing", "todo", "init", "waitingAck", "paused")]
        dashboard["active_tasks"] = active_tasks
        dashboard["active_tasks_count"] = len(active_tasks)
        # Garder aussi les taches recentes (7 derniers jours) terminées pour historique
        recent_done = [t for t in all_tasks if t.get("state", t.get("status", "")) in ("done", "cancelled", "error")][:10]
        dashboard["recent_tasks"] = recent_done
    except Exception:
        dashboard["active_tasks"] = []
        dashboard["active_tasks_count"] = 0
        dashboard["recent_tasks"] = []

    return dashboard

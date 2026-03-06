"""
Service de nettoyage des fichiers temporaires Firebase Storage.

Utilise l'API REST Firebase Storage avec un Service Account
pour supprimer les fichiers uploades temporairement par le frontend.

Prerequis :
- Variable FIREBASE_SERVICE_ACCOUNT dans config.py / .env
- Accepte soit le contenu JSON direct, soit un chemin vers le fichier JSON

Si le service account n'est pas configure, le cleanup est silencieusement ignore.
"""

import base64
import json
import logging
import urllib.parse
import os
from typing import Optional

logger = logging.getLogger("hapson-api")

# Bucket Firebase Storage
FIREBASE_BUCKET = "media-manager-23e89.firebasestorage.app"
FIREBASE_STORAGE_API = "https://firebasestorage.googleapis.com/v0/b"

# Credentials (lazy-loaded)
_credentials = None
_credentials_loaded = False


def _get_credentials():
    """
    Charger les credentials du service account (lazy, une seule fois).

    Supporte trois formats pour FIREBASE_SERVICE_ACCOUNT :
    - Contenu JSON direct (commence par '{') — ideal pour les variables d'environnement serveur
    - Chemin vers un fichier JSON — pour le developpement local
    - JSON encode en base64 — si le JSON direct pose probleme avec Docker/Dokploy
    """
    global _credentials, _credentials_loaded

    if _credentials_loaded:
        return _credentials

    _credentials_loaded = True

    from app.config.config import settings
    sa_value = settings.FIREBASE_SERVICE_ACCOUNT

    if not sa_value:
        logger.info("Firebase cleanup: pas de service account configure, cleanup desactive")
        return None

    try:
        from google.oauth2 import service_account
        scopes = [
            "https://www.googleapis.com/auth/firebase.storage",
            "https://www.googleapis.com/auth/devstorage.read_only",
        ]

        # Detecter si c'est du JSON direct ou un chemin de fichier
        stripped = sa_value.strip()
        if stripped.startswith("{"):
            # JSON direct dans la variable d'environnement
            sa_info = json.loads(stripped)
            _credentials = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
            logger.info("Firebase cleanup: service account charge depuis variable d'environnement (JSON)")
        elif os.path.exists(stripped):
            # Chemin vers un fichier JSON
            _credentials = service_account.Credentials.from_service_account_file(stripped, scopes=scopes)
            logger.info(f"Firebase cleanup: service account charge depuis fichier {stripped}")
        else:
            # Tenter le decodage base64
            try:
                decoded = base64.b64decode(stripped).decode("utf-8")
                sa_info = json.loads(decoded)
                _credentials = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
                logger.info("Firebase cleanup: service account charge depuis base64")
            except Exception:
                logger.warning("Firebase cleanup: valeur non reconnue (ni JSON, ni fichier, ni base64)")
                return None

        return _credentials
    except json.JSONDecodeError as e:
        logger.error(f"Firebase cleanup: JSON invalide dans FIREBASE_SERVICE_ACCOUNT: {e}")
        return None
    except Exception as e:
        logger.error(f"Firebase cleanup: erreur chargement service account: {e}")
        return None


def _get_auth_token() -> Optional[str]:
    """Obtenir un token d'acces valide pour l'API Firebase Storage."""
    creds = _get_credentials()
    if not creds:
        return None

    from google.auth.transport.requests import Request
    if creds.expired or not creds.token:
        creds.refresh(Request())

    return creds.token


def _extract_storage_path(url: str) -> Optional[str]:
    """
    Extraire le chemin du fichier depuis une URL Firebase Storage.

    URL format: https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_path}?alt=media&token=...
    Retourne le path decode (ex: "social/media/1709123456_abc123.jpg")
    """
    if "firebasestorage.googleapis.com" not in url:
        return None

    try:
        parts = url.split("/o/")
        if len(parts) < 2:
            return None
        encoded_path = parts[1].split("?")[0]
        return urllib.parse.unquote(encoded_path)
    except Exception:
        return None


def delete_firebase_file(file_path: str) -> bool:
    """
    Supprimer un fichier de Firebase Storage via l'API REST.

    Args:
        file_path: Chemin du fichier dans le bucket (ex: "social/media/xxx.jpg")

    Returns:
        True si supprime, False sinon
    """
    token = _get_auth_token()
    if not token:
        return False

    import httpx

    encoded_path = urllib.parse.quote(file_path, safe="")
    url = f"{FIREBASE_STORAGE_API}/{FIREBASE_BUCKET}/o/{encoded_path}"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.delete(url, headers={"Authorization": f"Bearer {token}"})

        if response.status_code in (200, 204):
            logger.info(f"Firebase: fichier supprime: {file_path}")
            return True
        elif response.status_code == 404:
            logger.info(f"Firebase: fichier deja absent: {file_path}")
            return True
        else:
            logger.warning(f"Firebase: suppression echouee ({response.status_code}): {file_path}")
            return False
    except Exception as e:
        logger.error(f"Firebase: erreur suppression {file_path}: {e}")
        return False


def cleanup_firebase_urls(urls: list[str]) -> int:
    """
    Supprimer les fichiers Firebase Storage correspondant aux URLs.

    Args:
        urls: Liste d'URLs Firebase Storage

    Returns:
        Nombre de fichiers supprimes
    """
    if not _get_credentials():
        return 0

    count = 0
    for url in urls:
        path = _extract_storage_path(url)
        if path:
            if delete_firebase_file(path):
                count += 1

    return count


def list_firebase_files(prefix: str = "social/") -> list[dict]:
    """
    Lister tous les fichiers dans Firebase Storage sous un prefix.

    Utilise l'API REST Firebase Storage avec pagination automatique.

    Args:
        prefix: Prefix du chemin a scanner (ex: "social/", "social/media/")

    Returns:
        Liste de dicts avec 'name' (chemin) et 'size' (octets).
        Liste vide si pas configure ou en cas d'erreur.
    """
    token = _get_auth_token()
    if not token:
        logger.warning("list_firebase_files: pas de token, impossible de lister")
        return []

    import httpx

    all_files = []
    page_token = None

    try:
        with httpx.Client(timeout=30.0) as client:
            while True:
                params: dict = {
                    "prefix": prefix,
                    "maxResults": 1000,
                }
                if page_token:
                    params["pageToken"] = page_token

                url = f"{FIREBASE_STORAGE_API}/{FIREBASE_BUCKET}/o"
                response = client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code != 200:
                    logger.error(
                        f"list_firebase_files: HTTP {response.status_code} — {response.text[:200]}"
                    )
                    break

                data = response.json()
                for item in data.get("items", []):
                    all_files.append({
                        "name": item["name"],
                        "size": int(item.get("size", 0)),
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        logger.info(f"list_firebase_files: {len(all_files)} fichier(s) sous '{prefix}'")
        return all_files

    except Exception as e:
        logger.error(f"list_firebase_files: erreur: {e}")
        return []


def cleanup_orphan_files(
    db_media_urls: list[str],
    prefix: str = "social/",
    dry_run: bool = True,
) -> dict:
    """
    Comparer les fichiers Firebase Storage avec les URLs referencees en DB.
    Identifier et optionnellement supprimer les fichiers orphelins.

    Args:
        db_media_urls: Toutes les URLs Firebase Storage referencees en DB
        prefix: Prefix du chemin a scanner dans le bucket
        dry_run: Si True, ne supprime rien (apercu uniquement)

    Returns:
        Dict avec les statistiques du nettoyage
    """
    # Extraire les paths depuis les URLs DB
    db_paths: set[str] = set()
    for url in db_media_urls:
        path = _extract_storage_path(url)
        if path:
            db_paths.add(path)

    logger.info(f"cleanup_orphan_files: {len(db_paths)} chemin(s) reference(s) en DB")

    # Lister les fichiers dans le bucket
    storage_files = list_firebase_files(prefix)

    if not storage_files:
        return {
            "total_storage_files": 0,
            "total_storage_size": 0,
            "referenced_count": 0,
            "orphan_count": 0,
            "orphan_size": 0,
            "deleted_count": 0,
            "delete_errors": 0,
            "dry_run": dry_run,
            "orphan_files": [],
        }

    # Identifier les orphelins
    storage_paths = {f["name"] for f in storage_files}
    referenced = storage_paths & db_paths
    orphan_files: list[str] = []
    orphan_size = 0

    for f in storage_files:
        if f["name"] not in db_paths:
            orphan_files.append(f["name"])
            orphan_size += f["size"]

    total_size = sum(f["size"] for f in storage_files)

    logger.info(
        f"cleanup_orphan_files: {len(orphan_files)} orphelin(s) sur "
        f"{len(storage_files)} fichier(s) (dry_run={dry_run})"
    )

    # Supprimer si pas en dry_run
    deleted_count = 0
    delete_errors = 0
    if not dry_run:
        for file_path in orphan_files:
            if delete_firebase_file(file_path):
                deleted_count += 1
            else:
                delete_errors += 1

    return {
        "total_storage_files": len(storage_files),
        "total_storage_size": total_size,
        "referenced_count": len(referenced),
        "orphan_count": len(orphan_files),
        "orphan_size": orphan_size,
        "deleted_count": deleted_count,
        "delete_errors": delete_errors,
        "dry_run": dry_run,
        "orphan_files": orphan_files,
    }

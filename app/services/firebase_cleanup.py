"""
Service de nettoyage des fichiers temporaires Firebase Storage.

Utilise l'API REST Firebase Storage avec un Service Account
pour supprimer les fichiers uploades temporairement par le frontend.

Prerequis :
- Variable FIREBASE_SERVICE_ACCOUNT dans config.py / .env
- Accepte soit le contenu JSON direct, soit un chemin vers le fichier JSON

Si le service account n'est pas configure, le cleanup est silencieusement ignore.
"""

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

    Supporte deux formats pour FIREBASE_SERVICE_ACCOUNT :
    - Contenu JSON direct (commence par '{') — ideal pour les variables d'environnement serveur
    - Chemin vers un fichier JSON — pour le developpement local
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
        scopes = ["https://www.googleapis.com/auth/firebase.storage"]

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
            logger.warning(f"Firebase cleanup: valeur non reconnue (ni JSON ni fichier existant)")
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

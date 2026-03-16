"""
Client Google Drive pour la gestion des sauvegardes.

Utilise l'API REST Google Drive v3 via httpx (meme pattern que scaleway_client.py).
Les tokens OAuth sont chiffres via Fernet (meme cle que TOTP).

Flux OAuth :
1. build_google_auth_url() → URL de redirection Google
2. exchange_google_code() → access_token + refresh_token
3. _ensure_valid_token() → rafraichit le token si expire
4. upload_to_drive() / list_drive_files() / download_from_drive()
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.config.config import settings
from app.utils.crypto import encrypt_totp_secret, decrypt_totp_secret

logger = logging.getLogger("hapson-api")

# URLs Google OAuth2 et Drive API
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
GOOGLE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email"

# Timeout pour les operations Drive (les uploads peuvent etre longs)
TIMEOUT_DEFAULT = 30.0
TIMEOUT_UPLOAD = 300.0


# ════════════════════════════════════════════════════════════════
# STATE PARAMETER (protection CSRF — meme pattern que social_oauth.py)
# ════════════════════════════════════════════════════════════════

def _sign_state(payload: str) -> str:
    """Signe un payload avec HMAC-SHA256 en utilisant SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def build_google_auth_url(user_id: int) -> tuple[str, str]:
    """
    Genere l'URL OAuth Google pour connecter Google Drive.

    Returns:
        Tuple (auth_url, state)
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth non configure. Ajoutez GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans .env"
        )

    callback_url = f"{settings.BACKEND_URL}/backup/config/oauth/callback"

    # State signe (protection CSRF)
    nonce = secrets.token_urlsafe(16)
    payload_dict = {"user_id": user_id, "purpose": "backup_gdrive", "nonce": nonce}
    payload_json = json.dumps(payload_dict, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    signature = _sign_state(payload_b64)
    state = f"{payload_b64}.{signature}"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "access_type": "offline",      # Pour obtenir un refresh_token
        "prompt": "consent",            # Forcer le consentement pour obtenir refresh_token
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return auth_url, state


def verify_google_state(state: str) -> dict:
    """
    Verifie et decode un parametre state signe.
    Retourne un dict avec user_id.
    """
    try:
        parts = state.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError("Format state invalide")

        payload_b64, received_signature = parts
        expected_signature = _sign_state(payload_b64)

        if not hmac.compare_digest(received_signature, expected_signature):
            raise ValueError("Signature state invalide")

        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_json)

        if payload.get("purpose") != "backup_gdrive":
            raise ValueError("Purpose invalide dans le state")

        return payload
    except Exception as e:
        logger.warning(f"Verification state Google OAuth echouee: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parametre state OAuth invalide ou expire"
        )


# ════════════════════════════════════════════════════════════════
# ECHANGE DE CODE ET REFRESH
# ════════════════════════════════════════════════════════════════

def exchange_google_code(code: str) -> dict:
    """
    Echange un code d'autorisation contre des tokens Google.

    Returns:
        Dict avec access_token, refresh_token, expires_in, email
    """
    callback_url = f"{settings.BACKEND_URL}/backup/config/oauth/callback"

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": callback_url,
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.post(GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            logger.error(f"Echange token Google echoue: {response.status_code} - {response.text[:500]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Echec de l'echange de token Google OAuth"
            )

        token_data = response.json()

        # Recuperer l'email de l'utilisateur
        email = None
        access_token = token_data.get("access_token")
        if access_token:
            try:
                with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
                    resp = client.get(
                        GOOGLE_USERINFO_URL,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                if resp.status_code == 200:
                    email = resp.json().get("email")
            except Exception as e:
                logger.warning(f"Impossible de recuperer l'email Google: {e}")

        return {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in", 3600),
            "email": email,
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout lors de l'echange de token Google"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau echange token Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur reseau lors de l'echange de token Google"
        )


def refresh_google_token(encrypted_refresh_token: str) -> dict:
    """
    Rafraichit un access_token Google a partir du refresh_token chiffre.

    Returns:
        Dict avec access_token, expires_in
    """
    refresh_token = decrypt_totp_secret(encrypted_refresh_token)

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.post(GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            logger.error(f"Refresh token Google echoue: {response.status_code} - {response.text[:300]}")
            return {"access_token": None, "expires_in": 0}

        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in", 3600),
        }

    except Exception as e:
        logger.error(f"Erreur refresh token Google: {e}")
        return {"access_token": None, "expires_in": 0}


def ensure_valid_token(db) -> str | None:
    """
    Verifie que le token Google est valide, le rafraichit si necessaire.
    Retourne un access_token valide ou None si impossible.
    """
    from app.db.crud.crud_backup import get_backup_config, upsert_backup_config

    config = get_backup_config(db)
    if not config or not config.is_connected or not config.google_refresh_token:
        return None

    # Verifier si le token est encore valide (marge de 5 min)
    now = datetime.now(timezone.utc)
    if config.google_token_expires_at and config.google_token_expires_at > now + timedelta(minutes=5):
        # Token encore valide, le dechiffrer et le retourner
        try:
            return decrypt_totp_secret(config.google_access_token)
        except Exception:
            pass

    # Token expire ou invalide, rafraichir
    result = refresh_google_token(config.google_refresh_token)
    if not result["access_token"]:
        return None

    # Sauvegarder le nouveau token
    new_expires_at = now + timedelta(seconds=result["expires_in"])
    upsert_backup_config(
        db,
        google_access_token=encrypt_totp_secret(result["access_token"]),
        google_token_expires_at=new_expires_at,
    )

    return result["access_token"]


# ════════════════════════════════════════════════════════════════
# OPERATIONS GOOGLE DRIVE
# ════════════════════════════════════════════════════════════════

def upload_to_drive(access_token: str, folder_id: str, filepath: str, filename: str) -> dict:
    """
    Upload un fichier vers Google Drive (multipart).

    Returns:
        Dict avec id (Drive file ID), name
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    metadata = {"name": filename, "parents": [folder_id]} if folder_id else {"name": filename}

    file_size = os.path.getsize(filepath)

    try:
        with open(filepath, "rb") as f:
            with httpx.Client(timeout=TIMEOUT_UPLOAD) as client:
                response = client.post(
                    f"{GOOGLE_UPLOAD_API}/files?uploadType=multipart",
                    headers=headers,
                    files={
                        "metadata": ("metadata", json.dumps(metadata), "application/json"),
                        "file": (filename, f, "application/gzip"),
                    },
                )

        if response.status_code not in (200, 201):
            logger.error(f"Upload Drive echoue: {response.status_code} - {response.text[:300]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Echec de l'upload vers Google Drive: {response.status_code}"
            )

        data = response.json()
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "size": file_size,
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout lors de l'upload vers Google Drive"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau upload Drive: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur reseau lors de l'upload vers Google Drive"
        )


def list_drive_files(access_token: str, folder_id: str) -> list[dict]:
    """
    Liste les fichiers dans un dossier Google Drive.

    Returns:
        Liste de dicts avec id, name, size, modifiedTime
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    query = f"'{folder_id}' in parents and trashed = false" if folder_id else "trashed = false"

    params = {
        "q": query,
        "fields": "files(id,name,size,modifiedTime)",
        "orderBy": "modifiedTime desc",
        "pageSize": 100,
    }

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.get(
                f"{GOOGLE_DRIVE_API}/files",
                headers=headers,
                params=params,
            )

        if response.status_code != 200:
            logger.error(f"Liste Drive echouee: {response.status_code} - {response.text[:300]}")
            return []

        return response.json().get("files", [])

    except Exception as e:
        logger.error(f"Erreur liste Drive: {e}")
        return []


def download_from_drive(access_token: str, file_id: str, dest_path: str) -> str:
    """
    Telecharge un fichier depuis Google Drive.

    Returns:
        Chemin local du fichier telecharge
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client(timeout=TIMEOUT_UPLOAD) as client:
            response = client.get(
                f"{GOOGLE_DRIVE_API}/files/{file_id}?alt=media",
                headers=headers,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Echec du telechargement depuis Google Drive: {response.status_code}"
            )

        with open(dest_path, "wb") as f:
            f.write(response.content)

        return dest_path

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout lors du telechargement depuis Google Drive"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau download Drive: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur reseau lors du telechargement depuis Google Drive"
        )


def create_drive_folder(access_token: str, folder_name: str, parent_id: str | None = None) -> dict:
    """
    Cree un dossier dans Google Drive.
    Fonctionne avec le scope drive.file car l'app cree le dossier.

    Returns:
        Dict avec id et name du dossier cree
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    metadata: dict = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.post(
                f"{GOOGLE_DRIVE_API}/files",
                headers=headers,
                json=metadata,
            )

        if response.status_code not in (200, 201):
            logger.error(f"Creation dossier Drive echouee: {response.status_code} - {response.text[:300]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Echec de la creation du dossier Google Drive"
            )

        data = response.json()
        return {"id": data.get("id"), "name": data.get("name")}

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout lors de la creation du dossier Google Drive"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau creation dossier Drive: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur reseau lors de la creation du dossier Google Drive"
        )


def list_drive_folders(access_token: str) -> list[dict]:
    """
    Liste les dossiers crees par cette application (scope drive.file).

    Returns:
        Liste de dicts avec id, name, createdTime
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": "mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        "fields": "files(id,name,createdTime)",
        "orderBy": "createdTime desc",
        "pageSize": 50,
    }

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.get(
                f"{GOOGLE_DRIVE_API}/files",
                headers=headers,
                params=params,
            )

        if response.status_code != 200:
            logger.error(f"Liste dossiers Drive echouee: {response.status_code} - {response.text[:300]}")
            return []

        return response.json().get("files", [])

    except Exception as e:
        logger.error(f"Erreur liste dossiers Drive: {e}")
        return []


def delete_drive_file(access_token: str, file_id: str) -> bool:
    """Supprime un fichier de Google Drive. Retourne True si succes."""
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client(timeout=TIMEOUT_DEFAULT) as client:
            response = client.delete(
                f"{GOOGLE_DRIVE_API}/files/{file_id}",
                headers=headers,
            )
        return response.status_code == 204

    except Exception as e:
        logger.error(f"Erreur suppression Drive: {e}")
        return False

"""
Service OAuth2 generique pour les plateformes sociales.

Gere le flux OAuth2 complet : generation d'URL d'autorisation,
echange de code contre token, recuperation du profil utilisateur.

Plateformes supportees : Facebook, Instagram, LinkedIn, Twitter/X.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")


# ════════════════════════════════════════════════════════════════
# PLATEFORMES SUPPORTEES
# ════════════════════════════════════════════════════════════════

SUPPORTED_PLATFORMS = {"facebook", "instagram", "linkedin", "twitter"}


def _get_platform_config(platform: str) -> dict:
    """
    Retourne la configuration OAuth2 pour une plateforme donnee.
    Leve HTTPException si la plateforme n'est pas supportee ou non configuree.
    """
    callback_url = f"{settings.BACKEND_URL}/social/accounts/callback"

    configs = {
        "facebook": {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "user_info_url": "https://graph.facebook.com/v18.0/me",
            "user_info_params": {"fields": "id,name,picture"},
            "scopes": "pages_manage_posts,pages_read_engagement,pages_read_user_content,pages_show_list,pages_manage_engagement,read_insights",
            "config_id": settings.FACEBOOK_CONFIG_ID,
            "redirect_uri": callback_url,
        },
        "instagram": {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "user_info_url": "https://graph.facebook.com/v18.0/me",
            "user_info_params": {"fields": "id,name,picture"},
            "scopes": "instagram_basic,instagram_content_publish,pages_show_list",
            "config_id": settings.FACEBOOK_CONFIG_ID,
            "redirect_uri": callback_url,
        },
        "linkedin": {
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
            "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
            "user_info_url": "https://api.linkedin.com/v2/userinfo",
            "user_info_params": {},
            "scopes": "openid profile w_member_social",
            "redirect_uri": callback_url,
        },
        "twitter": {
            "client_id": settings.TWITTER_CLIENT_ID,
            "client_secret": settings.TWITTER_CLIENT_SECRET,
            "auth_url": "https://twitter.com/i/oauth2/authorize",
            "token_url": "https://api.twitter.com/2/oauth2/token",
            "user_info_url": "https://api.twitter.com/2/users/me",
            "user_info_params": {"user.fields": "id,name,username,profile_image_url"},
            "scopes": "tweet.read tweet.write users.read offline.access",
            "redirect_uri": callback_url,
            "pkce": True,
        },
    }

    if platform not in configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plateforme '{platform}' non supportee. "
                   f"Plateformes valides : {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )

    config = configs[platform]

    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OAuth {platform} non configure. Ajoutez les credentials dans .env"
        )

    return config


# ════════════════════════════════════════════════════════════════
# STATE PARAMETER (protection CSRF)
# ════════════════════════════════════════════════════════════════

def _sign_state(payload: str) -> str:
    """Signe un payload avec HMAC-SHA256 en utilisant SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def generate_oauth_state(user_id: int, platform: str) -> str:
    """
    Genere un parametre state signe encodant user_id + platform + nonce.
    Format : base64url(json({user_id, platform, nonce})).signature_hmac
    """
    nonce = secrets.token_urlsafe(16)
    payload_dict = {
        "user_id": user_id,
        "platform": platform,
        "nonce": nonce,
    }
    payload_json = json.dumps(payload_dict, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    signature = _sign_state(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_oauth_state(state: str) -> dict:
    """
    Verifie et decode un parametre state signe.
    Retourne un dict avec user_id et platform.
    Leve HTTPException si invalide.
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

        if "user_id" not in payload or "platform" not in payload:
            raise ValueError("Champs manquants dans le state")

        return payload
    except Exception as e:
        logger.warning(f"Verification state OAuth echouee: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parametre state OAuth invalide ou expire"
        )


# ════════════════════════════════════════════════════════════════
# PKCE (pour Twitter/X)
# ════════════════════════════════════════════════════════════════

# Store en memoire pour les code_verifier PKCE (cle = state)
# En production multi-workers, utiliser Redis ou la BDD
_pkce_store: dict = {}


def _generate_pkce() -> tuple:
    """Genere un code_verifier et code_challenge PKCE (S256)."""
    code_verifier = secrets.token_urlsafe(43)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


# ════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES DU FLUX OAUTH2
# ════════════════════════════════════════════════════════════════

def build_authorization_url(platform: str, user_id: int) -> tuple:
    """
    Construit l'URL d'autorisation OAuth2 pour une plateforme donnee.

    Args:
        platform: 'facebook', 'instagram', 'linkedin', ou 'twitter'
        user_id: ID de l'utilisateur authentifie qui initie la connexion

    Returns:
        Tuple (authorization_url, state)
    """
    config = _get_platform_config(platform)
    state = generate_oauth_state(user_id, platform)

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "state": state,
        "response_type": "code",
    }

    # Facebook Login for Business : config_id + scope
    # Les permissions doivent etre configurees dans le config_id sur Meta Developer Portal
    # On envoie aussi le scope en complement pour forcer les permissions necessaires
    if config.get("config_id"):
        params["config_id"] = config["config_id"]
    # Toujours envoyer le scope (requis pour les permissions non incluses dans config_id)
    if config.get("scopes"):
        params["scope"] = config["scopes"]

    # PKCE pour Twitter
    if config.get("pkce"):
        code_verifier, code_challenge = _generate_pkce()
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
        _pkce_store[state] = code_verifier

    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    return auth_url, state


def exchange_code_for_token(platform: str, code: str, state: str) -> dict:
    """
    Echange un code d'autorisation contre des tokens d'acces.

    Args:
        platform: La plateforme sociale
        code: Le code d'autorisation du callback
        state: Le parametre state pour la recherche PKCE

    Returns:
        Dict avec access_token, refresh_token (optionnel), expires_in
    """
    config = _get_platform_config(platform)

    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "code": code,
        "redirect_uri": config["redirect_uri"],
        "grant_type": "authorization_code",
    }

    headers = {"Accept": "application/json"}

    # PKCE pour Twitter
    auth = None
    if config.get("pkce"):
        code_verifier = _pkce_store.pop(state, None)
        if not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PKCE code_verifier introuvable. Recommencez la connexion."
            )
        data["code_verifier"] = code_verifier
        # Twitter utilise Basic Auth pour l'echange de token
        auth = (config["client_id"], config["client_secret"])
        del data["client_id"]
        del data["client_secret"]

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                config["token_url"],
                data=data,
                headers=headers,
                auth=auth,
            )

        if response.status_code != 200:
            error_body = response.text[:500]
            logger.error(
                f"Echange token OAuth echoue pour {platform}: "
                f"{response.status_code} - {error_body}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Echec de l'echange de token OAuth ({platform})"
            )

        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de l'echange de token OAuth ({platform})"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau echange token OAuth ({platform}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau lors de l'echange de token OAuth ({platform})"
        )


def fetch_user_profile(platform: str, access_token: str) -> dict:
    """
    Recupere le profil utilisateur depuis l'API de la plateforme.

    Returns:
        Dict normalise : platform_user_id, name, picture_url
    """
    config = _get_platform_config(platform)

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                config["user_info_url"],
                params=config.get("user_info_params", {}),
                headers=headers,
            )

        if response.status_code != 200:
            logger.error(
                f"Recuperation profil OAuth echouee pour {platform}: "
                f"{response.status_code} - {response.text[:300]}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Impossible de recuperer le profil utilisateur ({platform})"
            )

        data = response.json()

        # Normalisation par plateforme
        if platform in ("facebook", "instagram"):
            return {
                "platform_user_id": data.get("id", ""),
                "name": data.get("name", "Unknown"),
                "picture_url": (
                    data.get("picture", {}).get("data", {}).get("url")
                    if isinstance(data.get("picture"), dict) else None
                ),
            }
        elif platform == "linkedin":
            return {
                "platform_user_id": data.get("sub", ""),
                "name": data.get("name", "Unknown"),
                "picture_url": data.get("picture"),
            }
        elif platform == "twitter":
            user_data = data.get("data", data)
            return {
                "platform_user_id": user_data.get("id", ""),
                "name": user_data.get("name", user_data.get("username", "Unknown")),
                "picture_url": user_data.get("profile_image_url"),
            }

        return {
            "platform_user_id": str(data.get("id", "")),
            "name": str(data.get("name", "Unknown")),
            "picture_url": None,
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout lors de la recuperation du profil ({platform})"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur reseau recuperation profil ({platform}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur reseau lors de la recuperation du profil ({platform})"
        )

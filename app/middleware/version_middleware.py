"""
Middleware pour gérer le versioning de l'API.

Ce middleware ajoute automatiquement les headers de version dans toutes les réponses
et permet de gérer les versions dépréciées.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.__version__ import (
    get_version,
    get_api_version,
    is_version_deprecated,
    VERSION_HEADER,
    MIN_VERSION_HEADER,
    VERSION_INFO
)
import logging

logger = logging.getLogger(__name__)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour injecter les informations de version dans les réponses.
    
    Ajoute automatiquement :
    - X-API-Version: Version actuelle de l'API
    - X-Min-Client-Version: Version minimale du client requise
    - Avertissements pour les versions dépréciées
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extraire la version de l'URL si présente (ex: /api/v1/...)
        path = request.url.path
        requested_version = None
        
        if path.startswith("/api/v"):
            parts = path.split("/")
            if len(parts) > 2:
                requested_version = parts[2]  # v1, v2, etc.
        
        # Vérifier si la version est dépréciée
        if requested_version and is_version_deprecated(requested_version):
            logger.warning(
                f"Deprecated API version {requested_version} accessed from "
                f"{request.client.host} - {request.method} {path}"
            )
            
            return JSONResponse(
                status_code=410,
                content={
                    "error": "API version deprecated",
                    "message": f"API version {requested_version} is deprecated and no longer available.",
                    "current_version": get_api_version(),
                    "upgrade_guide": VERSION_INFO.get("documentation_url"),
                },
                headers={
                    VERSION_HEADER: get_version(),
                    "X-Deprecated-Version": requested_version,
                }
            )
        
        # Continuer le traitement
        response = await call_next(request)
        
        # Ajouter les headers de version
        response.headers[VERSION_HEADER] = get_version()
        response.headers[MIN_VERSION_HEADER] = VERSION_INFO["min_client_version"]
        response.headers["X-API-Path-Version"] = get_api_version()
        
        # Ajouter un warning si la version est proche de la dépréciation
        if requested_version and requested_version != get_api_version():
            response.headers["Warning"] = (
                f'299 - "You are using API version {requested_version}. '
                f'Latest version is {get_api_version()}."'
            )
        
        return response

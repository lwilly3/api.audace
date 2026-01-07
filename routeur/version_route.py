"""
Route d'information sur la version de l'API.

Fournit des endpoints pour consulter les informations de version.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.__version__ import (
    get_version,
    get_version_info,
    get_breaking_changes,
    VERSION_INFO
)

router = APIRouter(
    prefix="/version",
    tags=["Version & Health"]
)


@router.get("/", summary="Informations de version de l'API")
async def get_api_version() -> Dict[str, Any]:
    """
    Retourne les informations complètes sur la version de l'API.
    
    Inclut :
    - Version actuelle
    - Date de release
    - Version d'API (v1, v2, etc.)
    - Breaking changes
    - Liens vers la documentation
    
    Returns:
        dict: Informations de version
    """
    return get_version_info()


@router.get("/current", summary="Version actuelle uniquement")
async def get_current_version() -> Dict[str, str]:
    """
    Retourne uniquement la version actuelle de l'API.
    
    Returns:
        dict: {"version": "X.Y.Z"}
    """
    return {"version": get_version()}


@router.get("/breaking-changes", summary="Liste des breaking changes")
async def get_api_breaking_changes() -> Dict[str, Any]:
    """
    Retourne la liste de tous les breaking changes par version.
    
    Utile pour les développeurs qui doivent migrer d'une version à l'autre.
    
    Returns:
        dict: Breaking changes groupés par version
    """
    return {
        "breaking_changes": get_breaking_changes(),
        "documentation": VERSION_INFO.get("documentation_url"),
        "changelog": VERSION_INFO.get("changelog_url")
    }


@router.get("/health", summary="Health check avec version")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint incluant les informations de version.
    
    Utilisé par les load balancers et systèmes de monitoring.
    
    Returns:
        dict: Status et informations de version
    """
    return {
        "status": "healthy",
        "version": get_version(),
        "api_version": VERSION_INFO["api_version"],
        "timestamp": VERSION_INFO.get("build_date")
    }


@router.get("/compatibility/{client_version}", summary="Vérifier la compatibilité")
async def check_compatibility(client_version: str) -> Dict[str, Any]:
    """
    Vérifie si une version client est compatible avec l'API actuelle.
    
    Args:
        client_version: Version du client à vérifier (ex: "1.0.0")
        
    Returns:
        dict: Informations de compatibilité
    """
    from packaging import version
    
    try:
        client_ver = version.parse(client_version)
        min_ver = version.parse(VERSION_INFO["min_client_version"])
        current_ver = version.parse(get_version())
        
        is_compatible = client_ver >= min_ver
        is_outdated = client_ver < current_ver
        
        return {
            "compatible": is_compatible,
            "outdated": is_outdated,
            "client_version": client_version,
            "api_version": get_version(),
            "min_required_version": VERSION_INFO["min_client_version"],
            "recommendation": (
                "Update your client to the latest version" if is_outdated
                else "Your client is up to date" if is_compatible
                else "Your client version is too old and not supported"
            )
        }
    except Exception as e:
        return {
            "error": "Invalid version format",
            "message": str(e),
            "example": "Use format X.Y.Z (e.g., 1.0.0)"
        }

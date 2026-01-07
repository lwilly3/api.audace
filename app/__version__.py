"""
Gestion centralisée des versions de l'API.

Ce module définit la version actuelle de l'API et fournit des utilitaires
pour le versioning.
"""

from typing import Dict, Any
from datetime import datetime

# Version actuelle de l'API (Semantic Versioning)
__version__ = "1.2.0"

# Informations détaillées de version
VERSION_INFO: Dict[str, Any] = {
    "version": __version__,
    "release_date": "2026-01-07",
    "api_version": "v1",  # Version de l'API pour le routing
    "min_client_version": "1.0.0",  # Version minimale du client supportée
    "deprecated_versions": [],  # Versions dépréciées
    "breaking_changes": {
        "1.2.0": [
            "Ajout des permissions Citations (non-breaking, nouveaux champs optionnels)"
        ],
        "1.1.0": [
            "Ajout des routes de suppression en masse des shows"
        ]
    },
    "changelog_url": "https://github.com/votre-org/votre-repo/blob/main/CHANGELOG.md",
    "documentation_url": "https://api.cloud.audace.ovh/docs"
}


def get_version() -> str:
    """Retourne la version actuelle de l'API."""
    return __version__


def get_api_version() -> str:
    """Retourne la version de l'API pour le routing (ex: 'v1')."""
    return VERSION_INFO["api_version"]


def get_version_info() -> Dict[str, Any]:
    """
    Retourne les informations complètes de version.
    
    Returns:
        dict: Informations détaillées incluant version, date de release, etc.
    """
    return {
        **VERSION_INFO,
        "build_date": datetime.now().isoformat(),
        "python_version": "3.11+",
        "framework": "FastAPI",
    }


def is_version_deprecated(version: str) -> bool:
    """
    Vérifie si une version est dépréciée.
    
    Args:
        version: Version à vérifier (ex: "v1", "v2")
        
    Returns:
        bool: True si la version est dépréciée
    """
    return version in VERSION_INFO["deprecated_versions"]


def get_breaking_changes(version: str = None) -> Dict[str, list]:
    """
    Retourne les breaking changes pour une version ou toutes les versions.
    
    Args:
        version: Version spécifique (optionnel)
        
    Returns:
        dict: Breaking changes par version
    """
    if version:
        return {version: VERSION_INFO["breaking_changes"].get(version, [])}
    return VERSION_INFO["breaking_changes"]


# Constantes pour le versioning d'URL
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"  # Pour future évolution

# Headers de version
VERSION_HEADER = "X-API-Version"
MIN_VERSION_HEADER = "X-Min-Client-Version"

"""
Schemas Pydantic pour l'extraction de sous-titres via yt-dlp.

Utilise par routeur/subtitle_route.py.
Formats supportes : SRT, VTT, texte brut.
"""

from pydantic import BaseModel
from typing import Optional, Literal


class SubtitleExtractRequest(BaseModel):
    """Demande d'extraction de sous-titres."""
    url: str
    lang: str = "fr"
    format: Literal["srt", "vtt", "txt"] = "txt"


class SubtitleTaskResponse(BaseModel):
    """Reponse initiale avec l'ID de tache."""
    task_id: str
    status: Literal["processing", "done", "error"]
    message: str


class SubtitleTaskStatus(BaseModel):
    """Statut d'une tache d'extraction (polling)."""
    task_id: str
    status: Literal["processing", "done", "error"]
    content: Optional[str] = None
    format: Optional[str] = None
    lang: Optional[str] = None
    message: Optional[str] = None


class AvailableLangsResponse(BaseModel):
    """Langues de sous-titres disponibles pour une video."""
    manual: list[str]
    auto: list[str]


class CookiesUploadResponse(BaseModel):
    """Reponse apres upload d'un fichier cookies."""
    ok: bool
    count: Optional[int] = None
    format_detected: Optional[str] = None
    error: Optional[str] = None


class CookiesStatusResponse(BaseModel):
    """Statut du fichier cookies sur le serveur."""
    has_cookies: bool
    count: Optional[int] = None
    size_bytes: Optional[int] = None
    modified_at: Optional[float] = None


class CookiesPasteRequest(BaseModel):
    """Cookies colles depuis le presse-papier (JSON Chrome)."""
    content: str

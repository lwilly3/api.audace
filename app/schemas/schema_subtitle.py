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

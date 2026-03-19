"""
Service d'extraction de sous-titres via yt-dlp.

Remplace le Cloudflare Worker (bloque par YouTube) pour extraire
les sous-titres de videos YouTube et 1000+ autres plateformes.
Supporte les formats VTT, SRT et texte brut.

Deux modes d'utilisation :
- Asynchrone (tache de fond) : extract_subtitles() + create_task() + get_task()
- Synchrone (pipeline IA) : extract_subtitles_sync() retourne directement le texte
"""

import os
import re
import uuid
import logging
from typing import Optional

import yt_dlp

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Stockage en memoire des taches async
# TODO: migrer vers Redis en production multi-worker
_tasks: dict[str, dict] = {}


def _build_ydl_opts(lang: str, output_path: str) -> dict:
    """Construit les options yt-dlp communes."""
    opts: dict = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang, f'{lang}-orig'],
        'subtitlesformat': 'vtt',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    if settings.YTDLP_PROXY:
        opts['proxy'] = settings.YTDLP_PROXY
    return opts


def convert_vtt_to_txt(vtt_content: str) -> str:
    """
    Convertit un fichier VTT en texte brut lisible.

    Supprime les timestamps, les numeros de sequence et les balises HTML.
    Dedoublonne les lignes consecutives identiques (artefact des sous-titres auto).
    """
    lines = vtt_content.split('\n')
    text_lines: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or '-->' in line:
            continue
        if re.match(r'^\d+$', line):
            continue
        # Supprimer les balises HTML (<c>, <b>, <i>, etc.)
        clean = re.sub(r'<[^>]+>', '', line)
        # Eviter les doublons consecutifs
        if clean and clean not in text_lines[-1:]:
            text_lines.append(clean)
    return '\n'.join(text_lines)


def _cleanup_temp_files(task_id: str) -> None:
    """Nettoie tous les fichiers temporaires d'une tache."""
    for f in os.listdir('/tmp'):
        if f.startswith(task_id):
            try:
                os.remove(f'/tmp/{f}')
            except OSError:
                pass


def _find_vtt_file(task_id: str) -> Optional[str]:
    """Trouve le fichier .vtt genere par yt-dlp dans /tmp."""
    for f in os.listdir('/tmp'):
        if f.startswith(task_id) and f.endswith('.vtt'):
            return f'/tmp/{f}'
    return None


def _extract_and_convert(url: str, lang: str, fmt: str, task_id: str) -> dict:
    """
    Logique commune d'extraction : telecharge les sous-titres et les convertit.

    Retourne un dict avec status, content, format, lang, message.
    """
    output_path = f"/tmp/{task_id}"
    ydl_opts = _build_ydl_opts(lang, output_path)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        vtt_file = _find_vtt_file(task_id)
        if not vtt_file:
            return {
                "status": "error",
                "message": f"Aucun sous-titre trouve pour la langue '{lang}'",
            }

        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Conversion selon le format demande
        if fmt == 'txt':
            content = convert_vtt_to_txt(content)

        logger.info(f"Sous-titres extraits ({len(content)} chars, {fmt}) pour {url}")

        return {
            "status": "done",
            "content": content,
            "format": fmt,
            "lang": lang,
        }

    except Exception as e:
        logger.error(f"Erreur extraction sous-titres pour {url}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        _cleanup_temp_files(task_id)


# ════════════════════════════════════════════════════════════════
# MODE ASYNCHRONE (tache de fond via BackgroundTasks)
# ════════════════════════════════════════════════════════════════

def create_task() -> str:
    """Cree une tache d'extraction et retourne son ID."""
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "processing"}
    return task_id


def get_task(task_id: str) -> Optional[dict]:
    """Recupere le statut d'une tache."""
    return _tasks.get(task_id)


def extract_subtitles(task_id: str, url: str, lang: str, fmt: str) -> None:
    """
    Extrait les sous-titres en tache de fond (BackgroundTasks FastAPI).

    Met a jour le dict _tasks avec le resultat.
    """
    result = _extract_and_convert(url, lang, fmt, task_id)
    _tasks[task_id] = result


# ════════════════════════════════════════════════════════════════
# MODE SYNCHRONE (pour le pipeline IA — ai_service.py)
# ════════════════════════════════════════════════════════════════

def extract_subtitles_sync(url: str, lang: str = "fr", fmt: str = "txt") -> str:
    """
    Extraction synchrone — retourne directement le texte.

    Utilise par ai_service.fetch_youtube_transcript() pour alimenter
    le pipeline de generation de contenu Mistral.

    Raises:
        RuntimeError si aucun sous-titre n'est trouve.
    """
    task_id = str(uuid.uuid4())
    result = _extract_and_convert(url, lang, fmt, task_id)

    if result["status"] == "error":
        raise RuntimeError(result.get("message", "Erreur extraction sous-titres"))

    return result.get("content", "")


# ════════════════════════════════════════════════════════════════
# DETECTION DES LANGUES DISPONIBLES
# ════════════════════════════════════════════════════════════════

def get_available_langs(url: str) -> dict:
    """
    Retourne les langues de sous-titres disponibles pour une URL video.
    Utile pour alimenter un selecteur de langue dans l'UI.
    """
    ydl_opts: dict = {'quiet': True, 'no_warnings': True}
    if settings.YTDLP_PROXY:
        ydl_opts['proxy'] = settings.YTDLP_PROXY

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "manual": list(info.get('subtitles', {}).keys()),
            "auto": list(info.get('automatic_captions', {}).keys()),
        }

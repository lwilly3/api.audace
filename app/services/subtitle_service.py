"""
Service d'extraction de sous-titres — architecture hybride.

Deux moteurs d'extraction :
1. youtube-transcript-api (YTA) — leger, rapide, YouTube uniquement
2. yt-dlp — universel, 1000+ plateformes, fallback YouTube

Strategie : YouTube → YTA d'abord, yt-dlp en fallback.
            Autres plateformes → yt-dlp directement.

Deux modes d'utilisation :
- Asynchrone (tache de fond) : extract_subtitles() + create_task() + get_task()
- Synchrone (pipeline IA) : extract_subtitles_sync() retourne directement le texte
"""

import json
import os
import re
import uuid
import logging
from typing import Optional

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Stockage en memoire des taches async
# TODO: migrer vers Redis en production multi-worker
_tasks: dict[str, dict] = {}

# Chemin du fichier cookies converti au format Netscape (cache en memoire)
_netscape_cookies_path: str | None = None


# ════════════════════════════════════════════════════════════════
# GESTION DES COOKIES (upload, paste, statut)
# ════════════════════════════════════════════════════════════════

def save_cookies_file(content: bytes, filename: str) -> dict:
    """
    Recoit un fichier cookies uploade, detecte le format (JSON Chrome ou Netscape),
    convertit si necessaire et stocke dans le chemin persistant.

    Retourne un dict avec le resultat (ok/erreur, nombre de cookies, format detecte).
    """
    global _netscape_cookies_path

    cookies_path = settings.YTDLP_COOKIES_PATH or "/app/data/cookies.txt"

    # Creer le dossier parent si necessaire
    os.makedirs(os.path.dirname(cookies_path), exist_ok=True)

    try:
        raw = content.decode('utf-8').strip()
    except UnicodeDecodeError:
        return {"ok": False, "error": "Fichier non lisible (encodage invalide)"}

    if not raw:
        return {"ok": False, "error": "Fichier vide"}

    # Detecter le format
    is_json = raw.startswith('[')
    is_netscape = raw.startswith('# Netscape') or raw.startswith('# HTTP') or '\t' in raw.split('\n')[0]

    if is_json:
        # Conversion JSON Chrome → Netscape
        try:
            cookies = json.loads(raw)
            if not isinstance(cookies, list):
                return {"ok": False, "error": "Format JSON invalide (liste attendue)"}

            lines = ['# Netscape HTTP Cookie File', '# Converted from Chrome JSON by RadioManager', '']
            for c in cookies:
                domain = c.get('domain', '')
                host_only = 'FALSE' if c.get('hostOnly', False) else 'TRUE'
                path = c.get('path', '/')
                secure = 'TRUE' if c.get('secure', False) else 'FALSE'
                expiration = str(int(c.get('expirationDate', 0)))
                name = c.get('name', '')
                value = c.get('value', '')
                lines.append(f"{domain}\t{host_only}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

            netscape_content = '\n'.join(lines) + '\n'
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(netscape_content)

            # Reset le cache
            _netscape_cookies_path = cookies_path
            logger.info(f"Cookies JSON Chrome convertis et sauvegardes ({len(cookies)} cookies) → {cookies_path}")
            return {"ok": True, "count": len(cookies), "format_detected": "chrome_json"}

        except (json.JSONDecodeError, KeyError) as e:
            return {"ok": False, "error": f"Erreur parsing JSON: {e}"}

    elif is_netscape:
        # Deja au format Netscape, sauvegarder directement
        with open(cookies_path, 'w', encoding='utf-8') as f:
            f.write(raw + '\n')

        cookie_count = sum(1 for line in raw.split('\n') if line.strip() and not line.startswith('#'))
        _netscape_cookies_path = cookies_path
        logger.info(f"Cookies Netscape sauvegardes ({cookie_count} cookies) → {cookies_path}")
        return {"ok": True, "count": cookie_count, "format_detected": "netscape"}

    else:
        return {"ok": False, "error": "Format non reconnu (attendu: JSON Chrome ou Netscape txt)"}


def get_cookies_status() -> dict:
    """
    Retourne le statut du fichier cookies : present, nombre de cookies, date de modification.
    """
    cookies_path = settings.YTDLP_COOKIES_PATH or "/app/data/cookies.txt"

    if not os.path.isfile(cookies_path):
        return {"has_cookies": False}

    try:
        stat = os.stat(cookies_path)
        with open(cookies_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        cookie_count = sum(1 for line in raw.split('\n') if line.strip() and not line.startswith('#'))
        return {
            "has_cookies": True,
            "count": cookie_count,
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }
    except Exception:
        return {"has_cookies": False}


# ════════════════════════════════════════════════════════════════
# YOUTUBE-TRANSCRIPT-API (moteur principal pour YouTube)
# ════════════════════════════════════════════════════════════════

def _extract_video_id(url: str) -> str | None:
    """Extrait l'ID (11 chars) depuis n'importe quel format d'URL YouTube."""
    pattern = r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


def _is_youtube_url(url: str) -> bool:
    """Verifie si l'URL est une video YouTube."""
    return "youtube.com" in url or "youtu.be" in url


def _seconds_to_vtt(seconds: float) -> str:
    """Convertit des secondes en timestamp VTT (HH:MM:SS.mmm)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _extract_via_yta(url: str, lang: str, fmt: str) -> dict:
    """
    Extraction via youtube-transcript-api.
    Plus legere que yt-dlp, moins detectee, mais YouTube uniquement.

    Retourne un dict compatible avec le format _extract_and_convert.
    """
    video_id = _extract_video_id(url)
    if not video_id:
        return {"status": "error", "message": f"Impossible d'extraire l'ID video depuis : {url}"}

    ytt = YouTubeTranscriptApi()

    try:
        transcript_list = ytt.list(video_id)
        # Tente la langue demandee, fallback anglais
        transcript = transcript_list.find_transcript([lang, "en"])
        entries = transcript.fetch()

    except NoTranscriptFound:
        return {"status": "error", "message": f"Aucun sous-titre disponible en '{lang}' pour {video_id}"}
    except TranscriptsDisabled:
        return {"status": "error", "message": f"Sous-titres desactives pour la video {video_id}"}
    except VideoUnavailable:
        return {"status": "error", "message": f"Video indisponible : {video_id}"}

    # Conversion selon le format demande
    if fmt == "vtt":
        lines = ["WEBVTT", ""]
        for e in entries:
            start = _seconds_to_vtt(e.start)
            end = _seconds_to_vtt(e.start + e.duration)
            lines += [f"{start} --> {end}", e.text, ""]
        content = "\n".join(lines)
    elif fmt == "json":
        content = json.dumps(
            [{"text": e.text, "start": e.start, "duration": e.duration} for e in entries],
            ensure_ascii=False, indent=2,
        )
    else:
        # txt par defaut
        content = "\n".join(e.text for e in entries)

    logger.info(f"[YTA] Sous-titres extraits ({len(content)} chars, {fmt}) pour {url}")

    return {
        "status": "done",
        "content": content,
        "format": fmt,
        "lang": lang,
    }


def _get_langs_via_yta(url: str) -> dict | None:
    """
    Retourne les langues disponibles via youtube-transcript-api.
    Plus rapide que yt-dlp pour cette operation.
    Retourne None en cas d'echec (fallback yt-dlp).
    """
    video_id = _extract_video_id(url)
    if not video_id:
        return None

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        manual = []
        auto = []
        for t in transcript_list:
            if t.is_generated:
                auto.append(t.language_code)
            else:
                manual.append(t.language_code)

        return {"manual": manual, "auto": auto}

    except Exception as e:
        logger.warning(f"[YTA] Detection langues echouee pour {url}: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# YT-DLP (moteur universel, fallback YouTube)
# ════════════════════════════════════════════════════════════════

def _ensure_netscape_cookies() -> str | None:
    """
    Convertit le fichier cookies JSON Chrome en format Netscape si necessaire.

    yt-dlp attend le format Netscape (comme wget/curl), mais la plupart
    des extensions Chrome exportent en JSON. Cette fonction detecte le format
    et convertit automatiquement.

    Retourne le chemin vers le fichier Netscape ou None si pas de cookies.
    """
    global _netscape_cookies_path

    # Deja converti
    if _netscape_cookies_path and os.path.isfile(_netscape_cookies_path):
        return _netscape_cookies_path

    cookies_path = settings.YTDLP_COOKIES_PATH
    if not cookies_path or not os.path.isfile(cookies_path):
        return None

    with open(cookies_path, 'r', encoding='utf-8') as f:
        raw = f.read().strip()

    # Si c'est deja au format Netscape (commence par # ou domaine)
    if raw.startswith('# Netscape') or raw.startswith('# HTTP') or not raw.startswith('['):
        _netscape_cookies_path = cookies_path
        return cookies_path

    # Conversion JSON Chrome → Netscape
    try:
        cookies = json.loads(raw)
        lines = ['# Netscape HTTP Cookie File', '# Converted from Chrome JSON by subtitle_service', '']
        for c in cookies:
            domain = c.get('domain', '')
            host_only = 'FALSE' if c.get('hostOnly', False) else 'TRUE'
            path = c.get('path', '/')
            secure = 'TRUE' if c.get('secure', False) else 'FALSE'
            expiration = str(int(c.get('expirationDate', 0)))
            name = c.get('name', '')
            value = c.get('value', '')
            lines.append(f"{domain}\t{host_only}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

        netscape_path = '/tmp/yt_cookies_netscape.txt'
        with open(netscape_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        _netscape_cookies_path = netscape_path
        logger.info(f"Cookies JSON convertis en Netscape ({len(cookies)} cookies) → {netscape_path}")
        return netscape_path

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Erreur conversion cookies JSON → Netscape: {e}")
        return None


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
        'ignore_no_formats_error': True,
        'extractor_args': {'youtube': {'player_client': ['tv', 'web']}},
    }
    if settings.YTDLP_PROXY:
        opts['proxy'] = settings.YTDLP_PROXY
    cookies = _ensure_netscape_cookies()
    if cookies:
        opts['cookiefile'] = cookies
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
    Extraction via yt-dlp (universel, 1000+ plateformes).

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

        logger.info(f"[yt-dlp] Sous-titres extraits ({len(content)} chars, {fmt}) pour {url}")

        return {
            "status": "done",
            "content": content,
            "format": fmt,
            "lang": lang,
        }

    except Exception as e:
        logger.error(f"[yt-dlp] Erreur extraction sous-titres pour {url}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        _cleanup_temp_files(task_id)


# ════════════════════════════════════════════════════════════════
# EXTRACTION HYBRIDE (YTA → yt-dlp fallback)
# ════════════════════════════════════════════════════════════════

def _extract_with_fallback(url: str, lang: str, fmt: str, task_id: str) -> dict:
    """
    Extraction hybride avec cascade de fallback :
      1. youtube-transcript-api → leger, peu detecte (YouTube seulement)
      2. yt-dlp → universel, plus robuste

    Retourne un dict avec status, content, format, lang, message.
    """
    if _is_youtube_url(url):
        logger.info(f"[subtitles] Tentative YTA pour {url}")
        result = _extract_via_yta(url, lang, fmt)
        if result["status"] == "done":
            return result
        logger.warning(f"[subtitles] YTA echoue ({result.get('message')}), fallback yt-dlp")

    # Fallback yt-dlp (autres plateformes ou si YTA echoue)
    logger.info(f"[subtitles] Tentative yt-dlp pour {url}")
    return _extract_and_convert(url, lang, fmt, task_id)


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

    Utilise la cascade YTA → yt-dlp pour YouTube, yt-dlp direct pour les autres.
    Met a jour le dict _tasks avec le resultat.
    """
    result = _extract_with_fallback(url, lang, fmt, task_id)
    _tasks[task_id] = result


# ════════════════════════════════════════════════════════════════
# MODE SYNCHRONE (pour le pipeline IA — ai_service.py)
# ════════════════════════════════════════════════════════════════

def extract_subtitles_sync(url: str, lang: str = "fr", fmt: str = "txt") -> str:
    """
    Extraction synchrone avec cascade de fallback :
      1. youtube-transcript-api → leger, peu detecte (YouTube seulement)
      2. yt-dlp → universel, plus robuste

    Utilise par ai_service.fetch_youtube_transcript() pour alimenter
    le pipeline de generation de contenu Mistral.

    Raises:
        RuntimeError si les deux methodes echouent.
    """
    task_id = str(uuid.uuid4())
    result = _extract_with_fallback(url, lang, fmt, task_id)

    if result["status"] == "error":
        raise RuntimeError(result.get("message", "Erreur extraction sous-titres"))

    return result.get("content", "")


# ════════════════════════════════════════════════════════════════
# DETECTION DES LANGUES DISPONIBLES
# ════════════════════════════════════════════════════════════════

def get_available_langs(url: str) -> dict:
    """
    Retourne les langues de sous-titres disponibles pour une URL video.
    YouTube → YTA (rapide), autres → yt-dlp.
    """
    if _is_youtube_url(url):
        result = _get_langs_via_yta(url)
        if result is not None:
            return result
        logger.warning(f"[subtitles] YTA langs echoue, fallback yt-dlp pour {url}")

    # Fallback yt-dlp
    ydl_opts: dict = {
        'quiet': True,
        'no_warnings': True,
        'ignore_no_formats_error': True,
        'extractor_args': {'youtube': {'player_client': ['tv', 'web']}},
    }
    if settings.YTDLP_PROXY:
        ydl_opts['proxy'] = settings.YTDLP_PROXY
    cookies = _ensure_netscape_cookies()
    if cookies:
        ydl_opts['cookiefile'] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "manual": list(info.get('subtitles', {}).keys()),
            "auto": list(info.get('automatic_captions', {}).keys()),
        }

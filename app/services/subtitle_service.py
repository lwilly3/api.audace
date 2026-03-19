"""
Service d'extraction de sous-titres via yt-dlp.

Remplace le Cloudflare Worker (bloque par YouTube) pour extraire
les sous-titres de videos YouTube et 1000+ autres plateformes.
Supporte les formats VTT, SRT et texte brut.

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

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Stockage en memoire des taches async
# TODO: migrer vers Redis en production multi-worker
_tasks: dict[str, dict] = {}

# Chemin du fichier cookies converti au format Netscape (cache en memoire)
_netscape_cookies_path: str | None = None


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
        'subtitlesformat': 'vtt/srt/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        # Eviter l'erreur "Requested format is not available" avec le client Android
        'format': 'best',
        # Utiliser le client Android pour contourner le bot check YouTube
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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


def _find_subtitle_file(task_id: str) -> Optional[str]:
    """Trouve le fichier de sous-titres (.vtt ou .srt) genere par yt-dlp dans /tmp."""
    for ext in ('.vtt', '.srt'):
        for f in os.listdir('/tmp'):
            if f.startswith(task_id) and f.endswith(ext):
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

        vtt_file = _find_subtitle_file(task_id)
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
    ydl_opts: dict = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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

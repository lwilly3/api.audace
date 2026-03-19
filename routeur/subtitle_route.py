"""
Routes d'extraction de sous-titres via yt-dlp.

Prefix : /social/subtitles
Tags : subtitles

Endpoints :
- POST /social/subtitles/extract        — Soumet une extraction async
- GET  /social/subtitles/status/{id}    — Poll le statut d'une tache
- GET  /social/subtitles/langs          — Liste les langues disponibles
- POST /social/subtitles/upload-cookies — Upload un fichier cookies YouTube
- POST /social/subtitles/paste-cookies — Coller des cookies JSON depuis le presse-papier
- GET  /social/subtitles/cookies-status — Statut du fichier cookies
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.schemas.schema_subtitle import (
    SubtitleExtractRequest,
    SubtitleTaskResponse,
    SubtitleTaskStatus,
    AvailableLangsResponse,
    CookiesUploadResponse,
    CookiesStatusResponse,
    CookiesPasteRequest,
)
from app.services.subtitle_service import (
    create_task,
    get_task,
    extract_subtitles,
    get_available_langs,
    save_cookies_file,
    get_cookies_status,
)

logger = logging.getLogger("hapson-api")

router = APIRouter(
    prefix="/social/subtitles",
    tags=["subtitles"],
)


@router.post("/extract", response_model=SubtitleTaskResponse)
async def request_extraction(
    req: SubtitleExtractRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Soumet une extraction de sous-titres en tache de fond."""
    task_id = create_task()
    background_tasks.add_task(
        extract_subtitles, task_id, req.url, req.lang, req.format
    )
    logger.info(
        f"Extraction sous-titres lancee (task={task_id}) "
        f"par user={current_user.id} pour {req.url}"
    )
    return SubtitleTaskResponse(
        task_id=task_id,
        status="processing",
        message="Extraction en cours…",
    )


@router.get("/status/{task_id}", response_model=SubtitleTaskStatus)
async def get_extraction_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Poll le statut d'une tache. Retourne le contenu quand status == 'done'."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tache introuvable"
        )
    return SubtitleTaskStatus(task_id=task_id, **task)


@router.get("/langs", response_model=AvailableLangsResponse)
async def list_available_langs(
    url: str = Query(..., description="URL de la video"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Retourne les langues de sous-titres disponibles pour une URL video."""
    try:
        langs = get_available_langs(url)
        return AvailableLangsResponse(**langs)
    except Exception as e:
        logger.error(f"Erreur detection langues pour {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post("/upload-cookies", response_model=CookiesUploadResponse)
async def upload_cookies(
    file: UploadFile = File(..., description="Fichier cookies (.txt Netscape ou .json Chrome)"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Upload un fichier cookies YouTube.

    Accepte deux formats :
    - JSON Chrome (exporte via extension EditThisCookie / Cookie-Editor)
    - Netscape TXT (format standard wget/curl)

    Le fichier est auto-converti et stocke de maniere persistante.
    Necessite la permission admin (super_admin ou can_manage_settings).
    """
    # Verification permission admin
    if not getattr(current_user, 'is_super_admin', False):
        perms = getattr(current_user, 'permissions', {}) or {}
        if not perms.get('can_manage_settings', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission requise : super_admin ou can_manage_settings"
            )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # Max 5 MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 5 MB)"
        )

    result = save_cookies_file(content, file.filename or "cookies.txt")
    logger.info(f"Upload cookies par user={current_user.id} — resultat: {result}")
    return CookiesUploadResponse(**result)


@router.post("/paste-cookies", response_model=CookiesUploadResponse)
async def paste_cookies(
    req: CookiesPasteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Coller des cookies YouTube depuis le presse-papier.

    Accepte le JSON copie depuis l'extension Cookie-Editor / EditThisCookie.
    Le backend detecte le format, convertit en Netscape et stocke.
    Necessite la permission admin (super_admin ou can_manage_settings).
    """
    if not getattr(current_user, 'is_super_admin', False):
        perms = getattr(current_user, 'permissions', {}) or {}
        if not perms.get('can_manage_settings', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission requise : super_admin ou can_manage_settings"
            )

    raw = req.content.strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contenu vide"
        )

    result = save_cookies_file(raw.encode('utf-8'), "pasted_cookies.json")
    logger.info(f"Paste cookies par user={current_user.id} — resultat: {result}")
    return CookiesUploadResponse(**result)


@router.get("/cookies-status", response_model=CookiesStatusResponse)
async def cookies_status(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Retourne le statut du fichier cookies (present, nombre, date)."""
    result = get_cookies_status()
    return CookiesStatusResponse(**result)

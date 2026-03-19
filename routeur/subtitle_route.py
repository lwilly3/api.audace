"""
Routes d'extraction de sous-titres via yt-dlp.

Prefix : /social/subtitles
Tags : subtitles

Endpoints :
- POST /social/subtitles/extract     — Soumet une extraction async
- GET  /social/subtitles/status/{id} — Poll le statut d'une tache
- GET  /social/subtitles/langs       — Liste les langues disponibles
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.schemas.schema_subtitle import (
    SubtitleExtractRequest,
    SubtitleTaskResponse,
    SubtitleTaskStatus,
    AvailableLangsResponse,
)
from app.services.subtitle_service import (
    create_task,
    get_task,
    extract_subtitles,
    get_available_langs,
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

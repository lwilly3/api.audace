import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from starlette import status

from app.db.database import get_db
from app.config.config import settings
from core.auth import oauth2
from app.models.model_user import User
from app.schemas.schema_public import (
    PublicAlertCreate, PublicAlertUpdate, PublicAlertResponse,
    ListenEventCreate, ListenStatsResponse,
    NowPlayingTrackCreate,
)
from app.db.crud.crud_public import (
    get_now_playing,
    get_weekly_schedule,
    get_active_alert,
    get_all_alerts,
    create_alert,
    update_alert,
    delete_alert,
    get_public_presenters,
    create_listen_event,
    get_listen_stats,
    store_now_playing_track,
    get_current_track,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/public",
    tags=["Public WordPress Integration"]
)


# =============================================
# P1 : Programme en Direct (PUBLIC - sans auth)
# =============================================

@router.get("/now-playing")
def now_playing_route(db: Session = Depends(get_db)):
    """
    Retourne l'emission en cours et la prochaine emission.
    Endpoint public - aucune authentification requise.
    Appele par le plugin WordPress pour afficher le programme en direct.
    """
    try:
        data = get_now_playing(db)
        # Enrichir avec la piste RadioDJ en cours
        data["current_track"] = get_current_track(db)
        return data
    except Exception as e:
        logger.exception("now-playing error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


# =============================================
# P2 : Grille des Programmes (PUBLIC - sans auth)
# =============================================

@router.get("/schedule")
def schedule_route(week: str = "current", db: Session = Depends(get_db)):
    """
    Retourne la grille des programmes pour une semaine donnee.
    Parametre week: 'current' (defaut), 'next', ou un offset numerique.
    Endpoint public - aucune authentification requise.
    """
    try:
        week_offset = 0
        if week == "next":
            week_offset = 1
        elif week not in ("current", ""):
            try:
                week_offset = int(week)
            except ValueError:
                week_offset = 0

        data = get_weekly_schedule(db, week_offset)
        return data
    except Exception as e:
        logger.exception("schedule error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


# =============================================
# P3 : Bandeau d'Alerte - Lecture (PUBLIC)
# =============================================

@router.get("/alert")
def get_alert_route(db: Session = Depends(get_db)):
    """
    Retourne l'alerte active actuellement.
    Endpoint public - aucune authentification requise.
    Retourne null si aucune alerte n'est active.
    """
    try:
        alert = get_active_alert(db)
        if not alert:
            return {"active": False}
        return {"active": True, **alert}
    except Exception as e:
        logger.exception("alert error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


# =============================================
# P3 : Alertes - Administration (PROTEGE - auth requise)
# =============================================

@router.get("/alerts", response_model=List[PublicAlertResponse])
def list_alerts_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Retourne la liste de toutes les alertes (admin)."""
    try:
        alerts = get_all_alerts(db)
        return alerts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne : {str(e)}"
        )


@router.post("/alerts", status_code=status.HTTP_201_CREATED, response_model=PublicAlertResponse)
def create_alert_route(
    alert_data: PublicAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Cree une nouvelle alerte publique."""
    try:
        alert = create_alert(db, alert_data.model_dump(), current_user.id)
        return alert
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la creation : {str(e)}"
        )


@router.patch("/alerts/{alert_id}", response_model=PublicAlertResponse)
def update_alert_route(
    alert_id: int,
    alert_data: PublicAlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Met a jour une alerte existante."""
    try:
        result = update_alert(db, alert_id, alert_data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alerte avec ID {alert_id} non trouvee"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise a jour : {str(e)}"
        )


@router.delete("/alerts/{alert_id}")
def delete_alert_route(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Supprime une alerte."""
    try:
        success = delete_alert(db, alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alerte avec ID {alert_id} non trouvee"
            )
        return {"message": "Alerte supprimee avec succes"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression : {str(e)}"
        )


# =============================================
# P4 : Fiches Animateurs (PUBLIC - sans auth)
# =============================================

@router.get("/presenters")
def presenters_route(db: Session = Depends(get_db)):
    """
    Retourne la liste des animateurs pour le site public.
    Endpoint public - aucune authentification requise.
    """
    try:
        presenters = get_public_presenters(db)
        return presenters
    except Exception as e:
        logger.exception("presenters error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


# =============================================
# P6 : Analytics - Reception Evenements (PUBLIC)
# =============================================

@router.post("/analytics/listen-event")
def listen_event_route(
    event: ListenEventCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Recoit un evenement d'ecoute depuis le plugin WordPress.
    Endpoint public - aucune authentification requise.
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referrer = request.headers.get("referer")

        result = create_listen_event(
            db,
            event.model_dump(),
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
        return result
    except Exception as e:
        logger.exception("listen-event error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


# =============================================
# P6 : Analytics - Statistiques (PROTEGE - auth requise)
# =============================================

@router.get("/analytics/listen-stats", response_model=ListenStatsResponse)
def listen_stats_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """
    Retourne les statistiques d'ecoute pour le dashboard SaaS.
    Endpoint protege - authentification requise.
    """
    try:
        stats = get_listen_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne : {str(e)}"
        )


# =============================================
# P7 : RadioDJ Now Playing Track (PUBLIC - auth par API key)
# =============================================

@router.post("/radiodj/track", status_code=status.HTTP_201_CREATED)
def radiodj_track_route(
    track_data: NowPlayingTrackCreate,
    key: str = Query(..., description="Cle API RadioDJ"),
    db: Session = Depends(get_db)
):
    """
    Recoit les infos de la piste en cours depuis RadioDJ.
    Protege par cle API via query parameter.
    RadioDJ appelle cette URL a chaque changement de piste.
    """
    if not settings.RADIODJ_API_KEY or key != settings.RADIODJ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cle API invalide"
        )

    try:
        result = store_now_playing_track(db, track_data.model_dump())
        return {"status": "ok", "track": result}
    except Exception as e:
        logger.exception("radiodj-track error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )

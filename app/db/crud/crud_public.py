from sqlalchemy.orm import joinedload, Session
from sqlalchemy import func, cast, Date, extract
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional

from app.models.model_show import Show
from app.models.model_segment import Segment
from app.models.model_presenter import Presenter
from app.models.model_public_alert import PublicAlert
from app.models.model_listen_event import ListenEvent
from app.models.model_now_playing_track import NowPlayingTrack


# =============================================
# P1 : Now Playing
# =============================================

def get_now_playing(db: Session) -> Dict[str, Any]:
    """
    Recupere l'emission en cours et la prochaine emission.
    L'emission en cours est celle avec le statut 'en-cours'.
    La prochaine est la plus proche en 'attente-diffusion'.
    """
    current_time = datetime.now()
    today = date.today()

    # Emission en cours (statut 'en-cours')
    current_show = db.query(Show).options(
        joinedload(Show.emission),
        joinedload(Show.presenters),
        joinedload(Show.segments).joinedload(Segment.guests)
    ).filter(
        Show.status == 'en-cours'
    ).order_by(Show.broadcast_date.desc()).first()

    # Prochaine emission (statut 'attente-diffusion', date future ou aujourd'hui)
    next_show = db.query(Show).options(
        joinedload(Show.emission),
        joinedload(Show.presenters),
        joinedload(Show.segments)
    ).filter(
        Show.status == 'attente-diffusion',
        Show.broadcast_date >= current_time
    ).order_by(Show.broadcast_date.asc()).first()

    def format_show(show, include_current_segment=False):
        if not show:
            return None

        presenters = [
            {
                "id": p.id,
                "name": p.name,
                "biography": p.biography,
                "profilePicture": p.profilePicture,
                "isMainPresenter": p.isMainPresenter
            }
            for p in show.presenters
        ]

        current_segment = None
        if include_current_segment and show.segments:
            sorted_segments = sorted(show.segments, key=lambda s: s.position)
            if show.broadcast_date:
                elapsed_minutes = (current_time - show.broadcast_date).total_seconds() / 60
                cumulative = 0
                for seg in sorted_segments:
                    cumulative += seg.duration
                    if cumulative > elapsed_minutes:
                        current_segment = {
                            "id": seg.id,
                            "title": seg.title,
                            "type": seg.type,
                            "duration": seg.duration,
                            "position": seg.position,
                            "startTime": seg.startTime,
                            "description": seg.description
                        }
                        break
            if not current_segment and sorted_segments:
                seg = sorted_segments[0]
                current_segment = {
                    "id": seg.id,
                    "title": seg.title,
                    "type": seg.type,
                    "duration": seg.duration,
                    "position": seg.position,
                    "startTime": seg.startTime,
                    "description": seg.description
                }

        return {
            "id": show.id,
            "title": show.title,
            "type": show.type,
            "broadcast_date": show.broadcast_date.isoformat() if show.broadcast_date else None,
            "duration": show.duration,
            "status": show.status,
            "description": show.description,
            "emission_title": show.emission.title if show.emission else None,
            "presenters": presenters,
            "current_segment": current_segment
        }

    return {
        "current_show": format_show(current_show, include_current_segment=True),
        "next_show": format_show(next_show, include_current_segment=False)
    }


# =============================================
# P2 : Grille des Programmes
# =============================================

JOUR_SEMAINE = {
    0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
    4: "vendredi", 5: "samedi", 6: "dimanche"
}


def get_weekly_schedule(db: Session, week_offset: int = 0) -> Dict[str, Any]:
    """
    Recupere la grille des programmes pour une semaine donnee.
    week_offset: 0 = semaine courante, 1 = semaine prochaine, etc.
    """
    today = date.today()
    # Calcul du lundi de la semaine demandee
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)

    shows = db.query(Show).options(
        joinedload(Show.emission),
        joinedload(Show.presenters)
    ).filter(
        func.date(Show.broadcast_date) >= monday,
        func.date(Show.broadcast_date) <= sunday
    ).order_by(Show.broadcast_date.asc()).all()

    # Grouper par jour
    days = {name: [] for name in JOUR_SEMAINE.values()}

    for show in shows:
        if show.broadcast_date:
            day_index = show.broadcast_date.weekday()
            day_name = JOUR_SEMAINE.get(day_index, "lundi")

            main_presenter = next(
                (p.name for p in show.presenters if p.isMainPresenter),
                (show.presenters[0].name if show.presenters else None)
            )

            days[day_name].append({
                "id": show.id,
                "title": show.title,
                "type": show.type,
                "broadcast_date": show.broadcast_date.isoformat(),
                "duration": show.duration,
                "status": show.status,
                "description": show.description,
                "emission_title": show.emission.title if show.emission else None,
                "presenter_name": main_presenter
            })

    return {
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
        "days": days
    }


# =============================================
# P3 : Alertes Publiques
# =============================================

def get_active_alert(db: Session) -> Optional[Dict[str, Any]]:
    """Recupere l'alerte active actuellement visible sur le site."""
    current_time = datetime.now()

    alert = db.query(PublicAlert).filter(
        PublicAlert.is_active == True,
        (PublicAlert.starts_at == None) | (PublicAlert.starts_at <= current_time),
        (PublicAlert.expires_at == None) | (PublicAlert.expires_at > current_time)
    ).order_by(PublicAlert.created_at.desc()).first()

    if not alert:
        return None

    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type,
        "url": alert.url,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }


def get_all_alerts(db: Session) -> List[Dict[str, Any]]:
    """Recupere toutes les alertes pour l'administration."""
    alerts = db.query(PublicAlert).order_by(PublicAlert.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "alert_type": a.alert_type,
            "is_active": a.is_active,
            "starts_at": a.starts_at.isoformat() if a.starts_at else None,
            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            "url": a.url,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None
        }
        for a in alerts
    ]


def create_alert(db: Session, alert_data: dict, user_id: int) -> Dict[str, Any]:
    """Cree une nouvelle alerte publique."""
    alert = PublicAlert(
        title=alert_data["title"],
        message=alert_data["message"],
        alert_type=alert_data.get("alert_type", "info"),
        is_active=alert_data.get("is_active", True),
        starts_at=alert_data.get("starts_at"),
        expires_at=alert_data.get("expires_at"),
        url=alert_data.get("url"),
        created_by=user_id
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type,
        "is_active": alert.is_active,
        "starts_at": alert.starts_at.isoformat() if alert.starts_at else None,
        "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
        "url": alert.url,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
    }


def update_alert(db: Session, alert_id: int, alert_data: dict) -> Optional[Dict[str, Any]]:
    """Met a jour une alerte existante."""
    alert = db.query(PublicAlert).filter(PublicAlert.id == alert_id).first()
    if not alert:
        return None

    for key, value in alert_data.items():
        if value is not None and hasattr(alert, key):
            setattr(alert, key, value)

    db.commit()
    db.refresh(alert)
    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type,
        "is_active": alert.is_active,
        "starts_at": alert.starts_at.isoformat() if alert.starts_at else None,
        "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
        "url": alert.url,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
    }


def delete_alert(db: Session, alert_id: int) -> bool:
    """Supprime une alerte."""
    alert = db.query(PublicAlert).filter(PublicAlert.id == alert_id).first()
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True


# =============================================
# P4 : Animateurs Publics
# =============================================

def get_public_presenters(db: Session) -> List[Dict[str, Any]]:
    """Recupere la liste des animateurs pour le site public."""
    presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False
    ).order_by(Presenter.name.asc()).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "biography": p.biography,
            "profilePicture": p.profilePicture
        }
        for p in presenters
    ]


# =============================================
# P6 : Statistiques d'Ecoute
# =============================================

def create_listen_event(
    db: Session,
    event_data: dict,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None
) -> Dict[str, Any]:
    """Enregistre un evenement d'ecoute provenant du site WordPress."""
    event = ListenEvent(
        session_id=event_data["session_id"],
        event_type=event_data["event_type"],
        duration=event_data.get("duration", 0),
        page_url=event_data.get("page_url"),
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    db.add(event)
    db.commit()
    return {"status": "ok", "event_id": event.id}


def get_listen_stats(db: Session) -> Dict[str, Any]:
    """Calcule les statistiques d'ecoute pour le dashboard SaaS."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Stats aujourd'hui (seuls les play comptent)
    today_plays = db.query(ListenEvent).filter(
        func.date(ListenEvent.created_at) == today,
        ListenEvent.event_type == 'play'
    )
    total_listens_today = today_plays.count()
    unique_sessions_today = db.query(
        func.count(func.distinct(ListenEvent.session_id))
    ).filter(
        func.date(ListenEvent.created_at) == today,
        ListenEvent.event_type == 'play'
    ).scalar() or 0

    # Duree moyenne (heartbeats de la semaine * 30s)
    heartbeats_week = db.query(ListenEvent).filter(
        func.date(ListenEvent.created_at) >= week_ago,
        ListenEvent.event_type == 'heartbeat'
    ).count()
    sessions_week = db.query(
        func.count(func.distinct(ListenEvent.session_id))
    ).filter(
        func.date(ListenEvent.created_at) >= week_ago,
        ListenEvent.event_type == 'play'
    ).scalar() or 0
    avg_duration = (heartbeats_week * 30.0 / sessions_week) if sessions_week > 0 else 0.0

    # Heure de pointe aujourd'hui
    peak_hour_query = db.query(
        extract('hour', ListenEvent.created_at).label('hour'),
        func.count(ListenEvent.id).label('cnt')
    ).filter(
        func.date(ListenEvent.created_at) == today,
        ListenEvent.event_type == 'play'
    ).group_by('hour').order_by(func.count(ListenEvent.id).desc()).first()
    peak_hour = int(peak_hour_query.hour) if peak_hour_query else None

    # Total semaine
    total_listens_week = db.query(ListenEvent).filter(
        func.date(ListenEvent.created_at) >= week_ago,
        ListenEvent.event_type == 'play'
    ).count()

    # Repartition journaliere (7 derniers jours) — single grouped query
    daily_rows = db.query(
        cast(ListenEvent.created_at, Date).label('day'),
        func.count(ListenEvent.id).label('count'),
        func.count(func.distinct(ListenEvent.session_id)).label('unique_sessions')
    ).filter(
        func.date(ListenEvent.created_at) >= week_ago,
        ListenEvent.event_type == 'play'
    ).group_by(cast(ListenEvent.created_at, Date)).all()

    daily_map = {row.day: {"count": row.count, "unique_sessions": row.unique_sessions} for row in daily_rows}
    daily_breakdown = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        entry = daily_map.get(d, {"count": 0, "unique_sessions": 0})
        daily_breakdown.append({
            "date": d.isoformat(),
            "count": entry["count"],
            "unique_sessions": entry["unique_sessions"]
        })

    return {
        "total_listens_today": total_listens_today,
        "unique_sessions_today": unique_sessions_today,
        "avg_duration_seconds": round(avg_duration, 1),
        "peak_hour": peak_hour,
        "total_listens_week": total_listens_week,
        "daily_breakdown": daily_breakdown
    }


# =============================================
# P7 : RadioDJ Now Playing Track
# =============================================

TRACK_STALENESS_SECONDS = 600  # 10 minutes


def store_now_playing_track(db: Session, track_data: dict) -> Dict[str, Any]:
    """
    Enregistre un nouveau morceau en cours de diffusion.
    Chaque appel cree une nouvelle ligne (historique).
    """
    track = NowPlayingTrack(
        artist=track_data.get("artist"),
        title=track_data["title"],
        album=track_data.get("album"),
        duration=track_data.get("duration"),
        track_type=track_data.get("track_type"),
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return {
        "id": track.id,
        "artist": track.artist,
        "title": track.title,
        "album": track.album,
        "duration": track.duration,
        "track_type": track.track_type,
        "started_at": track.started_at.isoformat() if track.started_at else None,
    }


EXCLUDED_TRACK_TYPES = {'jingle', 'sweeper', 'spot', 'voicetrack', 'id'}


def get_current_track(db: Session) -> Optional[Dict[str, Any]]:
    """
    Recupere le morceau le plus recent, sauf jingles/sweepers.
    Retourne None si le dernier morceau est trop ancien (staleness).
    """
    track = db.query(NowPlayingTrack).order_by(
        NowPlayingTrack.started_at.desc()
    ).first()

    if not track:
        return None

    # Staleness check
    elapsed = (datetime.now() - track.started_at).total_seconds()
    if elapsed > TRACK_STALENESS_SECONDS:
        return None

    # Exclure les jingles/sweepers connus
    if track.track_type and track.track_type.lower() in EXCLUDED_TRACK_TYPES:
        return None

    return {
        "artist": track.artist,
        "title": track.title,
        "album": track.album,
        "duration": track.duration,
        "track_type": track.track_type,
        "started_at": track.started_at.isoformat() if track.started_at else None,
    }

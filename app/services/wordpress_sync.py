import httpx
import logging
from sqlalchemy.orm import Session, joinedload
from app.models.model_show import Show
from app.models.model_segment import Segment
from app.config.config import settings

logger = logging.getLogger("hapson-api")


def sync_show_to_wordpress(show_id: int, db: Session) -> bool:
    """
    Synchronise un conducteur vers WordPress en creant un article
    via l'API REST du plugin Radio Audace Player.

    Appele quand un conducteur passe au statut 'en-cours'.
    """
    wp_site_url = getattr(settings, 'WORDPRESS_SITE_URL', None)
    wp_sync_secret = getattr(settings, 'WORDPRESS_SYNC_SECRET', None)

    if not wp_site_url or not wp_sync_secret:
        logger.warning("WordPress sync: URL ou secret non configure, synchronisation ignoree")
        return False

    try:
        show = db.query(Show).options(
            joinedload(Show.emission),
            joinedload(Show.presenters),
            joinedload(Show.segments).joinedload(Segment.guests)
        ).filter(Show.id == show_id).first()

        if not show:
            logger.error(f"WordPress sync: Show {show_id} non trouve")
            return False

        main_presenter = next(
            (p.name for p in show.presenters if p.isMainPresenter),
            (show.presenters[0].name if show.presenters else "")
        )

        payload = {
            "id": show.id,
            "title": show.title,
            "type": show.type,
            "description": show.description or "",
            "broadcast_date": show.broadcast_date.isoformat() if show.broadcast_date else None,
            "duration": show.duration,
            "status": show.status,
            "emission_title": show.emission.title if show.emission else "",
            "presenter_name": main_presenter,
            "segments": [
                {
                    "title": seg.title,
                    "type": seg.type,
                    "duration": seg.duration,
                    "position": seg.position,
                    "guests": [g.name for g in seg.guests]
                }
                for seg in sorted(show.segments, key=lambda s: s.position)
            ]
        }

        endpoint = f"{wp_site_url.rstrip('/')}/wp-json/rap/v1/sync-show"

        response = httpx.post(
            endpoint,
            json=payload,
            headers={
                "X-RAP-Sync-Secret": wp_sync_secret,
                "Content-Type": "application/json"
            },
            timeout=10.0
        )

        if response.status_code in (200, 201):
            logger.info(f"WordPress sync: Show {show_id} synchronise (post_id={response.json().get('post_id')})")
            return True
        else:
            logger.warning(f"WordPress sync: Echec pour show {show_id} - HTTP {response.status_code}: {response.text}")
            return False

    except httpx.TimeoutException:
        logger.warning(f"WordPress sync: Timeout pour show {show_id}")
        return False
    except Exception as e:
        logger.error(f"WordPress sync: Erreur inattendue pour show {show_id}: {str(e)}")
        return False

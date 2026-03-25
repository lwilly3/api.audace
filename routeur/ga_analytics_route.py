"""
Routes FastAPI pour Google Analytics 4 (GA4) — Web Analytics.

Prefix : /ga
Tags : ga-analytics

Endpoints :
- GET  /ga/sites               — Lister les proprietes GA4 configurees
- POST /ga/sites               — Ajouter une propriete GA4
- DELETE /ga/sites/{id}         — Supprimer une propriete GA4
- GET  /ga/sites/{id}/realtime  — Donnees temps reel (30 dernieres min)
- GET  /ga/sites/{id}/overview  — Vue d'ensemble (periode configurable)
- GET  /ga/sites/{id}/sources   — Sources de trafic
- GET  /ga/sites/{id}/pages     — Top pages
- GET  /ga/sites/{id}/geography — Geographie des visiteurs
- GET  /ga/sites/{id}/technology — Navigateurs, OS, appareils
- GET  /ga/sites/{id}/trends    — Series temporelles pour graphiques
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from core.auth import oauth2
from app.db.crud.crud_ga_property import (
    get_ga_properties,
    get_ga_property_by_id,
    create_ga_property,
    delete_ga_property,
)
from app.schemas.schema_ga_analytics import (
    GaPropertyCreate,
    GaPropertyResponse,
    GaRealtimeResponse,
    GaOverviewResponse,
    GaSourcesResponse,
    GaPagesResponse,
    GaGeographyResponse,
    GaTechnologyResponse,
    GaTrendsResponse,
)
from app.services import ga_analytics_service
from app.db.crud.crud_audit_logs import log_action

logger = logging.getLogger("hapson-api")

router = APIRouter(prefix="/ga", tags=["ga-analytics"])


# ═══ DIAGNOSTIC ═══

@router.get("/diagnostic")
def ga_diagnostic(
    current_user=Depends(oauth2.get_current_user),
):
    """Diagnostic de la configuration GA4 — affiche l'email du Service Account et teste la connexion."""
    import json
    from app.config.config import settings

    result: dict = {"configured": False, "client_email": None, "error": None}

    if not settings.GA_SERVICE_ACCOUNT_JSON:
        result["error"] = "GA_SERVICE_ACCOUNT_JSON est vide"
        return result

    try:
        info = json.loads(settings.GA_SERVICE_ACCOUNT_JSON)
        result["configured"] = True
        result["client_email"] = info.get("client_email", "non trouve dans le JSON")
        result["project_id"] = info.get("project_id", "non trouve")
    except json.JSONDecodeError as e:
        result["error"] = f"JSON invalide : {e}"
        return result

    # Tester l'initialisation du client
    try:
        ga_analytics_service._get_client()
        result["client_initialized"] = True
    except Exception as e:
        result["client_initialized"] = False
        result["client_error"] = str(e)

    return result


# ═══ SITES (GA4 Properties CRUD) ═══

@router.get("/sites", response_model=list[GaPropertyResponse])
def list_sites(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Lister les proprietes GA4 configurees."""
    return get_ga_properties(db)


@router.post("/sites", response_model=GaPropertyResponse, status_code=status.HTTP_201_CREATED)
def add_site(
    data: GaPropertyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Ajouter une propriete GA4."""
    prop = create_ga_property(db, data, current_user.id)
    log_action(db, user_id=current_user.id, action="ga_property_created",
               details=f"GA4 property {data.property_id} ({data.display_name})")
    return prop


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Supprimer une propriete GA4."""
    if not delete_ga_property(db, site_id):
        raise HTTPException(status_code=404, detail="Propriete GA4 introuvable")
    log_action(db, user_id=current_user.id, action="ga_property_deleted",
               details=f"GA4 property ID {site_id}")


# ═══ ANALYTICS DATA ═══

def _get_property_or_404(db: Session, site_id: int):
    """Helper : recuperer la propriete GA4 ou lever 404."""
    prop = get_ga_property_by_id(db, site_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propriete GA4 introuvable")
    return prop


@router.get("/sites/{site_id}/realtime", response_model=GaRealtimeResponse)
def site_realtime(
    site_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Donnees temps reel (30 dernieres minutes)."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_realtime(prop.property_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 realtime error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/overview", response_model=GaOverviewResponse)
def site_overview(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Vue d'ensemble des metriques."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_overview(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 overview error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/sources", response_model=GaSourcesResponse)
def site_sources(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Sources de trafic."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_sources(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 sources error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/pages", response_model=GaPagesResponse)
def site_pages(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Top pages visitees."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_top_pages(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 pages error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/geography", response_model=GaGeographyResponse)
def site_geography(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Geographie des visiteurs."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_geography(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 geography error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/technology", response_model=GaTechnologyResponse)
def site_technology(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Navigateurs, OS, appareils."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_technology(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 technology error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")


@router.get("/sites/{site_id}/trends", response_model=GaTrendsResponse)
def site_trends(
    site_id: int,
    period: str = Query("28d", pattern="^(7d|28d|90d)$"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Series temporelles pour graphiques."""
    prop = _get_property_or_404(db, site_id)
    try:
        return ga_analytics_service.get_trends(prop.property_id, period)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GA4 trends error for {prop.property_id}: {e}")
        raise HTTPException(status_code=502, detail="Erreur lors de la recuperation des donnees GA4")

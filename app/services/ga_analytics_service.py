"""
Service Google Analytics Data API v1 (GA4).

Wrappe le client BetaAnalyticsDataClient pour fournir des fonctions
de haut niveau renvoyant les donnees formatees pour le frontend.

- Authentification via Service Account (JSON dans variable d'environnement)
- Cache en memoire avec TTL configurable (5 min standard, 30s realtime)
- Realtime : pas de cache long (30s seulement)

Quotas : 10 000 requetes/jour/propriete (avec cache 5 min, largement suffisant)
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    RunRealtimeReportRequest,
    BatchRunReportsRequest,
    DateRange,
    Dimension,
    Metric,
    OrderBy,
)
from google.oauth2 import service_account

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# ─── Cache en memoire ───

_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 300       # 5 minutes pour les rapports standard
REALTIME_CACHE_TTL = 30       # 30 secondes pour le temps reel


def _get_cached(key: str, ttl: int = CACHE_TTL_SECONDS) -> Any:
    """Retourne la valeur en cache si encore valide, sinon None."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < ttl:
            return val
        del _cache[key]
    return None


def _set_cache(key: str, val: Any) -> None:
    """Met en cache une valeur avec le timestamp actuel."""
    _cache[key] = (time.time(), val)


# ─── Client GA4 ───

_client: Optional[BetaAnalyticsDataClient] = None


def _get_client() -> BetaAnalyticsDataClient:
    """Initialise le client GA4 avec le Service Account (singleton)."""
    global _client
    if _client is None:
        if not settings.GA_SERVICE_ACCOUNT_JSON:
            raise RuntimeError("GA_SERVICE_ACCOUNT_JSON non configure — impossible d'acceder a Google Analytics")
        info = json.loads(settings.GA_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        _client = BetaAnalyticsDataClient(credentials=creds)
        logger.info("Client Google Analytics Data API v1 initialise")
    return _client


def _prop(property_id: str) -> str:
    """Normalise l'ID de propriete en format 'properties/XXXXX'."""
    if property_id.startswith("properties/"):
        return property_id
    return f"properties/{property_id}"


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convertit '7d', '28d', '90d' en (start_date, end_date)."""
    days_map = {"7d": 7, "28d": 28, "90d": 90}
    days = days_map.get(period, 28)
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _previous_period_dates(period: str) -> tuple[str, str]:
    """Dates de la periode precedente (pour comparaison)."""
    days_map = {"7d": 7, "28d": 28, "90d": 90}
    days = days_map.get(period, 28)
    end = datetime.now() - timedelta(days=days)
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _safe_float(val: str, default: float = 0.0) -> float:
    """Convertit une string en float (les valeurs GA sont des strings)."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: str, default: int = 0) -> int:
    """Convertit une string en int."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _pct_change(current: float, previous: float) -> float:
    """Calcule le changement en pourcentage."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


# ═══ REALTIME ═══

def get_realtime(property_id: str) -> dict:
    """Donnees temps reel (30 dernieres minutes)."""
    cache_key = f"ga:realtime:{property_id}"
    cached = _get_cached(cache_key, REALTIME_CACHE_TTL)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)

    # Rapport temps reel avec plusieurs dimensions
    request = RunRealtimeReportRequest(
        property=prop,
        dimensions=[
            Dimension(name="unifiedScreenName"),
        ],
        metrics=[
            Metric(name="activeUsers"),
        ],
        limit=10,
    )
    response = client.run_realtime_report(request)

    top_pages = []
    for row in response.rows:
        top_pages.append({
            "page_title": row.dimension_values[0].value,
            "page_path": "",
            "active_users": _safe_int(row.metric_values[0].value),
        })

    # Sources
    req_sources = RunRealtimeReportRequest(
        property=prop,
        dimensions=[Dimension(name="source")],
        metrics=[Metric(name="activeUsers")],
        limit=10,
    )
    resp_sources = client.run_realtime_report(req_sources)
    top_sources = [
        {"source": r.dimension_values[0].value, "active_users": _safe_int(r.metric_values[0].value)}
        for r in resp_sources.rows
    ]

    # Appareils
    req_device = RunRealtimeReportRequest(
        property=prop,
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="activeUsers")],
    )
    resp_device = client.run_realtime_report(req_device)
    by_device = [
        {"device_category": r.dimension_values[0].value, "active_users": _safe_int(r.metric_values[0].value)}
        for r in resp_device.rows
    ]

    # Pays
    req_country = RunRealtimeReportRequest(
        property=prop,
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers")],
        limit=10,
    )
    resp_country = client.run_realtime_report(req_country)
    by_country = [
        {"country": r.dimension_values[0].value, "active_users": _safe_int(r.metric_values[0].value)}
        for r in resp_country.rows
    ]

    # Total actifs
    req_total = RunRealtimeReportRequest(
        property=prop,
        metrics=[Metric(name="activeUsers"), Metric(name="screenPageViews"), Metric(name="eventCount")],
    )
    resp_total = client.run_realtime_report(req_total)
    active_users = 0
    pageviews = 0
    events = 0
    if resp_total.rows:
        active_users = _safe_int(resp_total.rows[0].metric_values[0].value)
        pageviews = _safe_int(resp_total.rows[0].metric_values[1].value)
        events = _safe_int(resp_total.rows[0].metric_values[2].value)
    else:
        logger.warning(f"GA4 realtime: aucune donnee pour {property_id} — "
                       f"row_count={resp_total.row_count}, "
                       f"verifier que le Service Account a l'acces Lecteur sur cette propriete")

    result = {
        "active_users": active_users,
        "pageviews": pageviews,
        "events": events,
        "top_pages": top_pages,
        "top_sources": top_sources,
        "by_device": by_device,
        "by_country": by_country,
    }
    _set_cache(cache_key, result)
    return result


# ═══ OVERVIEW ═══

def get_overview(property_id: str, period: str = "28d") -> dict:
    """Vue d'ensemble des metriques avec comparaison periode precedente."""
    cache_key = f"ga:overview:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)
    prev_start, prev_end = _previous_period_dates(period)

    metrics = [
        Metric(name="activeUsers"),
        Metric(name="newUsers"),
        Metric(name="sessions"),
        Metric(name="screenPageViews"),
        Metric(name="averageSessionDuration"),
        Metric(name="bounceRate"),
        Metric(name="engagementRate"),
        Metric(name="engagedSessions"),
        Metric(name="eventCount"),
    ]

    # Periode courante
    req_current = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start, end_date=end)],
        metrics=metrics,
    )
    resp_current = client.run_report(req_current)

    # Periode precedente
    req_prev = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=prev_start, end_date=prev_end)],
        metrics=metrics,
    )
    resp_prev = client.run_report(req_prev)

    def _extract(resp: Any) -> list[float]:
        if resp.rows:
            return [_safe_float(v.value) for v in resp.rows[0].metric_values]
        logger.warning(f"GA4 overview: aucune donnee pour {property_id} (period={period}) — "
                       f"row_count={resp.row_count}, "
                       f"verifier que le Service Account a l'acces Lecteur")
        return [0.0] * 9

    cur = _extract(resp_current)
    prev = _extract(resp_prev)

    result = {
        "active_users": int(cur[0]),
        "new_users": int(cur[1]),
        "sessions": int(cur[2]),
        "page_views": int(cur[3]),
        "avg_session_duration": round(cur[4], 1),
        "bounce_rate": round(cur[5] * 100, 1) if cur[5] <= 1 else round(cur[5], 1),
        "engagement_rate": round(cur[6] * 100, 1) if cur[6] <= 1 else round(cur[6], 1),
        "engaged_sessions": int(cur[7]),
        "events_count": int(cur[8]),
        "active_users_change": _pct_change(cur[0], prev[0]),
        "sessions_change": _pct_change(cur[2], prev[2]),
        "page_views_change": _pct_change(cur[3], prev[3]),
        "bounce_rate_change": _pct_change(cur[5], prev[5]),
        "period_start": start,
        "period_end": end,
    }
    _set_cache(cache_key, result)
    return result


# ═══ SOURCES ═══

def get_sources(property_id: str, period: str = "28d") -> dict:
    """Sources de trafic (source/medium)."""
    cache_key = f"ga:sources:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)

    request = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
        ],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=20,
    )
    response = client.run_report(request)

    total_sessions = 0
    items = []
    for row in response.rows:
        sessions = _safe_int(row.metric_values[0].value)
        total_sessions += sessions
        bounce = _safe_float(row.metric_values[2].value)
        items.append({
            "source": row.dimension_values[0].value,
            "medium": row.dimension_values[1].value,
            "sessions": sessions,
            "users": _safe_int(row.metric_values[1].value),
            "bounce_rate": round(bounce * 100, 1) if bounce <= 1 else round(bounce, 1),
            "avg_session_duration": round(_safe_float(row.metric_values[3].value), 1),
            "conversions": _safe_int(row.metric_values[4].value),
        })

    result = {"items": items, "total_sessions": total_sessions}
    _set_cache(cache_key, result)
    return result


# ═══ TOP PAGES ═══

def get_top_pages(property_id: str, period: str = "28d") -> dict:
    """Top pages visitees."""
    cache_key = f"ga:pages:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)

    request = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="pageTitle"), Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="totalUsers"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
            Metric(name="entrances"),
        ],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=30,
    )
    response = client.run_report(request)

    total_pv = 0
    items = []
    for row in response.rows:
        pv = _safe_int(row.metric_values[0].value)
        total_pv += pv
        bounce = _safe_float(row.metric_values[3].value)
        items.append({
            "page_title": row.dimension_values[0].value,
            "page_path": row.dimension_values[1].value,
            "page_views": pv,
            "users": _safe_int(row.metric_values[1].value),
            "avg_time_on_page": round(_safe_float(row.metric_values[2].value), 1),
            "bounce_rate": round(bounce * 100, 1) if bounce <= 1 else round(bounce, 1),
            "entrances": _safe_int(row.metric_values[4].value),
        })

    result = {"items": items, "total_page_views": total_pv}
    _set_cache(cache_key, result)
    return result


# ═══ GEOGRAPHY ═══

def get_geography(property_id: str, period: str = "28d") -> dict:
    """Geographie des visiteurs (pays + villes)."""
    cache_key = f"ga:geography:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)
    date_range = [DateRange(start_date=start, end_date=end)]
    metrics = [Metric(name="totalUsers"), Metric(name="sessions"), Metric(name="screenPageViews")]

    # Par pays
    req_country = RunReportRequest(
        property=prop,
        date_ranges=date_range,
        dimensions=[Dimension(name="country")],
        metrics=metrics,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)],
        limit=20,
    )
    resp_country = client.run_report(req_country)

    by_country = [
        {
            "country": r.dimension_values[0].value,
            "city": None,
            "users": _safe_int(r.metric_values[0].value),
            "sessions": _safe_int(r.metric_values[1].value),
            "page_views": _safe_int(r.metric_values[2].value),
        }
        for r in resp_country.rows
    ]

    # Par ville
    req_city = RunReportRequest(
        property=prop,
        date_ranges=date_range,
        dimensions=[Dimension(name="city"), Dimension(name="country")],
        metrics=metrics,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)],
        limit=20,
    )
    resp_city = client.run_report(req_city)

    by_city = [
        {
            "country": r.dimension_values[1].value,
            "city": r.dimension_values[0].value,
            "users": _safe_int(r.metric_values[0].value),
            "sessions": _safe_int(r.metric_values[1].value),
            "page_views": _safe_int(r.metric_values[2].value),
        }
        for r in resp_city.rows
    ]

    result = {"by_country": by_country, "by_city": by_city}
    _set_cache(cache_key, result)
    return result


# ═══ TECHNOLOGY ═══

def get_technology(property_id: str, period: str = "28d") -> dict:
    """Navigateurs, OS, appareils."""
    cache_key = f"ga:technology:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)
    date_range = [DateRange(start_date=start, end_date=end)]
    metrics = [Metric(name="totalUsers"), Metric(name="sessions")]

    def _run_tech(dimension_name: str) -> list[dict]:
        req = RunReportRequest(
            property=prop,
            date_ranges=date_range,
            dimensions=[Dimension(name=dimension_name)],
            metrics=metrics,
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)],
            limit=10,
        )
        resp = client.run_report(req)
        total = sum(_safe_int(r.metric_values[0].value) for r in resp.rows) or 1
        return [
            {
                "name": r.dimension_values[0].value,
                "users": _safe_int(r.metric_values[0].value),
                "sessions": _safe_int(r.metric_values[1].value),
                "percentage": round(_safe_int(r.metric_values[0].value) / total * 100, 1),
            }
            for r in resp.rows
        ]

    result = {
        "by_browser": _run_tech("browser"),
        "by_os": _run_tech("operatingSystem"),
        "by_device": _run_tech("deviceCategory"),
    }
    _set_cache(cache_key, result)
    return result


# ═══ TRENDS ═══

def get_trends(property_id: str, period: str = "28d") -> dict:
    """Series temporelles pour les graphiques."""
    cache_key = f"ga:trends:{property_id}:{period}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prop = _prop(property_id)
    start, end = _period_to_dates(period)

    request = RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
    )
    response = client.run_report(request)

    points = []
    for row in response.rows:
        raw_date = row.dimension_values[0].value
        # Format YYYYMMDD → YYYY-MM-DD
        formatted = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date
        bounce = _safe_float(row.metric_values[3].value)
        points.append({
            "date": formatted,
            "active_users": _safe_int(row.metric_values[0].value),
            "sessions": _safe_int(row.metric_values[1].value),
            "page_views": _safe_int(row.metric_values[2].value),
            "bounce_rate": round(bounce * 100, 1) if bounce <= 1 else round(bounce, 1),
            "avg_session_duration": round(_safe_float(row.metric_values[4].value), 1),
        })

    result = {"points": points, "period_start": start, "period_end": end}
    _set_cache(cache_key, result)
    return result

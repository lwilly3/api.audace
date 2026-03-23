"""
Route dashboard — endpoints agreges pour le module Inventaire.

Fournit les statistiques, alertes et donnees recentes en un seul appel.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.crud.crud_inventory_equipment import get_inventory_stats
from app.db.crud.crud_inventory_subscription import get_subscription_alerts
from core.auth import oauth2


router = APIRouter(
    prefix="/inventory/dashboard",
    tags=["inventory-dashboard"]
)


class DashboardAlerts(BaseModel):
    """Reponse combinee pour le badge count et les alertes du dashboard."""
    low_stock_count: int = 0
    overdue_returns_count: int = 0
    expiring_subscriptions_count: int = 0
    expired_subscriptions_count: int = 0
    total_alerts: int = 0


@router.get("/alerts", response_model=DashboardAlerts)
def get_dashboard_alerts(
    subscription_days: int = Query(30, description="Jours avant expiration pour les alertes abonnements"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Retourne les alertes combinees pour le badge count du Launchpad :
    - Stock bas (equipements consommables)
    - Retours en retard
    - Abonnements expirant / expires
    """
    # Stats equipements (contient deja low_stock et overdue)
    stats = get_inventory_stats(db)

    # Alertes abonnements
    sub_alerts = get_subscription_alerts(db, days=subscription_days)

    expired_count = len(sub_alerts.expired)
    expiring_count = len(sub_alerts.expiring_soon) + len(sub_alerts.expiring_warning)

    total = (
        stats.low_stock_count
        + stats.overdue_returns_count
        + expired_count
        + expiring_count
    )

    return DashboardAlerts(
        low_stock_count=stats.low_stock_count,
        overdue_returns_count=stats.overdue_returns_count,
        expiring_subscriptions_count=expiring_count,
        expired_subscriptions_count=expired_count,
        total_alerts=total,
    )

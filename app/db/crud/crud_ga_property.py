"""
CRUD operations pour les proprietes Google Analytics 4.

Gestion des proprietes GA4 configurees dans la table ga_properties.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.model_ga_property import GaProperty
from app.schemas.schema_ga_analytics import GaPropertyCreate


def get_ga_properties(db: Session) -> list[GaProperty]:
    """Lister toutes les proprietes GA4 actives."""
    return db.query(GaProperty).filter(GaProperty.is_active == True).order_by(GaProperty.display_name).all()


def get_ga_property_by_id(db: Session, prop_id: int) -> GaProperty | None:
    """Recuperer une propriete par son ID interne."""
    return db.query(GaProperty).filter(GaProperty.id == prop_id, GaProperty.is_active == True).first()


def create_ga_property(db: Session, data: GaPropertyCreate, user_id: int) -> GaProperty:
    """Creer une nouvelle propriete GA4."""
    existing = db.query(GaProperty).filter(GaProperty.property_id == data.property_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La propriete GA4 '{data.property_id}' est deja configuree"
        )
    prop = GaProperty(
        property_id=data.property_id,
        display_name=data.display_name,
        website_url=data.website_url,
        created_by=user_id,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def delete_ga_property(db: Session, prop_id: int) -> bool:
    """Supprimer une propriete GA4."""
    prop = db.query(GaProperty).filter(GaProperty.id == prop_id).first()
    if not prop:
        return False
    db.delete(prop)
    db.commit()
    return True

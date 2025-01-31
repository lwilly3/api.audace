from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schema_segment import SegmentSearchFilter
from app.db.crud.crud_searche_conducteur import search_shows  # Assure-toi que la fonction est bien importée
from typing import Optional, List 
from datetime import datetime


router = APIRouter(
    prefix="/search_shows",
     tags=['search_shows']
     )

@router.get("/", response_model=dict)
def get_shows(
   keywords: Optional[str] = None,
    status: Optional[str] = None,
    dateFrom: Optional[datetime] = None,
    dateTo: Optional[datetime] = None,
    presenter: Optional[List[int]] = None,
    guest: Optional[List[int]] =None,
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
    db: Session = Depends(get_db)
):
    # keywords: '',
    #   dateFrom: '',
    #   dateTo: '',
    #   status: '',
    #   presenter: '',
    #   guest: '',

    """
    Endpoint pour récupérer les émissions filtrées.

    Args:
        filters (SegmentSearchFilter): Filtres à appliquer sur la recherche.
        skip (int): Nombre d'éléments à ignorer (pagination).
        limit (int): Nombre d'éléments à récupérer (pagination).
        db (Session): Session de base de données SQLAlchemy.

    Returns:
        dict: Résultats filtrés avec le nombre total d'éléments et les détails des émissions.
    """
    # print("filters", filters)
    return search_shows(db, keyword=keywords,status=status,date_from=dateFrom,date_to=dateTo, presenter_ids=presenter,guest_ids=guest, skip=skip, limit=limit)

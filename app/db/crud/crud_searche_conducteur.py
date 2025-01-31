from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models import Show, Segment, Presenter, Guest
from app.schemas.schema_segment import SegmentSearchFilter
from fastapi import HTTPException
from typing import Optional, List 
from datetime import datetime
from app.utils.format_datetime import format_datetime

class NotFoundError(Exception):
    """Exception levée lorsqu'aucun résultat ne correspond à la recherche."""
    def __init__(self, detail: str, code: int = 404):
        self.detail = detail
        self.code = code

def search_shows(db: Session, keyword=None, status=None,date_from=None,date_to=None,presenter_ids=None, guest_ids=None , skip: int = 0, limit: int = 10):
    """
    Recherche les émissions en fonction des filtres fournis et renvoie les résultats formatés.

    Args:
        db (Session): Session de base de données SQLAlchemy.
        filters (SegmentSearchFilter): Filtres pour affiner la recherche.
        skip (int): Nombre d'éléments à ignorer (pagination).
        limit (int): Nombre maximum d'éléments à récupérer (pagination).

    Returns:
        dict: Un dictionnaire contenant le nombre total de résultats et les données filtrées.
    """
    try:
        # Définition de la requête avec préchargement des relations
        query = db.query(Show).options(
            joinedload(Show.emission),  # Charger les détails de l'émission associée
            joinedload(Show.presenters),  # Charger les présentateurs associés
            joinedload(Show.segments).joinedload(Segment.guests)  # Charger les segments et leurs invités
        )

        # Filtrage par mot-clé (titre ou description)
        if keyword:
            query = query.join(Show.segments).filter(

                or_(  # Recherche dans le titre ou la description de l'émission ou des segments
                    Show.title.ilike(f"%{keyword}%"),
                    Show.description.ilike(f"%{keyword}%"),
                    Segment.title.ilike(f"%{keyword}%"),
                    Segment.description.ilike(f"%{keyword}%"),
                    Segment.technical_notes.ilike(f"%{keyword}%")
                    
                )
            )
        
           # Filtrage par mot-clé dans les segments (titre, description, notes techniques)
        # if keyword:
        #     query = query.join(Show.segments).filter(
        #         or_(
        #             Segment.title.ilike(f"%{keyword}%"),
        #             Segment.description.ilike(f"%{keyword}%"),
        #             Segment.technical_notes.ilike(f"%{keyword}%")
        #         )
        #     )

        # Filtrage par statut
        if status:
            query = query.filter(Show.status == status)

        # Filtrage par date de diffusion
        if date_from and date_to:
            query = query.filter(
                Show.broadcast_date.between(format_datetime(date_from), format_datetime(date_to))
            )

        # Filtrage par présentateurs
        if presenter_ids:
            query = query.join(Show.presenters).filter(
                Presenter.id.in_(presenter_ids)
            )

        # Filtrage par invités (vérifier les segments)
        if guest_ids:
            query = query.join(Show.segments).join(Segment.guests).filter(
                Guest.id.in_(guest_ids)
            )

        # Obtenir le total des résultats avant la pagination
        total = query.count()

        # Si aucun résultat n'est trouvé, lever une exception
        if total == 0:
            raise NotFoundError("Aucun résultat trouvé pour les filtres spécifiés.", 404)

        # Appliquer pagination
        shows = query.offset(skip).limit(limit).all()

        # Construction de la réponse au format get_show_details_all
        results = []
        for show in shows:
            show_info = {
                "id": show.id,
                "emission": show.emission.title if show.emission else "No Emission Linked",
                "emission_id": show.emission_id,
                "title": show.title,
                "type": show.type,
                "broadcast_date": show.broadcast_date,
                "duration": show.duration,
                "frequency": show.frequency,
                "description": show.description,
                "status": show.status,
                "presenters": [],
                "segments": []
            }

            # Ajouter les présentateurs associés
            for presenter in show.presenters:
                show_info["presenters"].append({
                    "id": presenter.id,
                    "name": presenter.name,
                    "contact_info": presenter.contact_info,
                    "biography": presenter.biography,
                    "isMainPresenter": presenter.isMainPresenter,
                })

            # Trier les segments par position
            sorted_segments = sorted(show.segments, key=lambda x: x.position)
            
            for segment in sorted_segments:
                segment_info = {
                    "id": segment.id,
                    "title": segment.title,
                    "type": segment.type,
                    "duration": segment.duration,
                    "description": segment.description,
                    "startTime": segment.startTime,
                    "position": segment.position,
                    "technical_notes": segment.technical_notes,
                    "guests": []
                }

                # Ajouter les invités associés au segment
                for guest in segment.guests:
                    segment_info["guests"].append({
                        "id": guest.id,
                        "name": guest.name,
                        "contact_info": guest.contact_info,
                        "biography": guest.biography,
                        "role": guest.role,
                        "avatar": guest.avatar,
                    })

                show_info["segments"].append(segment_info)

            results.append(show_info)

        return {
            "total": total,
            "data": results
        }

    except NotFoundError as e:
        # Gérer l'exception NotFoundError et renvoyer une réponse appropriée
        raise HTTPException(status_code=e.code, detail=e.detail)

    except Exception as e:
        # Gérer les autres exceptions et renvoyer une réponse appropriée
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de la recherche des émissions : {str(e)}")

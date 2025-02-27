
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List
from app.models import Show, User,Segment

def get_dashboard(db: Session) -> Dict[str, Any]:

    #     """
#     Récupère les données nécessaires pour le tableau de bord.
    
#     Args:
#         db (Session): Session de base de données SQLAlchemy.
    
#     Returns:
#         dict: Dictionnaire contenant les statistiques et le programme du jour.
    
#     Raises:
#         ValueError: Si les données de date sont invalides ou si aucune émission n'est trouvée.
#         SQLAlchemyError: Si une erreur de base de données survient.
#     """
    try:
        today = date.today()
        current_time = datetime.now()
#         # Vérification de la validité des dates

        if not today or not current_time:
            raise ValueError("Date ou heure invalide.")

#         # Programme du jour avec animateurs, segments, et invités

        programme_du_jour = db.query(Show).options(
            joinedload(Show.emission),
            joinedload(Show.presenters),
            joinedload(Show.segments).joinedload(Segment.guests)
        ).filter(
            func.date(Show.broadcast_date) == today
        ).order_by(Show.broadcast_date).all()

        # if not programme_du_jour and not db.query(Show).filter(func.date(Show.broadcast_date) == today).first():
        #     raise ValueError("Aucune émission trouvée pour aujourd'hui.")

        program_du_jour_details: List[Dict[str, Any]] = []
        for show in programme_du_jour:
            show_info = {
                "id": show.id,
                "emission": show.emission.title if show.emission else "Aucune émission liée",
                "emission_id": show.emission_id,
                "title": show.title,
                "type": show.type,
                "broadcast_date": show.broadcast_date,
                "duration": show.duration,
                "frequency": show.frequency,
                "description": show.description,
                "status": show.status,
                "presenters": [
                    {
                        "id": presenter.id,
                        "name": presenter.name,
                        "contact_info": presenter.contact_info,
                        "biography": presenter.biography,
                        "isMainPresenter": presenter.isMainPresenter
                    } for presenter in show.presenters
                ],
                "segments": []
            }

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
                    "guests": [
                        {
                            "id": guest.id,
                            "name": guest.name,
                            "contact_info": guest.contact_info,
                            "biography": guest.biography,
                            "role": guest.role,
                            "avatar": guest.avatar
                        } for guest in segment.guests
                    ]
                }
                show_info["segments"].append(segment_info)

            main_presenter = next((p for p in show_info["presenters"] if p["isMainPresenter"]), None)
            show_info["animateur"] = main_presenter["name"] if main_presenter else "Aucun animateur principal"

            program_du_jour_details.append(show_info)

        # Ajout de membres_equipe (approximation avec le nombre d'utilisateurs actifs)
        membres_equipe = db.query(User).filter(User.is_active == True).count()
        # Ajout de heures_direct (approximation avec les heures en direct calculées)
        heures_direct = db.query(func.sum(Show.duration)).filter(
            Show.status == 'en-cours',
            Show.broadcast_date <= current_time
        ).scalar() or 0 // 60

        response = {
            "emissions_du_jour": db.query(Show).filter(func.date(Show.broadcast_date) == today).count(),
            "en_direct_et_a_venir": db.query(Show).filter(
                Show.broadcast_date >= current_time,
                Show.status.in_(['en-cours', 'attente-diffusion'])
            ).count(),
            "programme_du_jour": program_du_jour_details,
            "membres_equipe": membres_equipe,
            "heures_direct": heures_direct,
            "emissions_planifiees": db.query(Show).filter(
                Show.broadcast_date > current_time,
                Show.status == 'attente-diffusion'
            ).count()
        }

        return response

    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e
    except ValueError as e:
        raise ValueError(f"Erreur de validation : {str(e)}") from e
    except Exception as e:
        raise Exception(f"Erreur inattendue : {str(e)}") from e
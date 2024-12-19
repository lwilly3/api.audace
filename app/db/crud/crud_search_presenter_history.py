from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import PresenterHistory  # Assurez-vous que le modèle PresenterHistory est importé correctement

# Fonction pour rechercher l'historique des présentateurs
def search_presenter_history(
    session: Session,  # Session de la base de données
    presenter_id: Optional[int] = None, 
    updated_by: Optional[int] = None, 
    date: Optional[datetime] = None
) -> List[PresenterHistory]:
    """
    Rechercher l'historique des modifications d'un présentateur par ID, utilisateur, ou date.
    """
    try:
        # Construire la requête de base
        query = session.query(PresenterHistory)

        # Appliquer les filtres en fonction des paramètres
        if presenter_id:
            query = query.filter(PresenterHistory.presenter_id == presenter_id)
        if updated_by:
            query = query.filter(PresenterHistory.updated_by == updated_by)
        if date:
            query = query.filter(PresenterHistory.updated_at.date() == date.date())

        # Exécuter la requête et récupérer les résultats
        return query.all()

    except SQLAlchemyError as e:
        # Capture de toutes les erreurs liées à SQLAlchemy
        session.rollback()  # Annule la transaction en cas d'erreur
        print(f"Une erreur est survenue lors de la recherche dans l'historique des présentateurs : {e}")
        return []  # Retourne une liste vide en cas d'erreur

    except Exception as e:
        # Capture des autres erreurs générales
        print(f"Une erreur inattendue est survenue : {e}")
        return []  # Retourne une liste vide en cas d'erreur









# # database.py
# from datetime import datetime
# from typing import List, Optional

# # Base de données simulée pour l'historique des présentateurs
# presenter_history_db = [
#     {"id": 1, "presenter_id": 1, "updated_by": 101, "update_date": datetime(2024, 5, 10), "changes": "Updated biography."},
#     {"id": 2, "presenter_id": 2, "updated_by": 102, "update_date": datetime(2024, 5, 12), "changes": "Updated contact details."},
#     {"id": 3, "presenter_id": 1, "updated_by": 101, "update_date": datetime(2024, 6, 5), "changes": "Changed profile picture."},
# ]

# def search_presenter_history(
#     presenter_id: Optional[int] = None, updated_by: Optional[int] = None, date: Optional[datetime] = None
# ) -> List[dict]:
#     """
#     Rechercher l'historique des modifications d'un présentateur par ID, utilisateur, ou date.
#     """
#     filtered_history = [
#         history
#         for history in presenter_history_db
#         if (presenter_id is None or presenter_id == history["presenter_id"]) and
#            (updated_by is None or updated_by == history["updated_by"]) and
#            (date is None or date.date() == history["update_date"].date())
#     ]

#     return filtered_history

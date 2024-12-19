
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import Presenter, PresenterHistory
# -------------------------
# Base de données simulée pour les présentateurs (modifiée pour SQLAlchemy)
# -------------------------

def search_presenters(db: Session, name: Optional[str] = None, biography: Optional[str] = None) -> List[dict]:
    """
    Rechercher des présentateurs par nom ou biographie dans la base de données.
    """
    try:
        query = db.query(Presenter)
        
        if name:
            query = query.filter(Presenter.name.ilike(f"%{name}%"))
        if biography:
            query = query.filter(Presenter.biography.ilike(f"%{biography}%"))
        
        return query.all()  # Retourne la liste des résultats

    except SQLAlchemyError as e:
        # Capture de toute exception SQLAlchemy (erreurs de requêtes, etc.)
        db.rollback()  # Annuler toute transaction en cours en cas d'erreur
        print(f"Une erreur est survenue lors de la recherche des présentateurs : {e}")
        return []  # Retourner une liste vide en cas d'erreur


def get_presenter_history(db: Session, presenter_id: int) -> List[dict]:
    """
    Récupérer l'historique des modifications d'un présentateur.
    """
    try:
        # Recherche dans l'historique des présentateurs pour un ID spécifique
        return db.query(PresenterHistory).filter(PresenterHistory.presenter_id == presenter_id).all()
    
    except SQLAlchemyError as e:
        # Capture d'une exception SQLAlchemy
        db.rollback()  # Annuler toute transaction en cours en cas d'erreur
        print(f"Une erreur est survenue lors de la récupération de l'historique du présentateur {presenter_id} : {e}")
        return []  # Retourner une liste vide en cas d'erreur


def update_presenter(db: Session, presenter_id: int, name: Optional[str] = None, biography: Optional[str] = None) -> Optional[dict]:
    """
    Mettre à jour les informations d'un présentateur.
    """
    try:
        presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
        
        if presenter:
            if name:
                presenter.name = name
            if biography:
                presenter.biography = biography

            db.commit()  # Effectuer la mise à jour dans la base de données
            db.refresh(presenter)  # Rafraîchir l'objet pour obtenir les nouvelles valeurs
            
            # Enregistrer l'historique de cette modification
            new_history = PresenterHistory(
                presenter_id=presenter.id,
                name=presenter.name,
                biography=presenter.biography,
                updated_by=1  # Utiliser l'ID de l'utilisateur qui a effectué la modification
            )
            db.add(new_history)
            db.commit()
            db.refresh(new_history)

            return presenter  # Retourner le présentateur mis à jour
        
        else:
            print(f"Le présentateur avec l'ID {presenter_id} n'a pas été trouvé.")
            return None  # Retourner None si le présentateur n'a pas été trouvé

    except SQLAlchemyError as e:
        # Capture d'une exception SQLAlchemy
        db.rollback()  # Annuler toute transaction en cours en cas d'erreur
        print(f"Une erreur est survenue lors de la mise à jour du présentateur {presenter_id} : {e}")
        return None  # Retourner None en cas d'erreur


def soft_delete_presenter(db: Session, presenter_id: int) -> bool:
    """
    Supprimer un présentateur en douceur (soft delete).
    """
    try:
        presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
        
        if presenter:
            presenter.is_deleted = True
            presenter.deleted_at = datetime.utcnow()
            db.commit()  # Appliquer la suppression douce
            return True
        else:
            print(f"Le présentateur avec l'ID {presenter_id} n'a pas été trouvé.")
            return False  # Retourner False si le présentateur n'a pas été trouvé

    except SQLAlchemyError as e:
        # Capture d'une exception SQLAlchemy
        db.rollback()  # Annuler toute transaction en cours en cas d'erreur
        print(f"Une erreur est survenue lors de la suppression douce du présentateur {presenter_id} : {e}")
        return False  # Retourner False en cas d'erreur











# # database.py
# from datetime import datetime

# # Base de données simulée des présentateurs
# presenters_db = [
#     {"id": 1, "name": "John Doe", "biography": "Experienced radio host", "created_at": datetime.now()},
#     {"id": 2, "name": "Jane Smith", "biography": "Famous TV presenter", "created_at": datetime.now()},
#     {"id": 3, "name": "Michael Brown", "biography": "Radio host with a passion for sports", "created_at": datetime.now()},
# ]

# def search_presenters(name=None, biography=None):
#     """
#     Rechercher des présentateurs par nom ou biographie.
#     """
#     return [
#         presenter
#         for presenter in presenters_db
#         if (name and name.lower() in presenter["name"].lower()) or
#            (biography and biography.lower() in presenter["biography"].lower())
#     ]

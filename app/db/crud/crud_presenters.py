# 
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from app.models import Presenter,User
from app.schemas import PresenterCreate, PresenterUpdate,PresenterResponsePaged
from app.models import User  # Si vous avez un modèle User pour gérer les permissions
from app.db.crud.crud_check_permission import check_permission

# Configuration du logger
logger = logging.getLogger(__name__)

# Exception personnalisée pour le non-trouvabilité d'un présentateur
class PresenterNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Presenter not found")

# CRUD pour les Présentateurs

def create_presenter(db: Session, presenter: PresenterCreate):

    detail_error_message="Error creating presenter"

    """
    Créer un nouveau présentateur dans la base de données avec validation des données.
    
    Args:
    - db (Session): La session de la base de données.
    - presenter (PresenterCreate): Les données du présentateur à créer.
    - user (User): L'utilisateur effectuant l'action.
    
    Returns:
    - Presenter: Le présentateur créé dans la base de données.
    
    Raises:
    - HTTPException: En cas d'erreur interne ou si un présentateur existe déjà avec ce nom.
    """
    try:
        
        # Vérification des permissions
        # check_permission(user, "create_presenter")
        
        # Vérification si un présentateur avec ce nom existe déjà
        existing_presenter = db.query(Presenter).filter(Presenter.name == presenter.name).first()
        existing_presenter_userID = db.query(Presenter).filter(Presenter.users_id == presenter.users_id).first()

        existing_UserId = db.query(User).filter(User.id == presenter.users_id).first()

        if existing_presenter:
            detail_error_message="Presenter with this name already exists"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail_error_message)
        
        if  existing_presenter_userID:
            detail_error_message="Presenter with this UserID already exists"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail_error_message)
        
        if not existing_UserId:
            detail_error_message="this UserID not exists"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail_error_message)
 

        # Création d'un nouveau présentateur
        presenter_db = Presenter(name=presenter.name, biography=presenter.biography, users_id=presenter.users_id)
        db.add(presenter_db)
        db.commit()
        db.refresh(presenter_db)

        logger.info(f"Presenter '{presenter.name}' created successfully.")
        return presenter_db
    except Exception as e:
        db.rollback()  # Rollback en cas d'erreur
        logger.error(f"Error creating presenter: {e}")
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail_error_message)




def get_presenter(db: Session, presenter_id: int):
    """
    Récupérer un présentateur spécifique de la base de données par son ID.
    
    Args:
    - db (Session): La session de la base de données.
    - presenter_id (int): L'ID du présentateur à récupérer.
    
    Returns:
    - Presenter: Le présentateur récupéré.
    
    Raises:
    - HTTPException: Si le présentateur n'est pas trouvé.
    """
    try:
        presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
        if not presenter:
            raise PresenterNotFoundError()
        
        return presenter
    except Exception as e:
        logger.error(f"Error fetching presenter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching presenter")




def get_all_presenters(db: Session, skip: int = 0, limit: int = 10) -> PresenterResponsePaged:
    """
    Récupérer tous les présentateurs de la base de données avec pagination.
    
    Args:
    - db (Session): La session de la base de données.
    - skip (int): Nombre de résultats à ignorer (pour la pagination).
    - limit (int): Nombre maximum de résultats à retourner.

    Returns:
    - dict: Un dictionnaire contenant le total des présentateurs et une liste paginée de présentateurs.
    """
    try:
        # Calculer le total des présentateurs
        total_presenters = db.query(Presenter).filter(Presenter.is_deleted == False).count()

        # Récupérer les présentateurs avec pagination
        presenters_and_counts = (
            db.query(Presenter)
            .filter(Presenter.is_deleted == False)  # Si vous utilisez une suppression logique
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Sérialiser chaque résultat
        serialized_results = []
        for presenter in presenters_and_counts:
            # presenter = presenter_and_count

            # Créer un dictionnaire pour chaque résultat
            serialized_presenter = {
                
                    "id": presenter.id,
                    "name": presenter.name,
                    "biography": presenter.biography,
                    "is_deleted": presenter.is_deleted,
                    "deleted_at": presenter.deleted_at,
                    "users_id": presenter.users_id,
                    "shows": [show.name for show in presenter.shows],
                
                       }
        serialized_results.append(serialized_presenter)

        return {
            "total": total_presenters,
            "presenters": presenters_and_counts,
        }



    except Exception as e:
            print({e})  
            logger.error(f"Error fetching presenters with votes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching presenters with votes",
            )




def update_presenter(db: Session, presenter_id: int, presenter_update: PresenterUpdate):
    """
    Mettre à jour un présentateur existant avec validation des données.
    
    Args:
    - db (Session): La session de la base de données.
    - presenter_id (int): L'ID du présentateur à mettre à jour.
    - presenter_update (PresenterUpdate): Les données mises à jour du présentateur.
    - user (User): L'utilisateur effectuant l'action.
    
    Returns:
    - Presenter: Le présentateur mis à jour.
    
    Raises:
    - HTTPException: Si le présentateur n'est pas trouvé ou si une erreur se produit.
    """
    try:
        # Vérification des permissions
        # check_permission(user, "update_presenter")
        print("try recuperation presenter")

        presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
        if not presenter:
            print("presenter not found")
            raise PresenterNotFoundError()

        # Mise à jour des attributs
        if presenter_update.name:
            print("presenter_update.name")
            presenter.name = presenter_update.name
        if presenter_update.biography:
            print("presenter_update.biography")
            presenter.biography = presenter_update.biography
        
        db.commit()
        print("db.commit")
        db.refresh(presenter)
        print("db.refresh(presenter)")
        
        logger.info(f"Presenter '{presenter.name}' updated successfully.")
        return presenter
    except Exception as e:
        print({e})
        db.rollback()  # Rollback en cas d'erreur
        logger.error(f"Error updating presenter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating presenter")

def delete_presenter(db: Session, presenter_id: int):
    """
    Supprimer un présentateur de la base de données (soft delete).
    
    Args:
    - db (Session): La session de la base de données.
    - presenter_id (int): L'ID du présentateur à supprimer.
    - user (User): L'utilisateur effectuant l'action.
    
    Returns:
    - Presenter: Le présentateur supprimé.
    
    Raises:
    - HTTPException: Si le présentateur n'est pas trouvé ou si une erreur se produit.
    """
    try:
        # Vérification des permissions
        # check_permission(user, "delete_presenter")

        presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
        if not presenter:
            raise PresenterNotFoundError()

        # Soft delete
        presenter.is_deleted = True
        presenter.deleted_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"Presenter '{presenter.name}' marked as deleted.")
        return presenter
    except Exception as e:
        db.rollback()  # Rollback en cas d'erreur
        logger.error(f"Error deleting presenter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting presenter")

def get_presenters(db: Session, skip: int = 0, limit: int = 10):
    """
    Récupérer la liste paginée des présentateurs.
    
    Args:
    - db (Session): La session de la base de données.
    - skip (int): Le nombre d'éléments à ignorer (pour la pagination).
    - limit (int): Le nombre d'éléments à récupérer.
    
    Returns:
    - List[Presenter]: La liste des présentateurs récupérés.
    """
    try:
        total = db.query(Presenter).count()
        presenters = db.query(Presenter).offset(skip).limit(limit).all()
        
        return {"total": total, "presenters": presenters}
    except Exception as e:
        logger.error(f"Error fetching presenters: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching presenters")






































# from datetime import datetime, timezone
# from sqlalchemy.orm import Session
# import app.models as models

# # CRUD pour les Présentateurs
# def create_presenter(db: Session, name: str, biography: str = None):
#     presenter = models.Presenter(name=name, biography=biography)
#     db.add(presenter)
#     db.commit()
#     db.refresh(presenter)
#     return presenter

# def get_presenter(db: Session, presenter_id: int):
#     return db.query(models.Presenter).filter(models.Presenter.id == presenter_id).first()

# def update_presenter(db: Session, presenter_id: int, name: str = None, biography: str = None):
#     presenter = db.query(models.Presenter).filter(models.Presenter.id == presenter_id).first()
#     if presenter:
#         if name:
#             presenter.name = name
#         if biography:
#             presenter.biography = biography
#         db.commit()
#         db.refresh(presenter)
#     return presenter

# def delete_presenter(db: Session, presenter_id: int):
#     presenter = db.query(models.Presenter).filter(models.Presenter.id == presenter_id).first()
#     if presenter:
#         presenter.is_deleted = True
#         presenter.deleted_at = datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
#         db.commit()
#     return presenter














# # from sqlalchemy.orm import Session
# # from models.model_presenter import Presenter
# # from schemas.schema_presenters import PresenterCreate, PresenterUpdate

# # def create_presenter(db: Session, presenter: PresenterCreate):
# #     new_presenter = Presenter(**presenter.dict())
# #     db.add(new_presenter)
# #     db.commit()
# #     db.refresh(new_presenter)
# #     return new_presenter

# # def get_presenter(db: Session, presenter_id: int):
# #     return db.query(Presenter).filter(Presenter.id == presenter_id).first()

# # def update_presenter(db: Session, presenter_id: int, presenter_update: PresenterUpdate):
# #     presenter = db.query(Presenter).filter(Presenter.id == presenter_id).first()
# #     for key, value in presenter_update.dict(exclude_unset=True).items():
# #         setattr(presenter, key, value)
# #     db.commit()
# #     db.refresh(presenter)
# #     return presenter

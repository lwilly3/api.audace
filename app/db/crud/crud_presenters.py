# 
import logging
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from app.models import Presenter,User
from app.schemas import PresenterCreate, PresenterUpdate,PresenterResponsePaged
from app.models import User  # Si vous avez un modèle User pour gérer les permissions
from app.db.crud.crud_check_permission import check_permission
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from sqlalchemy.orm import aliased

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


        
    # Vérification des permissions
    # check_permission(user, "create_presenter")
    
    # Vérification si un présentateur avec ce nom existe déjà
    existing_presenter = db.query(Presenter).filter(Presenter.name == presenter.name).first()
    existing_presenter_userID = db.query(Presenter).filter(Presenter.users_id == presenter.users_id).first()

    existing_UserId = db.query(User).filter(User.id == presenter.users_id).first()

    if existing_presenter:
        detail_error_message="Presenter with this name already exists"
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=detail_error_message)
    
    if  existing_presenter_userID:
        detail_error_message="Presenter with this UserID already exists"
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail_error_message)
    
    if not existing_UserId:
        detail_error_message="this UserID not exists"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_error_message)


    try:

        # Création d'un nouveau présentateur
        # presenter_db = Presenter(name=presenter.name, biography=presenter.biography, users_id=presenter.users_id)
        # Création d'un nouveau présentateur avec tous les champs
        presenter_db = Presenter(
            name=presenter.name,
            biography=presenter.biography,
            contact_info=presenter.contact_info,
            users_id=presenter.users_id,
            # profile_picture=presenter.profilePicture,
            # is_main_presenter=presenter.isMainPresenter
        )
        db.add(presenter_db)
        db.commit()
        db.refresh(presenter_db)

        # logger.info(f"Presenter '{presenter.name}' created successfully.")
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
        # Récupérer le présentateur avec la relation "user" chargée
        presenter = (
            db.query(Presenter)
            .options(joinedload(Presenter.user))
            .filter(Presenter.id == presenter_id)
            .first()
        )

        if not presenter:
            # raise PresenterNotFoundError()
                # if presenter is None:
            return JSONResponse(
                    status_code=404,
                    content={ "message": "Presenter not found" }
                )

        # Accéder à l'utilisateur associé
        user = presenter.user

        # Sérialiser les données
        serialized_presenter = {
            "id": presenter.id,
            "name": user.username + " " + user.family_name,
            "presenter_name": presenter.name,
            "biography": presenter.biography,
            "is_deleted": presenter.is_deleted,
            "deleted_at": presenter.deleted_at,
            "users_id": presenter.users_id,
            "contact_info": presenter.contact_info,
            "profilePicture": presenter.profilePicture,
            "shows_presented": len(presenter.shows),
            "username": user.username if user else None,
            "user_name": user.name if user else None,
            "family_name": user.family_name if user else None,
            "user_id": user.id if user else None,
        }

        return serialized_presenter
    except Exception as e:
        print({e})
        logger.error(f"Error fetching presenter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching presenter")




def get_presenter_by_user(db: Session, users_id: int):
    """
    Récupérer un présentateur spécifique de la base de données par son users_id.
    
    Args:
        db (Session): La session de la base de données.
        users_id (int): L'ID de l'utilisateur associé au présentateur.
    
    Returns:
        dict: Le présentateur sérialisé avec les détails de l'utilisateur associé.
    
    Raises:
        HTTPException: Si le présentateur n'est pas trouvé ou en cas d'erreur serveur.
    """
    try:
        # Récupérer le présentateur avec la relation "user" chargée, filtré par users_id
        presenter = (
            db.query(Presenter)
            .options(joinedload(Presenter.user))
            .filter(Presenter.users_id == users_id)
            .first()
        )

        if not presenter:
            raise HTTPException(status_code=404, detail="Presenter not found for this user")

        # Accéder à l'utilisateur associé
        user = presenter.user

        # Sérialiser les données
        serialized_presenter = {
            "id": presenter.id,
            "name": f"{user.username} {user.family_name}" if user else presenter.name,
            "presenter_name": presenter.name,
            "biography": presenter.biography,
            "is_deleted": presenter.is_deleted,
            "deleted_at": presenter.deleted_at,
            "users_id": presenter.users_id,
            "contact_info": presenter.contact_info,
            "profilePicture": presenter.profilePicture,
            "shows_presented": len(presenter.shows) if presenter.shows else 0,
            "username": user.username if user else None,
            "user_name": user.name if user else None,
            "family_name": user.family_name if user else None,
            "user_id": user.id if user else None,
        }

        return serialized_presenter
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching presenter by user_id: {e}")
        raise HTTPException(status_code=500, detail="Error fetching presenter")





def get_all_presenters(db: Session, skip: int = 0, limit: int = 10):
    """
    Récupérer tous les présentateurs de la base de données avec pagination.  -> PresenterResponsePaged
    
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
# Alias pour éviter les conflits
        UserAlias = aliased(User, name="user_alias")
        stmt = (
            select(Presenter, UserAlias)
            .join(UserAlias, Presenter.users_id == UserAlias.id)
            .filter(Presenter.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        results = db.execute(stmt).all()

        # Sérialiser chaque résultat
        serialized_results = []
        for presenter , user in results:
            # user = presenter.user
            # presenter = presenter_and_count

            # Créer un dictionnaire pour chaque résultat
            serialized_presenter ={
                "id": presenter.id,
                "name": user.username + " " + user.family_name,
                "biography": presenter.biography,
                "is_deleted": presenter.is_deleted,
                "deleted_at": presenter.deleted_at,
                "users_id": presenter.users_id,
                "contact_info": presenter.contact_info,
                "profilePicture": presenter.profilePicture,
                "shows_presented": len(presenter.shows),
                "username": user.username if user else None,
                "presenter_name": presenter.name,
                "user_name": user.name if user else None,
                "family_name": user.family_name if user else None,
                "user_id": user.id if user else None,
            }
            serialized_results.append(serialized_presenter)
           
            
                  

        return {
            "total": total_presenters,
            "presenters": serialized_results,
        }



    except Exception as e:
            print({e})  
            logger.error(f"Error fetching presenters with 00: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching presenters with 001",
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

def get_deleted_presenters(db: Session, skip: int = 0, limit: int = 10):
    """
    Récupérer tous les présentateurs supprimés (is_deleted=True) avec pagination.
    """
    return (
        db.query(Presenter)
          .filter(Presenter.is_deleted == True)
          .offset(skip)
          .limit(limit)
          .all()
    )

from fastapi import HTTPException
from starlette import status
from app.models.model_presenter import Presenter
from app.schemas.schema_presenters import PresenterCreate
from app.db.crud.crud_presenters import create_presenter  # éviter recursion

def assign_presenter(db: Session, presenter: PresenterCreate):
    """
    Assigne un statut de présentateur à un utilisateur.
    Réactive si supprimé, sinon crée un nouvel enregistrement.
    """
    existing_by_name = db.query(Presenter).filter(Presenter.name == presenter.name).first()
    if existing_by_name:
        # Si soft-deleted, on réactive uniquement le flag et la date
        if existing_by_name.is_deleted:
            existing_by_name.is_deleted = False
            existing_by_name.deleted_at = None
            db.commit()
            db.refresh(existing_by_name)
            return existing_by_name
        # Sinon, déléguer à create_presenter pour gérer le conflit ou autre
        return create_presenter(db, presenter)
    #si Presenter.user_id==presenter.user_id
    existing_by_user = db.query(Presenter).filter(Presenter.users_id == presenter.users_id).first()
    if existing_by_user:
        # Si soft-deleted, on réactive uniquement le flag et la date
        if existing_by_user.is_deleted:
            existing_by_user.is_deleted = False
            existing_by_user.deleted_at = None
            db.commit()
            db.refresh(existing_by_user)
            return existing_by_user
        # Sinon, déléguer à create_presenter pour gérer le conflit ou autre
        return create_presenter(db, presenter)      

    return create_presenter(db, presenter)


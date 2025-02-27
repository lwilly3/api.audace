# main.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, FastAPI, Depends,HTTPException
from app.db.crud.crud_role_permissions import  get_role_permissions
from app.db.crud.crud_roles import get_all_roles, get_role, create_role, update_role, delete_role
from app.db.crud.crud_permissions import get_all_permissions, get_permission
# from models.model_role import Role
from app.schemas import RoleRead, Permission
from core.auth import oauth2
from app.db.database import get_db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status
from app.db.crud.crud_permissions import update_user_permissions
from app.models.model_user import User






    # get_all_roles, get_role, create_role, update_role, delete_role, get_role_permissions,
    # get_all_permissions, get_permission


router=APIRouter(
    prefix="/permissions",
    tags=['permissions']
)
# Routes pour les rôles
@router.get("/roles", response_model=List[RoleRead])
def get_all_roles_route( current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer tous les rôles non supprimés.
    """
    return get_all_roles()


@router.get("/roles/{id}", response_model=RoleRead)
def get_role_route(id: int,  current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer un rôle spécifique.
    """
    return get_role(id)


@router.post("/roles", response_model=RoleRead)
def create_role_route(name: str, description: Optional[str] = None, permissions: List[int] = [], current_user: int = Depends(oauth2.get_current_user)):
    """
    Créer un nouveau rôle.
    """
    return create_role(name, description, permissions)


@router.put("/roles/{id}", response_model=RoleRead)
def update_role_route(id: int, name: Optional[str] = None, description: Optional[str] = None, permissions: Optional[List[int]] = None,  current_user: int = Depends(oauth2.get_current_user)):
    """
    Mettre à jour un rôle existant.
    """
    return update_role(id, name, description, permissions)


@router.delete("/roles/{id}")
def delete_role_route(id: int,  current_user: int = Depends(oauth2.get_current_user)):
    """
    Supprimer un rôle (soft delete).
    """
    return delete_role(id)


@router.get("/roles/{id}/permissions", response_model=List[Permission])
def get_role_permissions_route(id: int,  current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer les permissions associées à un rôle.
    """
    return get_role_permissions(id)


# Routes pour les permissions
@router.get("/permissions", response_model=List[Permission])
def get_all_permissions_route( current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer toutes les permissions disponibles.
    """
    return get_all_permissions()


@router.get("/permissions/{id}", response_model=Permission)
def get_permission_route(id: int,  current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer une permission spécifique.
    """
    return get_permission(id)



#/////////////////////////////////////////////////////////
   # update Permissions pour les Users
#/////////////////////////////////////////////////////////


# from fastapi import FastAPI, Depends, HTTPException
# from app.db.database import get_db
# from app.services.user_permissions_service import update_user_permissions
# from sqlalchemy.orm import Session
# from starlette import status



@router.put("/update_permissions/{user_id}")
def update_user_permissions_route(user_id: int, permissions: dict, userConnected: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    """
    Met à jour les permissions d'un utilisateur spécifique.
    
    Args:
        user_id (int): Identifiant de l'utilisateur.
        permissions (dict): Dictionnaire des permissions à modifier (ex. {"can_edit_users": true}).
        db (Session): Session de base de données injectée via Depends.
    
    Returns:
        dict: Message de succès.
    
    Raises:
        HTTPException: Avec un code d'erreur approprié en cas d'échec.
    """
    # user_id = userId.id

    try:
        result = update_user_permissions(db, user_id, permissions, userConnected.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne s'est produite : {str(e)}"
        )
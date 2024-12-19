# main.py
from typing import List, Optional
from fastapi import APIRouter, FastAPI, Depends
from app.db.crud.crud_role_permissions import  get_role_permissions
from app.db.crud.crud_roles import get_all_roles, get_role, create_role, update_role, delete_role
from app.db.crud.crud_permissions import get_all_permissions, get_permission
# from models.model_role import Role
from app.schemas import RoleRead, Permission
from core.auth import oauth2
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




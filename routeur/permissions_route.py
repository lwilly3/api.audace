# main.py
from typing import List, Optional,Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, FastAPI, Depends,HTTPException
from app.db.crud.crud_role_permissions import  get_role_permissions
from app.db.crud.crud_roles import get_all_roles, get_role, create_role, update_role, delete_role
from app.db.crud.crud_permissions import get_all_permissions, get_permission,get_user_permissions,check_permissions
# from models.model_role import Role
from app.schemas import RoleRead, Permission,RoleCreate,Role_Read,RoleUpdate
from core.auth import oauth2
from app.db.database import get_db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status
from app.db.crud.crud_permissions import update_user_permissions
from app.models.model_user import User

    # from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List, Dict, Any
# from app.db.database import get_db
# from app.oauth2 import get_current_user
from app.models.model_user import User
from app.db.crud.crud_role_template import (
    create_role_template, get_role_template, get_all_role_templates,
    update_role_template, delete_role_template, apply_role_template
    
)
from app.schemas.schema_permissions import (
    RoleTemplateCreate, RoleTemplateUpdate, RoleTemplateResponse
)





    # get_all_roles, get_role, create_role, update_role, delete_role, get_role_permissions,
    # get_all_permissions, get_permission


router=APIRouter(
    prefix="/permissions",
    tags=['permissions']
)


@router.get("/users/{user_id}", response_model=Dict[str, Any])
def get_user_permissions_route(user_id: int, db: Session = Depends(get_db)):
    """
    Récupère les permissions d'un utilisateur spécifique.

    Args:
        user_id (int): Identifiant de l'utilisateur.
        db (Session): Session de base de données injectée via Depends.

    Returns:
        dict: Dictionnaire contenant les permissions de l'utilisateur.

    Raises:
        HTTPException: Avec un code d'erreur approprié en cas d'échec (400, 404, 500).
    """
    try:
        permissions = get_user_permissions(db, user_id)
        if "error" in permissions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=permissions["error"])
        return permissions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Une erreur interne s'est produite : {str(e)}")




# Routes pour les rôles
@router.get("/roles", response_model=List[Role_Read])
def get_all_roles_route( current_user: int = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    """
    Récupérer tous les rôles non supprimés.
    """
    roles = get_all_roles(db)
    return roles if roles is not None else []


@router.get("/roles/{id}", response_model=RoleRead)
def get_role_route(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    return get_role(id, db)


@router.post("/roles", response_model=Role_Read)
def create_role_route(
    role: RoleCreate,
    current_user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau rôle.
    """
    return create_role(db, role)


@router.put("/roles/{id}", response_model=Role_Read)

def update_role_route(id: int, role_update: RoleUpdate,  current_user: int = Depends(oauth2.get_current_user),db: Session = Depends(get_db)):
    """
    Mettre à jour un rôle existant.
    """
    return update_role(db, id, role_update)


@router.delete("/roles/{id}")
def delete_role_route(id: int,  current_user: int = Depends(oauth2.get_current_user),db: Session = Depends(get_db)):
    """
    Supprimer un rôle (soft delete).
    """
    return delete_role(db,id)


@router.get("/roles/{id}/permissions", response_model=List[Permission])
def get_role_permissions_route(id: int,  current_user: int = Depends(oauth2.get_current_user),db: Session = Depends(get_db)):
    """
    Récupérer les permissions associées à un rôle.
    """
    return get_role_permissions(db,id)


# Routes pour les permissions
@router.get("/permissions", response_model=List[Permission])
def get_all_permissions_route( current_user: int = Depends(oauth2.get_current_user),db: Session = Depends(get_db)):
    """
    Récupérer toutes les permissions disponibles.
    """
    return get_all_permissions(db)


@router.get("/permissions/{id}", response_model=Permission)
def get_permission_route(id: int,  current_user: int = Depends(oauth2.get_current_user),db: Session = Depends(get_db)):
    """
    Récupérer une permission spécifique.
    """
    return get_permission(id,db)



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
        print("//////////////")
        print(permissions)
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
    


@router.patch("/users/{user_id}/patch_selected_permissions", response_model=Dict[str, Any], dependencies=[Depends(check_permissions)])
def patch_selected_permissions(
    user_id: int,
    permissions: Dict[str, bool],
    current_user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour uniquement un sous-ensemble de permissions pour l'utilisateur :
    can_acces_showplan_section, can_create_showplan,
    can_changestatus_owned_showplan, can_delete_showplan,
    can_edit_showplan, can_archive_showplan,
    can_acces_guests_section, can_view_guests,
    can_edit_guests, can_view_archives
    """
    allowed = {
        'can_acces_showplan_section', 'can_create_showplan', 'can_changestatus_owned_showplan',
        'can_delete_showplan', 'can_edit_showplan', 'can_archive_showplan',
        'can_acces_guests_section', 'can_view_guests', 'can_edit_guests', 'can_view_archives'
    }
    invalid = [p for p in permissions.keys() if p not in allowed]
    if invalid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Permissions invalides pour ce endpoint : {invalid}")
    # Appel à la fonction CRUD existante pour l'opération partielle
    return update_user_permissions(db, user_id, permissions, current_user.id)


    # /////////////////////////////////////////////////////////////////////

            # gestion template permissions des utilisateurs


    #/////////////////////////////////////////////////////////




# router = APIRouter(prefix="/permissions", tags=["Permissions"])



@router.post("/templates", response_model=RoleTemplateResponse)
def create_role_template_route(
    template: RoleTemplateCreate,
    user: User = Depends(check_permissions),
    db: Session = Depends(get_db)
):
    """Crée un nouveau modèle de rôle."""
    try:
        db_template = create_role_template(db, template)
        return db_template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/templates/{template_id}", response_model=RoleTemplateResponse)
def get_role_template_route(
    template_id: str,
    user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère un modèle de rôle par son ID."""
    try:
        return get_role_template(db, template_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/templates", response_model=List[RoleTemplateResponse])
def get_all_role_templates_route(
    user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère tous les modèles de rôles."""
    return get_all_role_templates(db)

@router.put("/templates/{template_id}", response_model=RoleTemplateResponse)
def update_role_template_route(
    template_id: str,
    template_update: RoleTemplateUpdate,
    user: User = Depends(check_permissions),
    db: Session = Depends(get_db)
):
    """Met à jour un modèle de rôle existant."""
    try:
        return update_role_template(db, template_id, template_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/templates/{template_id}", response_model=Dict[str, Any])
def delete_role_template_route(
    template_id: str,
    user: User = Depends(check_permissions),
    db: Session = Depends(get_db)
):
    """Supprime un modèle de rôle."""
    try:
        return delete_role_template(db, template_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/apply_template/{user_id}", response_model=Dict[str, Any])
def apply_role_template_route(
    user_id: int,
    template_id: str,
    user: User = Depends(check_permissions),
    db: Session = Depends(get_db)
):
    """Applique un modèle de rôle à un utilisateur."""
    try:
        return apply_role_template(db, user_id, template_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Route existante pour mettre à jour les permissions directement
@router.put("/update_permissions/{user_id}", response_model=Dict[str, Any])
def update_user_permissions_route(
    user_id: int,
    permissions: Dict[str, bool],
    user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les permissions d'un utilisateur spécifique."""
    try:
        return update_user_permissions(db, user_id, permissions, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Route existante pour récupérer les permissions
# @router.get("/users/{user_id}", response_model=Dict[str, Any])
# def get_user_permissions_route(
#     user_id: int,
#     user: User = Depends(oauth2.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Récupère les permissions d'un utilisateur."""
#     try:
#         return get_user_permissions(db, user_id)
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
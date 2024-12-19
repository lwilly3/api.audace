
from typing import List
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_roles import create_role, get_role, update_role, delete_role
# from app.db.crud.crud_role_permissions import create_permission
# import app.schemas. as schemas
import app.db.crud as crud
from app.schemas import RoleCreate, RoleRead, RoleUpdate, Permission ,PermissionCreate
# from app.db.crud.crud_roles import delete_role
from app.db.crud.crud_roles import add_role_to_user, remove_role_from_user  # Importer les fonctions CRUD
from core.auth import oauth2


router=APIRouter(
    prefix="/role",
    tags=['Role']
)


# Routes des rôles
@router.post("/roles/", response_model=RoleCreate)
def create_role(role: RoleCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Crée un rôle dans la base de données.
    La requête attend un objet 'RoleCreate' pour créer un nouveau rôle.
    """
    try:
        return create_role(db=db, role=role)  # Appelle la fonction CRUD pour créer un rôle
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création du rôle: {e}")  # Gère les erreurs

@router.get("/roles/{role_id}", response_model=RoleRead)
def get_role(role_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère un rôle par son ID.
    Si le rôle n'est pas trouvé, une exception est levée.
    """
    try:
        db_role = get_role(db=db, role_id=role_id)
        if db_role is None:
            raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
        return db_role
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

@router.get("/roles", response_model=List[RoleRead])
def get_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère une liste de rôles avec pagination.
    'skip' et 'limit' sont utilisés pour la pagination.
    """
    try:
        return get_roles(db=db, skip=skip, limit=limit)  # Appelle la fonction CRUD pour obtenir les rôles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

@router.put("/roles/{role_id}", response_model=RoleUpdate)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Met à jour un rôle existant avec de nouvelles informations.
    Si le rôle n'existe pas, une exception est levée.
    """
    try:
        db_role = update_role(db=db, role_id=role_id, role=role)
        if db_role is None:
            raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
        return db_role
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Supprime un rôle de la base de données.
    Si le rôle n'existe pas, une exception est levée.
    """
    try:
        db_role = delete_role(db=db, role_id=role_id)
        if db_role is None:
            raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
        return {"detail": "Role deleted successfully"}  # Retourne un message de succès
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

# Routes des permissions
@router.post("/permissions/", response_model=Permission)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Crée une nouvelle permission dans la base de données.
    """
    try:
        return create_permission(db=db, permission=permission)  # Appelle la fonction CRUD pour créer la permission
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création de la permission: {e}")  # Gère les erreurs

@router.get("/permissions/{permission_id}", response_model=Permission)
def get_permission(permission_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère une permission par son ID.
    Si la permission n'existe pas, une exception est levée.
    """
    try:
        db_permission = get_permission(db=db, permission_id=permission_id)
        if db_permission is None:
            raise HTTPException(status_code=404, detail="Permission not found")  # Si la permission n'existe pas
        return db_permission
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur







# Ajouter un rôle à un utilisateur
@router.post("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_201_CREATED)
def add_role_to_user_route(user_id: int, role_name: str, db: Session = Depends(get_db)):
    """
    Ajoute un rôle à un utilisateur.
    
    Args:
    - user_id (int): L'identifiant de l'utilisateur.
    - role_name (str): Le nom du rôle à ajouter.
    - db (Session): La session de la base de données.
    
    Returns:
    - User: L'utilisateur avec son rôle ajouté.
    """
    return add_role_to_user(user_id, role_name, db)


# Supprimer un rôle d'un utilisateur
@router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_200_OK)
def remove_role_from_user_route(user_id: int, role_name: str, db: Session = Depends(get_db)):
    """
    Supprime un rôle d'un utilisateur.
    
    Args:
    - user_id (int): L'identifiant de l'utilisateur.
    - role_name (str): Le nom du rôle à supprimer.
    - db (Session): La session de la base de données.
    
    Returns:
    - User: L'utilisateur avec son rôle supprimé.
    """
    return remove_role_from_user(user_id, role_name, db)














# from fastapi import FastAPI, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel

# app = FastAPI()

# # Simulated databases
# roles_db = {}  # Database pour les rôles
# permissions_db = {}  # Database pour les permissions

# # Models
# class Role(BaseModel):
#     """
#     Modèle pour représenter un rôle.
#     """
#     id: int
#     name: str
#     description: Optional[str] = None
#     permissions: List[int]  # Liste des IDs des permissions
#     is_deleted: bool = False


# class Permission(BaseModel):
#     """
#     Modèle pour représenter une permission.
#     """
#     id: int
#     name: str
#     description: Optional[str] = None


# # Routes pour les rôles
# @app.get("/roles", response_model=List[Role])
# def get_all_roles():
#     """
#     Récupérer tous les rôles non supprimés.
#     """
#     return [role for role in roles_db.values() if not role.is_deleted]


# @app.get("/roles/{id}", response_model=Role)
# def get_role(id: int):
#     """
#     Récupérer un rôle spécifique.
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     return role


# @app.post("/roles", response_model=Role)
# def create_role(name: str, description: Optional[str] = None, permissions: List[int] = []):
#     """
#     Créer un nouveau rôle.
#     """
#     role_id = len(roles_db) + 1
#     new_role = Role(id=role_id, name=name, description=description, permissions=permissions)
#     roles_db[role_id] = new_role
#     return new_role


# @app.put("/roles/{id}", response_model=Role)
# def update_role(id: int, name: Optional[str] = None, description: Optional[str] = None, permissions: Optional[List[int]] = None):
#     """
#     Mettre à jour un rôle existant.
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     if name:
#         role.name = name
#     if description:
#         role.description = description
#     if permissions is not None:
#         role.permissions = permissions
#     return role


# @app.delete("/roles/{id}")
# def delete_role(id: int):
#     """
#     Supprimer un rôle (soft delete).
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     role.is_deleted = True
#     return {"detail": f"Role {id} deleted successfully"}


# @app.get("/roles/{id}/permissions", response_model=List[Permission])
# def get_role_permissions(id: int):
#     """
#     Récupérer les permissions associées à un rôle.
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     return [permissions_db[perm_id] for perm_id in role.permissions if perm_id in permissions_db]


# # Routes pour les permissions
# @app.get("/permissions", response_model=List[Permission])
# def get_all_permissions():
#     """
#     Récupérer toutes les permissions disponibles.
#     """
#     return list(permissions_db.values())


# @app.get("/permissions/{id}", response_model=Permission)
# def get_permission(id: int):
#     """
#     Récupérer une permission spécifique.
#     """
#     permission = permissions_db.get(id)
#     if not permission:
#         raise HTTPException(status_code=404, detail="Permission not found")
#     return permission


# # Ajout de permissions de base (Simulation)
# permissions_db[1] = Permission(id=1, name="Create User", description="Permission to create a user")
# permissions_db[2] = Permission(id=2, name="Delete User", description="Permission to delete a user")
# permissions_db[3] = Permission(id=3, name="Update User", description="Permission to update a user")
# permissions_db[4] = Permission(id=4, name="View Reports", description="Permission to view reports")


from typing import List
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_roles import (
    create_role, update_role, delete_role, get_role_by_id, get_all_roles,
    list_user_roles, remove_roles_from_user, assign_roles_to_user,
    get_user_max_hierarchy, count_users_with_role
)
from app.models.model_role import Role, BUILTIN_ROLE_NAMES
from app.models.model_RoleTemplate import RoleTemplate
from app.models.model_user_permissions import UserPermissions
import app.db.crud as crud
from app.schemas import RoleCreate, RoleRead, RoleUpdate, Permission ,PermissionCreate,UserRoleAssign,UserSrearchResponse
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action
import logging

logger = logging.getLogger(__name__)


router=APIRouter(
    prefix="/roles",
    tags=['Role']
)




# Créer un rôle
@router.post("/", response_model=RoleRead, status_code=201)
def create_role_route(role: RoleCreate, db: Session = Depends(get_db)):
    """
    Créer un nouveau rôle.
    """
    db_role = create_role(db, role)
    if not db_role:
        raise HTTPException(status_code=400, detail="Role creation failed (possibly duplicate name)")
    log_action(db, 0, "create", "roles", db_role.id)
    return db_role

# Lister tous les rôles response_model=List[RoleRead]
@router.get("/all", )
def list_roles_route(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lister tous les rôles avec pagination.
    """
    roles = get_all_roles(db, skip=skip, limit=limit)
    return roles

# Récupérer un rôle par ID response_model=RoleRead
@router.get("/id/{role_id}", )
def get_role_route(role_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un rôle spécifique par son ID.
    """
    db_role = get_role_by_id(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

# Mettre à jour un rôle
@router.put("/update/{role_id}", response_model=RoleRead)
def update_role_route(role_id: int, role_update: RoleUpdate, db: Session = Depends(get_db)):
    """
    Mettre à jour un rôle existant. Les rôles système ne peuvent pas être renommés.
    """
    existing_role = get_role_by_id(db, role_id)
    if existing_role and existing_role.name in BUILTIN_ROLE_NAMES:
        raise HTTPException(status_code=403, detail="Les roles systeme ne peuvent pas etre modifies")
    db_role = update_role(db, role_id, role_update)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found or update failed (possibly duplicate name)")
    log_action(db, 0, "update", "roles", role_id)
    return db_role

# Supprimer un rôle
@router.delete("/del/{role_id}", status_code=204)
def delete_role_route(role_id: int, db: Session = Depends(get_db)):
    """
    Supprimer un rôle par son ID. Les rôles système ne peuvent pas être supprimés.
    """
    existing_role = get_role_by_id(db, role_id)
    if existing_role and existing_role.name in BUILTIN_ROLE_NAMES:
        raise HTTPException(status_code=403, detail="Les roles systeme ne peuvent pas etre supprimes")
    success = delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    log_action(db, 0, "delete", "roles", role_id)
    return None  # 204 No Content ne retourne pas de corps




# //////////////////////////// assigne roles ///////////////



# Assigner des rôles à un utilisateur avec protection hierarchique
@router.post("/assign/{user_id}", response_model=UserSrearchResponse)
def assign_roles_route(
    user_id: int,
    role_assign: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """
    Assigner un ou plusieurs rôles à un utilisateur.
    Verifie que l'acteur a un niveau superieur aux roles assignes.
    """
    actor_level = get_user_max_hierarchy(db, current_user.id)

    # Verifier que les roles a assigner ont un niveau < a celui de l'acteur
    roles_to_assign = db.query(Role).filter(Role.id.in_(role_assign.role_ids)).all()
    for role in roles_to_assign:
        if role.hierarchy_level >= actor_level:
            raise HTTPException(
                status_code=403,
                detail=f"Vous ne pouvez pas assigner le role '{role.name}' (niveau {role.hierarchy_level})"
            )

    user = assign_roles_to_user(db, user_id, role_assign.role_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found or invalid role IDs")

    # Auto-application du template de permissions pour le role de plus haut niveau
    highest_role = max(roles_to_assign, key=lambda r: r.hierarchy_level)
    template = db.query(RoleTemplate).filter(RoleTemplate.name == highest_role.name).first()
    if template:
        user_perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
        if user_perms:
            for perm, value in template.permissions.items():
                if hasattr(user_perms, perm):
                    setattr(user_perms, perm, value)
            db.commit()
            logger.info(f"Template '{template.name}' auto-applique a l'utilisateur {user_id}")

    log_action(db, current_user.id, "assign_roles", "user_roles", user_id)
    return user

# Retirer des rôles d'un utilisateur avec protection hierarchique
@router.post("/unassign/{user_id}")
def remove_roles_route(
    user_id: int,
    role_remove: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """
    Retirer un ou plusieurs rôles d'un utilisateur.
    Protege le dernier super_admin.
    """
    actor_level = get_user_max_hierarchy(db, current_user.id)

    # Verifier que les roles a retirer ont un niveau < a celui de l'acteur
    roles_to_remove = db.query(Role).filter(Role.id.in_(role_remove.role_ids)).all()
    for role in roles_to_remove:
        if role.hierarchy_level >= actor_level:
            raise HTTPException(
                status_code=403,
                detail=f"Vous ne pouvez pas retirer le role '{role.name}'"
            )
        # Protection dernier super_admin
        if role.name == "super_admin":
            sa_count = count_users_with_role(db, "super_admin")
            if sa_count <= 1:
                raise HTTPException(
                    status_code=403,
                    detail="Impossible de retirer le role super_admin du dernier super administrateur"
                )

    user = remove_roles_from_user(db, user_id, role_remove.role_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    log_action(db, current_user.id, "unassign_roles", "user_roles", user_id)
    return user

# Lister les rôles d'un utilisateur , response_model=List[RoleRead]
@router.get("/all_assigned/{user_id}")
def list_user_roles_route(user_id: int, db: Session = Depends(get_db)):
    """
    Lister tous les rôles associés à un utilisateur.
    """
    roles = list_user_roles(db, user_id)
    if roles is None:
        raise HTTPException(status_code=404, detail="User not found")
    return roles











# ////////////////////////// end assigne roles ///////////////






# # Routes des rôles
# @router.post("/roles/", response_model=RoleCreate)
# def create_role(role: RoleCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Crée un rôle dans la base de données.
#     La requête attend un objet 'RoleCreate' pour créer un nouveau rôle.
#     """
#     try:
#         return create_role(db=db, role=role)  # Appelle la fonction CRUD pour créer un rôle
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Erreur lors de la création du rôle: {e}")  # Gère les erreurs

# @router.get("/roles/{role_id}", response_model=RoleRead)
# def get_role(role_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Récupère un rôle par son ID.
#     Si le rôle n'est pas trouvé, une exception est levée.
#     """
#     try:
#         db_role = get_role(db=db, role_id=role_id)
#         if db_role is None:
#             raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
#         return db_role
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

# @router.get("/roles", response_model=List[RoleRead])
# def get_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Récupère une liste de rôles avec pagination.
#     'skip' et 'limit' sont utilisés pour la pagination.
#     """
#     try:
#         return get_roles(db=db, skip=skip, limit=limit)  # Appelle la fonction CRUD pour obtenir les rôles
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

# @router.put("/roles/{role_id}", response_model=RoleUpdate)
# def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Met à jour un rôle existant avec de nouvelles informations.
#     Si le rôle n'existe pas, une exception est levée.
#     """
#     try:
#         db_role = update_role(db=db, role_id=role_id, role=role)
#         if db_role is None:
#             raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
#         return db_role
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

# @router.delete("/roles/{role_id}")
# def delete_role(role_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Supprime un rôle de la base de données.
#     Si le rôle n'existe pas, une exception est levée.
#     """
#     try:
#         db_role = delete_role(db=db, role_id=role_id)
#         if db_role is None:
#             raise HTTPException(status_code=404, detail="Role not found")  # Si le rôle n'existe pas
#         return {"detail": "Role deleted successfully"}  # Retourne un message de succès
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur

# # Routes des permissions
# @router.post("/permissions/", response_model=Permission)
# def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Crée une nouvelle permission dans la base de données.
#     """
#     try:
#         return create_permission(db=db, permission=permission)  # Appelle la fonction CRUD pour créer la permission
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Erreur lors de la création de la permission: {e}")  # Gère les erreurs

# @router.get("/permissions/{permission_id}", response_model=Permission)
# def get_permission(permission_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
#     """
#     Récupère une permission par son ID.
#     Si la permission n'existe pas, une exception est levée.
#     """
#     try:
#         db_permission = get_permission(db=db, permission_id=permission_id)
#         if db_permission is None:
#             raise HTTPException(status_code=404, detail="Permission not found")  # Si la permission n'existe pas
#         return db_permission
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")  # Gestion des erreurs de serveur







# # Ajouter un rôle à un utilisateur
# @router.post("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_201_CREATED)
# def add_role_to_user_route(user_id: int, role_name: str, db: Session = Depends(get_db)):
#     """
#     Ajoute un rôle à un utilisateur.
    
#     Args:
#     - user_id (int): L'identifiant de l'utilisateur.
#     - role_name (str): Le nom du rôle à ajouter.
#     - db (Session): La session de la base de données.
    
#     Returns:
#     - User: L'utilisateur avec son rôle ajouté.
#     """
#     return add_role_to_user(user_id, role_name, db)


# # Supprimer un rôle d'un utilisateur
# @router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_200_OK)
# def remove_role_from_user_route(user_id: int, role_name: str, db: Session = Depends(get_db)):
#     """
#     Supprime un rôle d'un utilisateur.
    
#     Args:
#     - user_id (int): L'identifiant de l'utilisateur.
#     - role_name (str): Le nom du rôle à supprimer.
#     - db (Session): La session de la base de données.
    
#     Returns:
#     - User: L'utilisateur avec son rôle supprimé.
#     """
#     return remove_role_from_user(user_id, role_name, db)














# # from fastapi import FastAPI, HTTPException
# # from typing import List, Optional
# # from pydantic import BaseModel

# # app = FastAPI()

# # # Simulated databases
# # roles_db = {}  # Database pour les rôles
# # permissions_db = {}  # Database pour les permissions

# # # Models
# # class Role(BaseModel):
# #     """
# #     Modèle pour représenter un rôle.
# #     """
# #     id: int
# #     name: str
# #     description: Optional[str] = None
# #     permissions: List[int]  # Liste des IDs des permissions
# #     is_deleted: bool = False


# # class Permission(BaseModel):
# #     """
# #     Modèle pour représenter une permission.
# #     """
# #     id: int
# #     name: str
# #     description: Optional[str] = None


# # # Routes pour les rôles
# # @app.get("/roles", response_model=List[Role])
# # def get_all_roles():
# #     """
# #     Récupérer tous les rôles non supprimés.
# #     """
# #     return [role for role in roles_db.values() if not role.is_deleted]


# # @app.get("/roles/{id}", response_model=Role)
# # def get_role(id: int):
# #     """
# #     Récupérer un rôle spécifique.
# #     """
# #     role = roles_db.get(id)
# #     if not role or role.is_deleted:
# #         raise HTTPException(status_code=404, detail="Role not found")
# #     return role


# # @app.post("/roles", response_model=Role)
# # def create_role(name: str, description: Optional[str] = None, permissions: List[int] = []):
# #     """
# #     Créer un nouveau rôle.
# #     """
# #     role_id = len(roles_db) + 1
# #     new_role = Role(id=role_id, name=name, description=description, permissions=permissions)
# #     roles_db[role_id] = new_role
# #     return new_role


# # @app.put("/roles/{id}", response_model=Role)
# # def update_role(id: int, name: Optional[str] = None, description: Optional[str] = None, permissions: Optional[List[int]] = None):
# #     """
# #     Mettre à jour un rôle existant.
# #     """
# #     role = roles_db.get(id)
# #     if not role or role.is_deleted:
# #         raise HTTPException(status_code=404, detail="Role not found")
# #     if name:
# #         role.name = name
# #     if description:
# #         role.description = description
# #     if permissions is not None:
# #         role.permissions = permissions
# #     return role


# # @app.delete("/roles/{id}")
# # def delete_role(id: int):
# #     """
# #     Supprimer un rôle (soft delete).
# #     """
# #     role = roles_db.get(id)
# #     if not role or role.is_deleted:
# #         raise HTTPException(status_code=404, detail="Role not found")
# #     role.is_deleted = True
# #     return {"detail": f"Role {id} deleted successfully"}


# # @app.get("/roles/{id}/permissions", response_model=List[Permission])
# # def get_role_permissions(id: int):
# #     """
# #     Récupérer les permissions associées à un rôle.
# #     """
# #     role = roles_db.get(id)
# #     if not role or role.is_deleted:
# #         raise HTTPException(status_code=404, detail="Role not found")
# #     return [permissions_db[perm_id] for perm_id in role.permissions if perm_id in permissions_db]


# # # Routes pour les permissions
# # @app.get("/permissions", response_model=List[Permission])
# # def get_all_permissions():
# #     """
# #     Récupérer toutes les permissions disponibles.
# #     """
# #     return list(permissions_db.values())


# # @app.get("/permissions/{id}", response_model=Permission)
# # def get_permission(id: int):
# #     """
# #     Récupérer une permission spécifique.
# #     """
# #     permission = permissions_db.get(id)
# #     if not permission:
# #         raise HTTPException(status_code=404, detail="Permission not found")
# #     return permission


# # # Ajout de permissions de base (Simulation)
# # permissions_db[1] = Permission(id=1, name="Create User", description="Permission to create a user")
# # permissions_db[2] = Permission(id=2, name="Delete User", description="Permission to delete a user")
# # permissions_db[3] = Permission(id=3, name="Update User", description="Permission to update a user")
# # permissions_db[4] = Permission(id=4, name="View Reports", description="Permission to view reports")

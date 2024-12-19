from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends
from app.models import Role, Permission, RolePermission, User
from app.db.database import get_db
from core.auth import oauth2
# Récupérer tous les rôles
def get_all_roles(db: Session = Depends(get_db)) -> List[Role]:
    try:
        return db.query(Role).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la récupération des rôles")

# Récupérer un rôle par son ID
def get_role(id: int, db: Session) -> Role:
    try:
        role = db.query(Role).filter(Role.id == id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")
        return role
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la récupération du rôle")

# Créer un nouveau rôle
def create_role(name: str, description: Optional[str] = None, permissions: List[int] = [], db: Session = Depends(get_db)) -> Role:
    try:
        # Vérifie si un rôle avec le même nom existe déjà
        if db.query(Role).filter(Role.name == name).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un rôle avec ce nom existe déjà")

        # Crée un nouveau rôle
        new_role = Role(name=name, description=description)
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        # Associe les permissions au rôle
        for permission_id in permissions:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permission avec ID {permission_id} non trouvée")
            new_role.permissions.append(permission)

        db.commit()
        db.refresh(new_role)
        return new_role
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la création du rôle")

# Mettre à jour un rôle
def update_role(id: int, name: Optional[str] = None, description: Optional[str] = None, permissions: Optional[List[int]] = None, db: Session = Depends(get_db)) -> Role:
    try:
        role = db.query(Role).filter(Role.id == id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

        # Met à jour le nom et la description si fournis
        if name:
            role.name = name
        if description:
            role.description = description

        # Met à jour les permissions si fournies
        if permissions is not None:
            role.permissions = []  # Supprime toutes les permissions actuelles
            for permission_id in permissions:
                permission = db.query(Permission).filter(Permission.id == permission_id).first()
                if not permission:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permission avec ID {permission_id} non trouvée")
                role.permissions.append(permission)

        db.commit()
        db.refresh(role)
        return role
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la mise à jour du rôle")

# Supprimer un rôle
def delete_role(id: int, db: Session):
    try:
        role = db.query(Role).filter(Role.id == id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

        # Vérifier si des utilisateurs sont associés à ce rôle
        if db.query(User).filter(User.roles.contains(role)).count() > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de supprimer un rôle attribué à un utilisateur")

        db.delete(role)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la suppression du rôle")

# Récupérer les permissions associées à un rôle
def get_role_permissions(id: int, db: Session) -> List[Permission]:
    try:
        role = db.query(Role).filter(Role.id == id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")
        return role.permissions
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la récupération des permissions du rôle")

# Récupérer toutes les permissions
def get_all_permissions(db: Session) -> List[Permission]:
    try:
        return db.query(Permission).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la récupération des permissions")

# Récupérer une permission par son ID
def get_permission(id: int, db: Session) -> Permission:
    try:
        permission = db.query(Permission).filter(Permission.id == id).first()
        if not permission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission non trouvée")
        return permission
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la récupération de la permission")











# # crud.py
# from fastapi import HTTPException
# from .databases import roles_db, permissions_db
# from .models import Role, Permission
# from typing import List, Optional


# def get_all_roles() -> List[Role]:
#     """
#     Récupérer tous les rôles non supprimés.
#     """
#     return [role for role in roles_db.values() if not role.is_deleted]


# def get_role(id: int) -> Role:
#     """
#     Récupérer un rôle spécifique.
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     return role


# def create_role(name: str, description: Optional[str] = None, permissions: List[int] = []) -> Role:
#     """
#     Créer un nouveau rôle.
#     """
#     role_id = len(roles_db) + 1
#     new_role = Role(id=role_id, name=name, description=description, permissions=permissions)
#     roles_db[role_id] = new_role
#     return new_role


# def update_role(id: int, name: Optional[str] = None, description: Optional[str] = None, permissions: Optional[List[int]] = None) -> Role:
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


# def delete_role(id: int):
#     """
#     Supprimer un rôle (soft delete).
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     role.is_deleted = True
#     return {"detail": f"Role {id} deleted successfully"}


# def get_role_permissions(id: int) -> List[Permission]:
#     """
#     Récupérer les permissions associées à un rôle.
#     """
#     role = roles_db.get(id)
#     if not role or role.is_deleted:
#         raise HTTPException(status_code=404, detail="Role not found")
#     return [permissions_db[perm_id] for perm_id in role.permissions if perm_id in permissions_db]


# def get_all_permissions() -> List[Permission]:
#     """
#     Récupérer toutes les permissions disponibles.
#     """
#     return list(permissions_db.values())


# def get_permission(id: int) -> Permission:
#     """
#     Récupérer une permission spécifique.
#     """
#     permission = permissions_db.get(id)
#     if not permission:
#         raise HTTPException(status_code=404, detail="Permission not found")
#     return permission



















# # from sqlalchemy.orm import Session
# # from app.models.model_permission import Permission
# # from app.schemas.schema_permissions import PermissionCreate, PermissionUpdate

# # def create_permission(db: Session, permission: PermissionCreate):
# #     new_permission = Permission(**permission.dict())
# #     db.add(new_permission)
# #     db.commit()
# #     db.refresh(new_permission)
# #     return new_permission

# # def get_permission(db: Session, permission_id: int):
# #     return db.query(Permission).filter(Permission.id == permission_id).first()

# # def get_permissions(db: Session, skip: int = 0, limit: int = 10):
# #     return db.query(Permission).offset(skip).limit(limit).all()

# # def update_permission(db: Session, permission_id: int, permission_update: PermissionUpdate):
# #     permission = db.query(Permission).filter(Permission.id == permission_id).first()
# #     for key, value in permission_update.dict(exclude_unset=True).items():
# #         setattr(permission, key, value)
# #     db.commit()
# #     db.refresh(permission)
# #     return permission

# # def delete_permission(db: Session, permission_id: int):
# #     permission = db.query(Permission).filter(Permission.id == permission_id).first()
# #     if permission:
# #         db.delete(permission)
# #         db.commit()
# #     return permission

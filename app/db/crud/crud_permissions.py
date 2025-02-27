from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends
from app.models import Role, Permission, RolePermission, User
from app.db.database import get_db
from core.auth import oauth2
from typing import Dict, Any


from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import UserPermissions



def get_user_permissions(db: Session, user_id: int):
    """
    Récupère les permissions d'un utilisateur en fonction de son ID.

    :param db: Session de la base de données
    :param user_id: ID de l'utilisateur
    :return: Un dictionnaire contenant les permissions de l'utilisateur ou un message si l'utilisateur n'a pas de permissions
    """
    try:
        # Requête pour récupérer les permissions de l'utilisateur
        permissions = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()

        if not permissions:
            # Si aucune permission n'est trouvée pour cet utilisateur
            return {"error": f"Aucune permission trouvée pour l'utilisateur avec l'ID {user_id}"}

        # Retourner les permissions sous forme de dictionnaire
        return {
            # "user_id": permissions.user_id,
            "can_create_showplan": permissions.can_create_showplan,
            "can_edit_showplan": permissions.can_edit_showplan,
            "can_archive_showplan": permissions.can_archive_showplan,
            "can_delete_showplan": permissions.can_delete_showplan,
            "can_destroy_showplan": permissions.can_destroy_showplan,
            "can_changestatus_showplan": permissions.can_changestatus_showplan,
            # "granted_at": permissions.granted_at
        }

    except Exception as e:
        # Gestion des erreurs
        raise Exception(f"Une erreur est survenue lors de la récupération des permissions : {str(e)}")



def initialize_user_permissions(db: Session, user_id: int):
    """
    Fonction pour initialiser les permissions de l'utilisateur avec les valeurs par défaut.
    Si une erreur survient, elle est capturée et un message approprié est renvoyé.
    """
    try:
        # Vérifier si l'utilisateur a déjà des permissions
        existing_permissions = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()

        # Si des permissions existent déjà, ne pas les créer à nouveau
        if existing_permissions:
            return existing_permissions

        # Sinon, créer une nouvelle entrée avec les permissions par défaut
        new_permissions = UserPermissions(
            user_id=user_id,
            can_acces_showplan_broadcast_section=False,
            can_acces_showplan_section=False,
            can_create_showplan=False,
            can_edit_showplan=False,
            can_archive_showplan=False,
            can_archiveStatusChange_showplan=False,
            can_delete_showplan=False,
            can_destroy_showplan=False,
            can_changestatus_showplan=False,
            can_changestatus_owned_showplan=False,
            can_changestatus_archived_showplan=False,
            can_setOnline_showplan=False,
            can_viewAll_showplan=False,
            can_acces_users_section=False,
            can_view_users=False,
            can_edit_users=False,
            can_desable_users=False,
            can_delete_users=False,
            can_manage_roles=False,
            can_assign_roles=False,
            can_acces_guests_section=False,
            can_view_guests=False,
            can_edit_guests=False,
            can_delete_guests=False,
            can_acces_presenters_section=False,
            can_view_presenters=False,
            can_edit_presenters=False,
            can_delete_presenters=False,
            can_acces_emissions_section=False,
            can_view_emissions=False,
            can_create_emissions=False,
            can_edit_emissions=False,
            can_delete_emissions=False,
            can_manage_emissions=False,
            can_view_notifications=False,
            can_manage_notifications=False,
            can_view_audit_logs=False,
            can_view_login_history=False,
            can_manage_settings=False,
            can_view_messages=False,
            can_send_messages=False,
            can_delete_messages=False,
            can_view_files=False,
            can_upload_files=False,
            can_delete_files=False
        )
        # Ajouter la nouvelle entrée dans la session de la base de données
        db.add(new_permissions)
        db.commit()
        db.refresh(new_permissions)

        return new_permissions

    except SQLAlchemyError as e:
        # En cas d'erreur lors de l'exécution de la requête SQL
        db.rollback()  # Annuler la transaction si erreur
        raise Exception(f"Une erreur est survenue lors de l'initialisation des permissions : {str(e)}")

    except Exception as e:
        # En cas d'erreur générale
        raise Exception(f"Une erreur inattendue est survenue : {str(e)}")








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




# //////////////////////////////////////////////////////////////////////

         # # metre a jour les permissions de l'utilisateur

# //////////////////////////////////////////////////////////////////////////



def update_user_permissions(db: Session, user_id: int, permissions: Dict[str, bool], userConnected: int) -> Dict[str, Any]:
    """
    Met à jour les permissions d'un utilisateur dans la table user_permissions.
    
    Args:
        db (Session): Session de base de données SQLAlchemy.
        user_id (int): Identifiant de l'utilisateur.
        permissions (Dict[str, bool]): Dictionnaire des permissions à modifier (clé: nom de la permission, valeur: booléen).
    
    Returns:
        Dict[str, Any]: Résultat de l'opération avec un message de succès ou d'erreur.
    
    Raises:
        SQLAlchemyError: Si une erreur de base de données survient.
        ValueError: Si l'utilisateur n'est pas trouvé ou si les permissions sont invalides.
    """
    try:
        # Vérifier si l'utilisateur existe
        user_permission = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
        if not user_permission:
            raise ValueError(f"Aucun enregistrement de permissions trouvé pour l'utilisateur avec l'ID {user_id}")

        # Liste des permissions valides (basée sur le modèle UserPermissions)
        valid_permissions = {
            'can_create_showplan', 'can_edit_showplan', 'can_archive_showplan', 'can_archiveStatusChange_showplan',
            'can_delete_showplan', 'can_destroy_showplan', 'can_changestatus_showplan', 'can_changestatus_owned_showplan',
            'can_changestatus_archived_showplan', 'can_setOnline_showplan', 'can_viewAll_showplan',
            'can_view_users', 'can_edit_users', 'can_desable_users', 'can_delete_users',
            'can_manage_roles', 'can_assign_roles',
            'can_view_guests', 'can_edit_guests', 'can_delete_guests',
            'can_view_presenters', 'can_edit_presenters', 'can_delete_presenters',
            'can_manage_emissions',
            'can_view_notifications', 'can_manage_notifications',
            'can_view_audit_logs', 'can_view_login_history',
            'can_manage_settings',
            'can_view_messages', 'can_send_messages', 'can_delete_messages',
            'can_view_files', 'can_upload_files', 'can_delete_files',

            "can_acces_users_section",   
            "can_acces_emissions_section", "can_view_emissions", "can_create_emissions", "can_edit_emissions", "can_delete_emissions",
            "can_acces_presenters_section",
            "can_acces_guests_section",  "can_acces_showplan_section","can_acces_showplan_broadcast_section",
        }

        # Vérifier les permissions fournies
        invalid_permissions = [perm for perm in permissions.keys() if perm not in valid_permissions]
        if invalid_permissions:
            raise ValueError(f"Permissions invalides : {', '.join(invalid_permissions)}")

        # Mettre à jour les permissions
        for perm, value in permissions.items():
            setattr(user_permission, perm, value)

        db.commit()
        return {"message": f"Permissions mises à jour avec succès pour l'utilisateur"}

    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e
    except ValueError as e:
        db.rollback()
        raise ValueError(f"Erreur de validation : {str(e)}") from e
    except Exception as e:
        db.rollback()
        raise Exception(f"Erreur inattendue : {str(e)}") from e



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

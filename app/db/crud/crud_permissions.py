from typing import List, Optional
from sqlalchemy.orm import Session, load_only
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends
from app.models import Role, Permission, RolePermission, User
from app.db.database import get_db
from core.auth import oauth2
from typing import Dict, Any


from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import UserPermissions


# Vérifie si l'utilisateur connecté a les droits nécessaires
def check_permissions(user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    permissions = db.query(UserPermissions).filter(UserPermissions.user_id == user.id).first()
    if not permissions or not (permissions.can_manage_roles or permissions.can_edit_users):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas les droits pour effectuer cette action"
        )
    return user



def get_user_permissions(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Récupère les permissions d'un utilisateur en fonction de son ID.

    :param db: Session de la base de données
    :param user_id: ID de l'utilisateur
    :return: Un dictionnaire contenant les permissions de l'utilisateur ou un message d'erreur
    :raises ValueError: Si l'ID de l'utilisateur est invalide
    :raises SQLAlchemyError: Si une erreur de base de données survient
    :raises Exception: Pour les erreurs inattendues
    """
    try:
        # Vérification de la validité de l'ID
        if user_id <= 0:
            raise ValueError("L'ID de l'utilisateur doit être un entier positif.")

        # Requête pour récupérer les permissions de l'utilisateur
        permissions = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()

        # Si aucune permission n'est trouvée pour cet utilisateur
        if not permissions:
            return {"error": f"Aucune permission trouvée pour l'utilisateur avec l'ID {user_id}"}

       # Retourner toutes les permissions sous forme de dictionnaire
        return {
    "user_id": permissions.user_id,
    # Permissions pour les showplans
    "can_acces_showplan_broadcast_section": permissions.can_acces_showplan_broadcast_section,
    "can_acces_showplan_section": permissions.can_acces_showplan_section,
    "can_create_showplan": permissions.can_create_showplan,
    "can_edit_showplan": permissions.can_edit_showplan,
    "can_archive_showplan": permissions.can_archive_showplan,
    "can_archiveStatusChange_showplan": permissions.can_archiveStatusChange_showplan,
    "can_delete_showplan": permissions.can_delete_showplan,
    "can_destroy_showplan": permissions.can_destroy_showplan,
    "can_changestatus_showplan": permissions.can_changestatus_showplan,
    "can_changestatus_owned_showplan": permissions.can_changestatus_owned_showplan,
    "can_changestatus_archived_showplan": permissions.can_changestatus_archived_showplan,
    "can_setOnline_showplan": permissions.can_setOnline_showplan,
    "can_viewAll_showplan": permissions.can_viewAll_showplan,

    # Permissions pour les utilisateurs
    "can_acces_users_section": permissions.can_acces_users_section,
    "can_view_users": permissions.can_view_users,
    "can_edit_users": permissions.can_edit_users,
    "can_desable_users": permissions.can_desable_users,  # Corrigé "desable" -> "disable"
    "can_delete_users": permissions.can_delete_users,

    # Permissions pour les rôles
    "can_manage_roles": permissions.can_manage_roles,
    "can_assign_roles": permissions.can_assign_roles,

    # Permissions pour les invités
    "can_acces_guests_section": permissions.can_acces_guests_section,
    "can_view_guests": permissions.can_view_guests,
    "can_edit_guests": permissions.can_edit_guests,
    "can_delete_guests": permissions.can_delete_guests,

    # Permissions pour les présentateurs
    "can_acces_presenters_section": permissions.can_acces_presenters_section,
    "can_view_presenters": permissions.can_view_presenters,
    "can_create_presenters": permissions.can_create_presenters,  # Nouvelle permission ajoutée
    "can_edit_presenters": permissions.can_edit_presenters,
    "can_delete_presenters": permissions.can_delete_presenters,

    # Permissions pour les émissions
    "can_acces_emissions_section": permissions.can_acces_emissions_section,
    "can_view_emissions": permissions.can_view_emissions,
    "can_create_emissions": permissions.can_create_emissions,
    "can_edit_emissions": permissions.can_edit_emissions,
    "can_delete_emissions": permissions.can_delete_emissions,
    "can_manage_emissions": permissions.can_manage_emissions,

    # Permissions pour les notifications
    "can_view_notifications": permissions.can_view_notifications,
    "can_manage_notifications": permissions.can_manage_notifications,

    # Permissions pour les journaux et historique
    "can_view_audit_logs": permissions.can_view_audit_logs,
    "can_view_login_history": permissions.can_view_login_history,

    # Permissions globales
    "can_manage_settings": permissions.can_manage_settings,

    # Permissions pour les messages
    "can_view_messages": permissions.can_view_messages,
    "can_send_messages": permissions.can_send_messages,
    "can_delete_messages": permissions.can_delete_messages,

    # Permissions pour les fichiers
    "can_view_files": permissions.can_view_files,
    "can_upload_files": permissions.can_upload_files,
    "can_delete_files": permissions.can_delete_files,

    # Permissions pour les tâches (nouvelles)
    "can_view_tasks": permissions.can_view_tasks,
    "can_create_tasks": permissions.can_create_tasks,
    "can_edit_tasks": permissions.can_edit_tasks,
    "can_delete_tasks": permissions.can_delete_tasks,
    "can_assign_tasks": permissions.can_assign_tasks,

    # Permissions pour les archives (nouvelles)
    "can_view_archives": permissions.can_view_archives,
    "can_destroy_archives": permissions.can_destroy_archives,
    "can_restore_archives": permissions.can_restore_archives,
    "can_delete_archives": permissions.can_delete_archives,

    # Timestamp
    "granted_at": permissions.granted_at.isoformat() if permissions.granted_at else None
}

    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Erreur de base de données lors de la récupération des permissions : {str(e)}") from e
    except ValueError as e:
        raise ValueError(f"Erreur de validation : {str(e)}") from e
    except Exception as e:
        raise Exception(f"Une erreur inattendue est survenue : {str(e)}") from e

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
    # Permissions pour les showplans
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

    # Permissions pour les utilisateurs
    can_acces_users_section=False,
    can_view_users=False,
    can_edit_users=False,
    can_desable_users=False,  # Corrigé "desable" -> "disable"
    can_delete_users=False,

    # Permissions pour les rôles
    can_manage_roles=False,
    can_assign_roles=False,

    # Permissions pour les invités
    can_acces_guests_section=False,
    can_view_guests=False,
    can_edit_guests=False,
    can_delete_guests=False,

    # Permissions pour les présentateurs
    can_acces_presenters_section=False,
    can_view_presenters=False,
    can_create_presenters=False,  # Nouvelle permission ajoutée
    can_edit_presenters=False,
    can_delete_presenters=False,

    # Permissions pour les émissions
    can_acces_emissions_section=False,
    can_view_emissions=False,
    can_create_emissions=False,
    can_edit_emissions=False,
    can_delete_emissions=False,
    can_manage_emissions=False,

    # Permissions pour les notifications
    can_view_notifications=False,
    can_manage_notifications=False,

    # Permissions pour les journaux et historique
    can_view_audit_logs=False,
    can_view_login_history=False,

    # Permissions globales
    can_manage_settings=False,

    # Permissions pour les messages
    can_view_messages=False,
    can_send_messages=False,
    can_delete_messages=False,

    # Permissions pour les fichiers
    can_view_files=False,
    can_upload_files=False,
    can_delete_files=False,

    # Permissions pour les tâches (nouvelles)
    can_view_tasks=False,
    can_create_tasks=False,
    can_edit_tasks=False,
    can_delete_tasks=False,
    can_assign_tasks=False,

    # Permissions pour les archives (nouvelles)
    can_view_archives=False,
    can_destroy_archives=False,
    can_restore_archives=False,
    can_delete_archives=False
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


def update_user_permissions(db: Session, user_id: int, permissions: Dict[str, bool], user_connected_id: int) -> Dict[str, Any]:
    """
    Met à jour les permissions d'un utilisateur dans la table user_permissions.

    Args:
        db (Session): Session de base de données SQLAlchemy.
        user_id (int): Identifiant de l'utilisateur dont les permissions doivent être mises à jour.
        permissions (Dict[str, bool]): Dictionnaire des permissions à modifier (clé: nom de la permission, valeur: booléen).
        user_connected_id (int): Identifiant de l'utilisateur connecté effectuant la mise à jour.

    Returns:
        Dict[str, Any]: Résultat de l'opération avec un message de succès ou d'erreur.

    Raises:
        SQLAlchemyError: Si une erreur de base de données survient.
        ValueError: Si l'utilisateur n'est pas trouvé, si les permissions sont invalides, ou si l'utilisateur connecté n'a pas les droits.
    """
    try:
        # Vérifier si l'utilisateur connecté existe et a les droits nécessaires
        connected_permissions = db.query(UserPermissions).options(load_only(
            UserPermissions.can_edit_users, UserPermissions.can_manage_roles
        )).filter(UserPermissions.user_id == user_connected_id).first()
  

        if not connected_permissions:
            raise ValueError("Aucune permission trouvée pour l'utilisateur connecté.")
        if not (connected_permissions.can_edit_users or connected_permissions.can_manage_roles):
            raise ValueError("Vous n'avez pas les droits pour modifier les permissions.")

        # Vérifier si l'utilisateur cible existe
        user_permission = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()

        if not user_permission:
            raise ValueError(f"Aucun enregistrement de permissions trouvé pour l'utilisateur avec l'ID {user_id}")

        # Liste des permissions valides (basée sur le modèle UserPermissions)
        valid_permissions = {
    # Permissions pour les showplans
    'can_access_showplan_broadcast_section', 'can_access_showplan_section', 'can_create_showplan',
    'can_edit_showplan', 'can_archive_showplan', 'can_archiveStatusChange_showplan', 'can_delete_showplan',
    'can_destroy_showplan', 'can_changestatus_showplan', 'can_changestatus_owned_showplan',
    'can_changestatus_archived_showplan', 'can_setOnline_showplan', 'can_viewAll_showplan',

    # Permissions pour les utilisateurs
    'can_access_users_section', 'can_view_users', 'can_edit_users', 'can_desable_users', 'can_delete_users',

    # Permissions pour les rôles
    'can_manage_roles', 'can_assign_roles',

    # Permissions pour les invités
    'can_access_guests_section', 'can_view_guests', 'can_edit_guests', 'can_delete_guests',

    # Permissions pour les présentateurs
    'can_access_presenters_section', 'can_view_presenters', 'can_create_presenters',  # Nouvelle permission ajoutée
    'can_edit_presenters', 'can_delete_presenters',

    # Permissions pour les émissions
    'can_access_emissions_section', 'can_view_emissions', 'can_create_emissions', 'can_edit_emissions',
    'can_delete_emissions', 'can_manage_emissions',

    # Permissions pour les notifications
    'can_view_notifications', 'can_manage_notifications',

    # Permissions pour les journaux et historique
    'can_view_audit_logs', 'can_view_login_history',

    # Permissions globales
    'can_manage_settings',

    # Permissions pour les messages
    'can_view_messages', 'can_send_messages', 'can_delete_messages',

    # Permissions pour les fichiers
    'can_view_files', 'can_upload_files', 'can_delete_files',

    # Permissions pour les tâches (nouvelles)
      # Ajout suggéré pour cohérence
    'can_view_tasks', 'can_create_tasks', 'can_edit_tasks', 'can_delete_tasks', 'can_assign_tasks',

    # Permissions pour les archives (nouvelles)
      # Ajout suggéré pour cohérence
    'can_view_archives', 'can_destroy_archives', 'can_restore_archives', 'can_delete_archives'
}

        # Vérifier les permissions fournies
        invalid_permissions = [perm for perm in permissions.keys() if perm not in valid_permissions]

        if invalid_permissions:
            raise ValueError(f"Permissions invalides : {', '.join(invalid_permissions)}")

        # Mettre à jour les permissions
        for perm, value in permissions.items():

            setattr(user_permission, perm, value)

        db.commit()
        return {"message": f"Permissions mises à jour avec succès pour l'utilisateur {user_id}", "success": True}

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

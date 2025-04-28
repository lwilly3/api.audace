from datetime import datetime, timezone
import logging
from typing import List
from sqlalchemy.orm import Session,joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, LoginHistory, Notification, AuditLog, Presenter, Guest, ArchivedAuditLog, Role, RolePermission, Permission
from sqlalchemy.orm.exc import NoResultFound
from fastapi import HTTPException
from app.db.crud.crud_permissions import initialize_user_permissions
from sqlalchemy import exc, not_
from typing import Optional
from app.schemas import UserUpdate



logger = logging.getLogger(__name__)

def get_non_presenters(db: Session):
    """
    Récupérer la liste des utilisateurs qui ne sont pas des présentateurs.

    Args:
        db (Session): Session de la base de données.

    Returns:
        list: Liste des utilisateurs non présentateurs sérialisés.

    Raises:
        Exception: En cas d'erreur lors de l'exécution de la requête.
    """
    try:
        # Sous-requête pour obtenir les users_id des présentateurs
        presenter_users_subquery = (
            db.query(Presenter.users_id)
            .filter(Presenter.is_deleted == False)  # Exclure les présentateurs supprimés
            .subquery()
        )

        # Requête pour récupérer les utilisateurs qui ne sont pas dans la sous-requête
        non_presenters = (
            db.query(User)
            .filter(
                User.is_deleted == False,  # Exclure les utilisateurs supprimés
                not_(User.id.in_(presenter_users_subquery))  # Exclure les utilisateurs qui sont présentateurs
            )
            .all()
        )

        # Sérialisation des données
        serialized_users = [
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "family_name": user.family_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "profilePicture": user.profilePicture,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            for user in non_presenters
        ]

        return serialized_users

    except Exception as e:
        logger.error(f"Error fetching non-presenters in CRUD: {e}")
        raise

# -------------------------
# Fonction utilitaire pour récupérer un utilisateur avec leurs permissions
# -------------------------
def get_user_or_404_with_permissions(db: Session, user_id: int) -> dict:
    """
    Fonction pour récupérer un utilisateur avec ses permissions.
    Retourne un dictionnaire contenant les informations de l'utilisateur et de ses permissions.
    Si l'utilisateur n'est pas trouvé ou est inactif, lève une exception HTTP 404.
    """
    try:
        user = db.query(User).options(joinedload(User.permissions)).filter(
            User.id == user_id, User.is_active == True
        ).first()

        if not user:
            raise NoResultFound("User not found or inactive")

        # Structure les permissions sous forme de dictionnaire
        permissions = user.permissions

        # Retourne les données dans le format attendu par la réponse
        return {
            
                "id": user.id,
                "username": user.username,
                "email": user.email,
                
                "can_create_showplan": permissions.can_create_showplan,
                "can_edit_showplan": permissions.can_edit_showplan,
                "can_archive_showplan": permissions.can_archive_showplan,
                "can_delete_showplan": permissions.can_delete_showplan,
                "can_destroy_showplan": permissions.can_destroy_showplan,
                "can_changestatus_showplan": permissions.can_changestatus_showplan,                 
        }
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))





# -------------------------
# Fonction utilitaire pour récupérer un utilisateur ou lever une erreur 404
# -------------------------
def get_user_or_404(db: Session, user_id: int) -> User:
    """
    Fonction utilitaire pour récupérer un utilisateur ou lever une erreur si l'utilisateur est inactif ou inexistant.
    """
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return None
        return user
    except SQLAlchemyError as e:
        print(f"Error retrieving user with ID {user_id}: {e}")
        return None

# -------------------------
# Récupérer tous les utilisateurs actifs
# -------------------------
def get_all_users(db: Session) -> List[User]:
    """
    Récupérer tous les utilisateurs actifs dans la base de données.
    """
    try:  
        query = db.query(User).options(joinedload(User.roles)).filter(User.is_active == True)
        return query.all()
    except SQLAlchemyError as e:
        print(f"Error retrieving all users: {e}")
        return []

# -------------------------
# Créer un nouvel utilisateur
# -------------------------
def create_user(db: Session, user_data: dict) -> User:
    """
    Créer un nouvel utilisateur.
    """
    try:
        new_user = User(
            username=user_data['username'],
            name=user_data['name'],
            family_name=user_data['family_name'],
            # roles=user_data['roles'],
            email=user_data['email'],
            password=user_data['password'],
            is_active=True,  # L'utilisateur est actif par défaut
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        initialize_user_permissions(db, new_user.id)  # Initialiser les permissions de l'utilisateur
        return new_user
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return None

# -------------------------
# Mettre à jour un utilisateur existant
# -------------------------
def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Mettre à jour un utilisateur dans la base de données.
    
    Args:
        db (Session): Session SQLAlchemy.
        user_id (int): ID de l'utilisateur à mettre à jour.
        user_update (UserUpdate): Données de mise à jour.
    
    Returns:
        Optional[User]: L'utilisateur mis à jour ou None si non trouvé.
    """
    try:
        # Récupérer l'utilisateur existant
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Mettre à jour les champs fournis
        update_data = user_update.model_dump(exclude_unset=True)  # Remplace .dict() par .model_dump() pour Pydantic v2
        for key, value in update_data.items():
            if key == "roles":
                # Mettre à jour les rôles (supprimer les anciens, ajouter les nouveaux)
                if value is not None:
                    user.roles = [db.query(Role).get(role_id) for role_id in value if db.query(Role).get(role_id)]
            else:
                setattr(user, key, value)

        # Si is_deleted est True, mettre à jour deleted_at
        if user_update.is_deleted and not user.deleted_at:
            user.deleted_at = datetime.utcnow()

        db.commit()
        db.refresh(user)
        return user
    except exc.SQLAlchemyError as e:
        print(f"Erreur lors de la mise à jour de l'utilisateur : {e}")
        db.rollback()
        return None

# -------------------------
# Supprimer (soft delete) un utilisateur
# -------------------------
def delete_user(db: Session, user_id: int) -> bool:
    """
    Marquer un utilisateur comme supprimé (soft delete).
    """
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if user:
            user.is_active = False
            user.deleted_at = datetime.now(timezone.utc)  # Enregistrer la date de suppression
            db.commit()
            db.refresh(user)
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error deleting user with ID {user_id}: {e}")
        return False

# -------------------------
# Récupérer l'historique des connexions d'un utilisateur
# -------------------------
def get_user_logins(db: Session, user_id: int) -> List[LoginHistory]:
    """
    Récupérer l'historique des connexions d'un utilisateur.
    """
    try:
        return db.query(LoginHistory).filter(LoginHistory.user_id == user_id).all()
    except SQLAlchemyError as e:
        print(f"Error retrieving login history for user with ID {user_id}: {e}")
        return []

# -------------------------
# Récupérer les notifications d'un utilisateur
# -------------------------
def get_user_notifications(db: Session, user_id: int) -> List[Notification]:
    """
    Récupérer les notifications pour un utilisateur.
    """
    try:
        return db.query(Notification).filter(Notification.user_id == user_id).all()
    except SQLAlchemyError as e:
        print(f"Error retrieving notifications for user with ID {user_id}: {e}")
        return []

# -------------------------
# Récupérer les logs d'audit d'un utilisateur
# -------------------------
def get_user_audit_logs(db: Session, user_id: int) -> List[AuditLog]:
    """
    Récupérer les logs d'audit pour un utilisateur.
    """
    try:
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
    except SQLAlchemyError as e:
        print(f"Error retrieving audit logs for user with ID {user_id}: {e}")
        return []

# -------------------------
# Archivage des logs d'audit
# -------------------------
def archive_audit_log(db: Session, audit_log: AuditLog) -> ArchivedAuditLog:
    """
    Archiver un log d'audit dans la table des logs archivés.
    """
    try:
        archived_log = ArchivedAuditLog(
            user_id=audit_log.user_id,
            action=audit_log.action,
            table_name=audit_log.table_name,
            record_id=audit_log.record_id,
            timestamp=audit_log.timestamp,
        )
        db.add(archived_log)
        db.commit()
        db.refresh(archived_log)
        return archived_log
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error archiving audit log: {e}")
        return None

# -------------------------
# Ajouter une permission à un rôle
# -------------------------
def add_permission_to_role(db: Session, role_id: int, permission_id: int) -> RolePermission:
    """
    Ajouter une permission à un rôle.
    """
    try:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error adding permission to role: {e}")
        return None

# -------------------------
# Créer un rôle
# -------------------------
def create_role(db: Session, role_data: dict) -> Role:
    """
    Créer un nouveau rôle.
    """
    try:
        new_role = Role(name=role_data['name'])
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating role: {e}")
        return None

# -------------------------
# Créer un invité
# -------------------------
def create_guest(db: Session, guest_data: dict) -> Guest:
    """
    Créer un nouvel invité.
    """
    try:
        new_guest = Guest(
            name=guest_data['name'],
            biography=guest_data.get('biography')
        )
        db.add(new_guest)
        db.commit()
        db.refresh(new_guest)
        return new_guest
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating guest: {e}")
        return None






















# from datetime import datetime, timezone
# from typing import List
# from .models import UserInDB, LoginLog, Notification, AuditLog

# # Base de données simulée
# users_db = {}  # Dictionnaire pour stocker les utilisateurs actifs/inactifs
# logins_db = {}  # Dictionnaire pour stocker l'historique des connexions
# notifications_db = {}  # Dictionnaire pour stocker les notifications
# audit_logs_db = {}  # Dictionnaire pour stocker les logs d'audit

# def get_user_or_404(user_id: int) -> UserInDB:
#     """
#     Fonction utilitaire pour récupérer un utilisateur ou lever une erreur 404
#     """
#     if user_id not in users_db or not users_db[user_id].is_active:
#         return None
#     return users_db[user_id]

# def get_all_users() -> List[UserInDB]:
#     """
#     Récupérer tous les utilisateurs actifs.
#     """
#     return [u for u in users_db.values() if u.is_active]

# def create_user(user: UserInDB) -> UserInDB:
#     """
#     Créer un nouvel utilisateur.
#     """
#     user_id = len(users_db) + 1  # Génération d'un nouvel ID
#     new_user = UserInDB(
#         **user.dict(), id=user_id, created_at=datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
#     )
#     users_db[user_id] = new_user
#     return new_user

# def update_user(id: int, user: UserInDB) -> UserInDB:
#     """
#     Mettre à jour un utilisateur existant.
#     """
#     existing_user = get_user_or_404(id)
#     if not existing_user:
#         return None
#     updated_user = existing_user.copy(
#         update={**user.dict(), "updated_at": datetime.now(timezone.utc) }
#     )
#     users_db[id] = updated_user
#     return updated_user

# def delete_user(id: int) -> bool:
#     """
#     Supprimer (soft delete) un utilisateur.
#     """
#     user = get_user_or_404(id)
#     if not user:
#         return False
#     user.is_active = False
#     user.updated_at = datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
#     users_db[id] = user
#     return True

# def get_user_logins(id: int) -> List[LoginLog]:
#     """
#     Récupérer l'historique des connexions d'un utilisateur.
#     """
#     return [log for log in logins_db.values() if log.user_id == id]

# def get_user_notifications(id: int) -> List[Notification]:
#     """
#     Récupérer les notifications d'un utilisateur.
#     """
#     return [n for n in notifications_db.values() if n.user_id == id]

# def get_user_audit_logs(id: int) -> List[AuditLog]:
#     """
#     Récupérer les logs d'audit d'un utilisateur.
#     """
#     return [log for log in audit_logs_db.values() if log.user_id == id]






















# # from sqlalchemy.orm import Session
# # from app.models import User
# # from app.schemas.schema_users import UserCreate, UserUpdate

# # def create_user(db: Session, user: UserCreate):
# #     new_user = User(**user.dict())
# #     db.add(new_user)
# #     db.commit()
# #     db.refresh(new_user)
# #     return new_user

# # def get_user(db: Session, user_id: int):
# #     return db.query(User).filter(User.id == user_id).first()

# # def get_users(db: Session, skip: int = 0, limit: int = 10):
# #     return db.query(User).offset(skip).limit(limit).all()

# # def update_user(db: Session, user_id: int, user_update: UserUpdate):
# #     user = db.query(User).filter(User.id == user_id).first()
# #     for key, value in user_update.dict(exclude_unset=True).items():
# #         setattr(user, key, value)
# #     db.commit()
# #     db.refresh(user)
# #     return user

# # def delete_user(db: Session, user_id: int):
# #     user = db.query(User).filter(User.id == user_id).first()
# #     if user:
# #         db.delete(user)
# #         db.commit()
# #     return user
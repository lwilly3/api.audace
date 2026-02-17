"""
Script d'initialisation de l'utilisateur administrateur par défaut.

Ce module crée automatiquement les rôles système et un utilisateur super_admin
avec toutes les permissions si aucun n'existe dans la base de données.

Utilisé au démarrage de l'application pour garantir qu'il y a toujours
au moins un super_admin pouvant accéder au système.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.model_user import User
from app.models.model_role import Role, BUILTIN_ROLES
from app.models.model_user_permissions import UserPermissions
from app.models.model_RoleTemplate import RoleTemplate
from app.utils.utils import hash as hash_password
from app.db.crud.crud_permissions import initialize_user_permissions
import logging
import os

logger = logging.getLogger("init_admin")


def create_builtin_roles(db: Session) -> None:
    """
    Crée les rôles système s'ils n'existent pas encore.
    Met à jour le hierarchy_level des rôles existants.
    """
    for role_def in BUILTIN_ROLES:
        existing = db.query(Role).filter(Role.name == role_def["name"]).first()
        if not existing:
            new_role = Role(name=role_def["name"], hierarchy_level=role_def["hierarchy_level"])
            db.add(new_role)
            logger.info(f"  Role '{role_def['name']}' cree (level {role_def['hierarchy_level']})")
        else:
            if existing.hierarchy_level != role_def["hierarchy_level"]:
                existing.hierarchy_level = role_def["hierarchy_level"]
                logger.info(f"  Role '{role_def['name']}' mis a jour (level {role_def['hierarchy_level']})")
    db.commit()


# Permissions par defaut pour chaque role builtin
ALL_PERMISSIONS_TRUE = {
    "can_acces_showplan_broadcast_section": True, "can_acces_showplan_section": True,
    "can_create_showplan": True, "can_edit_showplan": True, "can_archive_showplan": True,
    "can_archiveStatusChange_showplan": True, "can_delete_showplan": True, "can_destroy_showplan": True,
    "can_changestatus_showplan": True, "can_changestatus_owned_showplan": True,
    "can_changestatus_archived_showplan": True, "can_setOnline_showplan": True, "can_viewAll_showplan": True,
    "can_acces_users_section": True, "can_view_users": True, "can_edit_users": True,
    "can_desable_users": True, "can_delete_users": True,
    "can_manage_roles": True, "can_assign_roles": True,
    "can_acces_guests_section": True, "can_view_guests": True, "can_edit_guests": True, "can_delete_guests": True,
    "can_acces_presenters_section": True, "can_view_presenters": True, "can_create_presenters": True,
    "can_edit_presenters": True, "can_delete_presenters": True,
    "can_acces_emissions_section": True, "can_view_emissions": True, "can_create_emissions": True,
    "can_edit_emissions": True, "can_delete_emissions": True, "can_manage_emissions": True,
    "can_view_notifications": True, "can_manage_notifications": True,
    "can_view_audit_logs": True, "can_view_login_history": True, "can_manage_settings": True,
    "can_view_messages": True, "can_send_messages": True, "can_delete_messages": True,
    "can_view_files": True, "can_upload_files": True, "can_delete_files": True,
    "can_view_tasks": True, "can_create_tasks": True, "can_edit_tasks": True,
    "can_delete_tasks": True, "can_assign_tasks": True,
    "can_view_archives": True, "can_destroy_archives": True, "can_restore_archives": True, "can_delete_archives": True,
    "quotes_view": True, "quotes_create": True, "quotes_edit": True, "quotes_delete": True,
    "quotes_publish": True, "stream_transcription_view": True, "stream_transcription_create": True,
    "quotes_capture_live": True,
    "inventory_view": True, "inventory_create": True, "inventory_edit": True,
    "inventory_delete": True, "inventory_manage": True,
    "inventory_movement_view": True, "inventory_movement_create": True,
    "inventory_movement_edit": True, "inventory_movement_delete": True,
    "inventory_category_view": True, "inventory_category_create": True,
    "inventory_category_edit": True, "inventory_category_delete": True,
    "inventory_location_view": True, "inventory_location_manage": True,
}

# Admin = tout sauf gestion super_admin (pour l'instant identique)
ADMIN_PERMISSIONS = {**ALL_PERMISSIONS_TRUE}

# Invite = aucune permission
INVITE_PERMISSIONS = {k: False for k in ALL_PERMISSIONS_TRUE}

# Public = permissions de base (voir son profil, notifications)
PUBLIC_PERMISSIONS = {**INVITE_PERMISSIONS, "can_view_notifications": True}

BUILTIN_TEMPLATES = {
    "super_admin": {"description": "Toutes les permissions (super administrateur)", "permissions": ALL_PERMISSIONS_TRUE},
    "Admin": {"description": "Permissions administrateur", "permissions": ADMIN_PERMISSIONS},
    "public": {"description": "Permissions de base", "permissions": PUBLIC_PERMISSIONS},
    "invite": {"description": "Aucune permission (utilisateur invite)", "permissions": INVITE_PERMISSIONS},
}


def create_builtin_templates(db: Session) -> None:
    """
    Cree les templates de permissions systeme s'ils n'existent pas encore.
    """
    for name, config in BUILTIN_TEMPLATES.items():
        existing = db.query(RoleTemplate).filter(RoleTemplate.name == name).first()
        if not existing:
            template = RoleTemplate(
                name=name,
                description=config["description"],
                permissions=config["permissions"]
            )
            db.add(template)
            logger.info(f"  Template '{name}' cree")
    db.commit()


def create_default_admin(db: Session) -> None:
    """
    Crée les rôles système et un utilisateur super_admin par défaut si aucun n'existe.
    """
    try:
        logger.info("=" * 60)
        logger.info("Initialisation des roles systeme et super administrateur")
        logger.info("=" * 60)

        # Etape 1: Creer les roles systeme
        logger.info("Etape 1/5: Creation des roles systeme...")
        create_builtin_roles(db)

        # Etape 1b: Creer les templates de permissions systeme
        logger.info("Etape 1b/5: Creation des templates de permissions...")
        create_builtin_templates(db)

        # Recuperer le role super_admin
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        # Aussi s'assurer que le role Admin existe (compatibilite)
        admin_role = db.query(Role).filter(Role.name == "Admin").first()

        if not super_admin_role:
            logger.error("Le role 'super_admin' n'a pas pu etre cree!")
            return

        # Verifier s'il existe au moins un utilisateur avec le role super_admin ou Admin
        logger.info("Etape 2/5: Recherche d'utilisateurs admin existants...")
        admin_users = db.query(User).join(User.roles).filter(
            Role.name.in_(["super_admin", "Admin"]),
            User.is_deleted == False
        ).all()

        if admin_users:
            logger.info(f"{len(admin_users)} utilisateur(s) admin trouve(s):")
            for admin in admin_users:
                role_names = [r.name for r in admin.roles]
                logger.info(f"   - {admin.username} (ID: {admin.id}, Roles: {role_names})")
                # Promouvoir les anciens "Admin" en super_admin si pas deja fait
                if super_admin_role not in admin.roles and admin_role in admin.roles:
                    admin.roles.append(super_admin_role)
                    logger.info(f"   -> Promu en super_admin")
            db.commit()
            logger.info("=" * 60)
            return
        
        # Aucun admin trouve, creer l'utilisateur admin par defaut
        logger.warning("Aucun utilisateur admin trouve dans la base de donnees!")
        logger.info("Etape 3/5: Creation de l'admin par defaut...")

        # Recuperer les credentials depuis les variables d'environnement
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
        default_email = os.getenv("ADMIN_EMAIL", "admin@audace.local")
        default_name = os.getenv("ADMIN_NAME", "Administrateur")
        default_family_name = os.getenv("ADMIN_FAMILY_NAME", "Système")

        logger.info(f"Credentials: Username={default_username}, Email={default_email}")

        # Verifier si l'username ou l'email existe deja
        existing_user = db.query(User).filter(
            (User.username == default_username) | (User.email == default_email)
        ).first()

        if existing_user:
            logger.warning(f"Utilisateur '{existing_user.username}' existe deja!")

            # Ajouter le role super_admin a cet utilisateur
            if super_admin_role not in existing_user.roles:
                existing_user.roles.append(super_admin_role)
            if admin_role and admin_role not in existing_user.roles:
                existing_user.roles.append(admin_role)

            update_all_permissions_to_true(db, existing_user.id)
            db.commit()
            logger.info(f"L'utilisateur '{existing_user.username}' a maintenant tous les droits super_admin")
            logger.info("=" * 60)
            return

        # Creer le nouvel utilisateur admin
        logger.info("Creation du nouvel utilisateur admin...")
        hashed_password = hash_password(default_password)

        try:
            admin_user = User(
                username=default_username,
                name=default_name,
                family_name=default_family_name,
                email=default_email,
                password=hashed_password,
                is_active=True
            )

            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info(f"Utilisateur cree avec ID: {admin_user.id}")

            # Initialiser les permissions
            initialize_user_permissions(db, admin_user.id)

            # Assigner les roles super_admin + Admin
            admin_user.roles.append(super_admin_role)
            if admin_role:
                admin_user.roles.append(admin_role)
            db.commit()
            logger.info("Roles super_admin + Admin assignes")

            # Mettre a jour toutes les permissions a True
            update_all_permissions_to_true(db, admin_user.id)
            db.commit()

        except Exception as create_error:
            db.rollback()
            logger.error(f"Erreur lors de la creation: {create_error}")
            raise

        logger.info("=" * 60)
        logger.info("UTILISATEUR SUPER ADMIN CREE AVEC SUCCES!")
        logger.info("=" * 60)
        logger.info(f"Username: {default_username}")
        logger.info(f"Password: {default_password}")
        logger.info(f"Email: {default_email}")
        logger.info(f"User ID: {admin_user.id}")
        logger.info("=" * 60)
        logger.warning("IMPORTANT: Changez le mot de passe par defaut!")
        logger.info("=" * 60)
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("=" * 60)
        logger.error("❌ ERREUR SQL lors de la création de l'admin par défaut")
        logger.error("=" * 60)
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("=" * 60)
        raise
    except Exception as e:
        db.rollback()
        logger.error("=" * 60)
        logger.error("❌ ERREUR INATTENDUE lors de la création de l'admin")
        logger.error("=" * 60)
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        raise


def update_all_permissions_to_true(db: Session, user_id: int) -> None:
    """
    Met à jour les permissions d'un utilisateur pour avoir tous les droits admin.
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur dont mettre à jour les permissions
    """
    try:
        permissions = db.query(UserPermissions).filter(
            UserPermissions.user_id == user_id
        ).first()
        
        if not permissions:
            logger.error(f"Aucune permission trouvée pour l'utilisateur {user_id}")
            return
        
        # Mettre à jour toutes les permissions à True (selon les champs réels du modèle)
        
        # Showplans
        permissions.can_acces_showplan_broadcast_section = True
        permissions.can_acces_showplan_section = True
        permissions.can_create_showplan = True
        permissions.can_edit_showplan = True
        permissions.can_archive_showplan = True
        permissions.can_archiveStatusChange_showplan = True
        permissions.can_delete_showplan = True
        permissions.can_destroy_showplan = True
        permissions.can_changestatus_showplan = True
        permissions.can_changestatus_owned_showplan = True
        permissions.can_changestatus_archived_showplan = True
        permissions.can_setOnline_showplan = True
        permissions.can_viewAll_showplan = True
        
        # Users
        permissions.can_acces_users_section = True
        permissions.can_view_users = True
        permissions.can_edit_users = True
        permissions.can_desable_users = True
        permissions.can_delete_users = True
        
        # Roles
        permissions.can_manage_roles = True
        permissions.can_assign_roles = True
        
        # Guests
        permissions.can_acces_guests_section = True
        permissions.can_view_guests = True
        permissions.can_edit_guests = True
        permissions.can_delete_guests = True
        
        # Presenters
        permissions.can_acces_presenters_section = True
        permissions.can_view_presenters = True
        permissions.can_create_presenters = True
        permissions.can_edit_presenters = True
        permissions.can_delete_presenters = True
        
        # Emissions
        permissions.can_acces_emissions_section = True
        permissions.can_view_emissions = True
        permissions.can_create_emissions = True
        permissions.can_edit_emissions = True
        permissions.can_delete_emissions = True
        permissions.can_manage_emissions = True
        
        # Notifications
        permissions.can_view_notifications = True
        permissions.can_manage_notifications = True
        
        # Audit logs
        permissions.can_view_audit_logs = True
        permissions.can_view_login_history = True
        
        # Settings
        permissions.can_manage_settings = True
        
        # Messages
        permissions.can_view_messages = True
        permissions.can_send_messages = True
        permissions.can_delete_messages = True
        
        # Files
        permissions.can_view_files = True
        permissions.can_upload_files = True
        permissions.can_delete_files = True
        
        # Tasks
        permissions.can_view_tasks = True
        permissions.can_create_tasks = True
        permissions.can_edit_tasks = True
        permissions.can_delete_tasks = True
        permissions.can_assign_tasks = True
        
        # Archives
        permissions.can_view_archives = True
        permissions.can_destroy_archives = True
        permissions.can_restore_archives = True
        permissions.can_delete_archives = True
        
        # Citations et transcriptions (module Firebase)
        permissions.quotes_view = True
        permissions.quotes_create = True
        permissions.quotes_edit = True
        permissions.quotes_delete = True
        permissions.quotes_publish = True
        permissions.stream_transcription_view = True
        permissions.stream_transcription_create = True
        permissions.quotes_capture_live = True
        
        logger.info(f"✅ Toutes les permissions admin activées pour l'utilisateur {user_id}")
        
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la mise à jour des permissions admin: {e}")
        raise


def verify_admin_exists(db: Session) -> bool:
    """
    Vérifie si au moins un utilisateur admin existe dans le système.
    
    Args:
        db: Session de base de données
        
    Returns:
        bool: True si au moins un admin existe, False sinon
    """
    try:
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            return False
        
        admin_count = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False,
            User.is_active == True
        ).count()
        
        return admin_count > 0
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la vérification de l'existence d'un admin: {e}")
        return False

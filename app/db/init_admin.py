"""
Script d'initialisation de l'utilisateur administrateur par défaut.

Ce module crée automatiquement un utilisateur admin avec toutes les permissions
si aucun utilisateur admin n'existe dans la base de données.

Utilisé au démarrage de l'application pour garantir qu'il y a toujours
au moins un admin pouvant accéder au système.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.model_user import User
from app.models.model_role import Role
from app.models.model_user_permissions import UserPermissions
from app.utils.utils import hash as hash_password
from app.db.crud.crud_permissions import initialize_user_permissions
import logging
import os

logger = logging.getLogger("init_admin")


def create_default_admin(db: Session) -> None:
    """
    Crée un utilisateur administrateur par défaut si aucun admin n'existe.
    
    Vérifie d'abord s'il existe au moins un utilisateur avec le rôle "Admin".
    Si aucun admin n'existe, crée un utilisateur admin avec :
    - Username: admin
    - Password: configurable via env (défaut: Admin@2024!)
    - Email: configurable via env (défaut: admin@audace.local)
    - Toutes les permissions activées
    
    Args:
        db: Session de base de données SQLAlchemy
        
    Note:
        Les credentials par défaut doivent être changés immédiatement après
        la première connexion en production !
    """
    try:
        logger.info("=" * 60)
        logger.info("Initialisation de l'utilisateur administrateur par défaut")
        logger.info("=" * 60)
        
        # Vérifier si le rôle Admin existe
        logger.info("Étape 1/5: Vérification du rôle 'Admin'...")
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        
        if not admin_role:
            logger.warning("⚠️  Le rôle 'Admin' n'existe pas. Création du rôle Admin...")
            admin_role = Role(name="Admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info("✅ Rôle 'Admin' créé avec succès (ID: {})".format(admin_role.id))
        else:
            logger.info(f"✅ Rôle 'Admin' trouvé (ID: {admin_role.id})")
        
        # Vérifier s'il existe au moins un utilisateur avec le rôle Admin
        logger.info("Étape 2/5: Recherche d'utilisateurs admin existants...")
        admin_users = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False
        ).all()
        
        if admin_users:
            logger.info(f"✅ {len(admin_users)} utilisateur(s) admin trouvé(s):")
            for admin in admin_users:
                logger.info(f"   - {admin.username} (ID: {admin.id}, Email: {admin.email})")
            logger.info("Pas besoin de créer un admin par défaut.")
            logger.info("=" * 60)
            return
        
        # Aucun admin trouvé, créer l'utilisateur admin par défaut
        logger.warning("⚠️  Aucun utilisateur admin trouvé dans la base de données!")
        logger.info("Étape 3/5: Création de l'admin par défaut...")
        
        # Récupérer les credentials depuis les variables d'environnement
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
        default_email = os.getenv("ADMIN_EMAIL", "admin@audace.local")
        default_name = os.getenv("ADMIN_NAME", "Administrateur")
        default_family_name = os.getenv("ADMIN_FAMILY_NAME", "Système")
        
        logger.info(f"Credentials utilisés:")
        logger.info(f"   - Username: {default_username}")
        logger.info(f"   - Email: {default_email}")
        logger.info(f"   - Name: {default_name} {default_family_name}")
        
        # Vérifier si l'username ou l'email existe déjà
        existing_user = db.query(User).filter(
            (User.username == default_username) | (User.email == default_email)
        ).first()
        
        if existing_user:
            logger.warning(f"⚠️  Un utilisateur avec le username '{default_username}' ou l'email '{default_email}' existe déjà!")
            logger.info(f"Utilisateur trouvé: {existing_user.username} (ID: {existing_user.id}, Email: {existing_user.email})")
            
            # Ajouter le rôle Admin à cet utilisateur s'il ne l'a pas
            if admin_role not in existing_user.roles:
                logger.info("Ajout du rôle Admin à cet utilisateur existant...")
                existing_user.roles.append(admin_role)
            else:
                logger.info("Cet utilisateur a déjà le rôle Admin")
            
            # Mettre à jour les permissions pour avoir tous les droits
            logger.info("Étape 4/5: Mise à jour des permissions...")
            update_all_permissions_to_true(db, existing_user.id)
            
            db.commit()
            logger.info(f"✅ L'utilisateur '{existing_user.username}' a maintenant tous les droits Admin")
            logger.info("=" * 60)
            return
        
        # Créer le nouvel utilisateur admin (même approche que create_user)
        logger.info("Création du nouvel utilisateur admin...")
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
            logger.info(f"✅ Utilisateur créé avec ID: {admin_user.id}")
            
            # Initialiser les permissions (comme dans create_user)
            logger.info("Initialisation des permissions...")
            initialize_user_permissions(db, admin_user.id)
            logger.info("✅ Permissions initialisées")
            
            # Assigner le rôle Admin
            logger.info("Assignation du rôle Admin...")
            admin_user.roles.append(admin_role)
            db.commit()
            logger.info("✅ Rôle Admin assigné")
            
            # Mettre à jour toutes les permissions à True pour l'admin
            logger.info("Activation de toutes les permissions admin...")
            update_all_permissions_to_true(db, admin_user.id)
            db.commit()
            
        except Exception as create_error:
            db.rollback()
            logger.error(f"❌ Erreur lors de la création: {create_error}")
            raise
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ UTILISATEUR ADMIN CRÉÉ AVEC SUCCÈS!")
        logger.info("=" * 60)
        logger.info(f"Username: {default_username}")
        logger.info(f"Password: {default_password}")
        logger.info(f"Email: {default_email}")
        logger.info(f"User ID: {admin_user.id}")
        logger.info("=" * 60)
        logger.warning("⚠️  IMPORTANT: Changez le mot de passe par défaut dès la première connexion!")
        
        if default_password == "Admin@2024!":
            logger.warning("⚠️  Mot de passe par défaut utilisé. Définissez ADMIN_PASSWORD dans les variables d'environnement pour plus de sécurité.")
        
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

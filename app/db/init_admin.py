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
import logging
import os

# Alias pour correspondre à la documentation
# UserPermission = UserPermissions

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
        # Vérifier si le rôle Admin existe
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        
        if not admin_role:
            logger.warning("Le rôle 'Admin' n'existe pas. Création du rôle Admin...")
            admin_role = Role(
                name="Admin",
                description="Administrateur système avec toutes les permissions"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info("Rôle 'Admin' créé avec succès")
        
        # Vérifier s'il existe au moins un utilisateur avec le rôle Admin
        admin_users = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False
        ).all()
        
        if admin_users:
            logger.info(f"{len(admin_users)} utilisateur(s) admin trouvé(s). Pas besoin de créer un admin par défaut.")
            return
        
        # Aucun admin trouvé, créer l'utilisateur admin par défaut
        logger.warning("Aucun utilisateur admin trouvé. Création de l'admin par défaut...")
        
        # Récupérer les credentials depuis les variables d'environnement
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
        default_email = os.getenv("ADMIN_EMAIL", "admin@audace.local")
        default_name = os.getenv("ADMIN_NAME", "Administrateur")
        default_family_name = os.getenv("ADMIN_FAMILY_NAME", "Système")
        
        # Vérifier si l'username ou l'email existe déjà
        existing_user = db.query(User).filter(
            (User.username == default_username) | (User.email == default_email)
        ).first()
        
        if existing_user:
            logger.error(f"Un utilisateur avec le username '{default_username}' ou l'email '{default_email}' existe déjà mais n'a pas le rôle Admin!")
            logger.info(f"Utilisateur existant trouvé: {existing_user.username} (ID: {existing_user.id})")
            
            # Ajouter le rôle Admin à cet utilisateur
            if admin_role not in existing_user.roles:
                existing_user.roles.append(admin_role)
                logger.info(f"Ajout du rôle Admin à l'utilisateur existant: {existing_user.username}")
            
            # Mettre à jour les permissions pour avoir tous les droits
            update_admin_permissions(db, existing_user.id)
            
            db.commit()
            logger.info(f"L'utilisateur '{existing_user.username}' a maintenant les droits Admin")
            return
        
        # Créer le nouvel utilisateur admin
        hashed_password = hash_password(default_password)
        
        admin_user = User(
            username=default_username,
            name=default_name,
            family_name=default_family_name,
            email=default_email,
            password=hashed_password,
            is_active=True,
            is_deleted=False
        )
        
        db.add(admin_user)
        db.flush()  # Obtenir l'ID sans commit complet
        
        # Assigner le rôle Admin
        admin_user.roles.append(admin_role)
        
        # Créer les permissions avec tous les droits
        create_admin_permissions(db, admin_user.id)
        
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✅ Utilisateur admin créé avec succès!")
        logger.info(f"   - Username: {default_username}")
        logger.info(f"   - Email: {default_email}")
        logger.warning(f"   ⚠️  IMPORTANT: Changez le mot de passe par défaut dès la première connexion!")
        
        if default_password == "Admin@2024!":
            logger.warning(f"   ⚠️  Mot de passe par défaut utilisé. Pour plus de sécurité, définissez ADMIN_PASSWORD dans les variables d'environnement.")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la création de l'admin par défaut: {e}")
        raise


def create_admin_permissions(db: Session, user_id: int) -> None:
    """
    Crée des permissions avec tous les droits pour un utilisateur admin.
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur pour lequel créer les permissions
    """
    try:
        # Vérifier si les permissions existent déjà
        existing_permissions = db.query(UserPermissions).filter(
            UserPermissions.user_id == user_id
        ).first()
        
        if existing_permissions:
            logger.info(f"Permissions existantes trouvées pour l'utilisateur {user_id}, mise à jour...")
            update_admin_permissions(db, user_id)
            return
        
        # Créer les permissions avec tous les droits
        admin_permissions = UserPermissions(
            user_id=user_id,
            # Permissions utilisateurs
            can_view_users=True,
            can_create_users=True,
            can_edit_users=True,
            can_delete_users=True,
            # Permissions shows
            can_view_shows=True,
            can_create_shows=True,
            can_edit_shows=True,
            can_delete_shows=True,
            can_publish_shows=True,
            # Permissions présentateurs
            can_view_presenters=True,
            can_create_presenters=True,
            can_edit_presenters=True,
            can_delete_presenters=True,
            # Permissions invités
            can_view_guests=True,
            can_create_guests=True,
            can_edit_guests=True,
            can_delete_guests=True,
            # Permissions émissions
            can_view_emissions=True,
            can_create_emissions=True,
            can_edit_emissions=True,
            can_delete_emissions=True,
            # Permissions segments
            can_view_segments=True,
            can_create_segments=True,
            can_edit_segments=True,
            can_delete_segments=True,
            # Permissions rôles
            can_view_roles=True,
            can_create_roles=True,
            can_edit_roles=True,
            can_delete_roles=True,
            can_assign_roles=True,
            # Permissions système
            can_manage_permissions=True,
            can_view_audit_logs=True,
            can_view_notifications=True,
            can_manage_settings=True,
            # Permissions statistiques
            can_view_statistics=True,
            can_export_data=True
        )
        
        db.add(admin_permissions)
        logger.info(f"Permissions admin créées pour l'utilisateur {user_id}")
        
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la création des permissions admin: {e}")
        raise


def update_admin_permissions(db: Session, user_id: int) -> None:
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
            create_admin_permissions(db, user_id)
            return
        
        # Mettre à jour toutes les permissions à True
        permissions.can_view_users = True
        permissions.can_create_users = True
        permissions.can_edit_users = True
        permissions.can_delete_users = True
        permissions.can_view_shows = True
        permissions.can_create_shows = True
        permissions.can_edit_shows = True
        permissions.can_delete_shows = True
        permissions.can_publish_shows = True
        permissions.can_view_presenters = True
        permissions.can_create_presenters = True
        permissions.can_edit_presenters = True
        permissions.can_delete_presenters = True
        permissions.can_view_guests = True
        permissions.can_create_guests = True
        permissions.can_edit_guests = True
        permissions.can_delete_guests = True
        permissions.can_view_emissions = True
        permissions.can_create_emissions = True
        permissions.can_edit_emissions = True
        permissions.can_delete_emissions = True
        permissions.can_view_segments = True
        permissions.can_create_segments = True
        permissions.can_edit_segments = True
        permissions.can_delete_segments = True
        permissions.can_view_roles = True
        permissions.can_create_roles = True
        permissions.can_edit_roles = True
        permissions.can_delete_roles = True
        permissions.can_assign_roles = True
        permissions.can_manage_permissions = True
        permissions.can_view_audit_logs = True
        permissions.can_view_notifications = True
        permissions.can_manage_settings = True
        permissions.can_view_statistics = True
        permissions.can_export_data = True
        
        logger.info(f"Permissions admin mises à jour pour l'utilisateur {user_id}")
        
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

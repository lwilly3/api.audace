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
# Genere dynamiquement depuis le modele UserPermissions
def _build_all_permissions_true() -> dict[str, bool]:
    """Construit dynamiquement le dict de toutes les permissions a True."""
    from sqlalchemy import inspect as sa_inspect, Boolean
    mapper = sa_inspect(UserPermissions)
    return {
        col.name: True
        for col in mapper.columns
        if col.name not in ("id", "user_id", "granted_at")
        and isinstance(col.type, Boolean)
    }

ALL_PERMISSIONS_TRUE = _build_all_permissions_true()

# Admin = tout sauf destruction archives (reservee au super_admin)
ADMIN_PERMISSIONS = {**ALL_PERMISSIONS_TRUE, "can_destroy_archives": False}

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

            # Sync les permissions de tous les super_admin a chaque demarrage
            # Garantit que les nouvelles permissions (ajoutees par migration) sont activees
            sync_superadmin_permissions(db)

            logger.info("=" * 60)
            return
        
        # Aucun admin trouve, creer l'utilisateur admin par defaut
        logger.warning("Aucun utilisateur admin trouve dans la base de donnees!")
        logger.info("Etape 3/5: Creation de l'admin par defaut...")

        # Recuperer les credentials depuis les variables d'environnement
        default_username = os.getenv("ADMIN_USERNAME", "admin@radiomanager.ovh")
        default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
        default_email = os.getenv("ADMIN_EMAIL", "admin@radiomanager.ovh")
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


def _get_all_boolean_permission_fields() -> list[str]:
    """
    Introspection du modele UserPermissions pour trouver dynamiquement
    toutes les colonnes Boolean (= permissions).
    Exclut les colonnes techniques : id, user_id, granted_at.
    """
    from sqlalchemy import inspect as sa_inspect, Boolean
    mapper = sa_inspect(UserPermissions)
    fields = []
    for col in mapper.columns:
        if col.name in ("id", "user_id", "granted_at"):
            continue
        if isinstance(col.type, Boolean):
            fields.append(col.name)
    return fields


def update_all_permissions_to_true(db: Session, user_id: int) -> None:
    """
    Met a jour les permissions d'un utilisateur pour avoir tous les droits admin.
    Utilise l'introspection du modele : toute nouvelle colonne Boolean dans
    UserPermissions sera automatiquement activee, sans modification manuelle.
    """
    try:
        permissions = db.query(UserPermissions).filter(
            UserPermissions.user_id == user_id
        ).first()

        if not permissions:
            logger.error(f"Aucune permission trouvee pour l'utilisateur {user_id}")
            return

        fields = _get_all_boolean_permission_fields()
        updated = 0
        for field in fields:
            if not getattr(permissions, field, True):
                setattr(permissions, field, True)
                updated += 1

        if updated:
            logger.info(f"  {updated} permission(s) activee(s) pour l'utilisateur {user_id}")
        logger.info(f"Toutes les permissions admin activees pour l'utilisateur {user_id} ({len(fields)} champs)")

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la mise a jour des permissions admin: {e}")
        raise


def sync_superadmin_permissions(db: Session) -> None:
    """
    Synchronise les permissions de TOUS les super_admin au demarrage.
    Garantit que les super_admin aient toujours toutes les permissions a True,
    y compris les nouvelles permissions ajoutees par migration Alembic.
    Appelee a chaque demarrage de l'application.
    """
    try:
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        if not super_admin_role:
            return

        super_admins = db.query(User).join(User.roles).filter(
            Role.name == "super_admin",
            User.is_deleted == False,
            User.is_active == True
        ).all()

        if not super_admins:
            return

        logger.info(f"Sync permissions pour {len(super_admins)} super_admin(s)...")
        for admin in super_admins:
            # S'assurer que la ligne UserPermissions existe
            perms = db.query(UserPermissions).filter(
                UserPermissions.user_id == admin.id
            ).first()
            if not perms:
                initialize_user_permissions(db, admin.id)
            update_all_permissions_to_true(db, admin.id)

        db.commit()
        logger.info("Sync permissions super_admin terminee")

    except SQLAlchemyError as e:
        logger.error(f"Erreur sync permissions super_admin: {e}")
        db.rollback()


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

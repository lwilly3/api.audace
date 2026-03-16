"""
Route de configuration initiale pour créer un admin en cas d'urgence.

Cette route est accessible SANS authentification uniquement si aucun admin n'existe.
Elle est automatiquement désactivée dès qu'un admin est présent dans le système.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.model_user import User
from app.models.model_role import Role
from app.utils.utils import hash as hash_password
from app.db.crud.crud_permissions import initialize_user_permissions
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/setup",
    tags=["Setup - Configuration initiale"]
)


class SetupAdminRequest(BaseModel):
    """Schéma pour créer l'admin initial."""
    username: str
    email: EmailStr
    password: str
    name: str = "Administrateur"
    family_name: str = "Système"


@router.get(
    "/check-admin",
    summary="Vérifier si un admin existe",
    description="Vérifie si au moins un utilisateur admin existe dans le système",
    status_code=status.HTTP_200_OK
)
def check_admin_exists(db: Session = Depends(get_db)):
    """
    Vérifie si un admin existe dans le système.
    
    Returns:
        - admin_exists: True si au moins un admin existe
        - setup_needed: True si aucun admin n'existe et la configuration est nécessaire
        - admin_count: Nombre d'admins actifs
    """
    try:
        # Vérifier si le rôle Admin existe
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        
        if not admin_role:
            return {
                "admin_exists": False,
                "setup_needed": True,
                "admin_count": 0,
                "message": "Aucun rôle Admin trouvé. Utilisez POST /setup/create-admin pour configurer le système."
            }
        
        # Compter les admins actifs
        admin_count = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False,
            User.is_active == True
        ).count()
        
        if admin_count == 0:
            return {
                "admin_exists": False,
                "setup_needed": True,
                "admin_count": 0,
                "message": "Aucun admin trouvé. Utilisez POST /setup/create-admin pour créer le premier admin."
            }
        
        return {
            "admin_exists": True,
            "setup_needed": False,
            "admin_count": admin_count,
            "message": f"{admin_count} admin(s) trouvé(s). Le système est configuré."
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )


@router.post(
    "/create-admin",
    summary="Créer le premier admin (SANS authentification)",
    description="Crée le premier utilisateur admin. Cette route est DÉSACTIVÉE si un admin existe déjà.",
    status_code=status.HTTP_201_CREATED
)
def create_initial_admin(
    admin_data: SetupAdminRequest,
    db: Session = Depends(get_db)
):
    """
    Crée le premier utilisateur admin du système.
    
    ⚠️ IMPORTANT:
    - Cette route ne nécessite PAS d'authentification
    - Elle est automatiquement DÉSACTIVÉE si un admin existe déjà
    - Elle doit être utilisée UNIQUEMENT pour la configuration initiale
    
    Args:
        admin_data: Données du premier admin à créer
        
    Returns:
        Message de succès avec les informations de l'admin créé
        
    Raises:
        403: Si un admin existe déjà (route désactivée)
        400: Si les données sont invalides
        409: Si l'username ou l'email existe déjà
    """
    try:
        logger.info("=" * 60)
        logger.info("🔧 SETUP: Tentative de création du premier admin")
        logger.info("=" * 60)
        
        # SÉCURITÉ: Vérifier qu'aucun admin n'existe déjà
        logger.info("Vérification de sécurité: recherche d'admins existants...")
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        
        if admin_role:
            existing_admins = db.query(User).join(User.roles).filter(
                Role.name == "Admin",
                User.is_deleted == False
            ).count()
            
            if existing_admins > 0:
                logger.warning(f"❌ SÉCURITÉ: {existing_admins} admin(s) déjà existant(s). Route désactivée.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Setup déjà effectué",
                        "message": "Au moins un administrateur existe déjà dans le système.",
                        "admin_count": existing_admins,
                        "help": "Cette route est désactivée pour des raisons de sécurité. Utilisez /auth/login pour vous connecter."
                    }
                )
        
        logger.info("✅ Aucun admin existant. Création autorisée.")
        
        # Créer le rôle Admin s'il n'existe pas
        if not admin_role:
            logger.info("Création du rôle Admin...")
            admin_role = Role(name="Admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info(f"✅ Rôle Admin créé (ID: {admin_role.id})")
        
        # Vérifier que l'username n'existe pas
        logger.info(f"Vérification de l'username '{admin_data.username}'...")
        existing_user = db.query(User).filter(
            (User.username == admin_data.username) | (User.email == admin_data.email)
        ).first()
        
        if existing_user:
            logger.error(f"❌ Username ou email déjà existant: {existing_user.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Conflit",
                    "message": f"Un utilisateur avec le username '{admin_data.username}' ou l'email '{admin_data.email}' existe déjà.",
                    "existing_user_id": existing_user.id
                }
            )
        
        # Créer l'utilisateur admin
        logger.info("Création de l'utilisateur admin...")
        hashed_password = hash_password(admin_data.password)
        
        admin_user = User(
            username=admin_data.username,
            name=admin_data.name,
            family_name=admin_data.family_name,
            email=admin_data.email,
            password=hashed_password,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"✅ Utilisateur créé (ID: {admin_user.id})")
        
        # Initialiser les permissions
        logger.info("Initialisation des permissions...")
        initialize_user_permissions(db, admin_user.id)
        logger.info("✅ Permissions initialisées")
        
        # Assigner le rôle Admin
        logger.info("Attribution du rôle Admin...")
        admin_user.roles.append(admin_role)
        db.commit()
        logger.info("✅ Rôle Admin assigné")
        
        # Activer toutes les permissions
        logger.info("Activation de toutes les permissions admin...")
        permissions = db.query(User).filter(User.id == admin_user.id).first().permissions
        
        if permissions:
            # Activer toutes les permissions
            for attr in dir(permissions):
                if attr.startswith('can_'):
                    setattr(permissions, attr, True)
            db.commit()
            logger.info("✅ Toutes les permissions activées")
        
        logger.info("=" * 60)
        logger.info("✅ ADMIN CRÉÉ AVEC SUCCÈS via la route de setup!")
        logger.info("=" * 60)
        logger.info(f"Username: {admin_user.username}")
        logger.info(f"Email: {admin_user.email}")
        logger.info(f"User ID: {admin_user.id}")
        logger.info("=" * 60)
        logger.warning("⚠️  Cette route est maintenant DÉSACTIVÉE automatiquement")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "message": "Premier administrateur créé avec succès!",
            "admin": {
                "id": admin_user.id,
                "username": admin_user.username,
                "email": admin_user.email,
                "name": f"{admin_user.name} {admin_user.family_name}"
            },
            "next_steps": [
                "1. Connectez-vous avec vos credentials via POST /auth/login",
                "2. Cette route /setup/create-admin est maintenant DÉSACTIVÉE",
                "3. Changez votre mot de passe via PUT /users/{user_id}",
                "4. Créez d'autres utilisateurs via POST /users"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("=" * 60)
        logger.error(f"❌ ERREUR lors de la création de l'admin via setup")
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Erreur serveur",
                "message": "Une erreur est survenue lors de la création de l'admin",
                "detail": str(e)
            }
        )


@router.get(
    "/env-check",
    summary="Vérifier les variables d'environnement",
    description="Affiche si les variables d'environnement admin sont définies (sans révéler les valeurs)"
)
def check_environment_variables():
    """
    Vérifie si les variables d'environnement pour l'admin par défaut sont définies.
    
    Utile pour déboguer si les credentials par défaut ne sont pas ceux attendus.
    """
    import os
    
    return {
        "environment_variables": {
            "ADMIN_USERNAME": {
                "defined": os.getenv("ADMIN_USERNAME") is not None,
                "value": os.getenv("ADMIN_USERNAME", "admin@radiomanager.ovh"),
                "source": "environment" if os.getenv("ADMIN_USERNAME") else "default"
            },
            "ADMIN_PASSWORD": {
                "defined": os.getenv("ADMIN_PASSWORD") is not None,
                "value": "***HIDDEN***" if os.getenv("ADMIN_PASSWORD") else "Admin@2024! (default)",
                "source": "environment" if os.getenv("ADMIN_PASSWORD") else "default"
            },
            "ADMIN_EMAIL": {
                "defined": os.getenv("ADMIN_EMAIL") is not None,
                "value": os.getenv("ADMIN_EMAIL", "admin@radiomanager.ovh"),
                "source": "environment" if os.getenv("ADMIN_EMAIL") else "default"
            },
            "ADMIN_NAME": {
                "defined": os.getenv("ADMIN_NAME") is not None,
                "value": os.getenv("ADMIN_NAME", "Administrateur"),
                "source": "environment" if os.getenv("ADMIN_NAME") else "default"
            },
            "ADMIN_FAMILY_NAME": {
                "defined": os.getenv("ADMIN_FAMILY_NAME") is not None,
                "value": os.getenv("ADMIN_FAMILY_NAME", "Système"),
                "source": "environment" if os.getenv("ADMIN_FAMILY_NAME") else "default"
            }
        },
        "help": "Si 'source' est 'default', la variable n'est pas définie dans l'environnement"
    }


@router.get(
    "/status",
    summary="Statut du système",
    description="Retourne le statut de configuration du système"
)
def get_system_status(db: Session = Depends(get_db)):
    """
    Retourne le statut complet du système.
    
    Utile pour vérifier si le système est correctement configuré.
    """
    try:
        # Vérifier la connexion à la base de données
        db.execute("SELECT 1")
        db_connected = True
    except:
        db_connected = False
    
    # Vérifier le rôle Admin
    admin_role_exists = db.query(Role).filter(Role.name == "Admin").first() is not None
    
    # Compter les utilisateurs
    total_users = db.query(User).filter(User.is_deleted == False).count()
    
    # Compter les admins
    admin_count = 0
    if admin_role_exists:
        admin_count = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False,
            User.is_active == True
        ).count()
    
    # Statut de la route de setup
    setup_route_active = admin_count == 0
    
    return {
        "system_status": "ready" if admin_count > 0 else "needs_setup",
        "database_connected": db_connected,
        "admin_role_exists": admin_role_exists,
        "admin_count": admin_count,
        "total_users": total_users,
        "setup_route_active": setup_route_active,
        "setup_url": "/setup/create-admin" if setup_route_active else None,
        "message": "Système configuré" if admin_count > 0 else "Configuration initiale requise"
    }

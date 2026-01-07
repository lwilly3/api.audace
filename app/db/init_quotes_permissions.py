"""
Script d'initialisation des permissions pour le module Citations.

Ce module configure les permissions par défaut pour chaque rôle selon la matrice définie :
- Admin : Toutes les permissions
- Éditeur : Toutes sauf édition/suppression des citations des autres
- Animateur : Consultation, création, édition de ses propres citations, transcription
- Community Manager : Consultation, création, édition, publication (pas de transcription)
- Invité : Consultation uniquement

Les permissions sont appliquées aux utilisateurs existants en fonction de leur rôle.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.model_user import User
from app.models.model_role import Role
from app.models.model_user_permissions import UserPermissions
import logging

logger = logging.getLogger("init_quotes_permissions")


# Matrice des permissions par rôle
ROLE_PERMISSIONS_MATRIX = {
    "Admin": {
        "quotes_view": True,
        "quotes_create": True,
        "quotes_edit": True,
        "quotes_delete": True,
        "quotes_publish": True,
        "stream_transcription_view": True,
        "stream_transcription_create": True,
        "quotes_capture_live": True,
    },
    "Éditeur": {
        "quotes_view": True,
        "quotes_create": True,
        "quotes_edit": True,  # Note: Limitation aux siennes gérée par la logique métier
        "quotes_delete": True,  # Note: Limitation aux siennes gérée par la logique métier
        "quotes_publish": True,
        "stream_transcription_view": True,
        "stream_transcription_create": True,
        "quotes_capture_live": True,
    },
    "Animateur": {
        "quotes_view": True,
        "quotes_create": True,
        "quotes_edit": True,  # Note: Limitation aux siennes gérée par la logique métier
        "quotes_delete": False,
        "quotes_publish": False,
        "stream_transcription_view": True,
        "stream_transcription_create": True,
        "quotes_capture_live": True,
    },
    "Community Manager": {
        "quotes_view": True,
        "quotes_create": True,
        "quotes_edit": True,
        "quotes_delete": False,
        "quotes_publish": True,
        "stream_transcription_view": True,
        "stream_transcription_create": False,
        "quotes_capture_live": False,
    },
    "Invité": {
        "quotes_view": True,
        "quotes_create": False,
        "quotes_edit": False,
        "quotes_delete": False,
        "quotes_publish": False,
        "stream_transcription_view": False,
        "stream_transcription_create": False,
        "quotes_capture_live": False,
    },
}


def initialize_quotes_permissions_for_role(db: Session, role_name: str) -> None:
    """
    Initialise les permissions Citations pour tous les utilisateurs d'un rôle donné.
    
    Args:
        db: Session de base de données
        role_name: Nom du rôle à traiter
    """
    try:
        logger.info(f"Traitement du rôle: {role_name}")
        
        # Récupérer le rôle
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            logger.warning(f"⚠️  Rôle '{role_name}' non trouvé, création...")
            role = Role(name=role_name)
            db.add(role)
            db.commit()
            db.refresh(role)
            logger.info(f"✅ Rôle '{role_name}' créé")
        
        # Récupérer la matrice de permissions pour ce rôle
        permissions_config = ROLE_PERMISSIONS_MATRIX.get(role_name)
        if not permissions_config:
            logger.warning(f"⚠️  Pas de configuration de permissions pour le rôle '{role_name}'")
            return
        
        # Récupérer tous les utilisateurs ayant ce rôle
        users = db.query(User).join(User.roles).filter(
            Role.name == role_name,
            User.is_deleted == False
        ).all()
        
        if not users:
            logger.info(f"   Aucun utilisateur trouvé avec le rôle '{role_name}'")
            return
        
        logger.info(f"   {len(users)} utilisateur(s) trouvé(s)")
        
        # Mettre à jour les permissions pour chaque utilisateur
        for user in users:
            user_permissions = db.query(UserPermissions).filter(
                UserPermissions.user_id == user.id
            ).first()
            
            if not user_permissions:
                logger.warning(f"   ⚠️  Pas de permissions trouvées pour {user.username}")
                continue
            
            # Appliquer les permissions selon la matrice
            for permission_name, permission_value in permissions_config.items():
                setattr(user_permissions, permission_name, permission_value)
            
            logger.info(f"   ✅ Permissions Citations mises à jour pour {user.username}")
        
        db.commit()
        logger.info(f"✅ Rôle '{role_name}' traité avec succès")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"❌ Erreur lors du traitement du rôle '{role_name}': {e}")
        raise


def initialize_all_quotes_permissions(db: Session) -> None:
    """
    Initialise les permissions Citations pour tous les rôles définis.
    
    Args:
        db: Session de base de données
    """
    try:
        logger.info("=" * 70)
        logger.info("INITIALISATION DES PERMISSIONS MODULE CITATIONS")
        logger.info("=" * 70)
        logger.info("")
        
        # Traiter chaque rôle
        for role_name in ROLE_PERMISSIONS_MATRIX.keys():
            initialize_quotes_permissions_for_role(db, role_name)
            logger.info("")
        
        logger.info("=" * 70)
        logger.info("✅ INITIALISATION TERMINÉE")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Résumé des permissions par rôle:")
        logger.info("")
        
        for role_name, permissions in ROLE_PERMISSIONS_MATRIX.items():
            enabled = [k for k, v in permissions.items() if v]
            logger.info(f"  {role_name}:")
            logger.info(f"    Permissions actives: {len(enabled)}/8")
            for perm in enabled:
                logger.info(f"      ✓ {perm}")
            logger.info("")
        
    except Exception as e:
        db.rollback()
        logger.error("=" * 70)
        logger.error("❌ ERREUR lors de l'initialisation des permissions")
        logger.error("=" * 70)
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("=" * 70)
        raise


def apply_quotes_permissions_to_user(db: Session, user_id: int, role_name: str) -> None:
    """
    Applique les permissions Citations à un utilisateur spécifique selon son rôle.
    
    Utile lors de la création d'un nouvel utilisateur ou du changement de rôle.
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        role_name: Nom du rôle à appliquer
    """
    try:
        permissions_config = ROLE_PERMISSIONS_MATRIX.get(role_name)
        if not permissions_config:
            logger.warning(f"⚠️  Pas de configuration pour le rôle '{role_name}'")
            return
        
        user_permissions = db.query(UserPermissions).filter(
            UserPermissions.user_id == user_id
        ).first()
        
        if not user_permissions:
            logger.error(f"❌ Permissions non trouvées pour l'utilisateur {user_id}")
            return
        
        # Appliquer les permissions
        for permission_name, permission_value in permissions_config.items():
            setattr(user_permissions, permission_name, permission_value)
        
        db.commit()
        logger.info(f"✅ Permissions Citations appliquées à l'utilisateur {user_id} (rôle: {role_name})")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de l'application des permissions: {e}")
        raise

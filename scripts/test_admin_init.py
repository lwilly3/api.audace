#!/usr/bin/env python3
"""
Script de test pour vérifier la création automatique de l'admin.

Ce script simule le démarrage de l'application et vérifie que
l'utilisateur admin est créé correctement.
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.init_admin import create_default_admin, verify_admin_exists
from app.models.model_user import User
from app.models.model_role import Role
from sqlalchemy import select
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_admin_init")


def test_admin_creation():
    """
    Teste la création automatique de l'admin.
    """
    logger.info("=" * 60)
    logger.info("TEST: Création automatique de l'utilisateur admin")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. Vérifier l'état initial
        logger.info("\n1. Vérification de l'état initial...")
        admin_exists_before = verify_admin_exists(db)
        logger.info(f"   Admin existe avant le test: {admin_exists_before}")
        
        # Compter les admins
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role:
            admin_count = db.query(User).join(User.roles).filter(
                Role.name == "Admin",
                User.is_deleted == False
            ).count()
            logger.info(f"   Nombre d'admins existants: {admin_count}")
        else:
            logger.warning("   ⚠️  Le rôle Admin n'existe pas encore")
        
        # 2. Appeler la fonction de création
        logger.info("\n2. Exécution de create_default_admin()...")
        create_default_admin(db)
        
        # 3. Vérifier le résultat
        logger.info("\n3. Vérification du résultat...")
        admin_exists_after = verify_admin_exists(db)
        logger.info(f"   Admin existe après le test: {admin_exists_after}")
        
        # Lister tous les admins
        admin_users = db.query(User).join(User.roles).filter(
            Role.name == "Admin",
            User.is_deleted == False
        ).all()
        
        logger.info(f"\n   📋 Liste des admins trouvés: {len(admin_users)}")
        for admin in admin_users:
            logger.info(f"      - ID: {admin.id}")
            logger.info(f"        Username: {admin.username}")
            logger.info(f"        Email: {admin.email}")
            logger.info(f"        Actif: {admin.is_active}")
            logger.info(f"        Permissions: {'Oui' if admin.permissions else 'Non'}")
            if admin.permissions:
                permissions_count = sum([
                    admin.permissions.can_view_users,
                    admin.permissions.can_create_users,
                    admin.permissions.can_edit_users,
                    admin.permissions.can_delete_users,
                    admin.permissions.can_manage_permissions,
                ])
                logger.info(f"        Nombre de permissions actives: {permissions_count}/40+")
            logger.info("")
        
        # 4. Test de connexion
        logger.info("4. Test de connexion avec les credentials par défaut...")
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_user = db.query(User).filter(User.username == default_username).first()
        
        if admin_user:
            from app.utils.utils import verify as verify_password
            default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
            
            password_valid = verify_password(default_password, admin_user.password)
            logger.info(f"   Mot de passe valide: {password_valid}")
            
            if password_valid:
                logger.info("   ✅ Connexion réussie avec les credentials par défaut!")
            else:
                logger.error("   ❌ Le mot de passe ne correspond pas!")
        else:
            logger.error(f"   ❌ Utilisateur '{default_username}' non trouvé!")
        
        # 5. Résumé
        logger.info("\n" + "=" * 60)
        if admin_exists_after:
            logger.info("✅ TEST RÉUSSI: L'admin existe et peut se connecter")
            logger.info("\n📝 Credentials de connexion:")
            logger.info(f"   Username: {default_username}")
            logger.info(f"   Password: {os.getenv('ADMIN_PASSWORD', 'Admin@2024!')}")
            logger.info(f"   Email: {admin_user.email if admin_user else 'N/A'}")
            logger.info("\n⚠️  IMPORTANT: Changez ces credentials en production!")
        else:
            logger.error("❌ TEST ÉCHOUÉ: Aucun admin n'a été créé")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR lors du test: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    test_admin_creation()

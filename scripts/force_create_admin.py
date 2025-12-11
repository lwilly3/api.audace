#!/usr/bin/env python3
"""
Script pour forcer la création manuelle de l'admin.

Utilise exactement la même fonction que le démarrage automatique.
Permet de tester et débugger la création de l'admin.
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.init_admin import create_default_admin
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("force_admin")


def main():
    """Force la création de l'admin manuellement."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔧 CRÉATION MANUELLE DE L'ADMIN")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Ce script va tenter de créer l'utilisateur admin")
    logger.info("en utilisant exactement la même fonction que le démarrage automatique.")
    logger.info("")
    
    # Demander confirmation
    response = input("⚠️  Voulez-vous continuer ? (o/n) : ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        logger.info("❌ Opération annulée")
        return
    
    logger.info("")
    logger.info("Création de la session de base de données...")
    db = SessionLocal()
    
    try:
        logger.info("Appel de create_default_admin()...")
        logger.info("")
        
        create_default_admin(db)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ OPÉRATION TERMINÉE")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Vous pouvez maintenant tester la connexion :")
        logger.info("  Username: admin")
        logger.info("  Password: Admin@2024! (ou votre variable d'env ADMIN_PASSWORD)")
        logger.info("")
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("❌ ERREUR")
        logger.error("=" * 70)
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("")
        
        import traceback
        logger.error("Traceback complet:")
        logger.error(traceback.format_exc())
        
    finally:
        logger.info("Fermeture de la session...")
        db.close()
        logger.info("Session fermée")


if __name__ == "__main__":
    main()

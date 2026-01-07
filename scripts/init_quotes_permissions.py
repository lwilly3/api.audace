#!/usr/bin/env python3
"""
Script pour initialiser les permissions du module Citations.

Ce script applique la matrice des permissions définie pour chaque rôle
à tous les utilisateurs existants dans la base de données.

Usage:
    python scripts/init_quotes_permissions.py
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.init_quotes_permissions import initialize_all_quotes_permissions
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("script_quotes_permissions")


def main():
    """Applique les permissions Citations à tous les utilisateurs."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔧 INITIALISATION DES PERMISSIONS MODULE CITATIONS")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Ce script va appliquer les permissions du module Citations")
    logger.info("à tous les utilisateurs existants selon leur rôle.")
    logger.info("")
    logger.info("Matrice des permissions:")
    logger.info("  • Admin: Toutes les permissions")
    logger.info("  • Éditeur: Toutes (avec restrictions métier sur édition/suppression)")
    logger.info("  • Animateur: Vue, création, édition (siennes), transcription, capture")
    logger.info("  • Community Manager: Vue, création, édition, publication")
    logger.info("  • Invité: Vue uniquement")
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
        logger.info("Application des permissions Citations...")
        logger.info("")
        
        initialize_all_quotes_permissions(db)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ OPÉRATION TERMINÉE AVEC SUCCÈS")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Les permissions du module Citations ont été appliquées")
        logger.info("à tous les utilisateurs selon leur rôle.")
        logger.info("")
        logger.info("Note importante:")
        logger.info("  Les restrictions 'Siennes' pour Éditeur et Animateur doivent")
        logger.info("  être gérées dans la logique métier (vérification du created_by)")
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

#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état de la base de données.

Ce script vérifie :
1. La connexion à la base de données
2. L'existence des tables
3. L'existence des migrations Alembic
4. L'existence d'utilisateurs
5. L'existence de rôles
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, engine
from sqlalchemy import inspect, text
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("diagnostic")


def check_database_connection():
    """Vérifie la connexion à la base de données."""
    logger.info("=" * 70)
    logger.info("1️⃣  VÉRIFICATION DE LA CONNEXION À LA BASE DE DONNÉES")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        db.close()
        logger.info("✅ Connexion à la base de données : OK")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la base de données: {e}")
        return False


def check_tables_exist():
    """Vérifie l'existence des tables principales."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("2️⃣  VÉRIFICATION DE L'EXISTENCE DES TABLES")
    logger.info("=" * 70)
    
    required_tables = [
        'users',
        'roles',
        'user_roles',
        'user_permissions',
        'alembic_version'
    ]
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"\n📋 Tables trouvées dans la base ({len(existing_tables)}) :")
        for table in sorted(existing_tables):
            logger.info(f"   - {table}")
        
        logger.info(f"\n🔍 Vérification des tables requises :")
        all_exist = True
        for table in required_tables:
            exists = table in existing_tables
            status = "✅" if exists else "❌"
            logger.info(f"   {status} {table}")
            if not exists:
                all_exist = False
        
        if all_exist:
            logger.info("\n✅ Toutes les tables requises existent")
        else:
            logger.error("\n❌ Certaines tables manquent. Avez-vous exécuté les migrations Alembic ?")
            logger.error("   Commande : alembic upgrade head")
        
        return all_exist
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des tables: {e}")
        return False


def check_alembic_version():
    """Vérifie la version Alembic."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("3️⃣  VÉRIFICATION DES MIGRATIONS ALEMBIC")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        version = result.fetchone()
        db.close()
        
        if version:
            logger.info(f"✅ Version Alembic actuelle : {version[0]}")
            return True
        else:
            logger.warning("⚠️  Aucune version Alembic trouvée")
            logger.warning("   Commande : alembic upgrade head")
            return False
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification de la version Alembic: {e}")
        logger.error("   Les migrations n'ont peut-être pas été exécutées")
        logger.error("   Commande : alembic upgrade head")
        return False


def check_users():
    """Vérifie l'existence d'utilisateurs."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("4️⃣  VÉRIFICATION DES UTILISATEURS")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        
        # Compter les utilisateurs
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE is_deleted = false"))
        user_count = result.fetchone()[0]
        
        logger.info(f"\n📊 Nombre d'utilisateurs actifs : {user_count}")
        
        if user_count > 0:
            # Lister les utilisateurs
            result = db.execute(text("""
                SELECT id, username, email, is_active, created_at 
                FROM users 
                WHERE is_deleted = false 
                ORDER BY id
            """))
            users = result.fetchall()
            
            logger.info(f"\n👥 Liste des utilisateurs :")
            for user in users:
                logger.info(f"   - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Actif: {user[3]}")
        else:
            logger.warning("⚠️  Aucun utilisateur trouvé dans la base de données")
            logger.warning("   Le script d'initialisation devrait créer un admin au démarrage")
        
        db.close()
        return user_count > 0
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des utilisateurs: {e}")
        return False


def check_roles():
    """Vérifie l'existence des rôles."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("5️⃣  VÉRIFICATION DES RÔLES")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        
        # Compter les rôles
        result = db.execute(text("SELECT COUNT(*) FROM roles"))
        role_count = result.fetchone()[0]
        
        logger.info(f"\n📊 Nombre de rôles : {role_count}")
        
        if role_count > 0:
            # Lister les rôles
            result = db.execute(text("SELECT id, name, description FROM roles ORDER BY id"))
            roles = result.fetchall()
            
            logger.info(f"\n🎭 Liste des rôles :")
            for role in roles:
                logger.info(f"   - ID: {role[0]}, Nom: {role[1]}, Description: {role[2] or 'N/A'}")
            
            # Vérifier si le rôle Admin existe
            result = db.execute(text("SELECT id FROM roles WHERE name = 'Admin'"))
            admin_role = result.fetchone()
            
            if admin_role:
                logger.info(f"\n✅ Le rôle 'Admin' existe (ID: {admin_role[0]})")
            else:
                logger.warning("\n⚠️  Le rôle 'Admin' n'existe pas")
                logger.warning("   Il sera créé au prochain démarrage de l'application")
        else:
            logger.warning("⚠️  Aucun rôle trouvé dans la base de données")
            logger.warning("   Le rôle Admin sera créé au démarrage de l'application")
        
        db.close()
        return role_count > 0
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des rôles: {e}")
        return False


def check_admin_users():
    """Vérifie l'existence d'utilisateurs admin."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("6️⃣  VÉRIFICATION DES ADMINISTRATEURS")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        
        # Chercher les admins
        result = db.execute(text("""
            SELECT u.id, u.username, u.email, u.is_active
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'Admin' AND u.is_deleted = false
        """))
        admins = result.fetchall()
        
        if admins:
            logger.info(f"✅ {len(admins)} administrateur(s) trouvé(s) :")
            for admin in admins:
                logger.info(f"   - ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}, Actif: {admin[3]}")
        else:
            logger.warning("⚠️  Aucun administrateur trouvé")
            logger.warning("   Un admin devrait être créé automatiquement au démarrage")
        
        db.close()
        return len(admins) > 0
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des admins: {e}")
        return False


def check_database_url():
    """Affiche la DATABASE_URL utilisée."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("7️⃣  CONFIGURATION DE LA BASE DE DONNÉES")
    logger.info("=" * 70)
    
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Masquer le mot de passe
        if "@" in database_url:
            parts = database_url.split("@")
            user_part = parts[0].split("://")[1].split(":")[0]
            host_part = parts[1]
            masked_url = f"postgresql://{user_part}:****@{host_part}"
            logger.info(f"📌 DATABASE_URL : {masked_url}")
        else:
            logger.info(f"📌 DATABASE_URL : {database_url}")
    else:
        logger.warning("⚠️  Variable DATABASE_URL non définie")
        logger.warning("   Vérifiez vos variables d'environnement")


def main():
    """Fonction principale."""
    logger.info("")
    logger.info("🔍 DIAGNOSTIC DE LA BASE DE DONNÉES")
    logger.info("")
    
    # Vérifier la DATABASE_URL
    check_database_url()
    
    # Vérifier la connexion
    if not check_database_connection():
        logger.error("\n❌ Impossible de se connecter à la base de données")
        logger.error("   Vérifiez votre configuration DATABASE_URL")
        return
    
    # Vérifier les tables
    tables_ok = check_tables_exist()
    if not tables_ok:
        logger.error("\n❌ Les tables n'existent pas")
        logger.error("   Exécutez : alembic upgrade head")
        return
    
    # Vérifier Alembic
    check_alembic_version()
    
    # Vérifier les utilisateurs
    users_exist = check_users()
    
    # Vérifier les rôles
    roles_exist = check_roles()
    
    # Vérifier les admins
    admin_exists = check_admin_users()
    
    # Résumé
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 RÉSUMÉ DU DIAGNOSTIC")
    logger.info("=" * 70)
    logger.info(f"Connexion BD       : ✅")
    logger.info(f"Tables             : {'✅' if tables_ok else '❌'}")
    logger.info(f"Utilisateurs       : {'✅' if users_exist else '⚠️  Aucun'}")
    logger.info(f"Rôles              : {'✅' if roles_exist else '⚠️  Aucun'}")
    logger.info(f"Administrateurs    : {'✅' if admin_exists else '⚠️  Aucun'}")
    logger.info("=" * 70)
    
    if not users_exist or not admin_exists:
        logger.info("")
        logger.info("💡 PROCHAINES ÉTAPES :")
        logger.info("1. Redémarrez votre application pour déclencher l'initialisation de l'admin")
        logger.info("   docker-compose restart")
        logger.info("   # ou sur Dokploy : redémarrer le service")
        logger.info("")
        logger.info("2. Vérifiez les logs au démarrage :")
        logger.info("   docker-compose logs | grep 'Initialisation de l'utilisateur'")
        logger.info("")
        logger.info("3. Si rien ne se passe, vérifiez que le fichier maintest.py")
        logger.info("   contient bien le lifespan event handler")
    else:
        logger.info("")
        logger.info("✅ Tout semble en ordre ! Vous pouvez vous connecter avec :")
        logger.info("   Username: admin")
        logger.info("   Password: Admin@2024! (ou votre mot de passe personnalisé)")
    
    logger.info("")


if __name__ == "__main__":
    main()

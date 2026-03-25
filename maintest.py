from functools import lru_cache  # Décorateur pour mettre en cache les appels de fonction
from contextlib import asynccontextmanager  # Pour le lifespan event handler
from fastapi import FastAPI, Request  # Classe principale pour créer une application FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware pour la gestion des CORS
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.__version__ import get_version, get_version_info, API_V1_PREFIX
# from db.init_db_rolePermissions import create_default_role_and_permission
# from app.db.init_db_rolePermissions import create_default_role_and_permission

# from app.db.database import get_db
from routeur.search_route import (
    search_show,
    search_user_route

)

from routeur import (
    #  posts,

       auth,
        #  votes,
       audit_log_route,
       guest_route,
         notification_route,
     permissions_route,
     role_route,
     users_route,
     presenter_route,
     guest_route,
     emission_route,
     show_route,
     dashbord_route,role_route,
     segment_route, # Ajout de l'importation du routeur de segments
     setup_route,  # Route de configuration initiale (sans auth)
     version_route,  # Route d'information sur la version
     ovh_route,  # Routes pour la consultation des services OVH
     scaleway_route,  # Routes pour la consultation des services Scaleway
     social_route,  # Routes pour le module Social (réseaux sociaux)
     public_route,  # Routes publiques pour l'integration WordPress
     article_route,  # Routes pour les articles WordPress (proxy wp-json)
     two_factor_route,  # Routes pour le 2FA (TOTP)
     backup_route,  # Routes pour la gestion des sauvegardes (Backup Management)
     subtitle_route,  # Routes pour l'extraction de sous-titres (yt-dlp)
     inventory_location_route,  # Routes pour les localisations inventaire (entreprises, sites, locaux)
     inventory_settings_route,  # Routes pour les parametres du module inventaire
     inventory_equipment_route,  # Routes pour les equipements inventaire
     inventory_movement_route,  # Routes pour les mouvements inventaire (transferts, prets, approbations)
     inventory_maintenance_route,  # Routes pour la maintenance inventaire
     inventory_subscription_route,  # Routes pour les abonnements/services inventaire
     inventory_dashboard_route,  # Routes pour le dashboard inventaire (alertes, stats)
     ga_analytics_route,  # Routes pour Google Analytics 4 (GA4 Web Analytics)
     rss_route,  # Routes pour l'agregateur RSS (Social)



)  # Importation des routeurs de l'appication


from routeur.search_route import (
    search_audit_log_route,
      search_guests_route,
     search_presenter_history,
       search_presenter_route,
       search_user_route
)
#   invites, posts, users, auth, votes, presentateur,
#     programs, segment_conducteur, competences, conducteur
from app.config.config import settings  # Importation des paramètres de configuration
from sqlalchemy import text
from app.middleware.logger import LoggerMiddleware  # Importation du middleware personnalisé

# Configuration du logger global
import logging
from logging.handlers import RotatingFileHandler  # Gestionnaire pour fichiers de logs rotatifs

# Configuration de base pour les logs
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Format des logs
file_handler = RotatingFileHandler(
    "api_logs.log", maxBytes=5 * 1024 * 1024, backupCount=3
)  # Fichier de logs avec rotation (5 Mo max, 3 sauvegardes)
file_handler.setFormatter(log_formatter)  # Appliquer le format au gestionnaire

# Handler console pour que les logs apparaissent dans Docker
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])  # Fichier + stdout
logger = logging.getLogger("hapson-api")  # Créer un logger spécifique pour l'API

@lru_cache
def get_settings():
    """
    Fonction pour charger les paramètres de configuration avec mise en cache.
    Améliore les performances en évitant les rechargements inutiles.
    """
    return settings()


def ensure_roles_require_2fa_column(db) -> None:
    """
    Garantit la presence de la colonne roles.require_2fa.

    Ce garde-fou evite un crash complet de l'API si la base est en retard
    par rapport au modele SQLAlchemy (cas observe apres reset partiel).
    """
    db.execute(text(
        """
        ALTER TABLE roles
        ADD COLUMN IF NOT EXISTS require_2fa BOOLEAN NOT NULL DEFAULT FALSE
        """
    ))
    db.commit()


def ensure_users_2fa_columns(db) -> None:
    """
    Garantit la presence des colonnes users liees au 2FA.

    Evite les erreurs UndefinedColumn au login quand une base ancienne
    n'a pas recu toutes les migrations 2FA.
    """
    db.execute(text(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE
        """
    ))
    db.execute(text(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS totp_secret_encrypted TEXT
        """
    ))
    db.execute(text(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS backup_codes_hash JSONB
        """
    ))
    db.commit()


# Lifespan event handler pour initialiser l'admin au démarrage
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire d'événements du cycle de vie de l'application.
    
    Startup:
        - Initialise l'utilisateur administrateur par défaut si aucun admin n'existe
        - Garantit qu'il y a toujours au moins un admin pouvant se connecter
    
    Shutdown:
        - Nettoyage des ressources si nécessaire
    """
    # Startup
    from app.db.database import SessionLocal
    from app.db.init_admin import create_default_admin
    from app.services.social_scheduler import scheduler as social_scheduler
    from app.services.backup_scheduler import backup_scheduler
    
    logger.info("🚀 Démarrage de l'application - Vérification de l'admin par défaut...")
    
    db = SessionLocal()
    try:
        ensure_roles_require_2fa_column(db)
        logger.info("✅ Verification schema roles.require_2fa terminee")
        ensure_users_2fa_columns(db)
        logger.info("✅ Verification schema users 2FA terminee")
        create_default_admin(db)
        logger.info("✅ Initialisation de l'admin terminée")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de l'admin: {e}")
    finally:
        db.close()
    
    # Démarrer le scheduler Social (tâches périodiques)
    social_scheduler.start()
    logger.info("✅ Social scheduler démarré")

    # Demarrer le scheduler Backup (sauvegarde automatique quotidienne)
    backup_scheduler.start()
    logger.info("✅ Backup scheduler demarre")

    yield  # L'application s'exécute ici

    # Shutdown
    backup_scheduler.stop()
    social_scheduler.stop()
    logger.info("🛑 Arrêt de l'application...")


# Initialisation de l'application FastAPI avec lifespan
app = FastAPI(
    lifespan=lifespan,
    title="Audace API",
    description="API pour la gestion des émissions radio",
    version=get_version(),  # Version dynamique depuis __version__.py
    docs_url="/docs",
    redoc_url="/redoc",
    # Force HTTPS pour Swagger UI (évite mixed content)
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
    # Force les URLs en HTTPS
    root_path="",
    servers=[
        {"url": "https://api.cloud.audace.ovh", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Local development"}
    ],
    # Informations de contact et licence
    contact={
        "name": "Audace API Support",
        "url": "https://api.cloud.audace.ovh",
        "email": "support@audace.ovh"
    },
    license_info={
        "name": "Proprietary",
    }
)


# Handler custom pour RequestValidationError — evite UnicodeDecodeError
# quand des fichiers binaires (.sql.gz) sont dans les details de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        clean_error = {}
        for key, value in error.items():
            if isinstance(value, bytes):
                clean_error[key] = f"<binary {len(value)} bytes>"
            else:
                clean_error[key] = value
        errors.append(clean_error)
    logger.warning(f"Validation error on {request.method} {request.url.path}: {errors}")
    return JSONResponse(status_code=422, content={"detail": errors})


# Ajout du middleware personnalisé pour journaliser les requêtes
app.add_middleware(LoggerMiddleware)

# Ajout du middleware de versioning de l'API
from app.middleware.version_middleware import APIVersionMiddleware
app.add_middleware(APIVersionMiddleware)

# Ajout du middleware CORS pour autoriser les requêtes provenant des domaines autorisés
origins = [
    "https://app.cloud.audace.ovh",
    "https://api.cloud.audace.ovh",
    "https://app.radio.audace.ovh",
    "https://api.radio.audace.ovh",
    "https://www.radioaudace.com",
    "https://radioaudace.com",
    "http://localhost:5180",
    "http://localhost:5173",
    "http://127.0.0.1:5180",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Liste des origines autorisées
    allow_credentials=True,  # Autorise l'envoi de cookies
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
    expose_headers=["X-Total-Count"],  # Expose le header de pagination au frontend
)

# Inclusion des routeurs pour structurer les endpoints de l'application
# ⚠️ IMPORTANT: setup_route doit être inclus EN PREMIER (pas d'auth requise)
app.include_router(setup_route.router)  # Routes de configuration initiale (SANS authentification)
app.include_router(version_route.router)  # Routes d'information sur la version
app.include_router(public_route.router)  # Routes publiques integration WordPress (SANS authentification)

# app.include_router(posts.router)  # Routes liées aux posts
app.include_router(users_route.router)  # Routes liées aux utilisateurs

# app.include_router(users.router)  # Routes liées aux utilisateurs
app.include_router(auth.router)  # Routes pour l'authentification
# app.include_router(votes.router)  # Routes pour les votes
app.include_router(presenter_route.router)  # Routes pour les présentateurs
# app.include_router(programs.router)  # Routes pour les programmes
# app.include_router(segment_conducteur.router)  # Routes pour les segments du conducteur
# app.include_router(conducteur.router)  # Routes pour le conducteur
# app.include_router(competences.router)  # Routes pour les compétences
# app.include_router(guest_route.router)  # Routes pour les invités
app.include_router(guest_route.router)  # Routes pour les invitations
app.include_router(emission_route.router)  # Routes pour les émissions 
app.include_router(show_route.router)  # Routes pour les émissions show_route
app.include_router(search_show.router)  # Routes pour les recherches de conducteurs 
app.include_router(dashbord_route.router) # Routes pour le tableau de bord  search_user_route
app.include_router(permissions_route.router) # Routes pour les permissions
app.include_router(search_user_route.router) # Routes pour les recherches d'utilisateurs role_route
app.include_router(role_route.router) # Routes pour les roles 
app.include_router(segment_route.router) # Routes pour les segments

# /// add pour test
app.include_router(notification_route.router) # Routes pour les notifications
app.include_router(audit_log_route.router) # Routes pour les journaux d'audit
app.include_router(ovh_route.router) # Routes pour la consultation des services OVH
app.include_router(scaleway_route.router) # Routes pour la consultation des services Scaleway
app.include_router(social_route.router) # Routes pour le module Social (réseaux sociaux)
app.include_router(article_route.router) # Routes pour les articles WordPress
app.include_router(two_factor_route.router) # Routes pour le 2FA (TOTP)
app.include_router(backup_route.router) # Routes pour la gestion des sauvegardes
app.include_router(subtitle_route.router) # Routes pour l'extraction de sous-titres
app.include_router(inventory_location_route.router) # Routes pour les localisations inventaire
app.include_router(inventory_settings_route.router) # Routes pour les parametres inventaire
app.include_router(inventory_equipment_route.router) # Routes pour les equipements inventaire
app.include_router(inventory_movement_route.router) # Routes pour les mouvements inventaire
app.include_router(inventory_maintenance_route.router) # Routes pour la maintenance inventaire
app.include_router(inventory_subscription_route.router) # Routes pour les abonnements inventaire
app.include_router(inventory_dashboard_route.router) # Routes pour le dashboard inventaire
app.include_router(ga_analytics_route.router) # Routes pour Google Analytics 4 (GA4 Web Analytics)
app.include_router(rss_route.router) # Routes pour l'agregateur RSS (Social)



# Endpoint par défaut pour vérifier que l'API est opérationnelle
@app.get("/")
def par_defaut():
    """
    Endpoint par défaut pour vérifier le bon fonctionnement de l'API.
    """
    return {"BIEBVENUE": "HAPSON API pour AMG"}

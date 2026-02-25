from functools import lru_cache  # Décorateur pour mettre en cache les appels de fonction
from contextlib import asynccontextmanager  # Pour le lifespan event handler
from fastapi import FastAPI  # Classe principale pour créer une application FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware pour la gestion des CORS
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
logging.basicConfig(level=logging.INFO, handlers=[file_handler])  # Configurer le niveau et le gestionnaire des logs
logger = logging.getLogger("hapson-api")  # Créer un logger spécifique pour l'API

@lru_cache
def get_settings():
    """
    Fonction pour charger les paramètres de configuration avec mise en cache.
    Améliore les performances en évitant les rechargements inutiles.
    """
    return settings()


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
    
    logger.info("🚀 Démarrage de l'application - Vérification de l'admin par défaut...")
    
    db = SessionLocal()
    try:
        create_default_admin(db)
        logger.info("✅ Initialisation de l'admin terminée")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de l'admin: {e}")
    finally:
        db.close()
    
    yield  # L'application s'exécute ici
    
    # Shutdown (optionnel)
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


# Ajout du middleware personnalisé pour journaliser les requêtes
app.add_middleware(LoggerMiddleware)

# Ajout du middleware de versioning de l'API
from app.middleware.version_middleware import APIVersionMiddleware
app.add_middleware(APIVersionMiddleware)

# Ajout du middleware CORS pour autoriser les requêtes provenant de tous les domaines
origins = ["*"]  # Permet l'accès depuis n'importe quelle origine
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Liste des origines autorisées
    allow_credentials=True,  # Autorise l'envoi de cookies
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
)

# Inclusion des routeurs pour structurer les endpoints de l'application
# ⚠️ IMPORTANT: setup_route doit être inclus EN PREMIER (pas d'auth requise)
app.include_router(setup_route.router)  # Routes de configuration initiale (SANS authentification)
app.include_router(version_route.router)  # Routes d'information sur la version

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



# Endpoint par défaut pour vérifier que l'API est opérationnelle
@app.get("/")
def par_defaut():
    """
    Endpoint par défaut pour vérifier le bon fonctionnement de l'API.
    """
    return {"BIEBVENUE": "HAPSON API pour AMG"}

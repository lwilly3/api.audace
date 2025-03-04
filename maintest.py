from functools import lru_cache  # Décorateur pour mettre en cache les appels de fonction
from fastapi import FastAPI  # Classe principale pour créer une application FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware pour la gestion des CORS
# from db.init_db_rolePermissions import create_default_role_and_permission
# from app.db.init_db_rolePermissions import create_default_role_and_permission

# from app.db.database import get_db
from routeur.search_route import (
    search_show

)

from routeur import (
    #  posts, 
     users,
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
     dashbord_route,

   
)  # Importation des routeurs de l'application


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


# Initialisation de l'application FastAPI
app = FastAPI()



# # Événement de démarrage
# @app.on_event("startup")
# def initialize_roles_permissions():
#     print("Initializing roles and permissions...")
#     # Utiliser la dépendance get_db
#     db = next(get_db())  # Obtenir une instance de session
#     create_default_role_and_permission(db)
#     print("Roles and permissions initialized successfully!")




# Ajout du middleware personnalisé pour journaliser les requêtes
app.add_middleware(LoggerMiddleware)

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
app.include_router(dashbord_route.router) # Routes pour le tableau de bord 
app.include_router(permissions_route.router)



# Endpoint par défaut pour vérifier que l'API est opérationnelle
@app.get("/")
def par_defaut():
    """
    Endpoint par défaut pour vérifier le bon fonctionnement de l'API.
    """
    return {"BIEBVENUE": "HAPSON API pour AMG"}

import time  # Module pour mesurer le temps
from fastapi import Request  # Classe pour représenter une requête HTTP
from starlette.middleware.base import BaseHTTPMiddleware  # Classe de base pour créer des middlewares
import logging  # Module pour la gestion des logs

# Configuration du logger
logger = logging.getLogger("hapson-api")  # Création d'un logger spécifique pour l'API

class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour journaliser les requêtes entrantes, les réponses et le temps de traitement.
    """
    async def dispatch(self, request: Request, call_next):
        # Temps de départ pour mesurer la durée de la requête
        start_time = time.time()

        # Log de la requête entrante
        logger.info(f"Incoming Request: {request.method} {request.url}")

        # Passer la requête au prochain middleware ou endpoint
        response = await call_next(request)

        # Calculer le temps de traitement
        process_time = time.time() - start_time

        # Log de la réponse avec le statut et le temps de traitement
        logger.info(f"Completed Request: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.2f}s")

        # Retourner la réponse au client
        return response

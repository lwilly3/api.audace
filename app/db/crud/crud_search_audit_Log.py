
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import AuditLog, User  # Assurez-vous que ces classes sont correctement importées

def search_audit_logs(db: Session, user_id=None, action=None, table_name=None):
    """
    Recherche des logs d'audit dans la base de données en fonction de critères spécifiques.
    
    Args:
    - db (Session): La session de base de données.
    - user_id (int, optionnel): L'ID de l'utilisateur pour filtrer les logs.
    - action (str, optionnel): L'action (create, update, delete) pour filtrer les logs.
    - table_name (str, optionnel): Le nom de la table pour filtrer les logs.

    Returns:
    - list: Liste des logs d'audit correspondant aux critères de recherche.
    
    Levée d'exceptions:
    - HTTP 500: Erreur interne du serveur si une exception se produit pendant la recherche.
    - HTTP 404: Si aucun log ne correspond aux critères de recherche.
    """
    try:
        # Construction de la requête de base pour les logs d'audit
        query = db.query(AuditLog).join(User).filter(
            (user_id is None or AuditLog.user_id == user_id),
            (action is None or AuditLog.action.ilike(f"%{action}%")),
            (table_name is None or AuditLog.table_name.ilike(f"%{table_name}%"))
        )

        # Exécution de la requête
        logs = query.all()

        # Si aucun log n'est trouvé, on lève une exception 404
        if not logs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching audit logs found.")

        return logs

    except SQLAlchemyError as e:
        # Gestion des erreurs avec une exception HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        # Autres erreurs possibles
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching audit logs: {str(e)}"
        )
















# # database.py
# from datetime import datetime

# # Base de données simulée pour les logs d'audit
# audit_logs_db = [
#     {"id": 1, "user_id": 1, "action": "create", "table_name": "users", "timestamp": datetime.now()},
#     {"id": 2, "user_id": 2, "action": "update", "table_name": "roles", "timestamp": datetime.now()},
#     {"id": 3, "user_id": 1, "action": "delete", "table_name": "users", "timestamp": datetime.now()},
# ]

# def search_audit_logs(user_id=None, action=None, table_name=None):
#     """
#     Rechercher des logs d'audit par utilisateur, action, ou table_name.
#     """
#     return [
#         log
#         for log in audit_logs_db
#         if (user_id is None or user_id == log["user_id"]) and
#            (action is None or action.lower() in log["action"].lower()) and
#            (table_name is None or table_name.lower() in log["table_name"].lower())
#     ]

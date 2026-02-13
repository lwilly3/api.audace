
# routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.schemas import AuditLogSearch
from app.db.crud.crud_search_audit_Log import search_audit_logs
from app.db.database import get_db
from core.auth import oauth2

router = APIRouter()

@router.get("/audit-logs/search", response_model=List[AuditLogSearch])
def search_audit_logs_route(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Rechercher des logs d'audit par utilisateur, action, ou table_name.
    """
    filtered_logs = search_audit_logs(db, user_id, action, table_name)

    if not filtered_logs:
        raise HTTPException(status_code=404, detail="No audit logs found matching the search criteria")

    return filtered_logs























# from fastapi import FastAPI, HTTPException, Query
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# app = FastAPI()

# # Simulated database of audit logs
# audit_logs_db = [
#     {"id": 1, "user_id": 1, "action": "create", "table_name": "users", "timestamp": datetime.now()},
#     {"id": 2, "user_id": 2, "action": "update", "table_name": "roles", "timestamp": datetime.now()},
#     {"id": 3, "user_id": 1, "action": "delete", "table_name": "users", "timestamp": datetime.now()},
# ]

# # Models
# class AuditLog(BaseModel):
#     """
#     Modèle pour représenter un log d'audit.
#     """
#     id: int
#     user_id: int
#     action: str
#     table_name: str
#     timestamp: datetime

# # Route pour rechercher des logs d'audit
# @app.get("/audit-logs/search", response_model=List[AuditLog])
# def search_audit_logs(user_id: Optional[int] = None, action: Optional[str] = None, table_name: Optional[str] = None):
#     """
#     Rechercher des logs d'audit par utilisateur, action, ou nom de la table.
#     La recherche peut être effectuée sur un ou plusieurs critères à la fois.
#     """
#     filtered_logs = []

#     for log in audit_logs_db:
#         if (user_id is None or user_id == log["user_id"]) and \
#            (action is None or action.lower() in log["action"].lower()) and \
#            (table_name is None or table_name.lower() in log["table_name"].lower()):
#             filtered_logs.append(log)

#     # Si aucun log n'est trouvé
#     if not filtered_logs:
#         raise HTTPException(status_code=404, detail="No audit logs found matching the search criteria")

#     # Retourner les résultats
#     return filtered_logs

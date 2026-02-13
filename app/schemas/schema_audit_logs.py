from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional, List

class AuditLogBase(BaseModel):
    """
    Modèle de base pour créer un log d'audit.
    """
    action: str
    user_id: Optional[int] = None
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    """
    Modèle pour représenter un log d'audit, avec l'ID généré par la base de données.
    """
    id: int
    timestamp: datetime
    username: Optional[str] = None  # Nom de l'utilisateur (joint depuis la table users)

    model_config = ConfigDict(from_attributes=True)


class AuditLogPaginated(BaseModel):
    """
    Réponse paginée pour les logs d'audit.
    """
    total: int
    items: List[AuditLog]
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class AuditLogStats(BaseModel):
    """
    Statistiques des logs d'audit.
    """
    total_logs: int
    actions: dict  # Comptage par type d'action
    tables: dict   # Comptage par table
    recent_activity: List[AuditLog]  # Les 10 dernières actions

    model_config = ConfigDict(from_attributes=True)

 
class AuditLogSearch(BaseModel):
    """
    Modèle pour rechercher un log d'audit.
    """
    id: int
    user_id: int
    action: str
    table_name: str
    timestamp: datetime
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

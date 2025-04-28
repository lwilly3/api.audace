from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional

class AuditLogBase(BaseModel):
    """
    Modèle de base pour créer un log d'audit (utilisé lors de la création ou mise à jour).
    """
    action: str
    user_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime = datetime.utcnow()  # Par défaut, utilise l'heure actuelle
    is_archived: bool = False
    model_config = ConfigDict(from_attributes=True)  # 💡 corrige l'avertissement




class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    """
    Modèle pour représenter un log d'audit, avec l'ID généré par la base de données.
    """
    id: int


    model_config = ConfigDict(from_attributes=True)  # 💡 corrige l'avertissement


 
class AuditLogSearch(BaseModel):
    """
    Modèle pour rechercher un log d'audit.
    """
    id: int
    user_id: int
    action: str
    table_name: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


















# # models.py
# from pydantic import BaseModel
# from datetime import datetime
# from typing import Optional

# class AuditLog(BaseModel):
#     """
#     Modèle pour représenter un log d'audit.
#     """
#     id: int
#     action: str
#     user_id: Optional[int] = None
#     details: Optional[str] = None
#     timestamp: datetime
#     is_archived: bool = False



# class AuditLogSearch(BaseModel):
#     """
#     Modèle pour représenter un log d'audit.
#     """
#     id: int
#     user_id: int
#     action: str
#     table_name: str
#     timestamp: datetime







# # from pydantic import BaseModel
# # from datetime import datetime

# # class AuditLogBase(BaseModel):
# #     user_id: int
# #     action: str
# #     table_name: str
# #     record_id: int

# # class AuditLogCreate(AuditLogBase):
# #     pass

# # class AuditLogRead(AuditLogBase):
# #     id: int
# #     timestamp: datetime

# #     model_config = {
# #         "from_attributes": True,
# #     }

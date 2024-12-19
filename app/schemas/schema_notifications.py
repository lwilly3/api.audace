# schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationCreate(BaseModel):
    """
    Schéma pour la création d'une notification.
    """
    user_id: int
    title: str
    message: str

    model_config = {
        "from_attributes": True,
    }

class NotificationUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'une notification.
    """
    title: Optional[str] = None
    message: Optional[str] = None
    read: Optional[bool] = None

    model_config = {
        "from_attributes": True,
    }

class NotificationRead(BaseModel):
    """
    Schéma pour une notification existante.
    """
    id: int
    user_id: int
    title: str
    message: str
    created_at: datetime
    read: bool = False
    is_deleted: bool = False

    model_config = {
        "from_attributes": True,
    }














# from pydantic import BaseModel
# from typing import Optional
# from datetime import datetime

# class NotificationBase(BaseModel):
#     message: str
#     read: bool

# class NotificationCreate(NotificationBase):
#     user_id: int

# class NotificationRead(NotificationBase):
#     id: int
#     timestamp: datetime

#     model_config = {
#         "from_attributes": True,  # Activates attribute-based mapping
#     }

# class NotificationUpdate(BaseModel):
#     read: Optional[bool]

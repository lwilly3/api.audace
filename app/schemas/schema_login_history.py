from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginHistoryBase(BaseModel):
    user_id: int
    ip_address: Optional[str]

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class LoginHistoryCreate(LoginHistoryBase):
    pass

    



class LoginHistoryRead(LoginHistoryBase):
    id: int
    timestamp: datetime

    model_config = {
        "from_attributes": True,
    }

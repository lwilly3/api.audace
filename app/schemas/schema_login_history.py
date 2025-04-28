from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class LoginHistoryBase(BaseModel):
    user_id: int
    ip_address: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class LoginHistoryCreate(LoginHistoryBase):
    pass

class LoginHistoryRead(LoginHistoryBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

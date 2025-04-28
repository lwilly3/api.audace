from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PresenterHistoryBase(BaseModel):
    presenter_id: int
    name: Optional[str]
    biography: Optional[str]
    updated_by: int


    model_config = ConfigDict(from_attributes=True)

class PresenterHistoryCreate(PresenterHistoryBase):
    pass

class PresenterHistoryRead(PresenterHistoryBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

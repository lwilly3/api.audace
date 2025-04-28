from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ArchivedAuditLogBase(BaseModel):
    user_id: int
    action: str
    table_name: str
    record_id: int

class ArchivedAuditLogCreate(ArchivedAuditLogBase):
    model_config = ConfigDict(from_attributes=True)

class ArchivedAuditLogRead(ArchivedAuditLogBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

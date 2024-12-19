from pydantic import BaseModel
from datetime import datetime

class ArchivedAuditLogBase(BaseModel):
    user_id: int
    action: str
    table_name: str
    record_id: int

class ArchivedAuditLogCreate(ArchivedAuditLogBase):
    pass

class ArchivedAuditLogRead(ArchivedAuditLogBase):
    id: int
    timestamp: datetime

    model_config = {
        "from_attributes": True,
    }

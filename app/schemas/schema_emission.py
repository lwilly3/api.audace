from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class EmissionCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Titre de l'émission", json_schema_extra={"example": "Ma super émission"})
    synopsis: Optional[str] = Field(None, max_length=1000, description="Synopsis de l'émission", json_schema_extra={"example": "Résumé..."})
    type : Optional[str] = Field(None, max_length=1000, description="Type de l'émission")
    duration :Optional[int] = Field(None, description="Durée de l'émission")
    frequency : Optional[str] = Field(None, max_length=1000, description="Fréquence de l'émission")
    description : Optional[str] = Field(None, max_length=1000, description="Description de l'émission")

    model_config = ConfigDict(from_attributes=True)


class EmissionResponse(EmissionCreate):
    id: int
    created_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmissionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Titre de l'émission")
    synopsis: Optional[str] = Field(None, max_length=1000, description="Synopsis de l'émission")
    type : Optional[str] = Field(None, max_length=1000, description="Type de l'émission")
    duration :Optional[int] = Field(None,  description="Durée de l'émission")
    frequency : Optional[str] = Field(None, max_length=1000, description="Fréquence de l'émission")
    description : Optional[str] = Field(None, max_length=1000, description="Description de l'émission")

    model_config = ConfigDict(from_attributes=True)


class EmissionSoftDelete(BaseModel):
    is_deleted: bool = True
    deleted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmissionPagination(BaseModel):
    skip: int = 0
    limit: int = 10

    model_config = ConfigDict(from_attributes=True)


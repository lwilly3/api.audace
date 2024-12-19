from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EmissionCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Titre de l'émission")
    synopsis: Optional[str] = Field(None, max_length=1000, description="Synopsis de l'émission")
 
    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }



class EmissionResponse(EmissionCreate):
    id: int
    created_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }



class EmissionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Titre de l'émission")
    synopsis: Optional[str] = Field(None, max_length=1000, description="Synopsis de l'émission")

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }



class EmissionSoftDelete(BaseModel):
    is_deleted: bool = True
    deleted_at: datetime

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class EmissionPagination(BaseModel):
    skip: int = 0
    limit: int = 10

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


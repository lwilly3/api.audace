
# models.py
from typing import List, Optional
from pydantic import BaseModel

class Role(BaseModel):
    """
    Modèle pour représenter un rôle.
    """
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[int]  # Liste des IDs des permissions
    is_deleted: bool = False


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class Permission(BaseModel):
    """
    Modèle pour représenter une permission.
    """
    id: int
    name: str
    description: Optional[str] = None


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }










# from pydantic import BaseModel

# Base Permission Schema
class PermissionBase(BaseModel):
    name: str
    

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schema for Creating a Permission
class PermissionCreate(PermissionBase):
    description: Optional[str] = None



    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }
    

# Schema for Reading a Permission
class PermissionRead(PermissionBase):
    id: int
    description: Optional[str] = None

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schema for Updating a Permission
class PermissionUpdate(BaseModel):
    name: str
    

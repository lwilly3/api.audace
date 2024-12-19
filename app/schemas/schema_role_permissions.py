from pydantic import BaseModel

class RolePermissionBase(BaseModel):
    role_id: int
    permission_id: int

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class RolePermissionCreate(RolePermissionBase):
    pass

class RolePermissionRead(RolePermissionBase):
    pass

    model_config = {
        "from_attributes": True,
    }

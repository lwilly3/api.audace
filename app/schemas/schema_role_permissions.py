from pydantic import BaseModel, ConfigDict

class RolePermissionBase(BaseModel):
    role_id: int
    permission_id: int

    model_config = ConfigDict(from_attributes=True)

class RolePermissionCreate(RolePermissionBase):
    pass

class RolePermissionRead(RolePermissionBase):
    pass

    model_config = ConfigDict(from_attributes=True)

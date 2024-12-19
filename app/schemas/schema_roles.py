from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int

    model_config = {
        "from_attributes": True,
    }

class RoleUpdate(BaseModel):
    name: str


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

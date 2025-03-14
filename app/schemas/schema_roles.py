from pydantic import BaseModel
# app/schemas/role.py
from typing import Optional, List

class RoleBase(BaseModel):
    name: str

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    users: Optional[List[int]] = None  # Liste des IDs des utilisateurs associés


    model_config = {
        "from_attributes": True,
    }

class RoleUpdate(BaseModel):
    name: Optional[str]


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

# Schéma pour assigner ou retirer des rôles
class UserRoleAssign(BaseModel):
    role_ids: List[int]  # Liste des IDs des rôles à assigner ou retirer

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

# ///////////////////////////////////////////



# # Schéma de base pour un rôle
# class RoleBase(BaseModel):
#     name: str

# Schéma pour la création d'un rôle
# class RoleCreate(RoleBase):
#     pass  # Hérite de RoleBase, pas besoin d'ajouter autre chose pour l'instant

# # Schéma pour la mise à jour d'un rôle
# class RoleUpdate(BaseModel):
#     name: Optional[str] = None

#     class Config:
#         from_attributes = True

# # Schéma pour la lecture d'un rôle (avec ID et relations)
# class RoleRead(RoleBase):
#     id: int
#     users: Optional[List[int]] = None  # Liste des IDs des utilisateurs associés

    # class Config:
    #     from_attributes = True
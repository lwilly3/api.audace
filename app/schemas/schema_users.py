
from pydantic import BaseModel, EmailStr
from typing import Optional,List
from datetime import datetime

class User(BaseModel):
    """
    Modèle de base pour créer ou mettre à jour un utilisateur.
    """
    username: str
    email: str
    is_active: bool = True


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class PermissionsResponse(BaseModel):
    can_create_showplan: bool
    can_edit_showplan: bool
    can_archive_showplan: bool
    can_delete_showplan: bool
    can_destroy_showplan: bool
    can_changestatus_showplan: bool


class UserInDB(User):
    """
    Modèle étendu pour inclure des informations supplémentaires stockées en base.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class UserWithPermissionsResponse(BaseModel):
    user: UserInDB
    permissions: PermissionsResponse

    model_config = {
            "from_attributes": True,  # Remplace orm_mode
        }

class LoginLog(BaseModel):
    """
    Modèle pour représenter une connexion utilisateur.
    """
    user_id: int
    timestamp: datetime
    ip_address: str


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class NotificationUser(BaseModel):
    """
    Modèle pour représenter une notification.
    """
    user_id: int
    message: str
    created_at: datetime

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class AuditLogUser(BaseModel):
    """
    Modèle pour représenter un log d'audit.
    """
    user_id: int
    action: str
    timestamp: datetime

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class UserSearch(BaseModel):
    """
    Modèle pour représenter un utilisateur.
    """
    id: int
    name: str
    email: str
    role: str
    created_at: datetime


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }




# from pydantic import BaseModel, EmailStr
# from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    name: Optional[str]=""
    family_name: Optional[str] =""
    # roles: Optional[str]=""
    phone_number: Optional[str] =""
   

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


    

# Schéma de base pour les rôles (si applicable)
class UserRoleRead(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    } # Remplace orm_mode dans Pydantic v2


class UserSrearchResponse(UserBase):
    id: int
    created_at:Optional[ datetime]
    profilePicture: Optional[str]
    is_active: Optional[bool] = True
    roles: Optional[List[UserRoleRead] ] # Liste des rôles associés à l'utilisateur

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    } # Remplace orm_mode dans Pydantic v2










class UserCreate(UserBase):
    password: str

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }

class UserRead(UserBase):
    id: int
    is_active: bool

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    family_name: Optional[str] = None
    phone_number: Optional[str] = None
    profilePicture: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None
    deleted_at: Optional[datetime] = None
    roles: Optional[List[int]] = None
    
    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }




# class UserCreate(BaseModel):
#     email:EmailStr
#     password:str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }



# class Token(BaseModel):
#     access_token:str
#     token_type:str

# class TokenData(BaseModel):
#     id: Optional[int]=None
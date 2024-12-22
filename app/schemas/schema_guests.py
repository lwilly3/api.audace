
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional,List







class GuestCreate(BaseModel):
    """Validation pour créer un invité."""
    name: str = Field(..., max_length=100, description="Nom de l'invité", example="Marie Claire")
    contact_info: Optional[str] = Field(None, max_length=255, description="Informations de contact", example="vie a douala")
    biography: Optional[str] = Field(None, description="Biographie", example="Marie Claire est une experte en développement durable.")
     # role phone email
    role: Optional[str] = Field(None, description="role", example="journalist")
    phone: Optional[str] = Field(None, description="phone", example="+237 05 06 07 06")
    email: Optional[str] = Field(None, description="email", example="Marie@gmail.com")


class GuestUpdate(BaseModel):
    """Validation pour mettre à jour un invité existant."""
    name: Optional[str] = Field(None, max_length=100, description="Nom de l'invité")
    contact_info: Optional[str] = Field(None, max_length=255, description="Informations de contact")
    biography: Optional[str] = Field(None, description="Biographie")
    role: Optional[str] = Field(None, description="role")
    phone: Optional[str] = Field(None, description="phone")
    email: Optional[str] = Field(None, description="email")



class GuestResponse(BaseModel):
    """Réponse après validation ou récupération d'un invité."""
    name: str
    contact_info: Optional[str]
    biography: Optional[str]
    role: Optional[str] = Field(None, description="role")
    phone: Optional[str] = Field(None, description="phone")
    email: Optional[str] = Field(None, description="email")
    segments: List[str] = Field(default=[], description="Liste des segments associés")


















# from datetime import datetime
# from pydantic import BaseModel
# from typing import Optional

# class GuestCreate(BaseModel):
#     """Modèle de validation pour la création d'un invité"""
#     name: str
#     contact_info: str
#     details: Optional[str] = None
#     is_active: bool = True  # Par défaut, un invité est actif

#     model_config = {
#         "from_attributes": True,  # Remplace orm_mode
#     }

# class GuestUpdate(BaseModel):
#     """Modèle de validation pour la mise à jour d'un invité"""
#     name: Optional[str] = None
#     contact_info: Optional[str] = None
#     details: Optional[str] = None
#     is_active: Optional[bool] = None  # Peut être mis à jour pour désactiver un invité


#     model_config = {
#         "from_attributes": True,  # Remplace orm_mode
#     }














# # # models.py
# # from pydantic import BaseModel
# # from datetime import datetime
# # from typing import Optional


# class Guest(BaseModel):
#     """
#     Modèle de base pour créer ou mettre à jour un invité.
#     """
#     name: str
#     contact_info: str
#     details: Optional[str] = None
#     is_active: bool = True  # Indique si l'invité est actif


# class GuestInDB(Guest):
#     """
#     Modèle étendu pour inclure des informations supplémentaires stockées en base.
#     """
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime] = None












# # # from pydantic import BaseModel
# # # from typing import Optional

# # # # Base Guest Schema
# # # class GuestBase(BaseModel):
# # #     name: str
# # #     biography: Optional[str]

# # # # Schema for Creating a Guest
# # # class GuestCreate(GuestBase):
# # #     pass

# # # # Schema for Reading a Guest
# # # class GuestRead(GuestBase):
# # #     id: int

# # #     model_config = {
# # #         "from_attributes": True,  # Activates attribute-based mapping
# # #     }

# # # # Schema for Updating a Guest
# # # class GuestUpdate(BaseModel):
# # #     name: Optional[str]
# # #     biography: Optional[str]

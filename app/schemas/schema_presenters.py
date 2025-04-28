from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from pydantic.networks import EmailStr

class PresenterBase(BaseModel):
    name: str
    biography: Optional[str] = None
    profilePicture: Optional[str] = None

    
    model_config = ConfigDict(from_attributes=True)


# class PresenterCreate(PresenterBase):
#     # name: str  # Le nom est obligatoire pour la création
#     pass

# class PresenterUpdate(PresenterBase):
#     name: Optional[str] = ""  # Le nom est facultatif pour la mise à jour
#     biography: Optional[str] = ""

#     model_config = {
#         "from_attributes": True,  # Remplace orm_mode
#     }


# class PresenterResponse(BaseModel):
#     id: int
#     name: str
#     biography: Optional[str] = None
#     # created_at: datetime


#     model_config = {
#         "from_attributes": True,
#     }



class PresenterHistory(BaseModel):
    """
    Modèle pour représenter l'historique des modifications d'un présentateur.
    """
    id: int
    presenter_id: int
    updated_by: int
    update_date: datetime
    changes: str


    model_config = ConfigDict(from_attributes=True)




class PresenterSearch(BaseModel):
    """
    Modèle pour représenter un présentateur.
    """
    id: int
    name: str
    biography: str
    profilePicture: Optional[str] = None

    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


    class PresenterRead(BaseModel):
        id: int
        name: str
        email: str

        model_config = ConfigDict(from_attributes=True)
        




        # //////////////////


class PresenterCreate(BaseModel):
    """Validation pour créer un nouveau présentateur."""
    name: str = Field(..., max_length=100, description="Nom du présentateur", json_schema_extra={"example": "Jean Dupont"})
    contact_info: Optional[str] = Field("", max_length=255, description="Informations de contact", json_schema_extra={"example": "jean.dupont@email.com"})
    biography: Optional[str] = Field("", description="Biographie", json_schema_extra={"example": "Jean Dupont est un journaliste spécialisé en économie."})
    users_id: int
    profilePicture: Optional[str] = None
    isMainPresenter: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class PresenterUpdate(BaseModel):
    """Validation pour mettre à jour un présentateur existant."""
    name: Optional[str] = Field(None, max_length=100, description="Nom du présentateur")
    contact_info: Optional[str] = Field(None, max_length=255, description="Informations de contact")
    biography: Optional[str] = Field(None, description="Biographie")
    profilePicture: Optional[str] = None
    isMainPresenter: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class PresenterResponse(BaseModel):
    """Réponse après validation ou récupération d'un présentateur."""
    name: str
    contact_info: Optional[str]
    biography: Optional[str]
    profilePicture: Optional[str]
    users_id: int
    shows: List[str] = Field(default=[], description="Liste des émissions associées")
    isMainPresenter: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)





class PresenterResponsePaged(BaseModel):
    total: int
    presenters: List[PresenterResponse]

    model_config = ConfigDict(from_attributes=True)

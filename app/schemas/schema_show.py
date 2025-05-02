from typing import List
from fastapi import Query
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from pydantic.fields import Field



# class ShowCreate(BaseModel):
#     """Validation des données pour créer une nouvelle émission."""
#     title: str = Field(..., max_length=255, description="Titre de l'émission", example="Actualités du jour")
#     type: str = Field(..., max_length=50, description="Type de l'émission", example="Actualité")
#     broadcast_date: Optional[datetime] = Field(None, description="Date de diffusion", example="2024-12-25T09:00:00Z")
#     duration: int = Field(..., gt=0, description="Durée de l'émission (minutes)", example=60)
#     frequency: Optional[str] = Field(None, max_length=50, description="Fréquence de l'émission", example="Hebdomadaire")
#     description: Optional[str] = Field(None, description="Description ou résumé", example="Une émission quotidienne sur les nouvelles locales.")
#     status: str = Field(default="En préparation", description="Statut de l'émission", example="Diffusé")

# class ShowUpdate(BaseModel):
#     """Validation pour mettre à jour une émission existante."""
#     title: Optional[str] = Field(None, max_length=255, description="Titre de l'émission")
#     type: Optional[str] = Field(None, max_length=50, description="Type de l'émission")
#     broadcast_date: Optional[datetime] = Field(None, description="Date de diffusion")
#     duration: Optional[int] = Field(None, gt=0, description="Durée de l'émission (minutes)")
#     frequency: Optional[str] = Field(None, max_length=50, description="Fréquence de l'émission")
#     description: Optional[str] = Field(None, description="Description ou résumé")
#     status: Optional[str] = Field(None, description="Statut de l'émission")

# class ShowResponse(BaseModel):
#     """Réponse après validation ou récupération d'une émission."""
#     title: str
#     type: str
#     broadcast_date: Optional[datetime]
#     duration: int
#     frequency: Optional[str]
#     description: Optional[str]
#     status: str
#     presenters: List[str] = Field(default=[], description="Liste des présentateurs associés")
#     segments: List[str] = Field(default=[], description="Liste des segments associés")
class ShowStatuslUpdate(BaseModel):
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class SegmentDetailCreate(BaseModel):
    title: str
    type: str
    position: int
    duration: Optional[int]
    description: Optional[str]
    guest_ids: Optional[List[int]]  # Liste des IDs des invités
    model_config = ConfigDict(from_attributes=True)


class ShowCreateWithDetail(BaseModel):
    title: str
    type: str
    broadcast_date: str
    duration: int
    frequency: Optional[str]
    description: Optional[str]
    status: str
    emission_id: Optional[int]
    presenter_ids: Optional[List[int]]  # Liste des IDs des présentateurs
    segments: Optional[List[SegmentDetailCreate]]

    model_config = ConfigDict(from_attributes=True)


class SegmentUpdateWithDetails(BaseModel):
    id: Optional[int]
    title: str
    type: str
    position: int
    duration: int
    description: Optional[str] = None
    guest_ids: Optional[List[int]] = []

    model_config = ConfigDict(from_attributes=True)


class ShowUpdateWithDetails(BaseModel):
    title: str
    type: str
    duration: int
    presenter_ids: List[int]
    segments: List[SegmentUpdateWithDetails]

    model_config = ConfigDict(from_attributes=True)


# Schéma pour créer un show
class ShowCreate(BaseModel):
    title: str
    type: str
    broadcast_date: Optional[datetime] = None
    duration: int
    frequency: Optional[str] = None
    description: Optional[str] = None
    status: str
    emission_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
    

# Schéma pour la mise à jour d'un show
class ShowUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    broadcast_date: Optional[datetime] = None
    duration: Optional[int] = None
    frequency: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    emission_id: Optional[int] = None
    presenter_ids: Optional[List[int]] = None # Liste des IDs des présentateurs
    segments: Optional[List[SegmentDetailCreate]]= None

    model_config = ConfigDict(from_attributes=True)


# Schéma pour la réponse (montrer les données d'un show)
class ShowOut(ShowCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShowWithdetailResponse(BaseModel):
    message: str
    show: 'ShowDetails'

    model_config = ConfigDict(from_attributes=True)

class ShowDetails(BaseModel):
    id: int
    type: str
    duration: int
    description: str
    created_at: datetime
    emission_id: int
    title: str
    broadcast_date: datetime
    frequency: str
    status: str
    # status: Literal['active', 'inactive']  # Assuming these are the possible values
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    # class Config:
    #     # To make Pydantic work with datetime formats
    #     json_encoders = {
    #         datetime: lambda v: v.isoformat()  # Convert datetime to ISO format
    #     }


#////// pour la creation et la lecture des conjucteurs detailler
# from pydantic import BaseModel
# from typing import List, Optional

class SegmentBase_jsonShow(BaseModel):
    title: str
    type: str
    duration: int
    description: Optional[str] = None
    startTime: Optional[str] = None
    position: int
    guests: List[int] = []# Liste des invités
    technical_notes:Optional[str] = None  

class PresenterBase_jsonShow(BaseModel):
    id: int
    isMainPresenter: Optional[bool] = False

class ShowBase_jsonShow(BaseModel):
    emission_id: int
    title: str
    type: str
    broadcast_date: str
    duration: int
    frequency: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "active"
    presenters: List[PresenterBase_jsonShow]
    segments: List[SegmentBase_jsonShow]

    model_config = ConfigDict(from_attributes=True)


class SearchShowFilters(BaseModel):
    keywords: Optional[str] = None
    status: Optional[str] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    presenter: Optional[List[int]] = None
    guest: Optional[List[int]] = None
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter (pagination)")
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum d'éléments à retourner")

    model_config = ConfigDict(from_attributes=True)
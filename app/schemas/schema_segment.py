from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List 
from datetime import datetime
from pydantic import BaseModel, Field, constr



from pydantic import BaseModel
from typing import Optional

class SegmentBase(BaseModel):
    title: str
    type: str
    duration: int
    description: Optional[str] = None
    technical_notes: Optional[str] = None
    position: int
    show_id: int
    startTime: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SegmentCreate(SegmentBase):
    pass

class SegmentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    duration: Optional[int] = None
    description: Optional[str] = None
    technical_notes: Optional[str] = None
    startTime: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SegmentPositionUpdate(BaseModel):
    position: int

    model_config = ConfigDict(from_attributes=True)

class SegmentResponse(SegmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SegmentSearchFilter(BaseModel):
    keyword: Optional[str] = Field(None, description="Recherche par mot-clé")
    status: Optional[str] = Field(None, description="Filtrer par statut")
    date_from: Optional[datetime] = Field(None, description="Date de début")
    date_to: Optional[datetime] = Field(None, description="Date de fin")
    presenter_ids: Optional[List[int]] = Field(None, description="Liste des IDs des présentateurs")
    guest_ids: Optional[List[int]] = Field(None, description="Liste des IDs des invités")

    model_config = ConfigDict(from_attributes=True)

# class SegmentBase(BaseModel):
#     """
#     Classe de base pour la validation des données d'un segment.
#     Utilisée comme parent pour `SegmentCreate` et `SegmentUpdate`.
#     """
#     title: Optional[str ] = Field(
#         None, description="Titre du segment, obligatoire lors de la création."
#     )
#     type: Optional[str] = Field(
#         None, description="Type du segment, par ex. 'Musique', 'Interview'."
#     )
#     duration: Optional[int] = Field(
#         None, ge=1, description="Durée du segment en secondes, doit être supérieure à 0."
#     )
#     description: Optional[str] = Field(
#         None, description="Description optionnelle du segment."
#     )
#     technical_notes: Optional[str] = Field(
#         None, description="Notes techniques optionnelles pour le segment."
#     )
#     position: Optional[int] = Field(
#         None, ge=0, description="Position du segment dans le show (>= 0)."
#     )
#     guests: Optional[List[int]] = Field(
#         None, description="Liste des IDs des invités associés au segment."
#     )

# class SegmentCreate(SegmentBase):
#     """
#     Classe utilisée pour valider les données nécessaires à la création d'un segment.
#     Hérite de `SegmentBase` et rend certains champs obligatoires.
#     """
#     title: str = Field(
#         ..., min_length=1, max_length=255, description="Titre du segment, obligatoire pour la création."
#     )
#     type: str = Field(
#         ..., min_length=1, max_length=100, description="Type du segment, obligatoire pour la création."
#     )
#     duration: int = Field(
#         ..., ge=1, description="Durée du segment en secondes, obligatoire et > 0."
#     )
#     show_id: int = Field(
#         ..., description="ID du show auquel ce segment est associé."
#     )
#     guests: list[int] = Field(
#         default_factory=list, description="Liste des IDs des invités associés au segment (facultatif)."
#     )

# class SegmentUpdate(SegmentBase):
#     """
#     Classe utilisée pour valider les données nécessaires à la mise à jour d'un segment.
#     Hérite de `SegmentBase` et rend tous les champs optionnels.
#     """
#     title: Optional[str] = Field(
#         None, description="Titre du segment à mettre à jour (facultatif)."
#     )
#     type: Optional[str] = Field(
#         None, description="Type du segment à mettre à jour (facultatif)."
#     )
#     duration: Optional[int] = Field(
#         None, ge=1, description="Nouvelle durée du segment en secondes (facultatif)."
#     )
#     position: Optional[int] = Field(
#         None, ge=0, description="Nouvelle position du segment (facultatif)."
#     )
#     guests: Optional[List[int]] = Field(
#         None, description="Nouvelle liste d'IDs des invités associés (facultatif)."
#     )

# class SegmentResponse(BaseModel):
#     """
#     Classe utilisée pour structurer la réponse d'un segment.
#     """
#     id: int
#     title: str
#     type: str
#     duration: int
#     description: Optional[str]
#     technical_notes: Optional[str]
#     position: int
#     show_id: int
#     created_at: datetime
#     updated_at: datetime
#     guests: List[int] = Field(
#         ..., description="Liste des IDs des invités associés au segment."
#     )

#     class Config:
#         orm_mode = True  # Permet la compatibilité avec les objets SQLAlchemy.

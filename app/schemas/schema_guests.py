from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List







class GuestCreate(BaseModel):
    """Validation pour créer un invité."""
    name: str = Field(..., max_length=100, description="Nom de l'invité", json_schema_extra={"example": "Marie Claire"})
    contact_info: Optional[str] = Field(None, max_length=255, description="Informations de contact", json_schema_extra={"example": "vie a douala"})
    biography: Optional[str] = Field(None, description="Biographie", json_schema_extra={"example": "Marie Claire est une experte en développement durable."})
     # role phone email
    role: Optional[str] = Field(None, description="role", json_schema_extra={"example": "journalist"})
    phone: Optional[str] = Field(None, description="phone", json_schema_extra={"example": "+237 05 06 07 06"})
    email: Optional[str] = Field(None, description="email", json_schema_extra={"example": "Marie@gmail.com"})
    avatar: Optional[str] = Field(None, description="avatar", json_schema_extra={"example": "https://www.google.com"})

    model_config = ConfigDict(from_attributes=True)





class GuestUpdate(BaseModel):
    """Validation pour mettre à jour un invité existant."""
    name: Optional[str] = Field(None, max_length=100, description="Nom de l'invité")
    contact_info: Optional[str] = Field(None, max_length=255, description="Informations de contact")
    biography: Optional[str] = Field(None, description="Biographie")
    role: Optional[str] = Field(None, description="role")
    phone: Optional[str] = Field(None, description="phone")
    email: Optional[str] = Field(None, description="email")
    avatar: Optional[str] = Field(None, description="avatar", json_schema_extra={"example": "https://www.google.com"})

    model_config = ConfigDict(from_attributes=True)



class GuestResponse(BaseModel):
    """Réponse après validation ou récupération d'un invité."""
    id: int  # Expose l'identifiant de l'invité
    name: str
    contact_info: Optional[str]
    biography: Optional[str]
    role: Optional[str] = Field(None, description="role")
    phone: Optional[str] = Field(None, description="phone")
    email: Optional[str] = Field(None, description="email")
    avatar: Optional[str] = Field(None, description="avatar", json_schema_extra={"example": "https://www.google.com"})

    segments: List[str] = Field(default=[], description="Liste des segments associés")

    model_config = ConfigDict(from_attributes=True)



class Contact(BaseModel):
    """Représente les informations de contact d'un invité."""
    email: Optional[str] = None  # Adresse email de l'invité, peut être nulle
    phone: Optional[str] = None  # Numéro de téléphone de l'invité, peut être nul

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class Appearance(BaseModel):
    """Représente une apparition d'un invité dans une émission."""
    show_id: int  # Identifiant unique du conducteur (Show)
    show_title: str  # Titre de l'émission
    broadcast_date: datetime  # Date de diffusion de l'émission

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class GuestResponseAndDetails(BaseModel):
    """Schéma de réponse de base pour les détails d'un invité."""
    id: int  # Identifiant unique de l'invité
    name: str  # Nom de l'invité
    role: Optional[str] = None  # Rôle de l'invité (ex. journaliste, expert)
    avatar: Optional[str] = None  # URL de l'avatar de l'invité
    created_at: datetime  # Date de création de l'invité
    biography: Optional[str] = None  # Biographie de l'invité
    contact: Contact  # Informations de contact
    contact_info: Optional[str] = None  # Ajout de contact_info, optionnel

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class GuestResponseWithAppearances(GuestResponse):
    """Schéma de réponse étendu incluant les apparitions de l'invité."""
    appearances: List[Appearance] = []  # Liste des participations de l'invité

    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }
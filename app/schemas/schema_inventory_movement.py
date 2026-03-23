from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


# ════════════════════════════════════════════════════════════════
# MOVEMENT CREATE
# ════════════════════════════════════════════════════════════════

class MovementCreate(BaseModel):
    equipment_id: int = Field(..., description="ID de l'equipement concerne")

    # Type de mouvement
    movement_type_id: int = Field(..., description="ID du type de mouvement (inventory_config_options)")
    movement_category: str = Field(..., max_length=50, description="Categorie fonctionnelle (assignment, return, loan, etc.)")

    # Lien mission
    mission_id: Optional[int] = Field(None, description="ID de la mission")
    mission_title: Optional[str] = Field(None, max_length=255, description="Titre de la mission")
    mission_type: Optional[str] = Field(None, max_length=50, description="Type de mission")

    # Origine
    from_company_id: Optional[int] = Field(None, description="ID entreprise d'origine")
    from_site_id: Optional[int] = Field(None, description="ID site d'origine")
    from_room_id: Optional[int] = Field(None, description="ID local d'origine")
    from_user_id: Optional[int] = Field(None, description="ID utilisateur d'origine")
    from_user_name: Optional[str] = Field(None, max_length=255, description="Nom utilisateur d'origine")
    from_specific_location: Optional[str] = Field(None, max_length=255, description="Emplacement specifique d'origine")

    # Destination
    to_company_id: Optional[int] = Field(None, description="ID entreprise de destination")
    to_site_id: Optional[int] = Field(None, description="ID site de destination")
    to_room_id: Optional[int] = Field(None, description="ID local de destination")
    to_user_id: Optional[int] = Field(None, description="ID utilisateur de destination")
    to_user_name: Optional[str] = Field(None, max_length=255, description="Nom utilisateur de destination")
    to_specific_location: Optional[str] = Field(None, max_length=255, description="Emplacement specifique de destination")
    to_external_location: Optional[str] = Field(None, description="Localisation externe (texte libre)")

    # Details
    date: datetime = Field(..., description="Date du mouvement")
    expected_return_date: Optional[datetime] = Field(None, description="Date de retour prevue")
    reason: str = Field(..., description="Raison du mouvement")
    notes: Optional[str] = Field(None, description="Notes complementaires")

    # Approbation
    requires_approval: bool = Field(False, description="Necessite une approbation")

    # Donnees complementaires
    return_condition_json: Optional[dict[str, Any]] = Field(None, description="Etat au retour")
    attachments_json: Optional[list[dict[str, Any]]] = Field(None, description="Pieces jointes [{name, url, type}]")
    signature_url: Optional[str] = Field(None, description="URL de la signature")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MOVEMENT RESPONSE
# ════════════════════════════════════════════════════════════════

class MovementResponse(BaseModel):
    id: int
    equipment_id: int

    # Noms enrichis (injectes par le CRUD via les relations)
    equipment_name: Optional[str] = None
    equipment_reference: Optional[str] = None

    # Type
    movement_type_id: int
    movement_type_name: Optional[str] = None
    movement_category: str

    # Mission
    mission_id: Optional[int] = None
    mission_title: Optional[str] = None
    mission_type: Optional[str] = None

    # Origine
    from_company_id: Optional[int] = None
    from_company_name: Optional[str] = None
    from_site_id: Optional[int] = None
    from_site_name: Optional[str] = None
    from_room_id: Optional[int] = None
    from_room_name: Optional[str] = None
    from_user_id: Optional[int] = None
    from_user_name: Optional[str] = None
    from_specific_location: Optional[str] = None

    # Destination
    to_company_id: Optional[int] = None
    to_company_name: Optional[str] = None
    to_site_id: Optional[int] = None
    to_site_name: Optional[str] = None
    to_room_id: Optional[int] = None
    to_room_name: Optional[str] = None
    to_user_id: Optional[int] = None
    to_user_name: Optional[str] = None
    to_specific_location: Optional[str] = None
    to_external_location: Optional[str] = None

    # Details
    date: datetime
    expected_return_date: Optional[datetime] = None
    actual_return_date: Optional[datetime] = None
    reason: str
    notes: Optional[str] = None

    # Approbation
    status: str
    requires_approval: bool
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Donnees complementaires
    return_condition_json: Optional[dict[str, Any]] = None
    attachments_json: Optional[list[dict[str, Any]]] = None
    signature_url: Optional[str] = None

    # Audit
    created_at: datetime
    created_by: int
    created_by_name: str
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MOVEMENT LIST RESPONSE (pagination)
# ════════════════════════════════════════════════════════════════

class MovementListResponse(BaseModel):
    items: list[MovementResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# APPROVAL / REJECTION BODIES
# ════════════════════════════════════════════════════════════════

class MovementApproveBody(BaseModel):
    """Corps de la requete d'approbation (pas de champs requis cote client)."""
    pass


class MovementRejectBody(BaseModel):
    reason: str = Field(..., description="Raison du rejet")

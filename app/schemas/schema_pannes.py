"""
@fileoverview schema_pannes.py — Schémas Pydantic v2 pour le module Gestion des Pannes

Schémas :
  - Acteur      : Create / Update / Response
  - FichePanne  : Create / Update / Response / ListResponse
  - PannesDashboard : réponse KPIs dashboard
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime


# ---------------------------------------------------------------------------
# VehicleInfo (sous-schéma pour les réponses FichePanne)
# ---------------------------------------------------------------------------

class VehicleInfo(BaseModel):
    id: int
    registration_number: str
    brand: Optional[str]
    model_name: Optional[str]
    company_name: str

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ---------------------------------------------------------------------------
# PanneCategory (LogisticsConfigOption avec list_type="panne_category")
# ---------------------------------------------------------------------------

class PanneCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    is_default: bool
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class PanneCategoryCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class PanneCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Acteur
# ---------------------------------------------------------------------------

class ActeurCreate(BaseModel):
    nom: str = Field(..., max_length=100, description="Nom de famille")
    prenom: Optional[str] = Field(None, max_length=100)
    role: str = Field(..., description="mecanicien / chauffeur / responsable")
    societe: Optional[str] = Field(None, max_length=100)
    telephone: Optional[str] = Field(None, max_length=30)
    actif: bool = Field(True)

    model_config = ConfigDict(from_attributes=True)


class ActeurUpdate(BaseModel):
    nom: Optional[str] = Field(None, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None)
    societe: Optional[str] = Field(None, max_length=100)
    telephone: Optional[str] = Field(None, max_length=30)
    actif: Optional[bool] = Field(None)

    model_config = ConfigDict(from_attributes=True)


class ActeurLierCompte(BaseModel):
    """Payload pour lier un acteur à un compte applicatif existant."""
    user_id: int = Field(..., description="ID de l'utilisateur à associer à cet acteur")

    model_config = ConfigDict(from_attributes=True)


class ActeurResponse(BaseModel):
    id: int
    nom: str
    prenom: Optional[str]
    role: str
    societe: Optional[str]
    telephone: Optional[str]
    actif: bool
    user_id: Optional[int]
    nom_complet: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ActeurListResponse(BaseModel):
    items: List[ActeurResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# FicheActeur (liaison, utilisée dans les réponses imbriquées)
# ---------------------------------------------------------------------------

class FicheActeurItem(BaseModel):
    """Acteur tel qu'il apparaît dans une fiche (avec son rôle sur la fiche)."""
    acteur_id: int
    role_sur_fiche: str
    acteur: ActeurResponse

    model_config = ConfigDict(from_attributes=True)


class FicheActeurCreate(BaseModel):
    """Payload pour ajouter un acteur à une fiche."""
    acteur_id: int
    role_sur_fiche: str = Field(..., description="mecanicien / chauffeur / responsable")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# FichePanne
# ---------------------------------------------------------------------------

class FichePanneCreate(BaseModel):
    date_panne: date = Field(..., description="Date de la panne")
    immatriculation: str = Field(..., max_length=255)
    numero_moteur: Optional[str] = Field(None, max_length=100)
    societe: str = Field(..., max_length=100, description="TRAFRIC SARL / BAJ SERVICES SA")
    km_depart: Optional[int] = Field(None, ge=0)
    km_fin: Optional[int] = Field(None, ge=0)
    service_demande: Optional[str] = Field(None)
    pieces_commandees: Optional[str] = Field(None)
    statut: str = Field('en_attente', description="en_attente / en_cours / cloture")
    category_id: int = Field(..., description="ID de la catégorie de panne (obligatoire)")
    vehicle_id: Optional[int] = Field(None, description="ID du véhicule enregistré (optionnel)")
    # Acteurs liés à la fiche
    acteurs: List[FicheActeurCreate] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FichePanneUpdate(BaseModel):
    date_panne: Optional[date] = None
    immatriculation: Optional[str] = Field(None, max_length=255)
    numero_moteur: Optional[str] = Field(None, max_length=100)
    societe: Optional[str] = Field(None, max_length=100)
    km_depart: Optional[int] = Field(None, ge=0)
    km_fin: Optional[int] = Field(None, ge=0)
    service_demande: Optional[str] = None
    pieces_commandees: Optional[str] = None
    statut: Optional[str] = None
    category_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    # Si fourni, remplace la liste complète des acteurs
    acteurs: Optional[List[FicheActeurCreate]] = None

    model_config = ConfigDict(from_attributes=True)


class FichePanneResponse(BaseModel):
    id: int
    numero_fiche: int
    date_panne: date
    immatriculation: str
    numero_moteur: Optional[str]
    societe: str
    km_depart: Optional[int]
    km_fin: Optional[int]
    service_demande: Optional[str]
    pieces_commandees: Optional[str]
    statut: str
    category_id: Optional[int]
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    vehicle_id: Optional[int]
    vehicle: Optional[VehicleInfo] = None
    acteurs: List[FicheActeurItem]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    created_by_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class FichePanneListItem(BaseModel):
    """Version allégée pour la liste (sans le détail complet des acteurs)."""
    id: int
    numero_fiche: int
    date_panne: date
    immatriculation: str
    societe: str
    statut: str
    category_id: Optional[int]
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    vehicle_id: Optional[int]
    # Noms des mécaniciens (pour affichage colonne dans le tableau)
    mecaniciens: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FichePanneListResponse(BaseModel):
    items: List[FichePanneListItem]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

class VehiculeRecurrent(BaseModel):
    immatriculation: str
    nombre_fiches: int

    model_config = ConfigDict(from_attributes=True)


class MecanicienActif(BaseModel):
    acteur_id: int
    nom_complet: str
    nombre_interventions: int

    model_config = ConfigDict(from_attributes=True)


class RepartitionSociete(BaseModel):
    societe: str
    nombre_fiches: int
    pourcentage: float

    model_config = ConfigDict(from_attributes=True)


class RepartitionCategorie(BaseModel):
    category_id: Optional[int]
    category_name: str
    category_color: Optional[str]
    nombre_fiches: int
    pourcentage: float

    model_config = ConfigDict(from_attributes=True)


class PannesDashboardResponse(BaseModel):
    total_fiches: int
    fiches_en_attente: int
    fiches_en_cours: int
    fiches_cloturees: int
    repartition_societe: List[RepartitionSociete]
    repartition_categorie: List[RepartitionCategorie]
    vehicules_recurrents: List[VehiculeRecurrent]   # Immatriculations avec > 1 fiche
    mecaniciens_actifs: List[MecanicienActif]        # Top mécaniciens par nombre d'interventions

    model_config = ConfigDict(from_attributes=True)

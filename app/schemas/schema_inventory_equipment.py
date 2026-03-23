from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Any


# ════════════════════════════════════════════════════════════════
# DOCUMENT
# ════════════════════════════════════════════════════════════════

class DocumentCreate(BaseModel):
    file_name: str = Field(..., max_length=500, description="Nom du fichier")
    display_name: str = Field(..., max_length=500, description="Nom d'affichage")
    description: Optional[str] = Field(None, description="Description du document")
    document_type: str = Field(..., max_length=50, description="Type de document")
    mime_type: str = Field(..., max_length=100, description="Type MIME")
    file_size: int = Field(..., description="Taille du fichier en octets")
    storage_url: str = Field(..., description="URL Firebase Storage")
    storage_path: str = Field(..., description="Chemin Firebase Storage")
    thumbnail_url: Optional[str] = Field(None, description="URL de la miniature")
    access_level: str = Field("company", max_length=50, description="Niveau d'acces")
    version: Optional[str] = Field(None, max_length=50, description="Version du document")
    is_latest: bool = Field(True, description="Est la derniere version")
    previous_version_id: Optional[int] = Field(None, description="ID de la version precedente")
    tags_json: Optional[list[str]] = Field(None, description="Tags du document")
    language: Optional[str] = Field(None, max_length=10, description="Langue du document")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration")

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: int
    equipment_id: int
    file_name: str
    display_name: str
    description: Optional[str] = None
    document_type: str
    mime_type: str
    file_size: int
    storage_url: str
    storage_path: str
    thumbnail_url: Optional[str] = None
    access_level: str
    version: Optional[str] = None
    is_latest: bool
    previous_version_id: Optional[int] = None
    tags_json: Optional[list[str]] = None
    language: Optional[str] = None
    expires_at: Optional[datetime] = None
    uploaded_at: datetime
    uploaded_by: int
    uploaded_by_name: str
    download_count: int = 0
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT CREATE
# ════════════════════════════════════════════════════════════════

class EquipmentCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Nom de l'equipement")
    reference: Optional[str] = Field(None, max_length=50, description="Reference (auto-generee si vide)")
    serial_number: Optional[str] = Field(None, max_length=255, description="Numero de serie")
    barcode: Optional[str] = Field(None, max_length=255, description="Code-barres")

    # Classification
    category_id: int = Field(..., description="ID de la categorie (inventory_config_options)")
    subcategory: Optional[str] = Field(None, max_length=255, description="Sous-categorie")
    brand: str = Field(..., max_length=255, description="Marque")
    model_name: str = Field(..., max_length=255, description="Modele")
    manufacturer: Optional[str] = Field(None, max_length=255, description="Fabricant")

    # Etat
    status_id: int = Field(..., description="ID du statut (inventory_config_options)")
    condition_id: int = Field(..., description="ID de l'etat/condition (inventory_config_options)")

    # Localisation
    company_id: int = Field(..., description="ID de l'entreprise")
    site_id: int = Field(..., description="ID du site")
    room_id: Optional[int] = Field(None, description="ID du local")
    specific_location: Optional[str] = Field(None, max_length=255, description="Emplacement specifique")

    # Affectation
    assigned_user_id: Optional[int] = Field(None, description="ID de l'utilisateur affecte")
    assigned_user_name: Optional[str] = Field(None, max_length=255, description="Nom de l'utilisateur affecte")
    assigned_user_email: Optional[str] = Field(None, max_length=255, description="Email de l'utilisateur affecte")
    expected_return_date: Optional[datetime] = Field(None, description="Date de retour prevue")
    assignment_notes: Optional[str] = Field(None, description="Notes d'affectation")

    # Acquisition
    acquisition_date: Optional[date] = Field(None, description="Date d'acquisition")
    acquisition_type: Optional[str] = Field(None, max_length=50, description="Type d'acquisition")
    purchase_price: Optional[float] = Field(None, description="Prix d'achat")
    current_value: Optional[float] = Field(None, description="Valeur actuelle")
    supplier: Optional[str] = Field(None, max_length=255, description="Fournisseur")
    invoice_number: Optional[str] = Field(None, max_length=255, description="Numero de facture")
    invoice_url: Optional[str] = Field(None, description="URL de la facture")

    # Garantie
    warranty_start_date: Optional[date] = Field(None, description="Debut de garantie")
    warranty_end_date: Optional[date] = Field(None, description="Fin de garantie")
    warranty_provider: Optional[str] = Field(None, max_length=255, description="Fournisseur de garantie")
    warranty_contract_number: Optional[str] = Field(None, max_length=255, description="Numero de contrat de garantie")
    warranty_notes: Optional[str] = Field(None, description="Notes de garantie")

    # Configuration technique
    config_settings_json: Optional[dict[str, Any]] = Field(None, description="Parametres de configuration")
    config_notes: Optional[str] = Field(None, description="Notes de configuration")
    firmware_version: Optional[str] = Field(None, max_length=100, description="Version du firmware")
    software_version: Optional[str] = Field(None, max_length=100, description="Version du logiciel")

    # Informations complementaires
    description: Optional[str] = Field(None, description="Description")
    notes: Optional[str] = Field(None, description="Notes")
    manual_url: Optional[str] = Field(None, description="URL du manuel")
    photos_json: Optional[list[str]] = Field(default=[], description="URLs des photos")
    specifications_json: Optional[dict[str, Any]] = Field(None, description="Specifications techniques")

    # Consommables
    is_consumable: bool = Field(False, description="Est un consommable")
    quantity: Optional[int] = Field(None, description="Quantite en stock")
    min_quantity: Optional[int] = Field(None, description="Quantite minimale (seuil alerte)")
    unit: Optional[str] = Field(None, max_length=50, description="Unite de mesure")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT RESPONSE
# ════════════════════════════════════════════════════════════════

class EquipmentResponse(BaseModel):
    id: int
    name: str
    reference: str
    serial_number: Optional[str] = None
    barcode: Optional[str] = None

    # Classification
    category_id: int
    category_name: Optional[str] = None
    subcategory: Optional[str] = None
    brand: str
    model_name: str
    manufacturer: Optional[str] = None

    # Etat
    status_id: int
    status_name: Optional[str] = None
    status_color: Optional[str] = None
    condition_id: int
    condition_name: Optional[str] = None

    # Localisation
    company_id: int
    company_name: Optional[str] = None
    site_id: int
    site_name: Optional[str] = None
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    specific_location: Optional[str] = None

    # Affectation
    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None
    assigned_user_email: Optional[str] = None
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[int] = None
    expected_return_date: Optional[datetime] = None
    assignment_notes: Optional[str] = None

    # Acquisition
    acquisition_date: Optional[date] = None
    acquisition_type: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None

    # Garantie
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    warranty_provider: Optional[str] = None
    warranty_contract_number: Optional[str] = None
    warranty_notes: Optional[str] = None

    # Configuration technique
    config_settings_json: Optional[dict[str, Any]] = None
    config_notes: Optional[str] = None
    last_configured_at: Optional[datetime] = None
    last_configured_by: Optional[int] = None
    firmware_version: Optional[str] = None
    software_version: Optional[str] = None

    # Informations complementaires
    description: Optional[str] = None
    notes: Optional[str] = None
    manual_url: Optional[str] = None
    photos_json: Optional[list[str]] = None
    specifications_json: Optional[dict[str, Any]] = None

    # Consommables
    is_consumable: bool = False
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None
    unit: Optional[str] = None

    # Archivage
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    archived_reason: Optional[str] = None

    # Audit
    created_at: datetime
    created_by: int
    created_by_name: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    is_deleted: bool = False

    # Documents (inclus uniquement dans le detail)
    documents: Optional[list[DocumentResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT BRIEF (version allegee pour les listes)
# ════════════════════════════════════════════════════════════════

class EquipmentBrief(BaseModel):
    id: int
    name: str
    reference: str
    serial_number: Optional[str] = None
    barcode: Optional[str] = None

    category_id: int
    category_name: Optional[str] = None
    brand: str
    model_name: str

    status_id: int
    status_name: Optional[str] = None
    status_color: Optional[str] = None
    condition_id: int
    condition_name: Optional[str] = None

    company_id: int
    company_name: Optional[str] = None
    site_id: int
    site_name: Optional[str] = None
    room_id: Optional[int] = None
    room_name: Optional[str] = None

    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None
    expected_return_date: Optional[datetime] = None

    is_consumable: bool = False
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None

    is_archived: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT UPDATE
# ════════════════════════════════════════════════════════════════

class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    barcode: Optional[str] = Field(None, max_length=255)

    category_id: Optional[int] = None
    subcategory: Optional[str] = Field(None, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    model_name: Optional[str] = Field(None, max_length=255)
    manufacturer: Optional[str] = None

    status_id: Optional[int] = None
    condition_id: Optional[int] = None

    company_id: Optional[int] = None
    site_id: Optional[int] = None
    room_id: Optional[int] = None
    specific_location: Optional[str] = Field(None, max_length=255)

    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = Field(None, max_length=255)
    assigned_user_email: Optional[str] = Field(None, max_length=255)
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[int] = None
    expected_return_date: Optional[datetime] = None
    assignment_notes: Optional[str] = None

    acquisition_date: Optional[date] = None
    acquisition_type: Optional[str] = Field(None, max_length=50)
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    supplier: Optional[str] = Field(None, max_length=255)
    invoice_number: Optional[str] = Field(None, max_length=255)
    invoice_url: Optional[str] = None

    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    warranty_provider: Optional[str] = Field(None, max_length=255)
    warranty_contract_number: Optional[str] = Field(None, max_length=255)
    warranty_notes: Optional[str] = None

    config_settings_json: Optional[dict[str, Any]] = None
    config_notes: Optional[str] = None
    last_configured_at: Optional[datetime] = None
    last_configured_by: Optional[int] = None
    firmware_version: Optional[str] = Field(None, max_length=100)
    software_version: Optional[str] = Field(None, max_length=100)

    description: Optional[str] = None
    notes: Optional[str] = None
    manual_url: Optional[str] = None
    photos_json: Optional[list[str]] = None
    specifications_json: Optional[dict[str, Any]] = None

    is_consumable: Optional[bool] = None
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None
    unit: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# EQUIPMENT LIST RESPONSE (pagination)
# ════════════════════════════════════════════════════════════════

class EquipmentListResponse(BaseModel):
    items: list[EquipmentBrief]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# ARCHIVE BODY
# ════════════════════════════════════════════════════════════════

class ArchiveBody(BaseModel):
    reason: Optional[str] = Field(None, description="Raison de l'archivage")


# ════════════════════════════════════════════════════════════════
# INVENTORY STATS
# ════════════════════════════════════════════════════════════════

class InventoryStatsResponse(BaseModel):
    total_count: int = 0
    by_status: list[dict[str, Any]] = []
    by_category: list[dict[str, Any]] = []
    by_company: list[dict[str, Any]] = []
    total_value: float = 0.0
    low_stock_count: int = 0
    overdue_returns_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# NEXT REFERENCE
# ════════════════════════════════════════════════════════════════

class NextReferenceResponse(BaseModel):
    reference: str

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


# ════════════════════════════════════════════════════════════════
# PARTS USED ITEM (sous-schema pour les pieces utilisees)
# ════════════════════════════════════════════════════════════════

class PartUsedItem(BaseModel):
    name: str = Field(..., description="Nom de la piece")
    quantity: int = Field(..., description="Quantite utilisee")
    unit_cost: Optional[float] = Field(None, description="Cout unitaire")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# ATTACHMENT ITEM (sous-schema pour les pieces jointes)
# ════════════════════════════════════════════════════════════════

class AttachmentItem(BaseModel):
    name: str = Field(..., description="Nom du fichier")
    url: str = Field(..., description="URL du fichier")
    type: str = Field(..., description="Type de fichier")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE CREATE
# ════════════════════════════════════════════════════════════════

class MaintenanceCreate(BaseModel):
    equipment_id: int = Field(..., description="ID de l'equipement")

    # Type et description
    type: str = Field(..., max_length=50, description="Type de maintenance (preventive, corrective, inspection, calibration, cleaning, upgrade, other)")
    title: str = Field(..., max_length=255, description="Titre de l'intervention")
    description: str = Field(..., description="Description de l'intervention")

    # Planification
    scheduled_date: Optional[datetime] = Field(None, description="Date planifiee")
    start_date: Optional[datetime] = Field(None, description="Date de debut")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    estimated_duration: Optional[int] = Field(None, description="Duree estimee (minutes)")
    actual_duration: Optional[int] = Field(None, description="Duree reelle (minutes)")

    # Intervenant
    performer_type: Optional[str] = Field(None, max_length=20, description="Type d'intervenant (internal, external)")
    performer_user_id: Optional[int] = Field(None, description="ID de l'utilisateur intervenant")
    performer_user_name: Optional[str] = Field(None, max_length=255, description="Nom de l'intervenant")
    performer_company: Optional[str] = Field(None, max_length=255, description="Societe de l'intervenant")
    performer_contact: Optional[str] = Field(None, max_length=255, description="Contact de l'intervenant")

    # Couts
    cost_labor: Optional[float] = Field(None, description="Cout main d'oeuvre")
    cost_parts: Optional[float] = Field(None, description="Cout pieces")
    cost_other: Optional[float] = Field(None, description="Autres couts")
    cost_total: Optional[float] = Field(None, description="Cout total")
    cost_currency: str = Field("XOF", max_length=10, description="Devise")

    # Pieces utilisees
    parts_used_json: Optional[list[dict[str, Any]]] = Field(None, description="Pieces utilisees [{name, quantity, unitCost}]")

    # Statut et resultat
    status: str = Field("scheduled", max_length=20, description="Statut (scheduled, in_progress, completed, cancelled)")
    result: Optional[str] = Field(None, max_length=20, description="Resultat (success, partial, failed)")
    findings: Optional[str] = Field(None, description="Constatations")
    recommendations: Optional[str] = Field(None, description="Recommandations")
    next_maintenance_date: Optional[datetime] = Field(None, description="Date de prochaine maintenance")

    # Documents joints
    attachments_json: Optional[list[dict[str, Any]]] = Field(None, description="Pieces jointes [{name, url, type}]")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE RESPONSE
# ════════════════════════════════════════════════════════════════

class MaintenanceResponse(BaseModel):
    id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    equipment_reference: Optional[str] = None

    # Type et description
    type: str
    title: str
    description: str

    # Planification
    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None

    # Intervenant
    performer_type: Optional[str] = None
    performer_user_id: Optional[int] = None
    performer_user_name: Optional[str] = None
    performer_company: Optional[str] = None
    performer_contact: Optional[str] = None

    # Couts
    cost_labor: Optional[float] = None
    cost_parts: Optional[float] = None
    cost_other: Optional[float] = None
    cost_total: Optional[float] = None
    cost_currency: str = "XOF"

    # Pieces utilisees
    parts_used_json: Optional[list[dict[str, Any]]] = None

    # Statut et resultat
    status: str = "scheduled"
    result: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    next_maintenance_date: Optional[datetime] = None

    # Documents joints
    attachments_json: Optional[list[dict[str, Any]]] = None

    # Audit
    created_at: datetime
    created_by: int
    created_by_name: str
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE UPDATE
# ════════════════════════════════════════════════════════════════

class MaintenanceUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None

    performer_type: Optional[str] = Field(None, max_length=20)
    performer_user_id: Optional[int] = None
    performer_user_name: Optional[str] = Field(None, max_length=255)
    performer_company: Optional[str] = Field(None, max_length=255)
    performer_contact: Optional[str] = Field(None, max_length=255)

    cost_labor: Optional[float] = None
    cost_parts: Optional[float] = None
    cost_other: Optional[float] = None
    cost_total: Optional[float] = None
    cost_currency: Optional[str] = Field(None, max_length=10)

    parts_used_json: Optional[list[dict[str, Any]]] = None

    status: Optional[str] = Field(None, max_length=20)
    result: Optional[str] = Field(None, max_length=20)
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    next_maintenance_date: Optional[datetime] = None

    attachments_json: Optional[list[dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# MAINTENANCE LIST RESPONSE (pagination)
# ════════════════════════════════════════════════════════════════

class MaintenanceListResponse(BaseModel):
    items: list[MaintenanceResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)

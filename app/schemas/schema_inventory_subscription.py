from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION CREATE
# ════════════════════════════════════════════════════════════════

class SubscriptionCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Nom de l'abonnement/service")
    description: Optional[str] = Field(None, description="Description")
    reference: Optional[str] = Field(None, max_length=100, description="Reference interne")

    # Classification
    category_id: int = Field(..., description="ID de la categorie (inventory_config_options)")

    # Fournisseur
    provider_name: str = Field(..., max_length=255, description="Nom du fournisseur")
    provider_website: Optional[str] = Field(None, description="Site web du fournisseur")
    provider_contact_email: Optional[str] = Field(None, max_length=255, description="Email de contact")
    provider_contact_phone: Optional[str] = Field(None, max_length=50, description="Telephone de contact")
    provider_account_number: Optional[str] = Field(None, max_length=255, description="Numero de compte client")

    # Cout
    cost_amount: float = Field(..., description="Montant du cout")
    cost_currency: str = Field("XOF", max_length=10, description="Devise")
    billing_cycle: str = Field(..., max_length=20, description="Cycle de facturation")
    next_billing_date: Optional[date] = Field(None, description="Prochaine date de facturation")

    # Dates
    start_date: date = Field(..., description="Date de debut")
    end_date: Optional[date] = Field(None, description="Date de fin")

    # Renouvellement
    renewal_type: str = Field(..., max_length=20, description="Type de renouvellement (automatic/manual)")
    auto_renew_period_months: Optional[int] = Field(None, description="Periode de renouvellement auto en mois")

    # Statut
    status: str = Field("active", max_length=20, description="Statut (active/expired/cancelled/pending)")

    # Entreprise
    company_id: Optional[int] = Field(None, description="ID de l'entreprise beneficiaire")

    # Notes
    notes: Optional[str] = Field(None, description="Notes")
    login_url: Optional[str] = Field(None, description="URL de connexion au service")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION RESPONSE
# ════════════════════════════════════════════════════════════════

class SubscriptionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    reference: Optional[str] = None

    # Classification
    category_id: int
    category_name: Optional[str] = None

    # Fournisseur
    provider_name: str
    provider_website: Optional[str] = None
    provider_contact_email: Optional[str] = None
    provider_contact_phone: Optional[str] = None
    provider_account_number: Optional[str] = None

    # Cout
    cost_amount: float
    cost_currency: str = "XOF"
    billing_cycle: str
    next_billing_date: Optional[date] = None

    # Dates
    start_date: date
    end_date: Optional[date] = None

    # Renouvellement
    renewal_type: str
    auto_renew_period_months: Optional[int] = None

    # Statut
    status: str = "active"

    # Entreprise
    company_id: Optional[int] = None
    company_name: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    login_url: Optional[str] = None

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

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION UPDATE
# ════════════════════════════════════════════════════════════════

class SubscriptionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=100)

    # Classification
    category_id: Optional[int] = None

    # Fournisseur
    provider_name: Optional[str] = Field(None, max_length=255)
    provider_website: Optional[str] = None
    provider_contact_email: Optional[str] = Field(None, max_length=255)
    provider_contact_phone: Optional[str] = Field(None, max_length=50)
    provider_account_number: Optional[str] = Field(None, max_length=255)

    # Cout
    cost_amount: Optional[float] = None
    cost_currency: Optional[str] = Field(None, max_length=10)
    billing_cycle: Optional[str] = Field(None, max_length=20)
    next_billing_date: Optional[date] = None

    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Renouvellement
    renewal_type: Optional[str] = Field(None, max_length=20)
    auto_renew_period_months: Optional[int] = None

    # Statut
    status: Optional[str] = Field(None, max_length=20)

    # Entreprise
    company_id: Optional[int] = None

    # Notes
    notes: Optional[str] = None
    login_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION LIST RESPONSE (pagination)
# ════════════════════════════════════════════════════════════════

class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# ARCHIVE BODY
# ════════════════════════════════════════════════════════════════

class SubscriptionArchiveBody(BaseModel):
    reason: Optional[str] = Field(None, description="Raison de l'archivage")


# ════════════════════════════════════════════════════════════════
# SUBSCRIPTION ALERT
# ════════════════════════════════════════════════════════════════

class SubscriptionAlertResponse(BaseModel):
    expired: list[SubscriptionResponse] = []
    expiring_soon: list[SubscriptionResponse] = []
    expiring_warning: list[SubscriptionResponse] = []
    total_alerts: int = 0

    model_config = ConfigDict(from_attributes=True)

"""Schemas Pydantic pour les reponses Scaleway."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class ScwMoneyValue(BaseModel):
    """Valeur monetaire formatee."""
    value: float = 0.0
    currency_code: str = "EUR"
    text: str = "0.00 EUR"

    model_config = ConfigDict(from_attributes=True)


class ScwProject(BaseModel):
    """Projet Scaleway."""
    id: Optional[str] = None
    name: Optional[str] = None
    organization_id: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwAccountInfo(BaseModel):
    """Informations du compte/organisation Scaleway."""
    organization_id: Optional[str] = None
    projects: list[dict] = []
    total_projects: int = 0

    model_config = ConfigDict(from_attributes=True)


class ScwInstance(BaseModel):
    """Instance (serveur) Scaleway."""
    id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    arch: Optional[str] = None
    commercial_type: Optional[str] = None
    image: Optional[dict] = None
    public_ip: Optional[dict] = None
    public_ips: list[dict] = []
    private_ip: Optional[str] = None
    volumes: Optional[dict] = None
    tags: list[str] = []
    zone: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    project: Optional[str] = None
    organization: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwConsumptionItem(BaseModel):
    """Element de consommation Scaleway."""
    category: Optional[str] = None
    product: Optional[str] = None
    project_id: Optional[str] = None
    value: Optional[ScwMoneyValue] = None

    model_config = ConfigDict(from_attributes=True)


class ScwConsumption(BaseModel):
    """Consommation globale Scaleway."""
    billing_period: str = ""
    consumptions: list[dict] = []
    total: Optional[ScwMoneyValue] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwInvoice(BaseModel):
    """Facture Scaleway."""
    id: Optional[str] = None
    organization_id: Optional[str] = None
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    billing_period: Optional[str] = None
    issued_date: Optional[str] = None
    due_date: Optional[str] = None
    total_taxed: Optional[ScwMoneyValue] = None
    total_untaxed: Optional[ScwMoneyValue] = None
    total_tax: Optional[ScwMoneyValue] = None
    invoice_type: Optional[str] = None
    state: Optional[str] = None
    number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwDnsZone(BaseModel):
    """Zone DNS Scaleway."""
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    ns: list[str] = []
    ns_default: list[str] = []
    ns_master: list[str] = []
    project_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwDnsRecord(BaseModel):
    """Enregistrement DNS."""
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    data: Optional[str] = None
    ttl: Optional[int] = None
    priority: Optional[int] = None
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScwDashboard(BaseModel):
    """Tableau de bord synthetique Scaleway."""
    total_instances: int = 0
    instances_by_state: dict = {}
    instances_by_zone: dict = {}
    running_count: int = 0
    stopped_count: int = 0
    dns_zones_count: int = 0
    consumption: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

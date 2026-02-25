from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime


class OvhAccountInfo(BaseModel):
    """Informations du compte OVH (/me)."""
    nichandle: Optional[str] = None
    firstname: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    organisation: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    currency: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class OvhRenewInfo(BaseModel):
    """Details de renouvellement d'un service."""
    automatic: Optional[bool] = None
    deleteAtExpiration: Optional[bool] = None
    forced: Optional[bool] = None
    manualPayment: Optional[bool] = None
    period: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OvhServiceInfo(BaseModel):
    """Infos de service OVH (expiration, statut, renouvellement)."""
    serviceId: Optional[int] = None
    status: Optional[str] = None
    creation: Optional[str] = None
    expiration: Optional[str] = None
    renew: Optional[OvhRenewInfo] = None
    contactAdmin: Optional[str] = None
    contactBilling: Optional[str] = None
    contactTech: Optional[str] = None
    domain: Optional[str] = None
    canDeleteAtExpiration: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class OvhServiceSummary(BaseModel):
    """Resume d'un service OVH depuis /me/service."""
    serviceId: Optional[int] = None
    resource: Optional[dict] = None
    route: Optional[dict] = None
    status: Optional[str] = None
    expiration: Optional[str] = None
    creation: Optional[str] = None
    renew: Optional[dict] = None
    contactAdmin: Optional[str] = None
    contactBilling: Optional[str] = None
    contactTech: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OvhBill(BaseModel):
    """Facture OVH."""
    billId: Optional[str] = None
    date: Optional[str] = None
    orderId: Optional[int] = None
    password: Optional[str] = None
    pdfUrl: Optional[str] = None
    priceWithTax: Optional[dict] = None
    priceWithoutTax: Optional[dict] = None
    tax: Optional[dict] = None
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OvhExpiringService(BaseModel):
    """Service proche de l'expiration."""
    serviceId: Optional[int] = None
    resource: Optional[str] = None
    status: Optional[str] = None
    expiration: Optional[str] = None
    days_remaining: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OvhEmailProAccount(BaseModel):
    """Compte Email Pro individuel avec details de renouvellement."""
    email: Optional[str] = None
    displayName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    login: Optional[str] = None
    domain: Optional[str] = None
    configured: Optional[bool] = None
    state: Optional[str] = None
    expirationDate: Optional[str] = None
    creationDate: Optional[str] = None
    renewPeriod: Optional[str] = None
    deleteAtExpiration: Optional[bool] = None
    currentUsage: Optional[int] = None
    quota: Optional[int] = None
    id: Optional[int] = None
    primaryEmailAddress: Optional[str] = None
    lastLogonDate: Optional[str] = None
    passwordLastUpdate: Optional[str] = None
    spamDetected: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class OvhDashboard(BaseModel):
    """Tableau de bord synthetique des services OVH."""
    total_services: int = 0
    services_by_type: dict = {}
    expiring_soon: list[dict] = []
    expired: list[dict] = []
    active_count: int = 0
    suspended_count: int = 0

    model_config = ConfigDict(from_attributes=True)

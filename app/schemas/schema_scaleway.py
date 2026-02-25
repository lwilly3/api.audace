"""Schemas Pydantic pour les reponses Dedibox (Online.net API)."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class DediboxUser(BaseModel):
    """Informations du compte utilisateur Dedibox."""
    id: Optional[int] = None
    login: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxServerLocation(BaseModel):
    """Localisation physique d'un serveur."""
    datacenter: Optional[str] = None
    room: Optional[str] = None
    bay: Optional[str] = None
    block: Optional[str] = None
    position: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxServerIp(BaseModel):
    """Adresse IP d'un serveur."""
    address: Optional[str] = None
    type: Optional[str] = None
    reverse: Optional[str] = None
    mac: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxServer(BaseModel):
    """Serveur dedie Dedibox."""
    id: Optional[int] = None
    offer: Optional[str] = None
    hostname: Optional[str] = None
    location: Optional[dict] = None
    boot_mode: Optional[str] = None
    last_reboot: Optional[str] = None
    power_status: Optional[str] = None
    abuse: Optional[str] = None
    os: Optional[dict] = None
    contacts: Optional[dict] = None
    disks: Optional[list] = None
    network: Optional[dict] = None
    ip: Optional[list] = None
    service_expiration: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxHosting(BaseModel):
    """Service d'hebergement web Dedibox."""
    id: Optional[int] = None
    offer: Optional[str] = None
    hostname: Optional[str] = None
    fqdn: Optional[str] = None
    status: Optional[str] = None
    platform: Optional[dict] = None
    disk: Optional[dict] = None
    contacts: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxDomain(BaseModel):
    """Domaine gere sur Dedibox."""
    id: Optional[int] = None
    name: Optional[str] = None
    dns_zone_status: Optional[str] = None
    status: Optional[str] = None
    contacts: Optional[dict] = None
    expiration_date: Optional[str] = None
    creation_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxFailoverIp(BaseModel):
    """IP failover Dedibox."""
    address: Optional[str] = None
    type: Optional[str] = None
    reverse: Optional[str] = None
    server_id: Optional[int] = None
    destination: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class DediboxDashboard(BaseModel):
    """Tableau de bord synthetique Dedibox."""
    total_servers: int = 0
    servers_by_status: dict = {}
    active_count: int = 0
    total_hostings: int = 0
    total_domains: int = 0
    failover_ips_count: int = 0
    user: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

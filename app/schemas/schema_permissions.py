# models.py
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Role(BaseModel):
    """
    Modèle pour représenter un rôle.
    """
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[int]  # Liste des IDs des permissions
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class Permission(BaseModel):
    """
    Modèle pour représenter une permission.
    """
    id: int
    name: str
    # description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# from pydantic import BaseModel

# Base Permission Schema
class PermissionBase(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)

# Schema for Creating a Permission
class PermissionCreate(PermissionBase):
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Schema for Reading a Permission
class PermissionRead(PermissionBase):
    id: int
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Schema for Updating a Permission
class PermissionUpdate(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


# Schéma de base pour les permissions (réutilisable)
class UserPermissionsSchema(BaseModel):
    # Permissions pour les showplans
    can_acces_showplan_broadcast_section: Optional[bool] = False
    can_acces_showplan_section: Optional[bool] = False
    can_create_showplan: Optional[bool] = False
    can_edit_showplan: Optional[bool] = False
    can_archive_showplan: Optional[bool] = False
    can_archiveStatusChange_showplan: Optional[bool] = False
    can_delete_showplan: Optional[bool] = False
    can_destroy_showplan: Optional[bool] = False
    can_changestatus_showplan: Optional[bool] = False
    can_changestatus_owned_showplan: Optional[bool] = False
    can_changestatus_archived_showplan: Optional[bool] = False
    can_setOnline_showplan: Optional[bool] = False
    can_viewAll_showplan: Optional[bool] = False

    # Permissions pour les utilisateurs
    can_acces_users_section: Optional[bool] = False
    can_view_users: Optional[bool] = False
    can_edit_users: Optional[bool] = False
    can_desable_users: Optional[bool] = False  # Corrigé "desable" -> "disable"
    can_delete_users: Optional[bool] = False

    # Permissions pour les rôles
    can_manage_roles: Optional[bool] = False
    can_assign_roles: Optional[bool] = False

    # Permissions pour les invités
    can_acces_guests_section: Optional[bool] = False
    can_view_guests: Optional[bool] = False
    can_edit_guests: Optional[bool] = False
    can_delete_guests: Optional[bool] = False

    # Permissions pour les présentateurs
    can_acces_presenters_section: Optional[bool] = False
    can_view_presenters: Optional[bool] = False
    can_create_presenters: Optional[bool] = False  # Nouvelle permission ajoutée
    can_edit_presenters: Optional[bool] = False
    can_delete_presenters: Optional[bool] = False

    # Permissions pour les émissions
    can_acces_emissions_section: Optional[bool] = False
    can_view_emissions: Optional[bool] = False
    can_create_emissions: Optional[bool] = False
    can_edit_emissions: Optional[bool] = False
    can_delete_emissions: Optional[bool] = False
    can_manage_emissions: Optional[bool] = False

    # Permissions pour les notifications
    can_view_notifications: Optional[bool] = False
    can_manage_notifications: Optional[bool] = False

    # Permissions pour les journaux et historique
    can_view_audit_logs: Optional[bool] = False
    can_view_login_history: Optional[bool] = False

    # Permissions globales
    can_manage_settings: Optional[bool] = False

    # Permissions pour les messages
    can_view_messages: Optional[bool] = False
    can_send_messages: Optional[bool] = False
    can_delete_messages: Optional[bool] = False

    # Permissions pour les fichiers
    can_view_files: Optional[bool] = False
    can_upload_files: Optional[bool] = False
    can_delete_files: Optional[bool] = False

    # Permissions pour les tâches (nouvelles)
    # can_access_tasks_section: Optional[bool] = False  # Ajout suggéré pour cohérence
    can_view_tasks: Optional[bool] = False
    can_create_tasks: Optional[bool] = False
    can_edit_tasks: Optional[bool] = False
    can_delete_tasks: Optional[bool] = False
    can_assign_tasks: Optional[bool] = False

    # Permissions pour les archives (nouvelles)
    # can_access_archives_section: Optional[bool] = False  # Ajout suggéré pour cohérence
    can_view_archives: Optional[bool] = False
    can_destroy_archives: Optional[bool] = False
    can_restore_archives: Optional[bool] = False
    can_delete_archives: Optional[bool] = False

    # Permissions pour le module Inventaire (Firebase)
    inventory_view: Optional[bool] = False  # Voir l'inventaire
    inventory_view_all_companies: Optional[bool] = False  # Voir l'inventaire de toutes les entreprises
    inventory_view_values: Optional[bool] = False  # Voir les valeurs/prix des équipements
    inventory_create: Optional[bool] = False  # Ajouter des équipements
    inventory_edit: Optional[bool] = False  # Modifier les équipements
    inventory_delete: Optional[bool] = False  # Supprimer/Archiver des équipements
    inventory_move: Optional[bool] = False  # Créer des mouvements (attributions, transferts)
    inventory_approve_transfers: Optional[bool] = False  # Approuver les transferts inter-sites
    inventory_approve_company_loans: Optional[bool] = False  # Approuver les prêts inter-entreprises
    inventory_maintenance_create: Optional[bool] = False  # Créer des maintenances
    inventory_maintenance_manage: Optional[bool] = False  # Gérer les maintenances
    inventory_manage_documents: Optional[bool] = False  # Gérer les documents/pièces jointes
    inventory_manage_settings: Optional[bool] = False  # Configurer les listes (catégories, statuts...)
    inventory_manage_locations: Optional[bool] = False  # Gérer les sites et locaux

    # Permissions pour les abonnements/services (Inventaire)
    inventory_subscriptions_view: Optional[bool] = False  # Voir les services/abonnements
    inventory_subscriptions_create: Optional[bool] = False  # Créer des abonnements
    inventory_subscriptions_edit: Optional[bool] = False  # Modifier des abonnements
    inventory_subscriptions_delete: Optional[bool] = False  # Supprimer des abonnements
    inventory_subscriptions_manage: Optional[bool] = False  # Gestion complète des services

    # Permissions pour les citations
    quotes_view: Optional[bool] = False
    quotes_create: Optional[bool] = False
    quotes_edit: Optional[bool] = False
    quotes_delete: Optional[bool] = False
    quotes_publish: Optional[bool] = False
    stream_transcription_view: Optional[bool] = False
    stream_transcription_create: Optional[bool] = False
    quotes_capture_live: Optional[bool] = False

    # Permissions pour le module OVH
    ovh_access_section: Optional[bool] = False  # Accéder à la section OVH
    ovh_view_services: Optional[bool] = False  # Voir les services OVH
    ovh_view_dashboard: Optional[bool] = False  # Voir le tableau de bord OVH
    ovh_view_billing: Optional[bool] = False  # Voir les factures OVH
    ovh_view_account: Optional[bool] = False  # Voir les infos du compte OVH
    ovh_manage: Optional[bool] = False  # Gestion complète du module OVH

    # Permissions pour le module Scaleway Dedibox
    scw_access_section: Optional[bool] = False  # Accéder à la section Scaleway
    scw_view_instances: Optional[bool] = False  # Voir les serveurs dédiés
    scw_view_dashboard: Optional[bool] = False  # Voir le tableau de bord Scaleway
    scw_view_billing: Optional[bool] = False  # Voir les hébergements
    scw_view_domains: Optional[bool] = False  # Voir les domaines
    scw_view_account: Optional[bool] = False  # Voir les infos du compte Scaleway
    scw_manage: Optional[bool] = False  # Gestion complète du module Scaleway

    model_config = ConfigDict(from_attributes=True)

# Schéma pour créer un modèle de rôle
class RoleTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, bool]  # Dictionnaire des permissions

    model_config = ConfigDict(from_attributes=True)

# Schéma pour mettre à jour un modèle de rôle
class RoleTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

    model_config = ConfigDict(from_attributes=True)

# Schéma pour retourner un modèle de rôle
class RoleTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: Dict[str, bool]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
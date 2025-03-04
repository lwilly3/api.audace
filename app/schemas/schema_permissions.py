
# models.py
from typing import List, Optional,Dict
from pydantic import BaseModel
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


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }


class Permission(BaseModel):
    """
    Modèle pour représenter une permission.
    """
    id: int
    name: str
    description: Optional[str] = None


    model_config = {
        "from_attributes": True,  # Remplace orm_mode
    }










# from pydantic import BaseModel

# Base Permission Schema
class PermissionBase(BaseModel):
    name: str
    

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schema for Creating a Permission
class PermissionCreate(PermissionBase):
    description: Optional[str] = None



    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }
    

# Schema for Reading a Permission
class PermissionRead(PermissionBase):
    id: int
    description: Optional[str] = None

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schema for Updating a Permission
class PermissionUpdate(BaseModel):
    name: str
    




# Schéma de base pour les permissions (réutilisable)
class UserPermissionsSchema(BaseModel):
    # can_acces_showplan_section: Optional[bool] = False
    # can_create_showplan: Optional[bool] = False
    # can_edit_users: Optional[bool] = False
    # Ajoute toutes les autres permissions ici si besoin, ou utilise Dict[str, bool] pour flexibilité
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
    can_acces_users_section: Optional[bool] = False
    can_view_users: Optional[bool] = False
    can_edit_users: Optional[bool] = False
    can_desable_users: Optional[bool] = False
    can_delete_users: Optional[bool] = False
    can_manage_roles: Optional[bool] = False
    can_assign_roles: Optional[bool] = False
    can_acces_guests_section: Optional[bool] = False
    can_view_guests: Optional[bool] = False
    can_edit_guests: Optional[bool] = False
    can_delete_guests: Optional[bool] = False
    can_acces_presenters_section: Optional[bool] = False
    can_view_presenters: Optional[bool] = False
    can_edit_presenters: Optional[bool] = False
    can_delete_presenters: Optional[bool] = False
    can_acces_emissions_section: Optional[bool] = False
    can_view_emissions: Optional[bool] = False
    can_create_emissions: Optional[bool] = False
    can_edit_emissions: Optional[bool] = False
    can_delete_emissions: Optional[bool] = False
    can_manage_emissions: Optional[bool] = False
    can_view_notifications: Optional[bool] = False
    can_manage_notifications: Optional[bool] = False
    can_view_audit_logs: Optional[bool] = False
    can_view_login_history: Optional[bool] = False
    can_manage_settings: Optional[bool] = False
    can_view_messages: Optional[bool] = False
    can_send_messages: Optional[bool] = False
    can_delete_messages: Optional[bool] = False
    can_view_files: Optional[bool] = False
    can_upload_files: Optional[bool] = False
    can_delete_files: Optional[bool] = False

    
    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schéma pour créer un modèle de rôle
class RoleTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, bool]  # Dictionnaire des permissions

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schéma pour mettre à jour un modèle de rôle
class RoleTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }

# Schéma pour retourner un modèle de rôle
class RoleTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: Dict[str, bool]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,  # Activates attribute-based mapping
    }
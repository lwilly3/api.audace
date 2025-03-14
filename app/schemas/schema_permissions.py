
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
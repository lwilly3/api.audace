"""
Schemas Pydantic pour la gestion des sauvegardes (Backup Management).

Conventions : ConfigDict(from_attributes=True), XxxResponse / XxxUpdate.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ── Config ──────────────────────────────────────────────────────

class BackupConfigResponse(BaseModel):
    """Configuration actuelle du backup (reponse API)."""
    is_connected: bool = False
    google_email: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    google_drive_folder_name: Optional[str] = None
    auto_backup_enabled: bool = False
    auto_backup_hour: int = 3
    retention_days: int = 30
    connected_at: Optional[datetime] = None
    token_valid: bool = False

    model_config = ConfigDict(from_attributes=True)


class BackupConfigUpdate(BaseModel):
    """Champs modifiables de la configuration."""
    google_drive_folder_id: Optional[str] = None
    google_drive_folder_name: Optional[str] = None
    auto_backup_enabled: Optional[bool] = None
    auto_backup_hour: Optional[int] = Field(None, ge=0, le=23)
    retention_days: Optional[int] = Field(None, ge=1, le=365)


# ── OAuth ───────────────────────────────────────────────────────

class OAuthUrlResponse(BaseModel):
    """URL de redirection Google OAuth."""
    redirect_url: str
    state: str


# ── History ─────────────────────────────────────────────────────

class BackupHistoryResponse(BaseModel):
    """Entree d'historique de backup."""
    id: int
    filename: str
    file_size_bytes: Optional[int] = None
    backup_type: str = "manual"
    status: str = "running"
    error_message: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    uploaded_to_drive: bool = False
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    triggered_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class BackupHistoryPaginated(BaseModel):
    """Historique pagine."""
    total: int
    items: list[BackupHistoryResponse]
    skip: int
    limit: int


# ── Trigger / Restore ──────────────────────────────────────────

class BackupTriggerResponse(BaseModel):
    """Reponse au declenchement d'un backup."""
    task_id: str
    backup_id: int
    message: str


class BackupRestoreRequest(BaseModel):
    """Requete de restauration (confirmation obligatoire)."""
    confirm: str = Field(..., description="Doit etre 'RESTAURER' pour confirmer")


class BackupRestoreResponse(BaseModel):
    """Reponse au declenchement d'une restauration."""
    task_id: str
    message: str


# ── Files ───────────────────────────────────────────────────────

class BackupFileInfo(BaseModel):
    """Info sur un fichier de backup (local ou Drive)."""
    filename: str
    size_bytes: Optional[int] = None
    source: str  # "local" ou "drive"
    google_drive_file_id: Optional[str] = None
    modified_at: Optional[datetime] = None


# ── Drive Folders ─────────────────────────────────────────────

class DriveFolderInfo(BaseModel):
    """Information sur un dossier Google Drive."""
    id: str
    name: str


class CreateFolderRequest(BaseModel):
    """Requete de creation d'un dossier Drive."""
    folder_name: str = Field(..., min_length=1, max_length=255)

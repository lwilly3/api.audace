from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


# ════════════════════════════════════════════════════════════════
# CONFIG OPTIONS
# ════════════════════════════════════════════════════════════════

class ConfigOptionCreate(BaseModel):
    list_type: str = Field(
        ..., max_length=50,
        description="Type de liste (category, equipment_status, movement_type, "
                    "mission_type, condition_state, document_type, service_category)",
    )
    name: str = Field(..., max_length=255, description="Nom de l'option")
    description: Optional[str] = Field(None, description="Description")
    color: Optional[str] = Field(None, max_length=20, description="Code couleur hexadecimal")
    icon: Optional[str] = Field(None, max_length=50, description="Nom d'icone Lucide")
    is_default: bool = Field(False, description="Option par defaut")
    sort_order: int = Field(0, description="Ordre de tri")

    model_config = ConfigDict(from_attributes=True)


class ConfigOptionResponse(BaseModel):
    id: int
    list_type: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool
    is_active: bool
    sort_order: int
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConfigOptionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ConfigOptionReorder(BaseModel):
    list_type: str = Field(..., max_length=50, description="Type de liste a reordonner")
    ordered_ids: list[int] = Field(..., description="IDs dans le nouvel ordre")

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# GLOBAL SETTINGS
# ════════════════════════════════════════════════════════════════

class GlobalSettingsResponse(BaseModel):
    """Retourne un dict plat cle → valeur (valeurs parsees selon leur type)."""
    settings: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class GlobalSettingsUpdate(BaseModel):
    """Dict de mises a jour : cle → nouvelle valeur."""
    entries: dict[str, str | int | bool | float] = Field(
        ..., description="Parametres a mettre a jour (cle → valeur)"
    )

    model_config = ConfigDict(from_attributes=True)

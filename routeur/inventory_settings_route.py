from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_inventory_settings import (
    get_options_by_type,
    get_option_by_id,
    create_option,
    update_option,
    soft_delete_option,
    reorder_options,
    get_all_global_settings,
    update_global_settings,
    seed_default_settings,
)
from app.schemas.schema_inventory_settings import (
    ConfigOptionCreate, ConfigOptionResponse, ConfigOptionUpdate,
    ConfigOptionReorder,
    GlobalSettingsResponse, GlobalSettingsUpdate,
)
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-settings"]
)


# ════════════════════════════════════════════════════════════════
# GLOBAL SETTINGS
# ════════════════════════════════════════════════════════════════

@router.get("/settings/", response_model=GlobalSettingsResponse)
def get_settings_route(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    settings = get_all_global_settings(db)
    return GlobalSettingsResponse(settings=settings)


@router.put("/settings/", response_model=GlobalSettingsResponse)
def update_settings_route(
    data: GlobalSettingsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    settings = update_global_settings(db, data.entries, current_user.id)
    log_action(db, current_user.id, "update", "inventory_global_settings", 0)
    return GlobalSettingsResponse(settings=settings)


# ════════════════════════════════════════════════════════════════
# CONFIG OPTIONS
# ════════════════════════════════════════════════════════════════

@router.get("/settings/options/{list_type}", response_model=list[ConfigOptionResponse])
def get_options_route(
    list_type: str,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    return get_options_by_type(db, list_type, include_inactive)


@router.post("/settings/options/", response_model=ConfigOptionResponse)
def create_option_route(
    data: ConfigOptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = create_option(db, data)
    log_action(db, current_user.id, "create", "inventory_config_options", result.id)
    return result


@router.put("/settings/options/reorder", response_model=list[ConfigOptionResponse])
def reorder_options_route(
    data: ConfigOptionReorder,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = reorder_options(db, data.list_type, data.ordered_ids)
    log_action(db, current_user.id, "reorder", "inventory_config_options", 0)
    return result


@router.put("/settings/options/{option_id}", response_model=ConfigOptionResponse)
def update_option_route(
    option_id: int,
    data: ConfigOptionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = update_option(db, option_id, data)
    log_action(db, current_user.id, "update", "inventory_config_options", option_id)
    return result


@router.delete("/settings/options/{option_id}", response_model=bool)
def delete_option_route(
    option_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = soft_delete_option(db, option_id)
    log_action(db, current_user.id, "soft_delete", "inventory_config_options", option_id)
    return result


# ════════════════════════════════════════════════════════════════
# SEED (initialisation des valeurs par defaut)
# ════════════════════════════════════════════════════════════════

@router.post("/settings/seed")
def seed_settings_route(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    result = seed_default_settings(db)
    log_action(db, current_user.id, "seed", "inventory_settings", 0)
    return result

from typing import Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

from app.models.model_inventory_settings import InventoryConfigOption, InventoryGlobalSettings
from app.schemas.schema_inventory_settings import (
    ConfigOptionCreate, ConfigOptionResponse, ConfigOptionUpdate,
)


# ════════════════════════════════════════════════════════════════
# CONFIG OPTIONS CRUD
# ════════════════════════════════════════════════════════════════

def get_options_by_type(
    db: Session,
    list_type: str,
    include_inactive: bool = False,
) -> list[ConfigOptionResponse]:
    """Retourne toutes les options d'un type donne, triees par sort_order."""
    try:
        query = db.query(InventoryConfigOption).filter(
            InventoryConfigOption.list_type == list_type,
            InventoryConfigOption.is_deleted == False,
        )
        if not include_inactive:
            query = query.filter(InventoryConfigOption.is_active == True)
        options = query.order_by(InventoryConfigOption.sort_order).all()
        return [ConfigOptionResponse.model_validate(o) for o in options]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation options: {str(e)}")


def get_option_by_id(db: Session, option_id: int) -> ConfigOptionResponse:
    """Retourne une option par son ID."""
    option = db.query(InventoryConfigOption).filter(
        InventoryConfigOption.id == option_id,
        InventoryConfigOption.is_deleted == False,
    ).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option non trouvee")
    return ConfigOptionResponse.model_validate(option)


def create_option(db: Session, data: ConfigOptionCreate) -> ConfigOptionResponse:
    """Cree une nouvelle option de configuration."""
    try:
        option = InventoryConfigOption(
            list_type=data.list_type,
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            is_default=data.is_default,
            sort_order=data.sort_order,
        )
        db.add(option)
        db.commit()
        db.refresh(option)
        return ConfigOptionResponse.model_validate(option)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur creation option: {str(e)}")


def update_option(db: Session, option_id: int, data: ConfigOptionUpdate) -> ConfigOptionResponse:
    """Met a jour une option existante."""
    try:
        option = db.query(InventoryConfigOption).filter(
            InventoryConfigOption.id == option_id,
            InventoryConfigOption.is_deleted == False,
        ).first()
        if not option:
            raise HTTPException(status_code=404, detail="Option non trouvee")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(option, field, value)

        db.commit()
        db.refresh(option)
        return ConfigOptionResponse.model_validate(option)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour option: {str(e)}")


def soft_delete_option(db: Session, option_id: int) -> bool:
    """Suppression douce d'une option."""
    try:
        option = db.query(InventoryConfigOption).filter(
            InventoryConfigOption.id == option_id,
        ).first()
        if not option:
            raise HTTPException(status_code=404, detail="Option non trouvee")
        option.is_deleted = True
        option.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur suppression option: {str(e)}")


def reorder_options(
    db: Session,
    list_type: str,
    ordered_ids: list[int],
) -> list[ConfigOptionResponse]:
    """Reordonne les options d'un type donne selon la liste d'IDs fournie."""
    try:
        options = db.query(InventoryConfigOption).filter(
            InventoryConfigOption.list_type == list_type,
            InventoryConfigOption.is_deleted == False,
            InventoryConfigOption.id.in_(ordered_ids),
        ).all()

        option_map = {o.id: o for o in options}
        for index, option_id in enumerate(ordered_ids):
            if option_id in option_map:
                option_map[option_id].sort_order = index

        db.commit()

        # Retourner les options dans le nouvel ordre
        return get_options_by_type(db, list_type)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur reordonnancement options: {str(e)}")


# ════════════════════════════════════════════════════════════════
# GLOBAL SETTINGS CRUD
# ════════════════════════════════════════════════════════════════

def _parse_setting_value(value: str, value_type: str) -> Any:
    """Parse une valeur de setting selon son type declare."""
    if value_type == "int":
        return int(value)
    elif value_type == "float":
        return float(value)
    elif value_type == "bool":
        return value.lower() in ("true", "1", "yes")
    return value  # string par defaut


def _infer_value_type(value: Any) -> str:
    """Infere le type d'une valeur pour le stockage."""
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    return "string"


def get_all_global_settings(db: Session) -> dict[str, Any]:
    """Retourne tous les parametres globaux sous forme de dict cle → valeur parsee."""
    try:
        settings = db.query(InventoryGlobalSettings).all()
        return {s.key: _parse_setting_value(s.value, s.value_type) for s in settings}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur recuperation parametres: {str(e)}")


def update_global_settings(
    db: Session,
    updates: dict[str, str | int | bool | float],
    user_id: int,
) -> dict[str, Any]:
    """Met a jour un ou plusieurs parametres globaux."""
    try:
        for key, value in updates.items():
            setting = db.query(InventoryGlobalSettings).filter(
                InventoryGlobalSettings.key == key
            ).first()

            str_value = str(value)
            inferred_type = _infer_value_type(value)

            if setting:
                setting.value = str_value
                setting.value_type = inferred_type
                setting.updated_by = user_id
            else:
                # Creer le parametre s'il n'existe pas
                new_setting = InventoryGlobalSettings(
                    key=key,
                    value=str_value,
                    value_type=inferred_type,
                    updated_by=user_id,
                )
                db.add(new_setting)

        db.commit()
        return get_all_global_settings(db)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur mise a jour parametres: {str(e)}")


# ════════════════════════════════════════════════════════════════
# SEED (valeurs par defaut)
# ════════════════════════════════════════════════════════════════

def seed_default_settings(db: Session) -> dict[str, Any]:
    """
    Cree les options de configuration et parametres globaux par defaut
    si la table est vide. Idempotent (ne duplique pas).
    """
    try:
        # ── Options de configuration ──────────────────────────────

        _DEFAULT_OPTIONS: list[dict] = [
            # Categories d'equipement
            {"list_type": "category", "name": "Audio", "color": "#6366f1", "icon": "Headphones", "sort_order": 0},
            {"list_type": "category", "name": "Video", "color": "#8b5cf6", "icon": "Video", "sort_order": 1},
            {"list_type": "category", "name": "Informatique", "color": "#3b82f6", "icon": "Monitor", "sort_order": 2},
            {"list_type": "category", "name": "Mobilier", "color": "#f59e0b", "icon": "Armchair", "sort_order": 3},
            {"list_type": "category", "name": "Cablage", "color": "#64748b", "icon": "Cable", "sort_order": 4},
            {"list_type": "category", "name": "Eclairage", "color": "#eab308", "icon": "Lightbulb", "sort_order": 5},
            {"list_type": "category", "name": "Alimentation", "color": "#ef4444", "icon": "Zap", "sort_order": 6},
            {"list_type": "category", "name": "Autre", "color": "#94a3b8", "icon": "Package", "sort_order": 7},

            # Statuts d'equipement
            {"list_type": "equipment_status", "name": "Disponible", "color": "#22c55e", "icon": "CheckCircle", "sort_order": 0},
            {"list_type": "equipment_status", "name": "En service", "color": "#3b82f6", "icon": "Play", "sort_order": 1},
            {"list_type": "equipment_status", "name": "En maintenance", "color": "#f59e0b", "icon": "Wrench", "sort_order": 2},
            {"list_type": "equipment_status", "name": "Hors service", "color": "#ef4444", "icon": "XCircle", "sort_order": 3},
            {"list_type": "equipment_status", "name": "Reserve", "color": "#8b5cf6", "icon": "Lock", "sort_order": 4},
            {"list_type": "equipment_status", "name": "En transit", "color": "#06b6d4", "icon": "Truck", "sort_order": 5},

            # Types de mouvement
            {"list_type": "movement_type", "name": "Assignation", "color": "#3b82f6", "icon": "UserPlus", "sort_order": 0},
            {"list_type": "movement_type", "name": "Retour", "color": "#22c55e", "icon": "RotateCcw", "sort_order": 1},
            {"list_type": "movement_type", "name": "Pret", "color": "#f59e0b", "icon": "Handshake", "sort_order": 2},
            {"list_type": "movement_type", "name": "Transfert inter-sites", "color": "#8b5cf6", "icon": "ArrowLeftRight", "sort_order": 3},
            {"list_type": "movement_type", "name": "Maintenance", "color": "#ef4444", "icon": "Wrench", "sort_order": 4},
            {"list_type": "movement_type", "name": "Mission", "color": "#06b6d4", "icon": "Briefcase", "sort_order": 5},

            # Etats de condition
            {"list_type": "condition_state", "name": "Neuf", "color": "#22c55e", "icon": "Sparkles", "sort_order": 0},
            {"list_type": "condition_state", "name": "Bon etat", "color": "#3b82f6", "icon": "ThumbsUp", "sort_order": 1},
            {"list_type": "condition_state", "name": "Usure normale", "color": "#f59e0b", "icon": "Minus", "sort_order": 2},
            {"list_type": "condition_state", "name": "Endommage", "color": "#ef4444", "icon": "AlertTriangle", "sort_order": 3},
            {"list_type": "condition_state", "name": "Hors service", "color": "#991b1b", "icon": "Ban", "sort_order": 4},

            # Types de document
            {"list_type": "document_type", "name": "Manuel", "color": "#3b82f6", "icon": "BookOpen", "sort_order": 0},
            {"list_type": "document_type", "name": "Configuration", "color": "#8b5cf6", "icon": "Settings", "sort_order": 1},
            {"list_type": "document_type", "name": "Fiche technique", "color": "#06b6d4", "icon": "FileText", "sort_order": 2},
            {"list_type": "document_type", "name": "Certificat", "color": "#22c55e", "icon": "Award", "sort_order": 3},
            {"list_type": "document_type", "name": "Garantie", "color": "#f59e0b", "icon": "Shield", "sort_order": 4},
            {"list_type": "document_type", "name": "Facture", "color": "#64748b", "icon": "Receipt", "sort_order": 5},
            {"list_type": "document_type", "name": "Rapport maintenance", "color": "#ef4444", "icon": "ClipboardList", "sort_order": 6},
            {"list_type": "document_type", "name": "Autre", "color": "#94a3b8", "icon": "File", "sort_order": 7},

            # Categories de service
            {"list_type": "service_category", "name": "Hebergement", "color": "#3b82f6", "icon": "Server", "sort_order": 0},
            {"list_type": "service_category", "name": "Domaine", "color": "#8b5cf6", "icon": "Globe", "sort_order": 1},
            {"list_type": "service_category", "name": "Cloud", "color": "#06b6d4", "icon": "Cloud", "sort_order": 2},
            {"list_type": "service_category", "name": "SaaS", "color": "#22c55e", "icon": "AppWindow", "sort_order": 3},
            {"list_type": "service_category", "name": "Telecom", "color": "#f59e0b", "icon": "Phone", "sort_order": 4},
            {"list_type": "service_category", "name": "Streaming", "color": "#ef4444", "icon": "Radio", "sort_order": 5},
            {"list_type": "service_category", "name": "Securite", "color": "#64748b", "icon": "ShieldCheck", "sort_order": 6},
            {"list_type": "service_category", "name": "Autre", "color": "#94a3b8", "icon": "Package", "sort_order": 7},
        ]

        created_options = 0
        for opt in _DEFAULT_OPTIONS:
            exists = db.query(InventoryConfigOption).filter(
                InventoryConfigOption.list_type == opt["list_type"],
                InventoryConfigOption.name == opt["name"],
            ).first()
            if not exists:
                db.add(InventoryConfigOption(**opt, is_default=True))
                created_options += 1

        # ── Parametres globaux ────────────────────────────────────

        _DEFAULT_GLOBAL_SETTINGS: list[dict] = [
            {"key": "reference_prefix", "value": "INV", "value_type": "string", "description": "Prefixe des references d'equipement"},
            {"key": "reference_counter", "value": "0", "value_type": "int", "description": "Compteur actuel de references auto-incrementees"},
            {"key": "default_warranty_months", "value": "24", "value_type": "int", "description": "Duree de garantie par defaut (mois)"},
            {"key": "low_stock_threshold", "value": "5", "value_type": "int", "description": "Seuil d'alerte de stock bas"},
            {"key": "auto_reference", "value": "true", "value_type": "bool", "description": "Generation automatique des references"},
            {"key": "require_movement_note", "value": "false", "value_type": "bool", "description": "Note obligatoire pour les mouvements"},
            {"key": "default_loan_days", "value": "14", "value_type": "int", "description": "Duree de pret par defaut (jours)"},
            {"key": "enable_barcode", "value": "false", "value_type": "bool", "description": "Activer le support code-barres"},
        ]

        created_settings = 0
        for gs in _DEFAULT_GLOBAL_SETTINGS:
            exists = db.query(InventoryGlobalSettings).filter(
                InventoryGlobalSettings.key == gs["key"],
            ).first()
            if not exists:
                db.add(InventoryGlobalSettings(**gs))
                created_settings += 1

        db.commit()

        return {
            "created_options": created_options,
            "created_settings": created_settings,
            "message": f"{created_options} options et {created_settings} parametres crees",
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur seed parametres par defaut: {str(e)}")

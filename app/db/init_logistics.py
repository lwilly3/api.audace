"""
@fileoverview Initialize default logistics configuration
Seeds initial configuration options for vehicles, drivers, teams, missions, etc.
Called during app startup to ensure default values exist.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.model_logistics_settings import LogisticsConfigOption, LogisticsGlobalSettings
import logging

logger = logging.getLogger(__name__)


def initialize_logistics_config(db: Session) -> None:
    """
    Initialize default logistics configuration at app startup.
    Idempotent — safe to call multiple times (checks existence before creating).
    
    Seeds:
    1. Vehicle segments (grumier, citerne, plateau, etc.)
    2. Vehicle statuses (active, maintenance, retired, damaged)
    3. Driver roles (driver, motor_boy)
    4. Driver statuses (active, on_leave, retired)
    5. Team statuses (active, inactive)
    6. Mission statuses (planned, in_progress, completed, cancelled)
    7. Cargo types (wood, fuel, containers, etc.)
    8. Maintenance types (preventive, corrective, inspection)
    9. Document types (insurance, inspection, license, contract)
    10. Reference prefixes and counters
    """
    try:
        # Check if already initialized (by seeing if we have any vehicle segments)
        existing = db.query(LogisticsConfigOption).filter_by(list_type="vehicle_segment").first()
        if existing:
            logger.info("✅ Logistics configuration already initialized")
            return

        # ====================================================================
        # VEHICLE SEGMENTS
        # ====================================================================
        vehicle_segments = [
            {"name": "grumier", "label": "Grumier (bois / logs)", "description": "Camion destiné au transport de bois et troncs"},
            {"name": "citerne", "label": "Citerne (liquides)", "description": "Camion citerne pour transport de carburant, eau, produits liquides"},
            {"name": "plateau", "label": "Plateau (conteneurs)", "description": "Plateau pour conteneurs et colis divers"},
            {"name": "benne", "label": "Benne (gravats)", "description": "Benne basculante pour matériaux en vrac"},
            {"name": "frigorifique", "label": "Frigo (denrées)", "description": "Camion réfrigéré pour produits alimentaires"},
            {"name": "autres", "label": "Autres", "description": "Autres types de véhicules"},
        ]
        for seg in vehicle_segments:
            db.add(LogisticsConfigOption(
                list_type="vehicle_segment",
                name=seg["name"],
                label=seg["label"],
                description=seg["description"],
                sort_order=vehicle_segments.index(seg)
            ))

        # ====================================================================
        # VEHICLE STATUSES
        # ====================================================================
        vehicle_statuses = [
            {"name": "active", "label": "Actif", "description": "Véhicule en service"},
            {"name": "maintenance", "label": "En maintenance", "description": "Véhicule en réparation ou maintenance"},
            {"name": "retired", "label": "Retiré du service", "description": "Véhicule retiré définitivement"},
            {"name": "damaged", "label": "Endommagé", "description": "Véhicule non opérationnel suite à dommages"},
        ]
        for status in vehicle_statuses:
            db.add(LogisticsConfigOption(
                list_type="vehicle_status",
                name=status["name"],
                label=status["label"],
                description=status["description"],
                sort_order=vehicle_statuses.index(status)
            ))

        # ====================================================================
        # DRIVER ROLES
        # ====================================================================
        driver_roles = [
            {"name": "driver", "label": "Chauffeur", "description": "Conducteur principal du véhicule"},
            {"name": "motor_boy", "label": "Motor Boy", "description": "Assistant / mécanicien du véhicule"},
        ]
        for role in driver_roles:
            db.add(LogisticsConfigOption(
                list_type="driver_role",
                name=role["name"],
                label=role["label"],
                description=role["description"],
                sort_order=driver_roles.index(role)
            ))

        # ====================================================================
        # DRIVER STATUSES
        # ====================================================================
        driver_statuses = [
            {"name": "active", "label": "Actif", "description": "Chauffeur en service"},
            {"name": "on_leave", "label": "En congé", "description": "Chauffeur en permission / congé"},
            {"name": "retired", "label": "Retraité", "description": "Chauffeur à la retraite"},
            {"name": "suspended", "label": "Suspendu", "description": "Chauffeur suspendu"},
        ]
        for status in driver_statuses:
            db.add(LogisticsConfigOption(
                list_type="driver_status",
                name=status["name"],
                label=status["label"],
                description=status["description"],
                sort_order=driver_statuses.index(status)
            ))

        # ====================================================================
        # TEAM STATUSES
        # ====================================================================
        team_statuses = [
            {"name": "active", "label": "Active", "description": "Équipe en service"},
            {"name": "inactive", "label": "Inactive", "description": "Équipe inactive"},
        ]
        for status in team_statuses:
            db.add(LogisticsConfigOption(
                list_type="team_status",
                name=status["name"],
                label=status["label"],
                description=status["description"],
                sort_order=team_statuses.index(status)
            ))

        # ====================================================================
        # MISSION STATUSES
        # ====================================================================
        mission_statuses = [
            {"name": "planned", "label": "Planifiée", "description": "Mission programmée, non démarrée"},
            {"name": "in_progress", "label": "En cours", "description": "Mission en cours de réalisation"},
            {"name": "completed", "label": "Complétée", "description": "Mission terminée avec succès"},
            {"name": "cancelled", "label": "Annulée", "description": "Mission annulée"},
        ]
        for status in mission_statuses:
            db.add(LogisticsConfigOption(
                list_type="mission_status",
                name=status["name"],
                label=status["label"],
                description=status["description"],
                sort_order=mission_statuses.index(status)
            ))

        # ====================================================================
        # CHECKPOINT TYPES
        # ====================================================================
        checkpoint_types = [
            {"name": "departure", "label": "Départ", "description": "Point de départ de la mission"},
            {"name": "loading", "label": "Chargement", "description": "Point de chargement de marchandise"},
            {"name": "unloading", "label": "Déchargement", "description": "Point de déchargement de marchandise"},
            {"name": "stop", "label": "Arrêt", "description": "Arrêt intermédiaire"},
            {"name": "arrival", "label": "Arrivée", "description": "Point d'arrivée final"},
        ]
        for ctype in checkpoint_types:
            db.add(LogisticsConfigOption(
                list_type="checkpoint_type",
                name=ctype["name"],
                label=ctype["label"],
                description=ctype["description"],
                sort_order=checkpoint_types.index(ctype)
            ))

        # ====================================================================
        # CARGO TYPES
        # ====================================================================
        cargo_types = [
            {"name": "wood", "label": "Bois", "description": "Bois / grumes"},
            {"name": "fuel", "label": "Carburant", "description": "Essence, diésel, autres carburants"},
            {"name": "containers", "label": "Conteneurs", "description": "Conteneurs et colis"},
            {"name": "food", "label": "Denrées", "description": "Produits alimentaires"},
            {"name": "materials", "label": "Matériaux", "description": "Matériaux en vrac (gravier, sable, etc.)"},
            {"name": "other", "label": "Autre", "description": "Autres types de cargo"},
        ]
        for cargo in cargo_types:
            db.add(LogisticsConfigOption(
                list_type="cargo_type",
                name=cargo["name"],
                label=cargo["label"],
                description=cargo["description"],
                sort_order=cargo_types.index(cargo)
            ))

        # ====================================================================
        # MAINTENANCE TYPES
        # ====================================================================
        maintenance_types = [
            {"name": "preventive", "label": "Préventive", "description": "Maintenance programmée préventive"},
            {"name": "corrective", "label": "Corrective", "description": "Réparation suite à panne"},
            {"name": "inspection", "label": "Inspection", "description": "Inspection technique ou contrôle"},
        ]
        for mtype in maintenance_types:
            db.add(LogisticsConfigOption(
                list_type="maintenance_type",
                name=mtype["name"],
                label=mtype["label"],
                description=mtype["description"],
                sort_order=maintenance_types.index(mtype)
            ))

        # ====================================================================
        # DOCUMENT TYPES
        # ====================================================================
        document_types = [
            {"name": "insurance", "label": "Assurance", "description": "Document d'assurance véhicule"},
            {"name": "inspection", "label": "Inspection technique", "description": "Certificat d'inspection technique"},
            {"name": "license", "label": "Licence", "description": "Licence / permis de conduire"},
            {"name": "contract", "label": "Contrat", "description": "Contrat de travail / engagement"},
            {"name": "medical", "label": "Médical", "description": "Document médical (visite médicale)"},
            {"name": "other", "label": "Autre", "description": "Autres documents"},
        ]
        for dtype in document_types:
            db.add(LogisticsConfigOption(
                list_type="document_type",
                name=dtype["name"],
                label=dtype["label"],
                description=dtype["description"],
                sort_order=document_types.index(dtype)
            ))

        # ====================================================================
        # GLOBAL SETTINGS
        # ====================================================================
        # Check if global settings exists
        existing_settings = db.query(LogisticsGlobalSettings).first()
        if not existing_settings:
            settings = LogisticsGlobalSettings(
                reference_prefix_vehicle="LOG",
                reference_counter_vehicle=0,
                fuel_consumption_alert_threshold=8.0,  # Alert if > 8 L/100km
                maintenance_alert_days=30,
                document_expiry_alert_days=30,
                tire_wear_percent_alert=20,  # Alert if wear >= 20%
            )
            db.add(settings)

        db.commit()
        logger.info("✅ Logistics configuration initialized successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error initializing logistics config: {e}")
        raise

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


def _seed_breakdown_types(db: Session) -> None:
    """Seed 18 default breakdown types (list_type='breakdown_type')."""
    breakdown_types = [
        # Groupe 1 — Systèmes mécaniques
        {"name": "Moteur",                        "description": "Surchauffe, perte de puissance, fuite huile moteur, casse interne",                          "group": "mechanical", "code": "engine_failure",         "sort_order": 1},
        {"name": "Transmission & Embrayage",      "description": "Disque/butée d'embrayage, boîte de vitesses, câble accélérateur",                           "group": "mechanical", "code": "transmission_clutch",    "sort_order": 2},
        {"name": "Roulements & Essieux",          "description": "Roulements, butées, moyeux, axes de mâchoire, arrêt-graisse",                               "group": "mechanical", "code": "bearings_axle",          "sort_order": 3},
        {"name": "Suspension & Silent-blocs",     "description": "Silent-blocs BV et barre stabilisatrice, coussins de lame, ressorts",                       "group": "mechanical", "code": "suspension_silentbloc",  "sort_order": 4},
        {"name": "Freinage & Garnitures",         "description": "Garnitures, poumons de frein, mâchoires, colonnes d'air, goujons",                          "group": "mechanical", "code": "braking_system",         "sort_order": 5},
        {"name": "Pneus & Roues",                 "description": "Crevaison, usure, montage roue de secours, goujons de roue tracteur",                       "group": "mechanical", "code": "tires_wheels",           "sort_order": 6},
        # Groupe 2 — Systèmes fluides & énergie
        {"name": "Électricité & Éclairage",       "description": "Feux de gabarit, ampoules, câblage, démarreur, bouton démarrage",                           "group": "fluids_energy", "code": "electrical_lighting",  "sort_order": 7},
        {"name": "Batterie",                      "description": "Batterie déchargée ou défectueuse, problème de démarrage",                                  "group": "fluids_energy", "code": "battery",              "sort_order": 8},
        {"name": "Filtres & Lubrifiants",         "description": "Filtres gasoil/décanteur, huile moteur, lave-glace, rinçage réservoir",                     "group": "fluids_energy", "code": "filters_lubricants",   "sort_order": 9},
        {"name": "Circuits hydrauliques & Pneumatiques", "description": "Raccords Ø12, fuites d'air remorque, membranes poumons, électrovanne, lève-cabine",  "group": "fluids_energy", "code": "hydraulic_pneumatic",  "sort_order": 10},
        {"name": "Fuite carburant",               "description": "Fuite au réservoir, joint de pompe alimentaire, tuyaux carburant",                          "group": "fluids_energy", "code": "fuel_leak",            "sort_order": 11},
        # Groupe 3 — Carrosserie & Structures
        {"name": "Soudure & Carrosserie",         "description": "Travaux de soudure, protection cabine, support électrovanne, structure",                    "group": "bodywork", "code": "welding_bodywork",           "sort_order": 12},
        {"name": "Vitrage & Cabine",              "description": "Vitre de portière, protection cabine arrière, étanchéité",                                  "group": "bodywork", "code": "glazing_cabin",             "sort_order": 13},
        {"name": "Équipement plateau / grumier",  "description": "Bride de lame, boulons, raccords de benne, chaînes d'arrimage, bâche",                     "group": "bodywork", "code": "flatbed_logger_equipment",  "sort_order": 14},
        {"name": "Équipement citerne",            "description": "Vannes, joints de citerne, couvercles, pompes de transfert, jauges",                        "group": "bodywork", "code": "tanker_equipment",          "sort_order": 15},
        # Groupe 4 — Maintenance & Incidents route
        {"name": "Maintenance préventive",        "description": "Révision planifiée, vidange, contrôle avant mission, entretien périodique",                 "group": "maintenance_incidents", "code": "preventive_maintenance", "sort_order": 16},
        {"name": "Accident & Sinistre",           "description": "Collision, tonneau, sinistre route, dommages tiers",                                        "group": "maintenance_incidents", "code": "accident_incident",      "sort_order": 17},
        {"name": "Autre / Non diagnostiqué",      "description": "Panne non identifiée en attente de diagnostic par le mécanicien",                           "group": "maintenance_incidents", "code": "other_undiagnosed",      "sort_order": 18, "is_default": True},
    ]
    for bt in breakdown_types:
        db.add(LogisticsConfigOption(
            list_type="breakdown_type",
            name=bt["name"],
            description=bt["description"],
            is_default=bt.get("is_default", False),
            sort_order=bt["sort_order"],
            metadata_json={"code": bt["code"], "group": bt["group"]},
        ))


def _seed_panne_categories(db: Session) -> None:
    """Seed the 9 default panne categories (list_type='panne_category')."""
    panne_categories = [
        {"name": "moteur",        "description": "Moteur (panne, surchauffe, huile)",              "color": "#ef4444"},
        {"name": "transmission",  "description": "Transmission (boîte, embrayage, différentiel)",  "color": "#f97316"},
        {"name": "electrique",    "description": "Électrique (batterie, alternateur, câblage)",    "color": "#eab308"},
        {"name": "freinage",      "description": "Freinage (freins, ABS, tambours)",               "color": "#3b82f6"},
        {"name": "pneumatiques",  "description": "Pneumatiques (pneus, jantes, crevaisons)",       "color": "#8b5cf6"},
        {"name": "carrosserie",   "description": "Carrosserie (cabine, structure, benne)",         "color": "#6b7280"},
        {"name": "climatisation", "description": "Climatisation / chauffage",                      "color": "#06b6d4"},
        {"name": "hydraulique",   "description": "Hydraulique (vérins, pompes, flexibles)",        "color": "#10b981"},
        {"name": "autre",         "description": "Autre catégorie de panne",                       "color": "#9ca3af", "is_default": True},
    ]
    for i, cat in enumerate(panne_categories):
        db.add(LogisticsConfigOption(
            list_type="panne_category",
            name=cat["name"],
            description=cat["description"],
            color=cat["color"],
            is_default=cat.get("is_default", False),
            sort_order=i,
        ))


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
            # Seed panne_category if not yet added (added in v0.35.0)
            existing_category = db.query(LogisticsConfigOption).filter_by(list_type="panne_category").first()
            if not existing_category:
                _seed_panne_categories(db)
                db.commit()
                logger.info("✅ Panne categories seeded (upgrade v0.35.0)")
            # Seed breakdown_types if not yet added (added in v0.36.0)
            existing_breakdown = db.query(LogisticsConfigOption).filter_by(list_type="breakdown_type").first()
            if not existing_breakdown:
                _seed_breakdown_types(db)
                db.commit()
                logger.info("✅ Breakdown types seeded (upgrade v0.36.0)")
            else:
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
        for i, seg in enumerate(vehicle_segments):
            db.add(LogisticsConfigOption(
                list_type="vehicle_segment",
                name=seg["name"],
                description=seg["description"],
                sort_order=i,
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
        for i, status in enumerate(vehicle_statuses):
            db.add(LogisticsConfigOption(
                list_type="vehicle_status",
                name=status["name"],
                description=status["description"],
                sort_order=i,
            ))

        # ====================================================================
        # DRIVER ROLES
        # ====================================================================
        driver_roles = [
            {"name": "driver", "label": "Chauffeur", "description": "Conducteur principal du véhicule"},
            {"name": "motor_boy", "label": "Motor Boy", "description": "Assistant / mécanicien du véhicule"},
        ]
        for i, role in enumerate(driver_roles):
            db.add(LogisticsConfigOption(
                list_type="driver_role",
                name=role["name"],
                description=role["description"],
                sort_order=i,
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
        for i, status in enumerate(driver_statuses):
            db.add(LogisticsConfigOption(
                list_type="driver_status",
                name=status["name"],
                description=status["description"],
                sort_order=i,
            ))

        # ====================================================================
        # TEAM STATUSES
        # ====================================================================
        team_statuses = [
            {"name": "active", "label": "Active", "description": "Équipe en service"},
            {"name": "inactive", "label": "Inactive", "description": "Équipe inactive"},
        ]
        for i, status in enumerate(team_statuses):
            db.add(LogisticsConfigOption(
                list_type="team_status",
                name=status["name"],
                description=status["description"],
                sort_order=i,
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
        for i, status in enumerate(mission_statuses):
            db.add(LogisticsConfigOption(
                list_type="mission_status",
                name=status["name"],
                description=status["description"],
                sort_order=i,
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
        for i, ctype in enumerate(checkpoint_types):
            db.add(LogisticsConfigOption(
                list_type="checkpoint_type",
                name=ctype["name"],
                description=ctype["description"],
                sort_order=i,
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
        for i, cargo in enumerate(cargo_types):
            db.add(LogisticsConfigOption(
                list_type="cargo_type",
                name=cargo["name"],
                description=cargo["description"],
                sort_order=i,
            ))

        # ====================================================================
        # MAINTENANCE TYPES
        # ====================================================================
        maintenance_types = [
            {"name": "preventive", "label": "Préventive", "description": "Maintenance programmée préventive"},
            {"name": "corrective", "label": "Corrective", "description": "Réparation suite à panne"},
            {"name": "inspection", "label": "Inspection", "description": "Inspection technique ou contrôle"},
        ]
        for i, mtype in enumerate(maintenance_types):
            db.add(LogisticsConfigOption(
                list_type="maintenance_type",
                name=mtype["name"],
                description=mtype["description"],
                sort_order=i,
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
        for i, dtype in enumerate(document_types):
            db.add(LogisticsConfigOption(
                list_type="document_type",
                name=dtype["name"],
                description=dtype["description"],
                sort_order=i,
            ))

        # ====================================================================
        # PANNE CATEGORIES
        # ====================================================================
        _seed_panne_categories(db)

        # ====================================================================
        # BREAKDOWN TYPES (types de panne multi-select)
        # ====================================================================
        _seed_breakdown_types(db)

        # ====================================================================
        # GLOBAL SETTINGS (key-value store)
        # ====================================================================
        settings_defaults = [
            {"key": "reference_prefix_vehicle", "value": "LOG", "value_type": "string", "description": "Préfixe référence véhicule"},
            {"key": "reference_counter_vehicle", "value": "0", "value_type": "int", "description": "Compteur référence véhicule"},
            {"key": "reference_prefix_mission", "value": "MIS", "value_type": "string", "description": "Préfixe référence mission"},
            {"key": "reference_counter_mission", "value": "0", "value_type": "int", "description": "Compteur référence mission"},
            {"key": "fuel_consumption_alert_threshold", "value": "8.0", "value_type": "float", "description": "Seuil alerte consommation L/100km"},
            {"key": "maintenance_alert_days", "value": "30", "value_type": "int", "description": "Jours avant alerte maintenance"},
            {"key": "document_expiry_alert_days", "value": "30", "value_type": "int", "description": "Jours avant alerte expiration document"},
            {"key": "tire_wear_percent_alert", "value": "20", "value_type": "int", "description": "Seuil alerte usure pneumatique (%)"},
        ]
        for setting in settings_defaults:
            existing_setting = db.query(LogisticsGlobalSettings).filter_by(key=setting["key"]).first()
            if not existing_setting:
                db.add(LogisticsGlobalSettings(**setting))

        db.commit()
        logger.info("✅ Logistics configuration initialized successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error initializing logistics config: {e}")
        raise

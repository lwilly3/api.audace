from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class UserPermissions(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Permissions existantes pour les showplans
    can_acces_showplan_broadcast_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_acces_showplan_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_create_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_edit_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_archive_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_archiveStatusChange_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_destroy_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_changestatus_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_changestatus_owned_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_changestatus_archived_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_setOnline_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_viewAll_showplan = Column(Boolean, default=False, server_default=text('false'), nullable=False)



    # Nouvelles permissions pour les utilisateurs
    can_acces_users_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_edit_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_desable_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)


    # Permissions pour les rôles
    can_manage_roles = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_assign_roles = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les invités
    can_acces_guests_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_guests = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_edit_guests = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_guests = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les présentateurs  
    can_acces_presenters_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_presenters = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_create_presenters = Column(Boolean, default=False, server_default=text('false'), nullable=True)  # Ajout suggéré
    can_edit_presenters = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_presenters = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les émissions  
    can_acces_emissions_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_emissions = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_create_emissions = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_edit_emissions = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_emissions = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_manage_emissions = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les notifications
    can_view_notifications = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_manage_notifications = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les journaux et historique
    can_view_audit_logs = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_login_history = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions globales
    can_manage_settings = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les Users  
    can_acces_users_section= Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_view_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_edit_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_desable_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_users = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    
    # Permissions pour les Roles
    can_manage_roles = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_assign_roles = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les Messages
    can_view_messages = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_send_messages = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_messages = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Permissions pour les Fichiers
    can_view_files = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_upload_files = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    can_delete_files = Column(Boolean, default=False, server_default=text('false'), nullable=False)



    # Timestamp
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)

     # Permissions pour les tâches
    can_view_tasks = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_create_tasks = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_edit_tasks = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_delete_tasks = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_assign_tasks = Column(Boolean, default=False, server_default=text('false'), nullable=True)


    # Permissions pour les archives
    can_view_archives = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_destroy_archives = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_restore_archives = Column(Boolean, default=False, server_default=text('false'), nullable=True)
    can_delete_archives = Column(Boolean, default=False, server_default=text('false'), nullable=True)  

    # Permissions pour le module Citations (intégration Firebase)
    quotes_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Visualiser les citations
    quotes_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer de nouvelles citations
    quotes_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier les citations existantes
    quotes_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer des citations
    quotes_publish = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Publier sur réseaux sociaux
    stream_transcription_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les transcriptions en direct
    stream_transcription_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Démarrer une transcription

    quotes_capture_live = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Capturer depuis transcription live

    # Permissions pour le module Inventaire (Firebase)
    inventory_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir l'inventaire
    inventory_view_all_companies = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir l'inventaire de toutes les entreprises
    inventory_view_values = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les valeurs/prix des équipements
    inventory_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Ajouter des équipements
    inventory_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier les équipements
    inventory_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer/Archiver des équipements
    inventory_move = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer des mouvements (attributions, transferts)
    inventory_approve_transfers = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Approuver les transferts inter-sites
    inventory_approve_company_loans = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Approuver les prêts inter-entreprises
    inventory_maintenance_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer des maintenances
    inventory_maintenance_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les maintenances
    inventory_manage_documents = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les documents/pièces jointes
    inventory_manage_settings = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Configurer les listes (catégories, statuts...)
    inventory_manage_locations = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les sites et locaux

    # Permissions pour les abonnements/services (Inventaire)
    inventory_subscriptions_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les services/abonnements
    inventory_subscriptions_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer des abonnements
    inventory_subscriptions_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier des abonnements
    inventory_subscriptions_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer des abonnements
    inventory_subscriptions_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gestion complète des services

    # Permissions pour le module OVH (consultation API)
    ovh_access_section = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Accéder à la section OVH
    ovh_view_services = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir la liste et détails des services
    ovh_view_dashboard = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir le tableau de bord OVH
    ovh_view_billing = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les factures OVH
    ovh_view_account = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les infos du compte OVH
    ovh_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gestion complète du module OVH

    # Permissions pour le module Scaleway (consultation API)
    scw_access_section = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Accéder à la section Scaleway
    scw_view_instances = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les instances/serveurs
    scw_view_dashboard = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir le tableau de bord Scaleway
    scw_view_billing = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir la facturation Scaleway
    scw_view_domains = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les domaines/DNS Scaleway
    scw_view_account = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les infos du compte Scaleway
    scw_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gestion complète du module Scaleway

    # Permissions pour le module Social (réseaux sociaux)
    social_access_section = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Accéder au module Social
    social_view_posts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les publications
    social_create_posts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer des publications
    social_edit_posts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier des publications
    social_delete_posts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer des publications
    social_publish_posts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Publier des publications
    social_view_inbox = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir l'inbox social
    social_reply_comments = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Répondre aux commentaires
    social_delete_comments = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer des commentaires
    social_reply_messages = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Répondre aux messages privés
    social_view_stats = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les statistiques
    social_export_stats = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Exporter les statistiques
    social_manage_accounts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les comptes sociaux
    social_manage_settings = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les paramètres Social
    social_view_articles = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les articles WordPress
    social_create_articles = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Créer des articles WordPress
    social_edit_articles = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier des articles WordPress
    social_delete_articles = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Supprimer des articles WordPress
    social_view_pinned = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les contenus epingles
    social_create_pinned = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Creer des contenus epingles
    social_edit_pinned = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Modifier des contenus epingles
    social_delete_pinned = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Desepingler des contenus

    # Permissions pour les flux RSS (Social)
    social_view_rss = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les flux RSS et articles
    social_manage_rss = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gerer les flux RSS (CRUD, refresh)

    # Permissions pour la sécurité (2FA)
    can_enforce_2fa = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Peut forcer le 2FA par rôle
    can_reset_user_2fa = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Peut reset le 2FA d'un utilisateur

    # Permissions pour les sauvegardes (Backup management)
    can_manage_backups = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # ════════════════════════════════════════════════════════════════
    # Permissions pour le module Logistique (transport terrestre)
    # ════════════════════════════════════════════════════════════════

    # Accès au module
    logistics_access_section = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Accéder à la section Logistique
    logistics_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Accéder au module
    logistics_view_all_companies = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir toutes les entreprises
    logistics_manage_settings = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Gérer les paramètres du module

    # Gestion des véhicules
    logistics_vehicles_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_vehicles_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_vehicles_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_vehicles_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion des chauffeurs
    logistics_drivers_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_drivers_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_drivers_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_drivers_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion des équipes
    logistics_teams_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_teams_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_teams_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_teams_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion des missions
    logistics_missions_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_missions_view_own = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Chauffeur: ses missions
    logistics_missions_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_missions_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_missions_submit = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Chauffeur: soumettre
    logistics_missions_add_photos = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Photos/observations
    logistics_missions_approve = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Superviseur: valider
    logistics_missions_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion du carburant
    logistics_fuel_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_fuel_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Chauffeur: saisir
    logistics_fuel_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_fuel_alerts = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Superviseur: alertes

    # Gestion de la maintenance
    logistics_maintenance_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_maintenance_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_maintenance_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_maintenance_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion des pneumatiques
    logistics_tires_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    logistics_tires_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Gestion des documents
    logistics_documents_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Financier & KPIs
    logistics_financial_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Montants et marges
    logistics_kpi_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # KPIs
    logistics_reports_export = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Rapports

    # Administration
    logistics_settings_manage = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Paramètres (frontend: logistics_manage_settings)

    # ===========================================================================
    # Module Gestion des Pannes
    # ===========================================================================

    # Accès au module
    pannes_access_section = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    # Fiches pannes
    pannes_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    pannes_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    pannes_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    pannes_delete = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Admin uniquement
    pannes_view_all_companies = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Voir les 2 sociétés

    # Acteurs (personnel terrain)
    acteurs_view = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    acteurs_create = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    acteurs_edit = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    acteurs_link_account = Column(Boolean, default=False, server_default=text('false'), nullable=False)  # Lier acteur → user

    # Relation avec la table users
    user = relationship("User", back_populates="permissions")




#1 can_access_showplan_section - Section "Show Plans"
#2 can_access_emissions_section - Section "Shows" (Émissions)
#3 can_access_guests_section - Section "Guests" (Invités)
#4 can_view_users - Section "Team" (Équipe)
#5 can_manage_roles - Section "Users" (Utilisateurs, probablement pour la gestion des rôles)
#6 can_view_messages - Section "Chat" (Messagerie)
#7 can_manage_settings - Section "Settings" (Paramètres)
#8 can_view_tasks - Section "Tasks" (Tâches)
#9 can_view_archives - Section "Archives"
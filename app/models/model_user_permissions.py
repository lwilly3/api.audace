from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class UserPermissions(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Permissions existantes pour les showplans
    can_acces_showplan_broadcast_section= Column(Boolean, default=False, nullable=False)
    can_acces_showplan_section= Column(Boolean, default=False, nullable=False)
    can_create_showplan = Column(Boolean, default=False, nullable=False)
    can_edit_showplan = Column(Boolean, default=False, nullable=False)
    can_archive_showplan = Column(Boolean, default=False, nullable=False)
    can_archiveStatusChange_showplan = Column(Boolean, default=False, nullable=False)
    can_delete_showplan = Column(Boolean, default=False, nullable=False)
    can_destroy_showplan = Column(Boolean, default=False, nullable=False)
    can_changestatus_showplan = Column(Boolean, default=False, nullable=False)
    can_changestatus_owned_showplan = Column(Boolean, default=False, nullable=False)
    can_changestatus_archived_showplan = Column(Boolean, default=False, nullable=False)
    can_setOnline_showplan = Column(Boolean, default=False, nullable=False)
    can_viewAll_showplan = Column(Boolean, default=False, nullable=False)



    # Nouvelles permissions pour les utilisateurs
    can_acces_users_section= Column(Boolean, default=False, nullable=False)
    can_view_users = Column(Boolean, default=False, nullable=False)
    can_edit_users = Column(Boolean, default=False, nullable=False)
    can_desable_users = Column(Boolean, default=False, nullable=False)
    can_delete_users = Column(Boolean, default=False, nullable=False)


    # Permissions pour les rôles
    can_manage_roles = Column(Boolean, default=False, nullable=False)
    can_assign_roles = Column(Boolean, default=False, nullable=False)

    # Permissions pour les invités
    can_acces_guests_section= Column(Boolean, default=False, nullable=False)
    can_view_guests = Column(Boolean, default=False, nullable=False)
    can_edit_guests = Column(Boolean, default=False, nullable=False)
    can_delete_guests = Column(Boolean, default=False, nullable=False)

    # Permissions pour les présentateurs  
    can_acces_presenters_section= Column(Boolean, default=False, nullable=False)
    can_view_presenters = Column(Boolean, default=False, nullable=False)
    can_create_presenters = Column(Boolean, default=False, nullable=True)  # Ajout suggéré
    can_edit_presenters = Column(Boolean, default=False, nullable=False)
    can_delete_presenters = Column(Boolean, default=False, nullable=False)

    # Permissions pour les émissions  
    can_acces_emissions_section= Column(Boolean, default=False, nullable=False)
    can_view_emissions = Column(Boolean, default=False, nullable=False)
    can_create_emissions = Column(Boolean, default=False, nullable=False)
    can_edit_emissions = Column(Boolean, default=False, nullable=False)
    can_delete_emissions = Column(Boolean, default=False, nullable=False)
    can_manage_emissions = Column(Boolean, default=False, nullable=False)

    # Permissions pour les notifications
    can_view_notifications = Column(Boolean, default=False, nullable=False)
    can_manage_notifications = Column(Boolean, default=False, nullable=False)

    # Permissions pour les journaux et historique
    can_view_audit_logs = Column(Boolean, default=False, nullable=False)
    can_view_login_history = Column(Boolean, default=False, nullable=False)

    # Permissions globales
    can_manage_settings = Column(Boolean, default=False, nullable=False)

    # Permissions pour les Users  
    can_acces_users_section= Column(Boolean, default=False, nullable=False)
    can_view_users = Column(Boolean, default=False, nullable=False)
    can_edit_users = Column(Boolean, default=False, nullable=False)
    can_desable_users = Column(Boolean, default=False, nullable=False)
    can_delete_users = Column(Boolean, default=False, nullable=False)
    
    # Permissions pour les Roles
    can_manage_roles = Column(Boolean, default=False, nullable=False)
    can_assign_roles = Column(Boolean, default=False, nullable=False)

    # Permissions pour les Messages
    can_view_messages = Column(Boolean, default=False, nullable=False)
    can_send_messages = Column(Boolean, default=False, nullable=False)
    can_delete_messages = Column(Boolean, default=False, nullable=False)

    # Permissions pour les Fichiers
    can_view_files = Column(Boolean, default=False, nullable=False)
    can_upload_files = Column(Boolean, default=False, nullable=False)
    can_delete_files = Column(Boolean, default=False, nullable=False)



    # Timestamp
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)

     # Permissions pour les tâches
    can_view_tasks = Column(Boolean, default=False, nullable=True)
    can_create_tasks = Column(Boolean, default=False, nullable=True)
    can_edit_tasks = Column(Boolean, default=False, nullable=True)
    can_delete_tasks = Column(Boolean, default=False, nullable=True)
    can_assign_tasks = Column(Boolean, default=False, nullable=True)


    # Permissions pour les archives
    can_view_archives = Column(Boolean, default=False, nullable=True)
    can_destroy_archives = Column(Boolean, default=False, nullable=True)
    can_restore_archives = Column(Boolean, default=False, nullable=True)
    can_delete_archives = Column(Boolean, default=False, nullable=True)  

    # Permissions pour le module Citations (intégration Firebase)
    quotes_view = Column(Boolean, default=False, nullable=False)  # Visualiser les citations
    quotes_create = Column(Boolean, default=False, nullable=False)  # Créer de nouvelles citations
    quotes_edit = Column(Boolean, default=False, nullable=False)  # Modifier les citations existantes
    quotes_delete = Column(Boolean, default=False, nullable=False)  # Supprimer des citations
    quotes_publish = Column(Boolean, default=False, nullable=False)  # Publier sur réseaux sociaux
    stream_transcription_view = Column(Boolean, default=False, nullable=False)  # Voir les transcriptions en direct
    stream_transcription_create = Column(Boolean, default=False, nullable=False)  # Démarrer une transcription
    quotes_capture_live = Column(Boolean, default=False, nullable=False)  # Capturer depuis transcription live

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
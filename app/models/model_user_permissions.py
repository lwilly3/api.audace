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



    # Relation avec la table users
    user = relationship("User", back_populates="permissions")
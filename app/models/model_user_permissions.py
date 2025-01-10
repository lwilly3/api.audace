from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base #metadata


class UserPermissions(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Permissions en booléens
    can_create_showplan = Column(Boolean, default=False, nullable=False)
    can_edit_showplan = Column(Boolean, default=False, nullable=False)
    can_archive_showplan = Column(Boolean, default=False, nullable=False)
    can_delete_showplan = Column(Boolean, default=False, nullable=False)
    can_destroy_showplan = Column(Boolean, default=False, nullable=False)
    can_changestatus_showplan = Column(Boolean, default=False, nullable=False)

    
    # Timestamp
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relation avec la table users
    user = relationship("User", back_populates="permissions")

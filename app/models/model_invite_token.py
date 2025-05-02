from sqlalchemy import Column, String, DateTime, Boolean, func
from datetime import datetime
from app.db.database import Base

class InviteToken(Base):
    __tablename__ = "invite_tokens"
    token = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

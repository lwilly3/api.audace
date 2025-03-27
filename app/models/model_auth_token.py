from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

# Modèle pour stocker les tokens invalidés
class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token = Column(String, primary_key=True, index=True)  # Le token JWT invalidé
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())  # Date de révocation du token
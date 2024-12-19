
# Importation des modules nécessaires
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import zlib
from datetime import datetime
from app.db.database import Base #metadata



# -------------------------
# Archivage des Logs d'Audit
# -------------------------
class ArchivedAuditLog(Base):
    __tablename__ = "archived_audit_logs"  # Table pour l'archivage des logs d'audit
    id = Column(Integer, primary_key=True)  # Identifiant du log archivé
    # user_id = Column(Integer, ForeignKey('users.id'))  # Référence à l'utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # Action effectuée
    table_name = Column(String, nullable=False)  # Table concernée
    record_id = Column(Integer, nullable=False)  # Identifiant de l'enregistrement concerné
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # Date et heure de l'action

    # # Relation vers l'utilisateur
    # user = relationship("User")
 # Relation inverse avec User
    user = relationship("User", back_populates="archived_audit_logs")
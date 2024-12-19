from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base #metadata
# -------------------------
# Logs d'Audit (Actions des utilisateurs)
# -------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"  # Table des logs d'audit

    id = Column(Integer, primary_key=True)  # Identifiant du log
    user_id = Column(Integer, ForeignKey('users.id'))  # Référence à l'utilisateur ayant effectué l'action
    action = Column(String, nullable=False)  # Action effectuée (par exemple : "create", "update", "delete")
    table_name = Column(String, nullable=False)  # Nom de la table concernée
    record_id = Column(Integer, nullable=False)  # Identifiant de l'enregistrement concerné
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # Date et heure de l'action

    # # Relation vers l'utilisateur
    # user = relationship("User", back_populates="audit_logs")
     # Relation inverse avec User
    user = relationship("User", back_populates="audit_logs")




# Ce fichier définit la table des logs d'audit, où chaque action effectuée par un utilisateur est enregistrée.
# Cela permet de tracer les modifications dans les données du système.
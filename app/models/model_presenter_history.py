
# Importation des modules nécessaires
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import zlib
from datetime import datetime

from app.db.database import Base #metadata






# # -------------------------
# # Historique des Modifications d'un Présentateur
# # -------------------------
# class PresenterHistory(Base):
#     __tablename__ = "presenter_history"  # Historique des modifications d'un présentateur
#     id = Column(Integer, primary_key=True)  # Identifiant de l'historique
#     presenter_id = Column(Integer, ForeignKey('presenters.id'))  # Référence au présentateur
#     name = Column(String)  # Nom du présentateur au moment de la modification
#     biography = Column(Text)  # Biographie du présentateur au moment de la modification
#     updated_at = Column(DateTime, default=datetime.utcnow)  # Date et heure de la mise à jour
#     updated_by = Column(Integer, ForeignKey('users.id'))  # Utilisateur ayant effectué la modification

#     # Relations vers le présentateur et l'utilisateur
#     presenter = relationship("Presenter")
#     updated_by_user = relationship("User")
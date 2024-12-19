from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,TIMESTAMP,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base #metadata
# -------------------------
# Historique des Connexions
# -------------------------
class LoginHistory(Base):
    __tablename__ = "login_history"  # Table pour l'historique des connexions

    id = Column(Integer, primary_key=True)  # Identifiant de la connexion
    user_id = Column(Integer, ForeignKey('users.id'))  # Référence à l'utilisateur
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # Date et heure de la connexion
    ip_address = Column(String, nullable=True)  # Adresse IP de la connexion (optionnel)
    login_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))  # Date/heure de connexion


    # # Relation vers l'utilisateur
    # user = relationship("User", back_populates="logins")
     # Relation inverse avec User
    user = relationship("User", back_populates="logins")




# Ce fichier définit la table des connexions des utilisateurs. 
# Chaque connexion est liée à un utilisateur et enregistre des 
# informations comme l'adresse IP et la date/heure de la connexion.
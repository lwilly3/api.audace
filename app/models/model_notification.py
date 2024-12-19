from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey,TIMESTAMP,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base #metadata
# -------------------------
# Notifications (Messages envoyés aux utilisateurs)
# -------------------------
# class Notification(Base):
#     __tablename__ = "notifications"  # Table des notifications

#     id = Column(Integer, primary_key=True)  # Identifiant de la notification
#     user_id = Column(Integer, ForeignKey('users.id'))  # Référence à l'utilisateur
#     message = Column(Text, nullable=False)  # Contenu du message
#     read = Column(Boolean, default=False)  # Statut de lecture de la notification
#     timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # Date et heure de la notification
#     created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))  # Date/heure de création

#     # Relation vers l'utilisateur
#     user = relationship("User", back_populates="notifications")




class Notification(Base):
    __tablename__ = "notifications"  # Table des notifications

    id = Column(Integer, primary_key=True)  # Identifiant de la notification
    user_id = Column(Integer, ForeignKey('users.id'))  # Référence à l'utilisateur
    message = Column(Text, nullable=False)  # Contenu du message
    read = Column(Boolean, default=False)  # Statut de lecture de la notification
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # Date et heure de la notification
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))  # Date/heure de création

    # Relation vers l'utilisateur
    user = relationship("User", back_populates="notifications")  # Correction ici






# Ce fichier définit la table des notifications, permettant d'envoyer des messages aux utilisateurs. 
# Le statut de lecture de la notification est également enregistré.
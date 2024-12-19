
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Table, Index
from sqlalchemy.orm import relationship
from app.db.database import Base




class ShowPresenter(Base):
    """
    Table dédiée pour la relation plusieurs-à-plusieurs entre "Show" et "Presenter".
    Permet de stocker des informations supplémentaires sur cette relation.
    """
    __tablename__ = "show_presenters"

    id = Column(Integer, primary_key=True)  # Identifiant unique de la relation
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False, index=True)  # Clé étrangère vers Show
   #  presenter_id = Column(Integer, ForeignKey("presenters.id"), nullable=False, index=True)  # Clé étrangère vers Presenter
    presenter_id = Column(Integer, ForeignKey("presenters.id", ondelete="CASCADE"), nullable=False)

    role = Column(String, nullable=True)  # Rôle du présentateur dans l'émission (e.g., Animateur, Invité)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)  # Date d'ajout de la relation

    # Définition des relations
    # show = relationship("Show", back_populates="show_presenters")  # Lien vers le modèle Show
    # presenter = relationship("Presenter", back_populates="show_presenters")  # Lien vers le modèle Presenter

    # show = relationship("Show", back_populates="presenters")
    # presenter = relationship("Presenter", back_populates="shows")
 # Relations inverses
   #  show = relationship("Show", back_populates="presenters")
   #  presenter = relationship("Presenter", back_populates="shows")

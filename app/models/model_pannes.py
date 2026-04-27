"""
@fileoverview model_pannes.py — Modèles SQLAlchemy pour le module Gestion des Pannes

Tables :
  - fiches_pannes  : fiches de panne (véhicules, service demandé, pièces, statut)
  - acteurs        : personnel terrain sans compte obligatoire (mécaniciens, chauffeurs, responsables)
  - fiche_acteur   : liaison N-N entre une fiche et ses acteurs
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, func, text
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Acteur(Base):
    """
    Personnel terrain pouvant intervenir sur une fiche de panne.
    N'a PAS besoin d'un compte de connexion pour exister dans le système.
    Lien optionnel vers un compte applicatif via user_id (FK → users).
    """
    __tablename__ = 'acteurs'

    id = Column(Integer, primary_key=True, index=True)

    # Identité
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)

    # Rôle principal de l'acteur dans l'entreprise
    # Valeurs : "mecanicien" / "chauffeur" / "responsable"
    role = Column(String(30), nullable=False)

    # Société d'appartenance (optionnel)
    societe = Column(String(100), nullable=True)

    # Contact
    telephone = Column(String(30), nullable=True)

    # Statut actif / archivé
    actif = Column(Boolean, default=True, nullable=False)

    # Lien optionnel vers un compte applicatif
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relations
    user = relationship('User', foreign_keys=[user_id])
    fiches = relationship('FicheActeur', back_populates='acteur', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_acteurs_role', 'role'),
        Index('ix_acteurs_societe', 'societe'),
        Index('ix_acteurs_actif', 'actif'),
        Index('ix_acteurs_user_id', 'user_id'),
    )

    @property
    def nom_complet(self) -> str:
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom


class FichePanne(Base):
    """
    Fiche de déclaration et de suivi d'une panne véhicule.
    Un véhicule (immatriculation) peut avoir plusieurs pannes.
    Plusieurs véhicules peuvent être listés sur une même fiche (séparés par '/').
    """
    __tablename__ = 'fiches_pannes'

    id = Column(Integer, primary_key=True, index=True)

    # Numéro de fiche métier (auto-incrémenté séquentiellement, indépendant de id)
    numero_fiche = Column(Integer, nullable=False, unique=True, index=True)

    # Date de la panne
    date_panne = Column(Date, nullable=False, index=True)

    # Immatriculation(s) — peut contenir "AA-123-BB / CC-456-DD" pour plusieurs véhicules
    immatriculation = Column(String(255), nullable=False, index=True)

    # Numéro moteur (optionnel)
    numero_moteur = Column(String(100), nullable=True)

    # Société concernée
    # Valeurs : "TRAFRIC SARL" / "BAJ SERVICES SA"
    societe = Column(String(100), nullable=False, index=True)

    # Kilométrage au départ (optionnel)
    km_depart = Column(Integer, nullable=True)

    # Kilométrage à la fin (optionnel)
    km_fin = Column(Integer, nullable=True)

    # Description libre du service demandé / nature de la panne
    service_demande = Column(Text, nullable=True)

    # Pièces commandées — format libre : "Filtre gasoil x1 | Huile moteur 15L"
    pieces_commandees = Column(Text, nullable=True)

    # Statut du traitement de la panne
    # Valeurs : "en_attente" / "en_cours" / "cloture"
    statut = Column(String(20), nullable=False, default='en_attente', index=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    created_by = Column(Integer, nullable=True)         # NULL si import Excel
    created_by_name = Column(String(255), nullable=True)  # NULL si import Excel

    # Relations
    acteurs = relationship('FicheActeur', back_populates='fiche', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_fiches_pannes_date_societe', 'date_panne', 'societe'),
        Index('ix_fiches_pannes_statut_societe', 'statut', 'societe'),
    )


class FicheActeur(Base):
    """
    Table de liaison N-N entre FichePanne et Acteur.
    Précise le rôle de l'acteur sur cette fiche spécifique
    (un chauffeur peut être responsable sur une autre fiche).
    """
    __tablename__ = 'fiche_acteur'

    fiche_id = Column(Integer, ForeignKey('fiches_pannes.id', ondelete='CASCADE'),
                      primary_key=True, nullable=False)
    acteur_id = Column(Integer, ForeignKey('acteurs.id', ondelete='CASCADE'),
                       primary_key=True, nullable=False)

    # Rôle de l'acteur sur cette fiche précise
    # Valeurs : "mecanicien" / "chauffeur" / "responsable"
    role_sur_fiche = Column(String(30), nullable=False)

    # Relations
    fiche = relationship('FichePanne', back_populates='acteurs')
    acteur = relationship('Acteur', back_populates='fiches')

    __table_args__ = (
        Index('ix_fiche_acteur_fiche_id', 'fiche_id'),
        Index('ix_fiche_acteur_acteur_id', 'acteur_id'),
    )

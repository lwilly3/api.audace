"""
@fileoverview model_logistics_vehicle_extras.py

Tables complémentaires au modèle véhicule logistique :

  - logistics_vehicle_compartments :
      Compartiments d'une citerne (porteur_citerne ou remorque citerne).
      Permet de décrire les N compartiments avec leur capacité et le type
      de carburant transporté.

  - logistics_vehicle_associations :
      Couples tracteur ↔ remorque.
      Permet de définir les associations par défaut (is_default=True) et
      d'enregistrer l'historique des couplages. Un tracteur peut changer
      de remorque et vice-versa.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, DECIMAL,
    ForeignKey, Index, func, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class LogisticsVehicleCompartment(Base):
    """
    Compartiment d'une citerne.

    S'applique aux véhicules de rôle :
      - porteur_citerne  (camion citerne monobloc)
      - remorque         de type citerne (remorque_citerne_*)

    Chaque compartiment a un numéro séquentiel, une capacité en litres
    et le type de produit transporté (gasoil, essence, jet_a1…).
    """
    __tablename__ = 'logistics_vehicle_compartments'

    id = Column(Integer, primary_key=True, index=True)

    # Véhicule porteur de ce compartiment
    vehicle_id = Column(
        Integer,
        ForeignKey('logistics_vehicles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Numéro de compartiment (1, 2, 3…) — unique par véhicule
    compartment_no = Column(Integer, nullable=False)

    # Capacité nominale du compartiment
    capacity_liters = Column(DECIMAL(10, 2), nullable=False)

    # Type de produit habituellement transporté (gasoil, essence, jet_a1, lubrifiants, autre)
    fuel_type = Column(String(50), nullable=True)

    # Libellé optionnel (ex : "C1", "Avant", "Central")
    label = Column(String(50), nullable=True)

    # Compartiment actif (False = désaffecté / bouchonné)
    is_active = Column(Boolean, default=True, nullable=False)

    notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relation inverse vers le véhicule
    vehicle = relationship('LogisticsVehicle', back_populates='compartments')

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'compartment_no', name='uq_compartment_vehicle_no'),
        Index('ix_compartment_vehicle_id', 'vehicle_id'),
    )


class LogisticsVehicleAssociation(Base):
    """
    Couple tracteur ↔ remorque.

    Permet d'associer un cab tracteur (vehicle_role='tracteur') à une
    remorque (vehicle_role='remorque'). Une association peut être :
      - is_default=True  : couple habituel, préchargé dans les formulaires
      - is_default=False : couplage ponctuel ou historique

    Un tracteur peut avoir plusieurs associations (différentes remorques),
    mais une seule par défaut. Idem pour une remorque.

    Interopérabilité : rien n'empêche de créer plusieurs associations
    avec le même tracteur ou la même remorque — la flexibilité est totale.
    """
    __tablename__ = 'logistics_vehicle_associations'

    id = Column(Integer, primary_key=True, index=True)

    # Tracteur (vehicle_role='tracteur')
    tractor_id = Column(
        Integer,
        ForeignKey('logistics_vehicles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Remorque (vehicle_role='remorque')
    trailer_id = Column(
        Integer,
        ForeignKey('logistics_vehicles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Entreprise (dénormalisation pour filtrage rapide)
    company_id = Column(
        Integer,
        ForeignKey('inventory_companies.id'),
        nullable=False,
        index=True,
    )

    # Couple par défaut pour ces deux engins
    is_default = Column(Boolean, default=False, nullable=False)

    # Statut : active / inactive (couple retiré mais conservé en historique)
    is_active = Column(Boolean, default=True, nullable=False)

    notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    tractor = relationship('LogisticsVehicle', foreign_keys=[tractor_id], back_populates='tractor_associations')
    trailer = relationship('LogisticsVehicle', foreign_keys=[trailer_id], back_populates='trailer_associations')
    company = relationship('InventoryCompany', foreign_keys=[company_id])

    __table_args__ = (
        Index('ix_assoc_tractor_id', 'tractor_id'),
        Index('ix_assoc_trailer_id', 'trailer_id'),
        Index('ix_assoc_company_id', 'company_id'),
    )

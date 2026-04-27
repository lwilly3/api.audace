"""
@fileoverview crud_pannes.py — Fonctions CRUD pour le module Gestion des Pannes

Opérations :
  - Acteur      : get_acteurs, get_acteur, create_acteur, update_acteur, link_acteur_to_user
  - FichePanne  : get_fiches_pannes, get_fiche_panne, create_fiche_panne, update_fiche_panne,
                  delete_fiche_panne, get_pannes_dashboard
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_
from typing import Optional, List
from datetime import date

from app.models.model_pannes import FichePanne, Acteur, FicheActeur
from app.schemas.schema_pannes import (
    ActeurCreate, ActeurUpdate,
    FichePanneCreate, FichePanneUpdate,
    FichePanneListItem, PannesDashboardResponse,
    RepartitionSociete, VehiculeRecurrent, MecanicienActif,
)


# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _get_next_numero_fiche(db: Session) -> int:
    """Calcule le prochain numéro de fiche de manière séquentielle (MAX + 1)."""
    result = db.execute(
        text("SELECT COALESCE(MAX(numero_fiche), 0) + 1 FROM fiches_pannes")
    ).scalar()
    return result


def _build_fiche_list_item(fiche: FichePanne) -> FichePanneListItem:
    """Construit un item de liste allégé à partir d'une FichePanne ORM."""
    mecaniciens = [
        fa.acteur.nom_complet
        for fa in fiche.acteurs
        if fa.role_sur_fiche == 'mecanicien' and fa.acteur
    ]
    return FichePanneListItem(
        id=fiche.id,
        numero_fiche=fiche.numero_fiche,
        date_panne=fiche.date_panne,
        immatriculation=fiche.immatriculation,
        societe=fiche.societe,
        statut=fiche.statut,
        mecaniciens=mecaniciens,
        created_at=fiche.created_at,
        updated_at=fiche.updated_at,
    )


# ---------------------------------------------------------------------------
# Acteur
# ---------------------------------------------------------------------------

def get_acteurs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    actif: Optional[bool] = None,
    societe: Optional[str] = None,
) -> dict:
    query = db.query(Acteur)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Acteur.nom).like(term),
                func.lower(Acteur.prenom).like(term),
            )
        )
    if role:
        query = query.filter(Acteur.role == role)
    if actif is not None:
        query = query.filter(Acteur.actif == actif)
    if societe:
        query = query.filter(Acteur.societe == societe)

    query = query.order_by(Acteur.nom, Acteur.prenom)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_acteur(db: Session, acteur_id: int) -> Optional[Acteur]:
    return db.query(Acteur).filter(Acteur.id == acteur_id).first()


def create_acteur(db: Session, data: ActeurCreate) -> Acteur:
    acteur = Acteur(**data.model_dump())
    db.add(acteur)
    db.commit()
    db.refresh(acteur)
    return acteur


def update_acteur(db: Session, acteur_id: int, data: ActeurUpdate) -> Optional[Acteur]:
    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(acteur, field, value)
    db.commit()
    db.refresh(acteur)
    return acteur


def link_acteur_to_user(db: Session, acteur_id: int, user_id: int) -> Optional[Acteur]:
    """Lie un acteur existant à un compte utilisateur applicatif."""
    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        return None
    acteur.user_id = user_id
    db.commit()
    db.refresh(acteur)
    return acteur


# ---------------------------------------------------------------------------
# FichePanne
# ---------------------------------------------------------------------------

def get_fiches_pannes(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    statut: Optional[str] = None,
    societe: Optional[str] = None,
    immatriculation: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
) -> dict:
    from sqlalchemy.orm import joinedload

    query = db.query(FichePanne).options(
        joinedload(FichePanne.acteurs).joinedload(FicheActeur.acteur)
    )

    if statut:
        query = query.filter(FichePanne.statut == statut)
    if societe:
        query = query.filter(FichePanne.societe == societe)
    if immatriculation:
        query = query.filter(
            FichePanne.immatriculation.ilike(f"%{immatriculation}%")
        )
    if date_debut:
        query = query.filter(FichePanne.date_panne >= date_debut)
    if date_fin:
        query = query.filter(FichePanne.date_panne <= date_fin)

    query = query.order_by(FichePanne.date_panne.desc(), FichePanne.numero_fiche.desc())
    total = query.count()
    fiches = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [_build_fiche_list_item(f) for f in fiches]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_fiche_panne(db: Session, fiche_id: int) -> Optional[FichePanne]:
    from sqlalchemy.orm import joinedload
    return (
        db.query(FichePanne)
        .options(joinedload(FichePanne.acteurs).joinedload(FicheActeur.acteur))
        .filter(FichePanne.id == fiche_id)
        .first()
    )


def create_fiche_panne(
    db: Session,
    data: FichePanneCreate,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
) -> FichePanne:
    numero = _get_next_numero_fiche(db)

    acteurs_data = data.acteurs
    fiche_dict = data.model_dump(exclude={'acteurs'})

    fiche = FichePanne(
        **fiche_dict,
        numero_fiche=numero,
        created_by=user_id,
        created_by_name=username,
    )
    db.add(fiche)
    db.flush()  # Obtenir fiche.id sans commit

    for a in acteurs_data:
        liaison = FicheActeur(
            fiche_id=fiche.id,
            acteur_id=a.acteur_id,
            role_sur_fiche=a.role_sur_fiche,
        )
        db.add(liaison)

    db.commit()
    db.refresh(fiche)
    return fiche


def update_fiche_panne(
    db: Session,
    fiche_id: int,
    data: FichePanneUpdate,
    user_id: Optional[int] = None,
) -> Optional[FichePanne]:
    from sqlalchemy.orm import joinedload

    fiche = (
        db.query(FichePanne)
        .options(joinedload(FichePanne.acteurs))
        .filter(FichePanne.id == fiche_id)
        .first()
    )
    if not fiche:
        return None

    update_dict = data.model_dump(exclude_none=True, exclude={'acteurs'})
    for field, value in update_dict.items():
        setattr(fiche, field, value)

    # Si la liste des acteurs est fournie, on la remplace entièrement
    if data.acteurs is not None:
        db.query(FicheActeur).filter(FicheActeur.fiche_id == fiche_id).delete()
        for a in data.acteurs:
            liaison = FicheActeur(
                fiche_id=fiche.id,
                acteur_id=a.acteur_id,
                role_sur_fiche=a.role_sur_fiche,
            )
            db.add(liaison)

    db.commit()
    db.refresh(fiche)
    return fiche


def delete_fiche_panne(db: Session, fiche_id: int) -> bool:
    fiche = db.query(FichePanne).filter(FichePanne.id == fiche_id).first()
    if not fiche:
        return False
    db.delete(fiche)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def get_pannes_dashboard(db: Session) -> PannesDashboardResponse:
    # Totaux par statut
    total_fiches = db.query(func.count(FichePanne.id)).scalar() or 0
    fiches_en_attente = (
        db.query(func.count(FichePanne.id))
        .filter(FichePanne.statut == 'en_attente')
        .scalar() or 0
    )
    fiches_en_cours = (
        db.query(func.count(FichePanne.id))
        .filter(FichePanne.statut == 'en_cours')
        .scalar() or 0
    )
    fiches_cloturees = (
        db.query(func.count(FichePanne.id))
        .filter(FichePanne.statut == 'cloture')
        .scalar() or 0
    )

    # Répartition par société
    societe_rows = (
        db.query(FichePanne.societe, func.count(FichePanne.id).label('nb'))
        .group_by(FichePanne.societe)
        .order_by(func.count(FichePanne.id).desc())
        .all()
    )
    repartition_societe = [
        RepartitionSociete(
            societe=row.societe,
            nombre_fiches=row.nb,
            pourcentage=round((row.nb / total_fiches * 100), 1) if total_fiches > 0 else 0.0,
        )
        for row in societe_rows
    ]

    # Véhicules récurrents (immatriculation avec > 1 fiche)
    vehicule_rows = (
        db.query(FichePanne.immatriculation, func.count(FichePanne.id).label('nb'))
        .group_by(FichePanne.immatriculation)
        .having(func.count(FichePanne.id) > 1)
        .order_by(func.count(FichePanne.id).desc())
        .limit(10)
        .all()
    )
    vehicules_recurrents = [
        VehiculeRecurrent(immatriculation=row.immatriculation, nombre_fiches=row.nb)
        for row in vehicule_rows
    ]

    # Mécaniciens les plus actifs (top 10)
    mecanicien_rows = (
        db.query(
            FicheActeur.acteur_id,
            Acteur.nom,
            Acteur.prenom,
            func.count(FicheActeur.fiche_id).label('nb'),
        )
        .join(Acteur, FicheActeur.acteur_id == Acteur.id)
        .filter(FicheActeur.role_sur_fiche == 'mecanicien')
        .group_by(FicheActeur.acteur_id, Acteur.nom, Acteur.prenom)
        .order_by(func.count(FicheActeur.fiche_id).desc())
        .limit(10)
        .all()
    )
    mecaniciens_actifs = [
        MecanicienActif(
            acteur_id=row.acteur_id,
            nom_complet=f"{row.prenom} {row.nom}".strip() if row.prenom else row.nom,
            nombre_interventions=row.nb,
        )
        for row in mecanicien_rows
    ]

    return PannesDashboardResponse(
        total_fiches=total_fiches,
        fiches_en_attente=fiches_en_attente,
        fiches_en_cours=fiches_en_cours,
        fiches_cloturees=fiches_cloturees,
        repartition_societe=repartition_societe,
        vehicules_recurrents=vehicules_recurrents,
        mecaniciens_actifs=mecaniciens_actifs,
    )

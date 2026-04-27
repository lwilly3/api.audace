"""
@fileoverview pannes_route.py — Endpoints REST pour le module Gestion des Pannes

Préfixe : /pannes  (fiches)  +  /acteurs
Auth    : Depends(oauth2.get_current_user) sur toutes les routes
Permissions (colonnes de UserPermissions) :
  - pannes_access_section   : accès au module
  - pannes_view             : lire les fiches
  - pannes_create           : créer une fiche
  - pannes_edit             : modifier une fiche
  - pannes_delete           : supprimer une fiche (admin)
  - pannes_view_all_companies : voir les fiches de toutes les sociétés
  - acteurs_view            : voir la liste des acteurs
  - acteurs_create          : créer un acteur
  - acteurs_edit            : modifier un acteur
  - acteurs_link_account    : lier un acteur à un compte
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from core.auth import oauth2
from app.db.database import get_db
from app.db.crud.crud_pannes import (
    get_acteurs,
    get_acteur,
    create_acteur,
    update_acteur,
    link_acteur_to_user,
    get_fiches_pannes,
    get_fiche_panne,
    create_fiche_panne,
    update_fiche_panne,
    delete_fiche_panne,
    get_pannes_dashboard,
)
from app.schemas.schema_pannes import (
    ActeurCreate,
    ActeurUpdate,
    ActeurLierCompte,
    ActeurResponse,
    ActeurListResponse,
    FichePanneCreate,
    FichePanneUpdate,
    FichePanneResponse,
    FichePanneListResponse,
    PannesDashboardResponse,
)

router = APIRouter(
    tags=["pannes"]
)


# ===========================================================================
# DASHBOARD
# ===========================================================================

@router.get("/pannes/dashboard", response_model=PannesDashboardResponse)
def get_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """KPIs agrégés du module Gestion des Pannes."""
    if not current_user.permissions.pannes_access_section:
        raise HTTPException(status_code=403, detail="Accès au module Pannes refusé")
    return get_pannes_dashboard(db)


# ===========================================================================
# FICHES PANNES
# ===========================================================================

@router.get("/pannes/", response_model=FichePanneListResponse)
def list_fiches_pannes_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    statut: Optional[str] = Query(None, description="en_attente / en_cours / cloture"),
    societe: Optional[str] = Query(None),
    immatriculation: Optional[str] = Query(None),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Liste des fiches de panne avec filtres."""
    if not current_user.permissions.pannes_view:
        raise HTTPException(status_code=403, detail="Permission pannes_view requise")
    return get_fiches_pannes(
        db,
        page=page,
        page_size=page_size,
        statut=statut,
        societe=societe,
        immatriculation=immatriculation,
        date_debut=date_debut,
        date_fin=date_fin,
    )


@router.post("/pannes/", response_model=FichePanneResponse, status_code=201)
def create_fiche_panne_endpoint(
    data: FichePanneCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Créer une nouvelle fiche de panne avec ses acteurs liés."""
    if not current_user.permissions.pannes_create:
        raise HTTPException(status_code=403, detail="Permission pannes_create requise")
    fiche = create_fiche_panne(
        db, data,
        user_id=current_user.id,
        username=current_user.username,
    )
    # Rechargement avec joinedload pour la réponse complète
    return get_fiche_panne(db, fiche.id)


@router.get("/pannes/{fiche_id}", response_model=FichePanneResponse)
def get_fiche_panne_endpoint(
    fiche_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Détail d'une fiche de panne."""
    if not current_user.permissions.pannes_view:
        raise HTTPException(status_code=403, detail="Permission pannes_view requise")
    fiche = get_fiche_panne(db, fiche_id)
    if not fiche:
        raise HTTPException(status_code=404, detail="Fiche de panne introuvable")
    return fiche


@router.patch("/pannes/{fiche_id}", response_model=FichePanneResponse)
def update_fiche_panne_endpoint(
    fiche_id: int,
    data: FichePanneUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Modifier une fiche (statut, champs, acteurs)."""
    if not current_user.permissions.pannes_edit:
        raise HTTPException(status_code=403, detail="Permission pannes_edit requise")
    fiche = update_fiche_panne(db, fiche_id, data, user_id=current_user.id)
    if not fiche:
        raise HTTPException(status_code=404, detail="Fiche de panne introuvable")
    return get_fiche_panne(db, fiche.id)


@router.delete("/pannes/{fiche_id}", status_code=204)
def delete_fiche_panne_endpoint(
    fiche_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Supprimer une fiche de panne (admin uniquement)."""
    if not current_user.permissions.pannes_delete:
        raise HTTPException(status_code=403, detail="Permission pannes_delete requise")
    deleted = delete_fiche_panne(db, fiche_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fiche de panne introuvable")


# ===========================================================================
# ACTEURS
# ===========================================================================

@router.get("/acteurs/", response_model=ActeurListResponse)
def list_acteurs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Recherche par nom ou prénom"),
    role: Optional[str] = Query(None, description="mecanicien / chauffeur / responsable"),
    actif: Optional[bool] = Query(None),
    societe: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Liste des acteurs avec recherche autocomplete."""
    if not current_user.permissions.acteurs_view:
        raise HTTPException(status_code=403, detail="Permission acteurs_view requise")
    return get_acteurs(db, page=page, page_size=page_size,
                       search=search, role=role, actif=actif, societe=societe)


@router.post("/acteurs/", response_model=ActeurResponse, status_code=201)
def create_acteur_endpoint(
    data: ActeurCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Créer un nouvel acteur (sans compte de connexion obligatoire)."""
    if not current_user.permissions.acteurs_create:
        raise HTTPException(status_code=403, detail="Permission acteurs_create requise")
    return create_acteur(db, data)


@router.get("/acteurs/{acteur_id}", response_model=ActeurResponse)
def get_acteur_endpoint(
    acteur_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Détail d'un acteur."""
    if not current_user.permissions.acteurs_view:
        raise HTTPException(status_code=403, detail="Permission acteurs_view requise")
    acteur = get_acteur(db, acteur_id)
    if not acteur:
        raise HTTPException(status_code=404, detail="Acteur introuvable")
    return acteur


@router.patch("/acteurs/{acteur_id}", response_model=ActeurResponse)
def update_acteur_endpoint(
    acteur_id: int,
    data: ActeurUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Modifier un acteur."""
    if not current_user.permissions.acteurs_edit:
        raise HTTPException(status_code=403, detail="Permission acteurs_edit requise")
    acteur = update_acteur(db, acteur_id, data)
    if not acteur:
        raise HTTPException(status_code=404, detail="Acteur introuvable")
    return acteur


@router.patch("/acteurs/{acteur_id}/lier-compte", response_model=ActeurResponse)
def lier_compte_endpoint(
    acteur_id: int,
    data: ActeurLierCompte,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Lier un acteur existant à un compte applicatif (user_id).
    Autorisé : admin (acteurs_link_account) ou l'utilisateur lui-même (user_id == current_user.id).
    """
    is_self = data.user_id == current_user.id
    has_perm = current_user.permissions.acteurs_link_account

    if not is_self and not has_perm:
        raise HTTPException(
            status_code=403,
            detail="Permission acteurs_link_account requise ou vous devez lier votre propre compte"
        )
    acteur = link_acteur_to_user(db, acteur_id, data.user_id)
    if not acteur:
        raise HTTPException(status_code=404, detail="Acteur introuvable")
    return acteur

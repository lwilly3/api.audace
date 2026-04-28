"""
@fileoverview pannes_route.py — Endpoints REST pour le module Gestion des Pannes

Préfixe : /pannes  (fiches)  +  /acteurs
Auth    : Depends(oauth2.get_current_user) sur toutes les routes
Permissions (colonnes de UserPermissions) :
  - logistics_pannes_access_section   : accès au module
  - logistics_pannes_view             : lire les fiches
  - logistics_pannes_create           : créer une fiche
  - logistics_pannes_edit             : modifier une fiche
  - logistics_pannes_delete           : supprimer une fiche (admin)
  - logistics_acteurs_view            : voir la liste des acteurs
  - logistics_acteurs_create          : créer un acteur
  - logistics_acteurs_edit            : modifier un acteur
  - logistics_acteurs_link_account    : lier un acteur à un compte
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
    get_panne_motifs,
    create_panne_motif,
    update_panne_motif,
    delete_panne_motif,
    get_breakdown_types,
    build_fiche_response,
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
    PanneMotifResponse,
    PanneMotifCreate,
    PanneMotifUpdate,
    BreakdownTypeResponse,
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
    if not current_user.permissions.logistics_pannes_access_section:
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
    motif_id: Optional[int] = Query(None, description="Filtrer par motif d'intervention"),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Liste des fiches de panne avec filtres."""
    if not current_user.permissions.logistics_pannes_view:
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
        category_id=motif_id,   # motif_id (API) → category_id (ORM)
    )


@router.post("/pannes/", response_model=FichePanneResponse, status_code=201)
def create_fiche_panne_endpoint(
    data: FichePanneCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Créer une nouvelle fiche de panne avec ses acteurs liés."""
    if not current_user.permissions.logistics_pannes_create:
        raise HTTPException(status_code=403, detail="Permission pannes_create requise")
    fiche = create_fiche_panne(
        db, data,
        user_id=current_user.id,
        username=current_user.username,
    )
    fiche = get_fiche_panne(db, fiche.id)
    return FichePanneResponse(**build_fiche_response(fiche))


# ===========================================================================
# MOTIFS D'INTERVENTION — DOIT être avant /{fiche_id} pour éviter le conflit
# ===========================================================================

@router.get("/pannes/motifs", response_model=list[PanneMotifResponse])
def list_panne_motifs_endpoint(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Liste des motifs d'intervention configurés (Panne / Entretien / Accident / Diagnostic)."""
    if not current_user.permissions.logistics_pannes_access_section:
        raise HTTPException(status_code=403, detail="Accès au module Pannes refusé")
    return get_panne_motifs(db, include_inactive=include_inactive)


@router.post("/pannes/motifs", response_model=PanneMotifResponse, status_code=201)
def create_panne_motif_endpoint(
    data: PanneMotifCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Créer un nouveau motif d'intervention."""
    if not current_user.permissions.logistics_manage_settings:
        raise HTTPException(status_code=403, detail="Permission logistics_manage_settings requise")
    return create_panne_motif(db, data)


@router.put("/pannes/motifs/{option_id}", response_model=PanneMotifResponse)
def update_panne_motif_endpoint(
    option_id: int,
    data: PanneMotifUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Modifier un motif d'intervention."""
    if not current_user.permissions.logistics_manage_settings:
        raise HTTPException(status_code=403, detail="Permission logistics_manage_settings requise")
    option = update_panne_motif(db, option_id, data)
    if not option:
        raise HTTPException(status_code=404, detail="Motif introuvable")
    return option


@router.delete("/pannes/motifs/{option_id}", status_code=204)
def delete_panne_motif_endpoint(
    option_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Désactiver un motif d'intervention (soft delete)."""
    if not current_user.permissions.logistics_manage_settings:
        raise HTTPException(status_code=403, detail="Permission logistics_manage_settings requise")
    deleted = delete_panne_motif(db, option_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Motif introuvable")


@router.get("/pannes/breakdown-types", response_model=list[BreakdownTypeResponse])
def list_breakdown_types_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Liste des types de panne (symptômes techniques multi-select) configurés."""
    if not current_user.permissions.logistics_pannes_access_section:
        raise HTTPException(status_code=403, detail="Accès au module Pannes refusé")
    return get_breakdown_types(db)


@router.get("/pannes/{fiche_id}", response_model=FichePanneResponse)
def get_fiche_panne_endpoint(
    fiche_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Détail d'une fiche de panne."""
    if not current_user.permissions.logistics_pannes_view:
        raise HTTPException(status_code=403, detail="Permission pannes_view requise")
    fiche = get_fiche_panne(db, fiche_id)
    if not fiche:
        raise HTTPException(status_code=404, detail="Fiche de panne introuvable")
    return FichePanneResponse(**build_fiche_response(fiche))


@router.patch("/pannes/{fiche_id}", response_model=FichePanneResponse)
def update_fiche_panne_endpoint(
    fiche_id: int,
    data: FichePanneUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Modifier une fiche (statut, champs, acteurs)."""
    if not current_user.permissions.logistics_pannes_edit:
        raise HTTPException(status_code=403, detail="Permission pannes_edit requise")
    fiche = update_fiche_panne(db, fiche_id, data, user_id=current_user.id)
    if not fiche:
        raise HTTPException(status_code=404, detail="Fiche de panne introuvable")
    fiche = get_fiche_panne(db, fiche.id)
    return FichePanneResponse(**build_fiche_response(fiche))


@router.delete("/pannes/{fiche_id}", status_code=204)
def delete_fiche_panne_endpoint(
    fiche_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Supprimer une fiche de panne (admin uniquement)."""
    if not current_user.permissions.logistics_pannes_delete:
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
    if not current_user.permissions.logistics_acteurs_view:
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
    if not current_user.permissions.logistics_acteurs_create:
        raise HTTPException(status_code=403, detail="Permission acteurs_create requise")
    return create_acteur(db, data)


@router.get("/acteurs/{acteur_id}", response_model=ActeurResponse)
def get_acteur_endpoint(
    acteur_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """Détail d'un acteur."""
    if not current_user.permissions.logistics_acteurs_view:
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
    if not current_user.permissions.logistics_acteurs_edit:
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
    Autorisé : admin (acteurs_link_account) ou l'utilisateur lui-même.
    """
    is_self = data.user_id == current_user.id
    has_perm = current_user.permissions.logistics_acteurs_link_account

    if not is_self and not has_perm:
        raise HTTPException(
            status_code=403,
            detail="Permission acteurs_link_account requise ou vous devez lier votre propre compte"
        )
    acteur = link_acteur_to_user(db, acteur_id, data.user_id)
    if not acteur:
        raise HTTPException(status_code=404, detail="Acteur introuvable")
    return acteur

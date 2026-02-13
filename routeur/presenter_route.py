from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_presenters import assign_presenter, create_presenter, get_all_presenters, get_presenter, get_presenter_by_user, update_presenter, delete_presenter, get_deleted_presenters
from app.schemas.schema_presenters import PresenterCreate, PresenterResponse,PresenterResponsePaged, PresenterUpdate
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router=APIRouter(
    prefix="/presenters",
    tags=['Presenters']
)

# Créer un présentateur , response_model=PresenterResponse
@router.post("/")
def create_presenter_route(presenter_to_create: PresenterCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenterCreated = create_presenter(db, presenter_to_create )
    log_action(db, current_user.id, "create", "presenters", presenterCreated.id if presenterCreated else 0)
    return presenterCreated

# Assigner ou réactiver un présentateur existant , response_model=PresenterResponse
@router.post("/assign")
def assign_presenter_route(
    presenter_to_assign: PresenterCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Assigne un statut de présentateur à un utilisateur existant ou crée un nouveau.
    Réactive si soft-deleted, sinon lève une erreur si déjà actif.
    """
    return assign_presenter(db, presenter_to_assign)
@router.get("/all")
def list_presenters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return get_all_presenters(db, skip, limit)


# Liste des présentateurs soft-deleted
@router.get("/deleted")
def list_deleted_presenters(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer les présentateurs marqués comme supprimés (is_deleted=True).
    """
    return get_deleted_presenters(db, skip, limit)



# Obtenir un présentateur par IDm
@router.get("/{presenter_id}")
def get_presenter_route(presenter_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenter = get_presenter(db, presenter_id)
    if presenter is None:
        # raise HTTPException(status_code=404, detail="Presenter not found")
        return JSONResponse(
            status_code=404,
            content={ "message": "Presenter not found" }
        )
    return presenter


@router.get("/by-user/{users_id}")
def get_presenter_by_user_route(
    users_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer un présentateur par son users_id.
    
    Args:
        users_id (int): L'ID de l'utilisateur associé au présentateur.
        db (Session): Session de la base de données.
        current_user (int): ID de l'utilisateur authentifié (via OAuth2).
    
    Returns:
        dict: Les détails du présentateur sérialisé.
    
    Raises:
        HTTPException: 404 si aucun présentateur n'est trouvé, 500 pour une erreur serveur.
    """
    presenter = get_presenter_by_user(db, users_id)
    if presenter is None:
        raise HTTPException(status_code=404, detail="Presenter not found for this user")
    return presenter



# Mettre à jour un présentateur
@router.put("/update/{presenter_id}")
def update_presenter_route(presenter_id: int, presenter_to_update: PresenterUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenter = update_presenter(db, presenter_id, presenter_to_update)
    if presenter is None:
        raise HTTPException(status_code=404, detail="Presenter not found")
    log_action(db, current_user.id, "update", "presenters", presenter_id)
    return presenter

# Supprimer un présentateur (soft delete)
@router.delete("/del/{presenter_id}")
def delete_presenter_route(presenter_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenter = delete_presenter(db, presenter_id)
    if presenter is None:
        return JSONResponse(
            status_code=404,
            content={ "message": "Presenter not found" }
        )
    log_action(db, current_user.id, "soft_delete", "presenters", presenter_id)
    return JSONResponse(
            status_code=204,
            content={ "message": "Presenter deleted successfully" }
        )










from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud.crud_presenters import  create_presenter, get_all_presenters, get_presenter, update_presenter, delete_presenter
from app.schemas.schema_presenters import PresenterCreate, PresenterResponse,PresenterResponsePaged, PresenterUpdate
from core.auth import oauth2

router=APIRouter(
    prefix="/presenters",
    tags=['Presenters']
)

# Créer un présentateur
@router.post("/")
def create_presenter_route(presenter_to_create: PresenterCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenterCreated = create_presenter(db, presenter_to_create )
    return presenterCreated



@router.get("/all")
def list_presenters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return get_all_presenters(db, skip, limit)

# Obtenir un présentateur par IDm
@router.get("/{presenter_id}")
def get_presenter_route(presenter_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenter = get_presenter(db, presenter_id)
    if presenter is None:
        raise HTTPException(status_code=404, detail="Presenter not found")
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
    return presenter

# Supprimer un présentateur (soft delete)
@router.delete("/del/{presenter_id}")
def delete_presenter_route(presenter_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    presenter = delete_presenter(db, presenter_id)
    if presenter is None:
        raise HTTPException(status_code=404, detail="Presenter not found")
    return {"message": "Presenter deleted successfully"}



















# from fastapi import FastAPI, HTTPException, Depends
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# # Création de l'application FastAPI
# app = FastAPI()

# # Simulated database
# # Une base de données simulée pour stocker les présentateurs et leur historique
# presenters_db = {}  # Dictionnaire pour les présentateurs actifs/inactifs
# presenters_history = {}  # Dictionnaire pour conserver l'historique des modifications


# # Modèles pour les données des présentateurs
# class Presenter(BaseModel):
#     # Modèle de base pour créer ou mettre à jour un présentateur
#     name: str
#     email: str
#     bio: Optional[str] = None
#     is_active: bool = True  # Indique si le présentateur est actif


# class PresenterInDB(Presenter):
#     # Modèle étendu pour inclure des informations supplémentaires stockées en base
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime] = None


# # Fonction utilitaire pour récupérer un présentateur, ou lever une erreur 404
# def get_presenter_or_404(presenter_id: int) -> PresenterInDB:
#     if presenter_id not in presenters_db or not presenters_db[presenter_id].is_active:
#         raise HTTPException(status_code=404, detail="Presenter not found")
#     return presenters_db[presenter_id]


# # Routes
# @app.get("/presenters", response_model=List[PresenterInDB])
# def get_all_presenters():
#     """
#     Récupérer tous les présentateurs actifs.
#     """
#     return [p for p in presenters_db.values() if p.is_active]


# @app.get("/presenters/{id}", response_model=PresenterInDB)
# def get_presenter(id: int):
#     """
#     Récupérer un présentateur spécifique par son ID.
#     Lève une erreur 404 si le présentateur n'existe pas ou est inactif.
#     """
#     return get_presenter_or_404(id)


# @app.post("/presenters", response_model=PresenterInDB)
# def create_presenter(presenter: Presenter):
#     """
#     Créer un nouveau présentateur.
#     Attribue automatiquement un ID unique et enregistre la création dans l'historique.
#     """
#     presenter_id = len(presenters_db) + 1  # Génération d'un nouvel ID
#     new_presenter = PresenterInDB(
#         **presenter.dict(), id=presenter_id, created_at=datetime.utcnow()
#     )
#     presenters_db[presenter_id] = new_presenter  # Ajout dans la base simulée
#     presenters_history[presenter_id] = [new_presenter.dict()]  # Initialisation de l'historique
#     return new_presenter


# @app.put("/presenters/{id}", response_model=PresenterInDB)
# def update_presenter(id: int, presenter: Presenter):
#     """
#     Mettre à jour un présentateur existant.
#     Enregistre les modifications dans l'historique des modifications.
#     """
#     existing_presenter = get_presenter_or_404(id)  # Vérifie si le présentateur existe
#     updated_presenter = existing_presenter.copy(
#         update={**presenter.dict(), "updated_at": datetime.utcnow()}
#     )
#     presenters_db[id] = updated_presenter  # Mise à jour dans la base simulée
#     presenters_history[id].append(updated_presenter.dict())  # Ajout dans l'historique
#     return updated_presenter


# @app.delete("/presenters/{id}")
# def delete_presenter(id: int):
#     """
#     Supprimer (soft delete) un présentateur.
#     Marque le présentateur comme inactif et enregistre l'heure de suppression.
#     """
#     presenter = get_presenter_or_404(id)  # Vérifie si le présentateur existe
#     presenter.is_active = False  # Marque comme inactif
#     presenter.updated_at = datetime.utcnow()  # Date de suppression
#     presenters_db[id] = presenter  # Mise à jour dans la base simulée
#     presenters_history[id].append(presenter.dict())  # Ajout dans l'historique
#     return {"detail": "Presenter soft-deleted successfully"}


# @app.get("/presenters/history/{id}", response_model=List[dict])
# def get_presenter_history(id: int):
#     """
#     Récupérer l'historique des modifications d'un présentateur.
#     Renvoie toutes les versions sauvegardées pour cet ID.
#     """
#     if id not in presenters_history:
#         raise HTTPException(status_code=404, detail="No history found for presenter")
#     return presenters_history[id]








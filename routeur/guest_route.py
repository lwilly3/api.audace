# # routes.py
# from fastapi import APIRouter, HTTPException
# from typing import List, Optional
# from app.db.crud.crud_guests import get_all_active_guests, get_guest_by_id, create_guest, update_guest, soft_delete_guest
# from app.schemas import GuestInDB,GuestCreate,GuestUpdate



# guest.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.crud.crud_guests import get_guest_by_id, get_guests, create_guest, update_guest, delete_guest
from app.schemas import GuestResponse, GuestCreate, GuestUpdate
from app.db.database import get_db
from typing import List
from core.auth import oauth2
# current_user: int = Depends(oauth2.get_current_user)
router = APIRouter(

    prefix="/guests",
    tags=["guests"],
)

@router.post("/", response_model=GuestResponse)
def create_guest_route(
    guest: GuestCreate,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """Route pour créer un invité."""
    try:
        return create_guest(db=db, guest=guest)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création de l'invité: {str(e)}")

@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest_route(
    guest_id: int,
    db: Session = Depends(get_db),  current_user: int = Depends(oauth2.get_current_user)
):
    """Route pour récupérer un invité par ID."""
    try:
        db_guest = get_guest_by_id(db=db, guest_id=guest_id)
        if db_guest is None:
            raise HTTPException(status_code=404, detail="Invité non trouvé")
        return db_guest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'invité: {str(e)}")

@router.get("/")
def get_guests_route(
    skip: int = 0, limit: int = 10,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """Route pour récupérer la liste des invités.   , current_user: int = Depends(oauth2.get_current_user)"""
    try:
        return  get_guests(db=db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des invités: {str(e)}")

@router.put("/{guest_id}", response_model=GuestResponse)
def update_guest_route(
    guest_id: int,
    guest_update: GuestUpdate,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    """Route pour mettre à jour un invité."""
    try:
        db_guest = update_guest(db=db, guest_id=guest_id, guest_update=guest_update)
        if db_guest is None:
            raise HTTPException(status_code=404, detail="Invité non trouvé")
        return db_guest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour de l'invité: {str(e)}")

@router.delete("/{guest_id}", response_model=dict)
def delete_guest_route(
    guest_id: int,
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    """Route pour supprimer un invité."""
    try:
        if not delete_guest(db=db, guest_id=guest_id):
            raise HTTPException(status_code=404, detail="Invité non trouvé")
        return {"message": "Invité supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'invité: {str(e)}")











# @router.post("/guests", response_model=GuestInDB)
# def create_guest_route(guest: Guest):
#     """
#     Ajouter un nouvel invité.
#     """
#     new_guest = create_guest(guest.name, guest.contact_info, guest.details)
#     return new_guest




# @router.put("/guests/{id}", response_model=GuestInDB)
# def update_guest_route(id: int, guest: Guest):
#     """
#     Mettre à jour un invité existant.
#     """
#     updated_guest = update_guest(id, guest.name, guest.contact_info, guest.details)
#     if not updated_guest:
#         raise HTTPException(status_code=404, detail="Guest not found")
#     return updated_guest

# @router.put("/guests/{id}", response_model=GuestInDB)
# def update_guest_route(id: int, guest: GuestUpdate):
#     """
#     Mettre à jour un invité existant.
#     """
#     updated_guest = update_guest(id, guest.name, guest.contact_info, guest.details)
#     if not updated_guest:
#         raise HTTPException(status_code=404, detail="Guest not found")
#     return updated_guest



# @router.delete("/guests/{id}")
# def delete_guest_route(id: int):
#     """
#     Supprimer (soft delete) un invité.
#     """
#     success = soft_delete_guest(id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Guest not found")
#     return {"detail": "Guest soft-deleted successfully"}

















# from fastapi import FastAPI, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime


# app = FastAPI()


# # Simulated database for guests
# guests_db = {}  # Dictionnaire pour stocker les invités actifs/inactifs


# # Modèles pour les données des invités
# class Guest(BaseModel):
#     """
#     Modèle de base pour créer ou mettre à jour un invité.
#     """
#     name: str
#     contact_info: str
#     details: Optional[str] = None
#     is_active: bool = True  # Indique si l'invité est actif


# class GuestInDB(Guest):
#     """
#     Modèle étendu pour inclure des informations supplémentaires stockées en base.
#     """
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime] = None


# # Fonction utilitaire pour récupérer un invité, ou lever une erreur 404
# def get_guest_or_404(guest_id: int) -> GuestInDB:
#     if guest_id not in guests_db or not guests_db[guest_id].is_active:
#         raise HTTPException(status_code=404, detail="Guest not found")
#     return guests_db[guest_id]


# # Routes
# @app.get("/guests", response_model=List[GuestInDB])
# def get_all_guests():
#     """
#     Récupérer tous les invités actifs.
#     """
#     return [g for g in guests_db.values() if g.is_active]


# @app.get("/guests/{id}", response_model=GuestInDB)
# def get_guest(id: int):
#     """
#     Récupérer un invité spécifique par son ID.
#     Lève une erreur 404 si l'invité n'existe pas ou est inactif.
#     """
#     return get_guest_or_404(id)


# @app.post("/guests", response_model=GuestInDB)
# def create_guest(guest: Guest):
#     """
#     Ajouter un nouvel invité.
#     Attribue automatiquement un ID unique.
#     """
#     guest_id = len(guests_db) + 1  # Génération d'un nouvel ID
#     new_guest = GuestInDB(
#         **guest.dict(), id=guest_id, created_at=datetime.utcnow()
#     )
#     guests_db[guest_id] = new_guest  # Ajout dans la base simulée
#     return new_guest


# @app.put("/guests/{id}", response_model=GuestInDB)
# def update_guest(id: int, guest: Guest):
#     """
#     Mettre à jour un invité existant.
#     """
#     existing_guest = get_guest_or_404(id)  # Vérifie si l'invité existe
#     updated_guest = existing_guest.copy(
#         update={**guest.dict(), "updated_at": datetime.utcnow()}
#     )
#     guests_db[id] = updated_guest  # Mise à jour dans la base simulée
#     return updated_guest


# @app.delete("/guests/{id}")
# def delete_guest(id: int):
#     """
#     Supprimer (soft delete) un invité.
#     Marque l'invité comme inactif et enregistre l'heure de suppression.
#     """
#     guest = get_guest_or_404(id)  # Vérifie si l'invité existe
#     guest.is_active = False  # Marque comme inactif
#     guest.updated_at = datetime.utcnow()  # Date de suppression
#     guests_db[id] = guest  # Mise à jour dans la base simulée
#     return {"detail": "Guest soft-deleted successfully"}

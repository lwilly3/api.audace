


# guest.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.crud.crud_guests import get_guest_by_id, get_guests, create_guest, update_guest, delete_guest,search_guest
from app.schemas import GuestResponse, GuestCreate, GuestUpdate
from app.db.database import get_db
from typing import List
from core.auth import oauth2
from app.db.crud.crud_guests import GuestService
from app.schemas.schema_guests import GuestResponseWithAppearances
from app.exceptions.guest_exceptions import GuestNotFoundException, DatabaseQueryException
from app.db.crud.crud_audit_logs import log_action





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
        result = create_guest(db=db, guest=guest)
        log_action(db, current_user.id, "create", "guests", result.id if result else 0)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création de l'invité: {str(e)}")

@router.get("/search")
def search_guests(query: str, db: Session = Depends(get_db)):
    response = GuestService.search_guest_detailed(db, query)
    return response


@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest_route(
    guest_id: int,
    db: Session = Depends(get_db),  current_user: int = Depends(oauth2.get_current_user)
):
    """Route pour récupérer un invité par ID."""
    try:
        db_guest = get_guest_by_id(db=db, guest_id=guest_id)
        if db_guest is None:
            return JSONResponse(
            status_code=404,
            content={"detail": "Invité non trouvé"}
        )
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
        log_action(db, current_user.id, "update", "guests", guest_id)
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
        log_action(db, current_user.id, "delete", "guests", guest_id)
        return {"message": "Invité supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'invité: {str(e)}")




# //////////////////////////// recuperation des invite avec leurs details//////////


@router.get("/details/{guest_id}",
    response_model=GuestResponseWithAppearances,
    summary="Récupérer les détails d'un invité",
    description="Retourne les informations d'un invité ainsi que ses participations aux émissions."
)
async def get_guest_details_with_appearances(guest_id: int, db: Session = Depends(get_db)):
    """
    Endpoint pour récupérer les détails d'un invité avec ses apparitions.
    
    Args:
        guest_id (int): Identifiant de l'invité à récupérer.
        db (Session): Session SQLAlchemy injectée via dépendance.
    
    Returns:
        GuestResponseWithAppearances: Détails de l'invité et liste de ses participations.
    
    Raises:
        HTTPException: 404 si l'invité n'est pas trouvé, 500 en cas d'erreur serveur.
    """
    try:
        # Étape 1 : Récupérer l'invité
        guest = GuestService.get_guest_by_id_allinfo(db, guest_id)
        
        # Étape 2 : Récupérer les participations
        appearances = GuestService.get_guest_appearances(db, guest_id)
        
        # Étape 3 : Construire et retourner la réponse
        response = GuestService.build_guest_response(guest, appearances)
        return response
    
    except GuestNotFoundException as e:
        # Erreur 404 pour un invité non trouvé
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseQueryException as e:
        # Erreur 500 pour une erreur de base de données
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Gestion des erreurs inattendues
        raise HTTPException(status_code=500, detail=f"Erreur inattendue: {str(e)}")






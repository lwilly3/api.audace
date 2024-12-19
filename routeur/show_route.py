from fastapi import FastAPI, HTTPException, Depends,APIRouter,status
from sqlalchemy.orm import Session
from typing import List
from app.schemas import ShowCreate, ShowUpdate,ShowCreateWithDetail,ShowUpdateWithDetails, SegmentUpdateWithDetails, ShowWithdetailResponse
from app.db.crud.crud_show import create_show, get_shows, get_show_by_id, update_show, delete_show, create_show_with_details,update_show_with_details, get_show_with_details
from app.db.database import get_db # Assurez-vous d'avoir une fonction SessionLocal pour obtenir la session DB
from app.schemas import ShowOut  # Modèle Show que vous avez défini précédemment
from core.auth import oauth2
# Initialisation de l'application FastAPI
router = APIRouter(
        prefix="/shows",
     tags=['shows']
    
)

# créer un conducteur avec ses segments
# /////////////////////////////////

@router.post("/detail",  status_code=status.HTTP_201_CREATED)
async def create_show_with_details_endpoint(show_data: ShowCreateWithDetail, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Endpoint pour créer un show avec ses segments, présentateurs et invités.
    
    Args:
        - show_data (ShowCreate): Les données du show envoyées par le frontend.
        - db (Session): La session de la base de données injectée via Depends.

    Returns:
        - dict: Confirmation avec les détails du show créé.
    """
    try:
        # Appel du service pour créer un show avec ses segments et relations
        show = create_show_with_details(db=db, show_data=show_data)

        # Retourne les données du show créé
        return {
            "message": "Show created successfully.",
            "show": show
        }

    except HTTPException as http_exc:
        # Erreurs spécifiques levées par le service
        raise http_exc

    except Exception as e:
        # Gestion des erreurs inattendues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

#  mise a joure show avec details
# ///////////////////////////////////

@router.put("/detail/{show_id}")
async def update_show(
    show_id: int, 
    show_data: ShowUpdate, 
    db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    """
    Met à jour un show avec ses segments, présentateurs et invités.

    Args:
        - show_id (int): ID du show à mettre à jour.
        - show_data (ShowUpdate): Les nouvelles données pour le show.
        - db (Session): Session de base de données.

    Returns:
        - ShowUpdate: Les détails du show mis à jour.
    """
    updated_show = update_show_with_details(db, show_id, show_data.dict())
    if not updated_show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with ID {show_id} not found."
        )
    return updated_show




# Route pour créer un nouveau show
@router.post("/", response_model=ShowOut, status_code=201)
def create_new_show_route(show: ShowCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Crée un nouveau show.
    """
    return create_show(db=db, show=show)

# Route pour récupérer tous les shows
@router.get("/", response_model=List[ShowOut])
def read_shows_route(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère une liste de tous les shows.
    """
    print(current_user.id)
    return get_shows(db=db, skip=skip, limit=limit)

# Route pour récupérer un show par son ID
@router.get("/{show_id}", response_model=ShowOut)
def read_show_route(show_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère un show par son ID.
    """
    db_show = get_show_by_id(db=db, show_id=show_id)
    if db_show is None:
        raise HTTPException(status_code=404, detail="Show non trouvé")
    return db_show

# Route pour récupérer un show detaillé par son ID
@router.get("/getdetail/{show_id}")
def read_Detailed_show_route(show_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupère un show par son ID.
    """
    db_show = get_show_with_details(db=db, show_id=show_id)
    if db_show is None:
        raise HTTPException(status_code=404, detail="Show non trouvé")
    return db_show

# Route pour mettre à jour un show existant
@router.put("/upd/{show_id}", response_model=ShowOut)
def update_existing_show_route(show_id: int, show: ShowUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Met à jour un show existant.
    """
    return update_show(db=db, show_id=show_id, show=show)

# Route pour supprimer un show
@router.delete("/del/{show_id}", response_model=ShowOut)
def delete_existing_show_route(show_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Supprime un show par son ID.
    """
    db_show = delete_show(db=db, show_id=show_id)
    if db_show is None:
        raise HTTPException(status_code=404, detail="Show non trouvé")
    return db_show
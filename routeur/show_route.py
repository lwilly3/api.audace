from fastapi import FastAPI, HTTPException, Depends,APIRouter,status
from sqlalchemy.orm import Session
from typing import List
from app.schemas import ShowCreate, ShowUpdate,ShowCreateWithDetail,ShowUpdateWithDetails, SegmentUpdateWithDetails, ShowWithdetailResponse, ShowBase_jsonShow, ShowStatuslUpdate
from app.db.crud.crud_show import create_show, get_shows, get_show_by_id, update_show, delete_show, create_show_with_details,update_show_with_details, get_show_with_details,get_show_details_all,get_show_details_by_id,create_show_with_elements_from_json,update_show_status,get_production_show_details,get_show_details_owned, delete_all_shows, delete_shows_by_user
from app.db.database import get_db # Assurez-vous d'avoir une fonction SessionLocal pour obtenir la session DB
from app.schemas import ShowOut  # Modèle Show que vous avez défini précédemment
from core.auth import oauth2
from app.models.model_user import User
# Initialisation de l'application FastAPI
router = APIRouter(
        prefix="/shows",
     tags=['shows']
    
)





# //==========================================================? cc
# //==========================================================?
# //==========================================================?
# //==========================================================?


# Route pour créer un nouveau show

# Route pour créer une émission avec ses segments et présentateurs
@router.post("/new")
async def create_show_new(
    shows_data: List[ShowBase_jsonShow], 
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    try:
# Appel de la fonction pour insérer les données dans la base
# Appel de la fonction pour insérer les données dans la base
        new_show = create_show_with_elements_from_json(db=db, shows_data=shows_data, curent_user_id=current_user.id)
        return {"message": "Émission créée avec succès", "show_id": new_show.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Route pour récupérer tous les détails des émissions
@router.get("/x")
def get_all_show_details(db: Session = Depends(get_db)):
    # print("get_all_show_details")
    shows = get_show_details_all(db)
    return shows

# Route pour récupérer les détails d'une émission par ID
@router.get("/x/{show_id}", response_model=dict)
def get_show_details(show_id: int, db: Session = Depends(get_db)):
    show = get_show_details_by_id(db, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show

# Route pour récupérer tous les détails des émissions pret a etre diffusé
@router.get("/production")
def get_all_show_details_for_production(db: Session = Depends(get_db)):
    # print("get_all_show_details")
    shows = get_production_show_details(db)
    return shows


# Route pour récupérer tous les détails des émissions pret a etre diffusé
@router.get("/owned")
def get_all_show_details_owned_by_user(db: Session = Depends(get_db), user_id: User = Depends(oauth2.get_current_user)):
    # print("get_all_show_details")
    shows = get_show_details_owned(db, user_id.id)
    return shows




# ///////////////////////////////// modifier statut show avec id

@router.patch("/status/{show_id}")
async def update_show_status_route(
    show_id: int,
    show_data: ShowStatuslUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour le statut d'un show.

    Args:
        - show_id (int): ID du show à mettre à jour.
        - show_data (ShowPartialUpdate): Données partiellement mises à jour.
        - db (Session): Session de base de données.

    Returns:
        - dict: ID du show et statut mis à jour.
    """
    if not show_data.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status field is required."
        )

    return update_show_status(db, show_id, show_data.status)

# créer un conducteur avec ses segments
# ///////////////////////////////// , current_user: int = Depends(oauth2.get_current_user)

@router.post("/detail",  status_code=status.HTTP_201_CREATED)
async def create_show_with_details_endpoint(show_data: ShowCreateWithDetail, db: Session = Depends(get_db),current_user: User = Depends(oauth2.get_current_user)):
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
        show = create_show_with_details(db=db, show_data=show_data, curent_user_id=current_user.id)

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

@router.patch("/detail/{show_id}")
async def update_show_details_route( # Renamed from update_show
    show_id: int, 
    show_data: ShowUpdate, 
    db: Session = Depends(get_db)
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
    # Note: The original code called update_show_with_details here. 
    # Assuming this is correct based on the function's purpose.
    updated_show = update_show_with_details(db, show_id, show_data.dict()) 
    if not updated_show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with ID {show_id} not found."
        )
    return updated_show




# Route pour créer un nouveau show
@router.post("/", response_model=ShowOut, status_code=201)
def create_new_show_route(show: ShowCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau show.
    """
    return create_show(db=db, show=show)

# Route pour récupérer tous les shows
@router.get("/", response_model=List[ShowOut])
def read_shows_route(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Récupère une liste de tous les shows.
    """
    # print(current_user.id)
    return get_shows(db=db, skip=skip, limit=limit)

# Route pour récupérer un show par son ID
@router.get("/{show_id}", response_model=ShowOut)
def read_show_route(show_id: int, db: Session = Depends(get_db)):
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




# # //==========================================================?
# # //==========================================================?
# # //==========================================================?
# # //==========================================================?

# # Route pour récupérer tous les détails des émissions
# @router.get("/x")
# def get_all_show_details(db: Session = Depends(get_db)):
#     # print("get_all_show_details")
#     shows = get_show_details_all(db)
#     return shows

# # Route pour récupérer les détails d'une émission par ID
# @router.get("/x/{show_id}", response_model=dict)
# def get_show_details(show_id: int, db: Session = Depends(get_db)):
#     show = get_show_details_by_id(db, show_id)
#     if not show:
#         raise HTTPException(status_code=404, detail="Show not found")
#     return show

# DELETE all shows
@router.delete('/all', summary='Supprimer tous les shows')
def delete_all_shows_route(db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    """Supprime tous les shows et retourne le nombre supprimés"""
    count = delete_all_shows(db)
    return {'deleted': count}

# DELETE shows by creator
@router.delete('/user/{user_id}', summary='Supprimer shows par utilisateur')
def delete_shows_by_user_route(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(oauth2.get_current_user)):
    """Supprime tous les shows créés par un utilisateur donné"""
    count = delete_shows_by_user(db, user_id)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Aucun show trouvé pour l'utilisateur {user_id}")
    return {'deleted': count}
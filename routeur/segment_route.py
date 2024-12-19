from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import SegmentCreate, SegmentUpdate, SegmentResponse, SegmentPositionUpdate
from app.models import Segment
from app.db.crud.crud_segments import create_segment, get_segments, get_segment_by_id, update_segment, update_segment_position, soft_delete_segment
from typing import List
from core.auth import oauth2
# Création d'un routeur FastAPI pour regrouper toutes les routes liées aux segments
router = APIRouter(
           prefix="/segments",
     tags=['segments']
    
)



# 1. Créer un segment
@router.post("/", response_model=SegmentResponse)
def create_route(segment: SegmentCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return create_segment(db, segment)

# 2. Récupérer tous les segments
@router.get("/", response_model=list[SegmentResponse])
def read_all_route(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return get_segments(db)

# 3. Récupérer un segment par ID
@router.get("/{segment_id}", response_model=SegmentResponse)
def read_route(segment_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    segment = get_segment_by_id(db, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment

# 4. Modifier un segment
@router.put("/{segment_id}", response_model=SegmentResponse)
def update_route(segment_id: int, segment: SegmentUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    db_segment = get_segment_by_id(db, segment_id)
    if not db_segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return update_segment(db, db_segment, segment)

# 5. Modifier la position d'un segment
@router.patch("/{segment_id}/position", response_model=SegmentResponse)
def update_position_route(segment_id: int, position_update: SegmentPositionUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    db_segment = get_segment_by_id(db, segment_id)
    if not db_segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return update_segment_position(db, db_segment, position_update.position)

# 6. Soft delete d'un segment
@router.delete("/{segment_id}", response_model=dict)
def delete_route(segment_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    db_segment = get_segment_by_id(db, segment_id)
    if not db_segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return soft_delete_segment(db, db_segment)














# # Route pour créer un nouveau segment
# @router.post("/segments", response_model=Segment)
# def create_segment_route(segment_data: SegmentCreate, db: Session = Depends(get_db)):
#     """
#     Cette route permet de créer un nouveau segment pour une émission.
#     - Elle prend les données de création du segment (SegmentCreate) comme entrée.
#     - La base de données est automatiquement récupérée grâce à `Depends(get_db)`.
#     - La fonction `create_segment` est appelée pour insérer le segment dans la base de données.
#     - Retourne le segment créé sous forme d'un objet de type `Segment`.
#     """
#     return create_segment(db, segment_data)

# # Route pour récupérer un segment par son ID
# @router.get("/segments/{segment_id}", response_model=Segment)
# def get_segment_route(segment_id: int, db: Session = Depends(get_db)):
#     """
#     Cette route permet de récupérer un segment spécifique en fonction de son ID.
#     - Le segment est récupéré via la fonction `get_segment_by_id`.
#     - Si le segment n'existe pas, une erreur 404 est levée (gérée dans la fonction appelée).
#     - Retourne les détails du segment sous forme d'un objet `Segment`.
#     """
#     return get_segment_by_id(db, segment_id)

# # Route pour récupérer tous les segments, avec pagination (optionnelle)
# @router.get("/segments", response_model=List[Segment])
# def get_segments_route(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     """
#     Cette route permet de récupérer tous les segments.
#     - La pagination est implémentée via les paramètres `skip` et `limit`.
#     - `skip` définit combien de segments sont ignorés au début, et `limit` définit le nombre de segments à renvoyer.
#     - La fonction `get_all_segments` est utilisée pour obtenir les segments avec ces paramètres.
#     - Retourne une liste d'objets `Segment`.
#     """
#     return get_all_segments(db, skip, limit)

# # Route pour mettre à jour un segment existant
# @router.put("/segments/{segment_id}", response_model=Segment)
# def update_segment_route(segment_id: int, segment_data: SegmentUpdate, db: Session = Depends(get_db)):
#     """
#     Cette route permet de mettre à jour un segment existant en fonction de son ID.
#     - Les nouvelles données du segment sont envoyées sous forme de `SegmentUpdate`.
#     - Si le segment n'existe pas, une erreur 404 est levée.
#     - La fonction `update_segment` est utilisée pour appliquer les modifications dans la base de données.
#     - Retourne le segment mis à jour.
#     """
#     return update_segment(db, segment_id, segment_data)

# # Route pour supprimer un segment
# @router.delete("/segments/{segment_id}")
# def delete_segment_route(segment_id: int, db: Session = Depends(get_db)):
#     """
#     Cette route permet de supprimer un segment en fonction de son ID.
#     - Si le segment n'existe pas, une erreur 404 est levée.
#     - La fonction `delete_segment` est utilisée pour supprimer le segment de la base de données.
#     - Retourne un message indiquant que le segment a été supprimé avec succès.
#     """
#     delete_segment(db, segment_id)
#     return {"detail": "Segment deleted successfully"}

# # Route pour récupérer tous les segments d'une émission spécifique
# @router.get("/shows/{show_id}/segments", response_model=List[Segment])
# async def read_segments_by_show(show_id: int, db: Session = Depends(get_db)):
#     """
#     Cette route permet de récupérer tous les segments associés à une émission donnée, triés par position.
#     - Le `show_id` est l'identifiant de l'émission pour laquelle on souhaite obtenir les segments.
#     - La fonction `get_segments_by_show` est utilisée pour récupérer les segments de cette émission.
#     - Si aucun segment n'est trouvé, une erreur 404 est levée.
#     - Retourne une liste de segments sous forme d'objets `Segment`, triée par position.
#     """
#     segments = get_segments_by_show(db, show_id)
#     return segments

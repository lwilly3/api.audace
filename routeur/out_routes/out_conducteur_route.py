
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from app.db.database import get_db
from app.db.crud import crud_conducteur, crud_show_segemt
from app.schemas.schema_conducteur import ShowPlanCreate, ShowPlanUpdate, ShowPlanSegmentCreate, ShowPlanSegmentUpdate, ShowPlanSegment, ShowPlan, ShowPlanSearch

router = APIRouter(
    prefix="/conducteur",
    tags=["CONDUCTEUR"]
)


# Route : Créer un ShowPlan
@router.post("/show_plans/", response_model=ShowPlan)
def create_show_plan(show_plan: ShowPlanCreate, db: Session = Depends(get_db)):
    return crud_conducteur.create_show_plan(db, show_plan)


# Route : Mettre à jour un ShowPlan
@router.put("/show_plans/{show_plan_id}", response_model=ShowPlan)
def update_show_plan(show_plan_id: int, show_plan: ShowPlanUpdate, db: Session = Depends(get_db)):
    try:
        return crud_conducteur.update_show_plan(db, show_plan_id, show_plan)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Show plan not found")


# Route : Supprimer un ShowPlan
@router.delete("/show_plans/{show_plan_id}", response_model=bool)
def delete_show_plan(show_plan_id: int, db: Session = Depends(get_db)):
    try:
        return crud_conducteur.delete_show_plan(db, show_plan_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Show plan not found")


# Route : Ajouter un segment à un ShowPlan
@router.post("/show_plans/{show_plan_id}/segments", response_model=ShowPlanSegment)
def create_show_plan_segment(show_plan_id: int, segment: ShowPlanSegmentCreate, db: Session = Depends(get_db)):
    try:
        crud_conducteur.get_show_plan(db, show_plan_id)  # Vérifier si le ShowPlan existe
        return crud_conducteur.create_show_plan_segment(db, show_plan_id, segment)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Show plan not found")


# Route : Mettre à jour un segment
@router.put("/segments/{segment_id}", response_model=ShowPlanSegment)
def update_show_plan_segment(segment_id: int, segment: ShowPlanSegmentUpdate, db: Session = Depends(get_db)):
    try:
        return crud_conducteur.update_show_plan_segment(db, segment_id, segment)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Segment not found")


# Route : Supprimer un segment
@router.delete("/segments/{segment_id}", response_model=bool)
def delete_show_plan_segment(segment_id: int, db: Session = Depends(get_db)):
    try:
        return crud_conducteur.delete_show_plan_segment(db, segment_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Segment not found")





# Recherche de conducteurs (plans d'émission)
@router.get("/show_plans/search/", response_model=List[ShowPlan])
def search_show_plans(search_params: ShowPlanSearch, db: Session = Depends(get_db)):
    """
    Recherche des conducteurs (plans d'émission) en fonction de critères comme le titre, la description ou la date.
    """
    return crud_conducteur.search_show_plans(db=db, search_params=search_params)


# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import func
# from app.db.database import get_db
# # from app.models import ShowPlan
# from app.schemas.schema_conducteur import ShowPlanCreate, ShowPlanUpdate, ShowPlanSegmentCreate, ShowPlanSegmentUpdate, ShowPlanSegment,ShowPlan
# from sqlalchemy.orm import joinedload

# router = APIRouter(

#      prefix="/conducteur",  # Préfixe pour toutes les routes dans ce module
#     tags=['CONDUCTEUR']  # Tag utilisé pour organiser les routes dans la documentation de FastAPI

# )




# # Ajouter un nouveau conducteur
# @router.post("/show_plans/", response_model=ShowPlan)
# def create_show_plan(show_plan: ShowPlanCreate, db: Session = Depends(get_db)):
#     new_show_plan = ShowPlan(**show_plan.model_dump())
#     db.add(new_show_plan)
#     db.commit()
#     db.refresh(new_show_plan)
#     return new_show_plan

# # Mettre à jour un conducteur
# @router.put("/show_plans/{show_plan_id}", response_model=ShowPlan)
# def update_show_plan(show_plan_id: int, show_plan: ShowPlanUpdate, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")
#     for key, value in show_plan.model_dump().items():
#         setattr(db_show_plan, key, value)
#     db.commit()
#     db.refresh(db_show_plan)
#     return db_show_plan

# # Supprimer un conducteur
# @router.delete("/show_plans/{show_plan_id}", response_model=ShowPlan)
# def delete_show_plan(show_plan_id: int, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")
#     db.delete(db_show_plan)
#     db.commit()
#     return db_show_plan


# # Ajouter un segment au conducteur
# @router.post("/show_plans/{show_plan_id}/segments", response_model=ShowPlanSegment)
# def create_show_plan_segment(show_plan_id: int, segment: ShowPlanSegmentCreate, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")
    
#     new_segment = ShowPlanSegment(**segment.model_dump(), show_plan_id=show_plan_id)
#     db.add(new_segment)
#     db.commit()
#     db.refresh(new_segment)
#     return new_segment

# # Mettre à jour un segment du conducteur
# @router.put("/show_plans/{show_plan_id}/segments/{segment_id}", response_model=ShowPlanSegment)
# def update_show_plan_segment(show_plan_id: int, segment_id: int, segment: ShowPlanSegmentUpdate, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")
    
#     db_segment = db.query(ShowPlanSegment).filter(ShowPlanSegment.id == segment_id, ShowPlanSegment.show_plan_id == show_plan_id).first()
#     if not db_segment:
#         raise HTTPException(status_code=404, detail="Segment not found")
    
#     for key, value in segment.model_dump().items():
#         setattr(db_segment, key, value)
#     db.commit()
#     db.refresh(db_segment)
#     return db_segment

# # Supprimer un segment du conducteur
# @router.delete("/show_plans/{show_plan_id}/segments/{segment_id}", response_model=ShowPlanSegment)
# def delete_show_plan_segment(show_plan_id: int, segment_id: int, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")
    
#     db_segment = db.query(ShowPlanSegment).filter(ShowPlanSegment.id == segment_id, ShowPlanSegment.show_plan_id == show_plan_id).first()
#     if not db_segment:
#         raise HTTPException(status_code=404, detail="Segment not found")
    
#     db.delete(db_segment)
#     db.commit()
#     return db_segment

# # Déplacer la position d'un segment dans le conducteur
# @router.put("/show_plans/{show_plan_id}/segments/{segment_id}/move", response_model=ShowPlanSegment)
# def move_show_plan_segment(show_plan_id: int, segment_id: int, new_position: int, db: Session = Depends(get_db)):
#     db_show_plan = db.query(ShowPlan).filter(ShowPlan.id == show_plan_id).first()
#     if not db_show_plan:
#         raise HTTPException(status_code=404, detail="Show plan not found")

#     db_segment = db.query(ShowPlanSegment).filter(ShowPlanSegment.id == segment_id, ShowPlanSegment.show_plan_id == show_plan_id).first()
#     if not db_segment:
#         raise HTTPException(status_code=404, detail="Segment not found")

#     # Si la position cible est identique à la position actuelle, on ne fait rien
#     if db_segment.position == new_position:
#         return db_segment

#     # Récupérer tous les segments du plan, triés par position actuelle
#     segments = db.query(ShowPlanSegment).filter(ShowPlanSegment.show_plan_id == show_plan_id).order_by(ShowPlanSegment.position).all()

#     # Si la position cible est déjà occupée, ajuster les positions des segments
#     if any(segment.position == new_position for segment in segments):
#         raise HTTPException(status_code=400, detail="Target position is already occupied")

#     # Décaler les segments suivants pour faire de la place à la nouvelle position
#     for segment in segments:
#         if segment.position >= new_position:
#             segment.position += 1  # Décaler les segments suivants

#     db_segment.position = new_position  # Appliquer la nouvelle position
#     db.commit()  # Commit des changements
#     db.refresh(db_segment)
#     return db_segment

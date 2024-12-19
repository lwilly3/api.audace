
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.crud.crud_presenters import (
    get_presenter, get_presenters, create_presenter, update_presenter, delete_presenter
)
from app.schemas import PresenterCreate, PresenterUpdate, PresenterResponse
from app.db.database import get_db

router = APIRouter()

@router.get("/presenters", response_model=list[PresenterResponse])
def read_presenters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_presenters(db, skip=skip, limit=limit)

@router.get("/presenters/{presenter_id}", response_model=PresenterResponse)
def read_presenter(presenter_id: int, db: Session = Depends(get_db)):
    presenter = get_presenter(db, presenter_id)
    if not presenter:
        raise HTTPException(status_code=404, detail="Presenter not found")
    return presenter

@router.post("/presenters", response_model=PresenterResponse)
def create_presenter_endpoint(presenter: PresenterCreate, db: Session = Depends(get_db)):
    return create_presenter(db, presenter)

@router.put("/presenters/{presenter_id}", response_model=PresenterResponse)
def update_presenter_endpoint(presenter_id: int, presenter: PresenterUpdate, db: Session = Depends(get_db)):
    updated_presenter = update_presenter(db, presenter_id, presenter)
    if not updated_presenter:
        raise HTTPException(status_code=404, detail="Presenter not found")
    return updated_presenter

@router.delete("/presenters/{presenter_id}")
def delete_presenter_endpoint(presenter_id: int, db: Session = Depends(get_db)):
    deleted_presenter = delete_presenter(db, presenter_id)
    if not deleted_presenter:
        raise HTTPException(status_code=404, detail="Presenter not found")
    return {"message": "Presenter deleted successfully"}

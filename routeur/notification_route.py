# routes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.schemas import NotificationRead, NotificationCreate, NotificationUpdate
from app.db.database import get_db
from core.auth import oauth2
from app.db.crud.crud_notifications import create_notification, get_user_notifications, update_notification, delete_notification, get_notification_by_id
from app.models import model_user



router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

@router.get("/", response_model=List[NotificationRead])
def get_all_notifications_route(db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    """
    Récupérer toutes les notifications non supprimées.
    """
    result = get_user_notifications(user_id=current_user.id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="No notifications found")
    return result


@router.get("/{id}", response_model=NotificationRead)
def get_notification_route(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer une notification spécifique.
    """
    notification = get_notification_by_id(id, db)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/", response_model=NotificationRead)
def create_notification_route(
    notification: NotificationCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    """
    Envoyer une nouvelle notification à un utilisateur.
    """
    new_notification = create_notification(notification=notification, db=db, current_user=current_user)
    return new_notification


@router.put("/{id}", response_model=NotificationRead)
def update_notification_route(
    id: int, notification_update: NotificationUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)
):
    """
    Mettre à jour une notification.
    """
    updated_notification = update_notification(notification_id=id, notification_update=notification_update, db=db, current_user=current_user)
    if not updated_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return updated_notification


@router.delete("/{id}")
def delete_notification_route(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Supprimer une notification (soft delete).
    """
    success = delete_notification(notification_id=id, db=db, current_user=current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"detail": f"Notification {id} deleted successfully"}
















# from fastapi import FastAPI, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# app = FastAPI()

# # Simulated database
# notifications_db = {}

# # Models
# class Notification(BaseModel):
#     """
#     Modèle pour représenter une notification.
#     """
#     id: int
#     user_id: int
#     title: str
#     message: str
#     created_at: datetime
#     read: bool = False
#     is_deleted: bool = False


# # Routes
# @app.get("/notifications", response_model=List[Notification])
# def get_all_notifications():
#     """
#     Récupérer toutes les notifications non supprimées.
#     """
#     return [notif for notif in notifications_db.values() if not notif.is_deleted]


# @app.get("/notifications/{id}", response_model=Notification)
# def get_notification(id: int):
#     """
#     Récupérer une notification spécifique.
#     """
#     notification = notifications_db.get(id)
#     if not notification or notification.is_deleted:
#         raise HTTPException(status_code=404, detail="Notification not found")
#     return notification


# @app.post("/notifications", response_model=Notification)
# def create_notification(user_id: int, title: str, message: str):
#     """
#     Envoyer une nouvelle notification à un utilisateur.
#     """
#     notif_id = len(notifications_db) + 1
#     new_notification = Notification(
#         id=notif_id,
#         user_id=user_id,
#         title=title,
#         message=message,
#         created_at=datetime.now(),
#     )
#     notifications_db[notif_id] = new_notification
#     return new_notification


# @app.put("/notifications/{id}", response_model=Notification)
# def update_notification(id: int, title: Optional[str] = None, message: Optional[str] = None, read: Optional[bool] = None):
#     """
#     Mettre à jour une notification.
#     """
#     notification = notifications_db.get(id)
#     if not notification or notification.is_deleted:
#         raise HTTPException(status_code=404, detail="Notification not found")
#     if title:
#         notification.title = title
#     if message:
#         notification.message = message
#     if read is not None:
#         notification.read = read
#     return notification


# @app.delete("/notifications/{id}")
# def delete_notification(id: int):
#     """
#     Supprimer une notification (soft delete).
#     """
#     notification = notifications_db.get(id)
#     if not notification or notification.is_deleted:
#         raise HTTPException(status_code=404, detail="Notification not found")
#     notification.is_deleted = True
#     return {"detail": f"Notification {id} deleted successfully"}

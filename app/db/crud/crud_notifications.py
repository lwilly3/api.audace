from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from core.auth import oauth2
from app.models import Notification
from app.schemas import NotificationCreate, NotificationUpdate
from app.schemas.schema_notifications import NotificationRead
# CRUD pour les notifications

def create_notification(
    notification: NotificationCreate, 
    db: Session = Depends(get_db),  # Obtention de la session de la base de données via la dépendance get_db
    current_user: int = Depends(oauth2.get_current_user)  # Obtention de l'utilisateur authentifié via la dépendance oauth2.get_current_user
) -> NotificationRead:
    """Créer une nouvelle notification"""
    try:
        # Création de la notification en utilisant les données envoyées dans la requête, à l'aide du schéma NotificationCreate
        new_notification = Notification(**notification.model_dump())  
        db.add(new_notification)  # Ajout de la notification à la session de la base de données
        db.commit()  # Sauvegarde les modifications dans la base de données
        db.refresh(new_notification)  # Rafraîchit l'instance de la notification avec les données de la base de données
        return new_notification  # Retourne la notification nouvellement créée
    except Exception as e:
        # En cas d'erreur, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating notification: {str(e)}")

def get_user_notifications(
    user_id: int,  # ID de l'utilisateur pour lequel on veut récupérer les notifications
    skip: int = 0,  # Nombre d'éléments à ignorer pour la pagination
    limit: int = 10,  # Nombre maximal de notifications à récupérer
    db: Session = Depends(get_db),  # Obtention de la session de la base de données
    current_user: int = Depends(oauth2.get_current_user)  # Obtention de l'utilisateur authentifié
) -> list:
    """Récupérer toutes les notifications d'un utilisateur spécifique"""
    try:
        # Récupère les notifications de l'utilisateur spécifié, en s'assurant qu'elles ne sont pas supprimées (is_deleted == False)
        notifications = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_deleted == False).offset(skip).limit(limit).all()
        return notifications  # Retourne la liste des notifications récupérées
    except Exception as e:
        # En cas d'erreur, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching notifications: {str(e)}")

def update_notification(
    notification_id: int,  # ID de la notification à mettre à jour
    notification_update: NotificationUpdate,  # Données à mettre à jour, envoyées via le schéma NotificationUpdate
    db: Session = Depends(get_db),  # Obtention de la session de la base de données
    current_user: int = Depends(oauth2.get_current_user)  # Obtention de l'utilisateur authentifié
) -> NotificationRead:
    """Mettre à jour une notification spécifique"""
    try:
        # Recherche la notification existante à l'aide de son ID
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        # Si la notification est trouvée, on met à jour ses champs en fonction des données envoyées
        if notification:
            # Parcourt les clés et les valeurs des données envoyées et met à jour les champs correspondants
            for key, value in notification_update.dict(exclude_unset=True).items():
                setattr(notification, key, value)
            
            # Sauvegarde les changements dans la base de données
            db.commit()
            db.refresh(notification)  # Rafraîchit l'instance de la notification avec les données mises à jour
            return notification  # Retourne la notification mise à jour
        else:
            # Si la notification n'est pas trouvée, une exception HTTP 404 est levée
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except Exception as e:
        # En cas d'erreur, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating notification: {str(e)}")

def delete_notification(
    notification_id: int,  # ID de la notification à supprimer
    db: Session = Depends(get_db),  # Obtention de la session de la base de données
    current_user: int = Depends(oauth2.get_current_user)  # Obtention de l'utilisateur authentifié
) -> bool:
    """Supprimer une notification (soft delete)"""
    try:
        # Recherche la notification à l'aide de son ID
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        # Si la notification est trouvée, on effectue un "soft delete" en mettant à jour le champ is_deleted à True
        if notification:
            notification.is_deleted = True
            db.commit()  # Sauvegarde les modifications dans la base de données
            return True  # Retourne True pour indiquer que la suppression a réussi
        else:
            # Si la notification n'est pas trouvée, une exception HTTP 404 est levée
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except Exception as e:
        # En cas d'erreur, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting notification: {str(e)}")


# Fonction pour récupérer une notification par son ID
def get_notification_by_id(
    notification_id: int,  # ID de la notification 
    db: Session = Depends(get_db),  # Session de base de données
    current_user: int = Depends(oauth2.get_current_user)  # Utilisateur authentifié
) -> NotificationRead:
    """Récupérer une notification spécifique par son ID"""
    try:
        # Recherche de la notification dans la base de données
        notification = db.query(Notification).filter(Notification.id == notification_id, Notification.is_deleted == False).first()

        # Si la notification est trouvée, elle est retournée
        if notification:
            return notification
        else:
            # Si la notification n'est pas trouvée, lever une exception 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
    except Exception as e:
        # En cas d'erreur, lever une exception 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching notification: {str(e)}"
        )





















# from sqlalchemy.orm import Session
# from app.models.model_notification import Notification
# from app.schemas.schema_notifications import NotificationCreate, NotificationUpdate

# # CRUD pour les notifications
# def create_notification(db: Session, notification: NotificationCreate) -> Notification:
#     """Créer une nouvelle notification"""
#     new_notification = Notification(**notification.dict())  # Conversion du schéma en modèle
#     db.add(new_notification)
#     db.commit()
#     db.refresh(new_notification)
#     return new_notification

# def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> list:
#     """Récupérer toutes les notifications d'un utilisateur spécifique"""
#     return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_deleted == False).offset(skip).limit(limit).all()

# def update_notification(db: Session, notification_id: int, notification_update: NotificationUpdate) -> Notification:
#     """Mettre à jour une notification spécifique"""
#     notification = db.query(Notification).filter(Notification.id == notification_id).first()
#     if notification:
#         for key, value in notification_update.dict(exclude_unset=True).items():
#             setattr(notification, key, value)  # Mise à jour des champs
#         db.commit()
#         db.refresh(notification)
#     return notification

# def delete_notification(db: Session, notification_id: int) -> bool:
#     """Supprimer une notification (soft delete)"""
#     notification = db.query(Notification).filter(Notification.id == notification_id).first()
#     if notification:
#         notification.is_deleted = True  # Soft delete
#         db.commit()
#         return True
#     return False


















# # # database.py
# # from models import Notification
# # from datetime import datetime

# # # Base de données simulée
# # notifications_db = {}

# # def get_notification_by_id(notification_id: int) -> Notification:
# #     """Récupérer une notification par son ID"""
# #     return notifications_db.get(notification_id)

# # def get_all_notifications() -> list:
# #     """Récupérer toutes les notifications non supprimées"""
# #     return [notif for notif in notifications_db.values() if not notif.is_deleted]

# # def create_notification(user_id: int, title: str, message: str) -> Notification:
# #     """Créer une nouvelle notification"""
# #     notif_id = len(notifications_db) + 1
# #     new_notification = Notification(
# #         id=notif_id,
# #         user_id=user_id,
# #         title=title,
# #         message=message,
# #         created_at=datetime.now(),
# #     )
# #     notifications_db[notif_id] = new_notification
# #     return new_notification

# # def update_notification(notification_id: int, title: str = None, message: str = None, read: bool = None) -> Notification:
# #     """Mettre à jour une notification"""
# #     notification = notifications_db.get(notification_id)
# #     if notification:
# #         if title:
# #             notification.title = title
# #         if message:
# #             notification.message = message
# #         if read is not None:
# #             notification.read = read
# #     return notification

# # def delete_notification(notification_id: int) -> bool:
# #     """Supprimer une notification (soft delete)"""
# #     notification = notifications_db.get(notification_id)
# #     if notification:
# #         notification.is_deleted = True
# #         return True
# #     return False














# # # from sqlalchemy.orm import Session
# # # from app.models.model_notification import Notification
# # # from app.schemas.schema_notifications import NotificationCreate, NotificationUpdate

# # # def create_notification(db: Session, notification: NotificationCreate):
# # #     new_notification = Notification(**notification.dict())
# # #     db.add(new_notification)
# # #     db.commit()
# # #     db.refresh(new_notification)
# # #     return new_notification

# # # def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 10):
# # #     return db.query(Notification).filter(Notification.user_id == user_id).offset(skip).limit(limit).all()

# # # def update_notification(db: Session, notification_id: int, notification_update: NotificationUpdate):
# # #     notification = db.query(Notification).filter(Notification.id == notification_id).first()
# # #     for key, value in notification_update.dict(exclude_unset=True).items():
# # #         setattr(notification, key, value)
# # #     db.commit()
# # #     db.refresh(notification)
# # #     return notification

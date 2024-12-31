
# crud_guest.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.model_guest import Guest
from app.schemas import GuestCreate, GuestUpdate,GuestResponse
from typing import List

def create_guest(db: Session, guest: GuestCreate) -> GuestResponse:
    """Créer un nouvel invité."""
    try:
        db_guest = Guest(
            name=guest.name,
            contact_info=guest.contact_info,
            biography=guest.biography,
            role=guest.role,
            email=guest.email,
            phone=guest.phone

        )

        db.add(db_guest)
        db.commit()
        db.refresh(db_guest)
        return db_guest
    except SQLAlchemyError as e:
        db.rollback()  # Annule la transaction en cas d'erreur
        raise Exception(f"Erreur lors de la création de l'invité : {str(e)}")

def get_guest_by_id(db: Session, guest_id: int) -> GuestResponse:
    """Récupérer un invité par son ID."""
    try:
        return db.query(Guest).filter(Guest.id == guest_id).first()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération de l'invité avec ID {guest_id}: {str(e)}")

def get_guests(db: Session, skip: int = 0, limit: int = 10):
    """Récupérer tous les invités avec pagination."""
    try:
        gest_result =  db.query(Guest).offset(skip).limit(limit).all()
        serialized_guests = []
        for guest in gest_result:
            guests = {
                    "email": guest.email,
                    "id": guest.id,
                    "role": guest.role,
                    "biography": guest.biography,
                    "avatar": guest.avatar,
                    # "updated_at": "2024-12-19T17:29:22.037544",
                    # "deleted_at": null,
                    "phone": guest.phone,
                    "name": guest.name,
                    "contact_info": guest.contact_info,
                    # "created_at": "2024-12-19T17:29:22.037544",
                    # "is_deleted": false   
                    "showSegment_participation": len(guest.segments)
        }
            serialized_guests.append(guests)
        return serialized_guests
    
        # return guests
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des invités : {str(e)}")

def update_guest(db: Session, guest_id: int, guest_update: GuestUpdate) -> GuestResponse:
    """Mettre à jour un invité existant."""
    try:
        db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
        if db_guest:
            for key, value in guest_update.model_dump(exclude_unset=True).items():
                setattr(db_guest, key, value)
            db.commit()
            db.refresh(db_guest)
            return db_guest
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Erreur lors de la mise à jour de l'invité avec ID {guest_id}: {str(e)}")

def delete_guest(db: Session, guest_id: int) -> bool:
    """Supprimer un invité."""
    try:
        db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
        if db_guest:
            db.delete(db_guest)
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Erreur lors de la suppression de l'invité avec ID {guest_id}: {str(e)}")









# from typing import Optional
# from sqlalchemy.orm import Session
# from datetime import datetime, timezone
# from app.schemas import GuestInDB
# from app.schemas.schema_guests import GuestCreate, GuestUpdate
# from sqlalchemy.exc import SQLAlchemyError

# # CRUD pour les invités
# def get_guest_by_id(db: Session, guest_id: int) -> GuestInDB:
#     """Récupérer un invité par son ID"""
#     try:
#         return db.query(GuestInDB).filter(GuestInDB.id == guest_id).first()
#     except SQLAlchemyError as e:
#         raise Exception(f"Erreur lors de la récupération de l'invité avec ID {guest_id} : {str(e)}")

# def get_all_active_guests(db: Session) -> list:
#     """Récupérer tous les invités actifs"""
#     try:
#         return db.query(GuestInDB).filter(GuestInDB.is_active == True).all()
#     except SQLAlchemyError as e:
#         raise Exception(f"Erreur lors de la récupération des invités actifs : {str(e)}")

# def create_guest(db: Session, name: str, contact_info: str, details: Optional[str]) -> GuestInDB:
#     """Créer un nouvel invité"""
#     try:
#         guest_id = len(db.query(GuestInDB).all()) + 1  # Génération d'un nouvel ID basé sur la taille actuelle
#         new_guest = GuestInDB(
#             id=guest_id,
#             name=name,
#             contact_info=contact_info,
#             details=details,
#             is_active=True,
#             created_at=datetime.now(timezone.utc)  # Utilisation de datetime avec timezone
#         )
#         db.add(new_guest)
#         db.commit()
#         db.refresh(new_guest)
#         return new_guest
#     except SQLAlchemyError as e:
#         db.rollback()  # Annule la transaction en cas d'erreur
#         raise Exception(f"Erreur lors de la création de l'invité : {str(e)}")

# def update_guest(db: Session, guest_id: int, name: Optional[str], contact_info: Optional[str], details: Optional[str]) -> GuestInDB:
#     """Mettre à jour un invité existant"""
#     try:
#         guest = db.query(GuestInDB).filter(GuestInDB.id == guest_id).first()
#         if guest:
#             if name:
#                 guest.name = name
#             if contact_info:
#                 guest.contact_info = contact_info
#             if details:
#                 guest.details = details
#             guest.updated_at = datetime.now(timezone.utc)  # Utilisation de datetime avec timezone
#             db.commit()
#             db.refresh(guest)
#         return guest
#     except SQLAlchemyError as e:
#         db.rollback()  # Annule la transaction en cas d'erreur
#         raise Exception(f"Erreur lors de la mise à jour de l'invité avec ID {guest_id} : {str(e)}")

# def soft_delete_guest(db: Session, guest_id: int) -> bool:
#     """Supprimer un invité (soft delete)"""
#     try:
#         guest = db.query(GuestInDB).filter(GuestInDB.id == guest_id).first()
#         if guest:
#             guest.is_active = False
#             guest.updated_at = datetime.now(timezone.utc)  # Utilisation de datetime avec timezone
#             db.commit()
#             db.refresh(guest)
#             return True
#         return False
#     except SQLAlchemyError as e:
#         db.rollback()  # Annule la transaction en cas d'erreur
#         raise Exception(f"Erreur lors de la suppression de l'invité avec ID {guest_id} : {str(e)}")






















# # # database.py
# # from models import GuestInDB
# # from datetime import datetime, timezone

# # # Base de données simulée
# # guests_db = {}

# # def get_guest_by_id(guest_id: int) -> GuestInDB:
# #     """Récupérer un invité par son ID"""
# #     return guests_db.get(guest_id)

# # def get_all_active_guests() -> list:
# #     """Récupérer tous les invités actifs"""
# #     return [g for g in guests_db.values() if g.is_active]

# # def create_guest(name: str, contact_info: str, details: Optional[str]) -> GuestInDB:
# #     """Créer un nouvel invité"""
# #     guest_id = len(guests_db) + 1  # Génération d'un nouvel ID
# #     new_guest = GuestInDB(
# #         id=guest_id,
# #         name=name,
# #         contact_info=contact_info,
# #         details=details,
# #         is_active=True,
# #         created_at=datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
# #     )
# #     guests_db[guest_id] = new_guest
# #     return new_guest

# # def update_guest(guest_id: int, name: Optional[str], contact_info: Optional[str], details: Optional[str]) -> GuestInDB:
# #     """Mettre à jour un invité existant"""
# #     guest = guests_db.get(guest_id)
# #     if guest:
# #         if name:
# #             guest.name = name
# #         if contact_info:
# #             guest.contact_info = contact_info
# #         if details:
# #             guest.details = details
# #         guest.updated_at = datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
# #         guests_db[guest_id] = guest
# #     return guest

# # def soft_delete_guest(guest_id: int) -> bool:
# #     """Supprimer un invité (soft delete)"""
# #     guest = guests_db.get(guest_id)
# #     if guest:
# #         guest.is_active = False
# #         guest.updated_at = datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime
# #         guests_db[guest_id] = guest
# #         return True
# #     return False










# # from sqlalchemy.orm import Session
# # from app.models.model_guest import Guest
# # from app.schemas.schema_guests import GuestCreate, GuestUpdate

# # def create_guest(db: Session, guest: GuestCreate):
# #     new_guest = Guest(**guest.dict())
# #     db.add(new_guest)
# #     db.commit()
# #     db.refresh(new_guest)
# #     return new_guest

# # def get_guest(db: Session, guest_id: int):
# #     return db.query(Guest).filter(Guest.id == guest_id).first()

# # def update_guest(db: Session, guest_id: int, guest_update: GuestUpdate):
# #     guest = db.query(Guest).filter(Guest.id == guest_id).first()
# #     for key, value in guest_update.dict(exclude_unset=True).items():
# #         setattr(guest, key, value)
# #     db.commit()
# #     db.refresh(guest)
# #     return guest


# crud_guest.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.model_guest import Guest
from app.schemas import GuestCreate, GuestUpdate,GuestResponse
from typing import List
from sqlalchemy import or_
from typing import Dict, Any
from app.models.model_guest import Guest  # Modèle SQLAlchemy pour la table guests
from app.models.model_segment import Segment  # Modèle SQLAlchemy pour la table segments
from app.models.model_show import Show  # Modèle SQLAlchemy pour la table shows
from app.schemas.schema_guests import GuestResponseWithAppearances
from app.exceptions.guest_exceptions import GuestNotFoundException, DatabaseQueryException


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






#///////////////////// pour la recherche //////////////////////////

def search_guest(session: Session, query: str) -> Dict[str, Any]:
    """
    Recherche d'un invité dans la base de données en fonction d'un mot-clé,
    avec gestion des exceptions et codes de réponse.

    :param session: Session SQLAlchemy active.
    :param query: Chaîne de recherche (nom, email, téléphone ou autre).
    :return: Dictionnaire contenant les résultats ou un message d'erreur.
    """
    try:
        # Vérifier si le mot-clé de recherche est vide
        if not query.strip():
            return {
                "status_code": 400,
                "message": "Le mot-clé de recherche ne peut pas être vide."
            }
        
        # Recherche dans la base de données
        results = session.query(Guest).filter(
            Guest.is_deleted == False,  # Exclure les invités supprimés
            or_(
                Guest.name.ilike(f"%{query}%"),       # Recherche par nom
                Guest.email.ilike(f"%{query}%"),      # Recherche par email
                Guest.phone.ilike(f"%{query}%"),      # Recherche par numéro de téléphone
                Guest.role.ilike(f"%{query}%"),       # Recherche par rôle
                Guest.contact_info.ilike(f"%{query}%"),  # Recherche par infos de contact
                Guest.biography.ilike(f"%{query}%")   # Recherche par biographie
            )
        ).all()
        
        # Vérifier si des résultats ont été trouvés
        if not results:
            return {
                "status_code": 404,
                "message": "Aucun invité correspondant trouvé.",
                "data": []
            }
        
        # Structurer les résultats pour la réponse
        guests_data = [
            {
                "id": guest.id,
                "name": guest.name,
                "email": guest.email,
                "phone": guest.phone,
                "role": guest.role,
                "contact_info": guest.contact_info,
                "biography": guest.biography,
                # "created_at": guest.created_at,
                # "updated_at": guest.updated_at,
                # "is_deleted": guest.is_deleted,
                "showSegment_participation": len(guest.segments)

            }
            for guest in results
        ]

        return {
            "status_code": 200,
            "message": "Recherche effectuée avec succès.",
            "data": guests_data
        }

    except SQLAlchemyError as e:
        # Gérer les erreurs liées à SQLAlchemy
        return {
            "status_code": 500,
            "message": f"Erreur interne de la base de données : {str(e)}",
            "data": []
        }

    except Exception as e:
        # Gérer d'autres exceptions
        return {
            "status_code": 500,
            "message": f"Une erreur inattendue s'est produite : {str(e)}",
            "data": []
        }





# /////////////////////// service pour recuperer un invite avec ses detailles/////////////////

# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from typing import List





class GuestService:
    """Service contenant la logique métier pour la gestion des invités."""

    @staticmethod
    def get_guest_by_id_allinfo(db: Session, guest_id: int) -> Guest:
        """
        Récupère un invité par son ID depuis la base de données.
        
        Args:
            db (Session): Session SQLAlchemy pour interagir avec la DB.
            guest_id (int): Identifiant de l'invité à récupérer.
        
        Returns:
            Guest: Objet Guest correspondant à l'invité trouvé.
        
        Raises:
            GuestNotFoundException: Si l'invité n'existe pas ou est supprimé.
            DatabaseQueryException: En cas d'erreur lors de la requête SQL.
        """
        try:
            guest = db.query(Guest).filter(
                Guest.id == guest_id,
                Guest.is_deleted.is_(False)  # Exclut les invités marqués comme supprimés
            ).first()
            if not guest:
                raise GuestNotFoundException(guest_id)
            return guest
        except SQLAlchemyError as e:
            raise DatabaseQueryException(f"Erreur lors de la récupération de l'invité: {str(e)}")

    @staticmethod
    def get_guest_appearances(db: Session, guest_id: int) -> List[Show]:
        """
        Récupère la liste des émissions auxquelles un invité a participé.
        
        Args:
            db (Session): Session SQLAlchemy pour interagir avec la DB.
            guest_id (int): Identifiant de l'invité.
        
        Returns:
            List[Show]: Liste des objets Show représentant les émissions.
        
        Raises:
            DatabaseQueryException: En cas d'erreur lors de la requête SQL.
        """
        try:
            # Jointure entre Show, Segment et la relation many-to-many segment_guests
            appearances = (
                db.query(Show)
                .join(Segment, Show.id == Segment.show_id)
                .join(Segment.guests)  # Relation many-to-many avec Guest
                .filter(Segment.guests.any(id=guest_id))
                .all()
            )
            return appearances
        except SQLAlchemyError as e:
            raise DatabaseQueryException(f"Erreur lors de la récupération des participations: {str(e)}")

    @staticmethod
    def build_guest_response(guest: Guest, appearances: List[Show]) -> GuestResponseWithAppearances:
        """
        Construit une réponse structurée avec les détails de l'invité et ses participations.
        
        Args:
            guest (Guest): Objet Guest contenant les informations de base.
            appearances (List[Show]): Liste des émissions associées.
        
        Returns:
            GuestResponseWithAppearances: Réponse formatée pour l'API, incluant l'ID du conducteur.
        """
        return GuestResponseWithAppearances(
            id=guest.id,
            name=guest.name,
            role=guest.role,
            avatar=guest.avatar,
            created_at=guest.created_at,
            biography=guest.biography,
            contact_info=guest.contact_info,
            
            contact={
                "email": guest.email,
                "phone": guest.phone
            },
            appearances=[
                {
                    "show_id": show.id,  # Ajout de l'ID du conducteur
                    "show_title": show.title,
                    "broadcast_date": show.broadcast_date
                }
                for show in appearances
                if show.broadcast_date  # Exclut les émissions sans date de diffusion
            ]
        )
    
    @staticmethod
    def search_guest_detailed(db: Session, query: str) -> Dict[str, Any]:
        """
        Recherche des invités dans la base de données en fonction d'un mot-clé.
        
        Args:
            db (Session): Session SQLAlchemy pour interagir avec la DB.
            query (str): Chaîne de recherche (nom, email, téléphone, rôle, etc.).
        
        Returns:
            Dict[str, Any]: Dictionnaire contenant le statut, un message et les résultats formatés.
        
        Raises:
            DatabaseQueryException: En cas d'erreur lors de la requête SQL.
        """
        try:
            # Vérifier si le mot-clé de recherche est vide
            if not query.strip():
                return {
                    "status_code": 400,
                    "message": "Le mot-clé de recherche ne peut pas être vide.",
                    "data": []
                }

            # Recherche dans la base de données avec filtrage insensible à la casse
            results = db.query(Guest).filter(
                Guest.is_deleted.is_(False),
                or_(
                    Guest.name.ilike(f"%{query}%"),
                    Guest.email.ilike(f"%{query}%"),
                    Guest.phone.ilike(f"%{query}%"),
                    Guest.role.ilike(f"%{query}%"),
                    Guest.contact_info.ilike(f"%{query}%"),
                    Guest.biography.ilike(f"%{query}%")
                )
            ).all()

            # Vérifier si des résultats ont été trouvés
            if not results:
                return {
                    "status_code": 404,
                    "message": "Aucun invité correspondant trouvé.",
                    "data": []
                }

            # Structurer les résultats avec les participations
            guests_data = []
            for guest in results:
                appearances = GuestService.get_guest_appearances(db, guest.id)
                guest_response = GuestService.build_guest_response(guest, appearances)
                guests_data.append(guest_response)

            return {
                "status_code": 200,
                "message": "Recherche effectuée avec succès.",
                "data": guests_data
            }

        except SQLAlchemyError as e:
            raise DatabaseQueryException(f"Erreur interne de la base de données : {str(e)}")
        except Exception as e:
            raise DatabaseQueryException(f"Une erreur inattendue s'est produite : {str(e)}")
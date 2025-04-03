from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.models import Emission
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from app.schemas.schema_emission import EmissionCreate, EmissionResponse  # Importez les classes de validation Pydantic

# Créer une émission (Create)
def create_emission(db: Session, emission_create: EmissionCreate) -> EmissionResponse:
    """
    Fonction pour créer une nouvelle émission dans la base de données.
    Elle prend les données de l'émission envoyées par l'utilisateur (via EmissionCreate),
    les valide et les insère dans la base de données.
    """
    try:
        # Créer un objet Emission à partir des données envoyées dans EmissionCreate
        new_emission = Emission(
            title=emission_create.title,  # Titre de l'émission
            synopsis=emission_create.synopsis,  # Synopsis de l'émission (peut être vide)
            created_at=datetime.now(timezone.utc),  # Date et heure de création (UTC)
            type=emission_create.type if hasattr(emission_create, 'type') else None,  # Optionnel
            duration=emission_create.duration if hasattr(emission_create, 'duration') else None,  # Optionnel
            frequency=emission_create.frequency if hasattr(emission_create, 'frequency') else None,  # Optionnel
            description=emission_create.description if hasattr(emission_create, 'description') else None  # Optionnel
        )
        
        # Ajouter l'objet Emission à la session de base de données
        db.add(new_emission)
        
        # Commit la transaction pour sauvegarder l'émission dans la base de données
        db.commit()
        
        # Rafraîchir l'objet pour obtenir les dernières valeurs après le commit
        db.refresh(new_emission)
        
        # Retourner la nouvelle émission au format de réponse Pydantic
        return EmissionResponse.from_orm(new_emission)
    
    except SQLAlchemyError as e:
        db.rollback()  # Annuler la transaction en cas d'erreur SQL
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la création de l'émission: {str(e)}"
        )
    except ValidationError as e:
        # Si une erreur de validation survient lors de la création, on lève une exception HTTP 422
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de validation des données: {str(e)}"
        )


# Lire toutes les émissions (Read)
def get_emissions(db: Session, skip: int = 0, limit: int = 10) -> list[EmissionResponse]:
    """
    Fonction pour récupérer une liste d'émissions depuis la base de données.
    Elle renvoie les émissions paginées selon les paramètres `skip` et `limit`.
    """
    try:
        # # Interroger la base de données pour récupérer les émissions avec un décalage (skip) et une limite (limit)
        # emissions = db.query(Emission).offset(skip).limit(limit).all()
    # Interroger la base de données pour récupérer les émissions non supprimées
        # avec un décalage (skip) et une limite (limit)
        emissions = db.query(Emission).filter(Emission.is_deleted == False).offset(skip).limit(limit).all()
        
        # Retourner les émissions sous forme de liste d'objets Pydantic
        return [EmissionResponse.from_orm(emission) for emission in emissions]
    
    except SQLAlchemyError as e:
        # En cas d'erreur SQL, on lève une exception HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des émissions: {str(e)}"
        )


# Lire une émission par son ID (Read)
def get_emission_by_id(db: Session, emission_id: int) -> EmissionResponse:
    """
    Fonction pour récupérer une émission spécifique en utilisant son ID.
    Si l'émission n'est pas trouvée, une exception HTTP 404 est levée.
    """
    try:
        # Rechercher l'émission dans la base de données par son ID
        emission = db.query(Emission).filter(Emission.id == emission_id).first()
        
        # Si l'émission n'existe pas, on lève une exception HTTP 404
        if not emission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Émission non trouvée"
            )
        
        # Retourner l'émission trouvée sous forme de réponse Pydantic
        return EmissionResponse.from_orm(emission)
    
    except SQLAlchemyError as e:
        # En cas d'erreur SQL, on lève une exception HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'émission: {str(e)}"
        )


# Mettre à jour une émission (Update)
def update_emission(db: Session, emission_id: int, emission_update: EmissionCreate) -> EmissionResponse:
    """
    Fonction pour mettre à jour une émission existante avec les nouvelles informations.
    Les champs qui ne sont pas fournis ne seront pas modifiés.
    """
    try:
        # Chercher l'émission dans la base de données par son ID
        emission = db.query(Emission).filter(Emission.id == emission_id).first()
        
        # Si l'émission n'existe pas, on lève une exception HTTP 404
        if not emission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Émission non trouvée"

            )
        

        # Appliquer les modifications, si elles sont fournies
        if emission_update.title:
            emission.title = emission_update.title
        if emission_update.synopsis:
            emission.synopsis = emission_update.synopsis
        if emission_update.type:
            emission.type = emission_update.type
        if emission_update.duration:
            emission.duration = emission_update.duration       
        if emission_update.frequency:
            emission.frequency = emission_update.frequency
        if emission_update.description:
            emission.description = emission_update.description 
        # Enregistrer les modifications dans la base de données
        db.commit()
        
        # Rafraîchir l'objet pour obtenir les dernières valeurs après le commit
        db.refresh(emission)
        
        # Retourner l'émission mise à jour au format de réponse Pydantic
        return EmissionResponse.from_orm(emission)
    
    except SQLAlchemyError as e:
        db.rollback()  # Annuler la transaction en cas d'erreur SQL
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la mise à jour de l'émission: {str(e)}"
        )


# Supprimer une émission (Delete)
def delete_emission(db: Session, emission_id: int) -> bool:
    """
    Fonction pour supprimer une émission de la base de données.
    Si l'émission n'existe pas, une exception HTTP 404 est levée.
    """
    try:
        # Rechercher l'émission dans la base de données par son ID
        emission = db.query(Emission).filter(Emission.id == emission_id).first()
        
        # Si l'émission n'existe pas, on lève une exception HTTP 404
        if not emission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Émission non trouvée"
            )
        
        # Supprimer l'émission de la base de données
        db.delete(emission)
        db.commit()  # Valider la suppression
        
        return True  # Retourner True pour indiquer que la suppression a réussi
    
    except SQLAlchemyError as e:
        db.rollback()  # Annuler la transaction en cas d'erreur SQL
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression de l'émission: {str(e)}"
        )


# Supprimer une émission (soft delete)
def soft_delete_emission(db: Session, emission_id: int) -> bool:
    """
    Fonction pour effectuer une suppression douce (soft delete) d'une émission.
    Cela marque l'émission comme supprimée sans la retirer physiquement de la base de données.
    """
    try:
        # Rechercher l'émission dans la base de données par son ID
        emission = db.query(Emission).filter(Emission.id == emission_id).first()
        
        # Si l'émission n'existe pas, on lève une exception HTTP 404
        if not emission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Émission non trouvée"
            )
        
        # Mettre à jour les attributs pour indiquer une suppression douce
        emission.is_deleted = True
        emission.deleted_at = datetime.utcnow()  # Date et heure de la suppression douce
        
        db.commit()  # Sauvegarder les modifications
        db.refresh(emission)  # Rafraîchir l'objet pour obtenir les nouvelles valeurs
        
        return True  # Retourner True pour indiquer que la suppression douce a réussi
    
    except SQLAlchemyError as e:
        db.rollback()  # Annuler la transaction en cas d'erreur SQL
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression douce de l'émission: {str(e)}"
        )

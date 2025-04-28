
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Segment
from app.schemas import SegmentCreate, SegmentUpdate
from fastapi import HTTPException

# Créer un segment
def create_segment(db: Session, segment: SegmentCreate):
    try:
        # Calculate the new position for the segment
        max_position_result = db.query(func.max(Segment.position)).scalar()
        new_position = (max_position_result + 1) if max_position_result is not None else 1

        # Prepare data, excluding 'position' if present in input schema
        # Use model_dump() instead of deprecated dict()
        segment_data = segment.model_dump()
        # Remove position from input data as we calculate it server-side
        segment_data.pop('position', None)

        # Create the new segment with the calculated position
        new_segment = Segment(**segment_data, position=new_position)

        db.add(new_segment)
        db.commit()
        db.refresh(new_segment)
        return new_segment
    except Exception as e:
        db.rollback()
        # Provide more context in the error if possible
        print(f"Error creating segment: {e}") # Add logging
        raise HTTPException(status_code=500, detail=f"Failed to create segment: {str(e)}")

# def create_segment(db: Session, segment: SegmentCreate):
#     try:
#         # Insérer le segment à la position la plus haute
#         # max_position = db.query(Segment.position).filter(Segment.is_deleted == False).order_by(Segment.position.desc()).first()
#         max_position = db.query(Segment.position).order_by(Segment.position.desc()).first()
#         new_position = (max_position[0] + 1) if max_position else 1
#         new_segment = Segment(**segment.dict(), position=new_position)
        
#         db.add(new_segment)
#         db.commit()
#         db.refresh(new_segment)
#         return new_segment
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create segment: {str(e)}")

# Récupérer tous les segments
def get_segments(db: Session):
    try:
        return db.query(Segment).order_by(Segment.position).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve segments: {str(e)}")

# Récupérer un segment par ID
# Récupérer un segment par ID (CORRECTED)
def get_segment_by_id(db: Session, segment_id: int):
    """
    Récupère un segment actif (non supprimé logiquement) par son ID.
    """
    try:
        # AJOUTER le filtre is_deleted == False
        segment = db.query(Segment).filter(
            Segment.id == segment_id,
        ).first()

        # Maintenant, si le segment existe mais is_deleted=True,
        # la requête retournera None, et ce check lèvera le 404 attendu.
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        return segment
    except HTTPException as http_exc:
        # Relayer les exceptions HTTP spécifiques (comme le 404 ci-dessus)
        raise http_exc
    except Exception as e:
        # Logguer l'erreur est une bonne pratique ici
        print(f"Unexpected error in get_segment_by_id for ID {segment_id}: {e}")
        # Retourner 500 pour les erreurs inattendues (DB down, etc.)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve segment: {str(e)}")
# def get_segment_by_id(db: Session, segment_id: int):
#     try:
#         segment = db.query(Segment).filter(Segment.id == segment_id).first()
#         if not segment:
#             raise HTTPException(status_code=404, detail="Segment not found")
#         return segment
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve segment: {str(e)}")

# Modifier un segment
# Fix update_segment to use model_dump()
def update_segment(db: Session, db_segment: Segment, segment: SegmentUpdate):
    try:
        # Use model_dump() instead of dict()
        update_data = segment.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_segment, key, value)
        db.commit()
        db.refresh(db_segment)
        return db_segment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update segment: {str(e)}")
# def update_segment(db: Session, db_segment: Segment, segment: SegmentUpdate):
#     try:
#         for key, value in segment.dict(exclude_unset=True).items():
#             setattr(db_segment, key, value)
#         db.commit()
#         db.refresh(db_segment)
#         return db_segment
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to update segment: {str(e)}")

# Modifier la position d'un segment
def update_segment_position(db: Session, db_segment: Segment, position: int):
    try:
        # Réorganiser les positions des autres segments si nécessaire
        active_segments = db.query(Segment).order_by(Segment.position).all()
        if db_segment.position != position:
            # Si la position a changé, réorganiser les autres segments
            reorganize_positions(db, db_segment, position)

        db_segment.position = position
        db.commit()
        db.refresh(db_segment)
        return db_segment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update position: {str(e)}")

# Réorganiser les positions des segments
def reorganize_positions(db: Session, db_segment: Segment, new_position: int):
    """
    Réorganise les positions des segments actifs pour maintenir la continuité.
    """
    active_segments = (
        db.query(Segment)
        .order_by(Segment.position)
        .all()
    )

    # Réattribuer les positions séquentiellement
    for index, segment in enumerate(active_segments):
        if segment.id == db_segment.id:
            continue
        if segment.position >= new_position:
            segment.position += 1
        db.commit()

# Suppression (soft delete) d'un segment
def soft_delete_segment(db: Session, db_segment: Segment):
    try:
        # Étape 1: Marquer le segment comme supprimé
        # db_segment.is_deleted = True
        # db.commit()
        db.delete(db_segment) # Marquer pour suppression
        db.commit() 
        
        # Étape 2: Réorganiser les positions
        reorganize_positions(db, db_segment, db_segment.position)

        return {"message": "Segment deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete segment: {str(e)}")























# from sqlalchemy.exc import SQLAlchemyError  # Pour gérer les erreurs SQLAlchemy
# from fastapi import HTTPException, status  # Pour lever des erreurs HTTP en cas de problème
# from sqlalchemy.orm import Session
# from app.schemas import SegmentCreate, SegmentUpdate  # Importer les modèles Pydantic
# from app.models import Segment,SegmentGuest
# from typing import List









# def create_segment(db: Session, segment_data: SegmentCreate) -> Segment:
#     """
#     Crée un nouveau segment pour une émission.
    
#     - Si la position n'est pas fournie, elle est automatiquement définie comme la dernière disponible.
#     - Gère les erreurs liées à la base de données avec un rollback.
#     """
#     try:
#         # Calcul automatique de la position si elle n'est pas fournie ou est égale à 0
#         if segment_data.position is None or segment_data.position == 0:
#             last_position = (
#                 db.query(Segment)  # Requête pour trouver le dernier segment de l'émission
#                 .filter(Segment.show_id == segment_data.show_id)
#                 .order_by(Segment.position.desc())  # Trier par position décroissante
#                 .first()  # Prendre le dernier segment
#             )
#             # Définir la nouvelle position : dernière position + 1 ou 1 s'il n'y a aucun segment
#             segment_data.position = (last_position.position + 1) if last_position else 1

#         # Créer l'objet Segment avec les données fournies
#         segment = Segment(**segment_data.dict())
#         db.add(segment)  # Ajouter le segment à la session
#         db.commit()  # Confirmer les modifications dans la base de données
#         db.refresh(segment)  # Actualiser l'objet pour récupérer les données sauvegardées
#         return segment

#     except SQLAlchemyError as e:  # Gestion des erreurs de la base de données
#         db.rollback()  # Annuler toutes les modifications si une erreur survient
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la création du segment : {str(e)}"
#         )




# def update_segment(db: Session, segment_id: int, segment_data: SegmentUpdate) -> Segment:
#     """
#     Met à jour un segment existant.
    
#     - Vérifie si le segment existe avant de le modifier.
#     - Réorganise les positions si la position d'un segment est modifiée.
#     - Gère les erreurs avec des exceptions et un rollback en cas de problème.
#     """
#     try:
#         # Vérifier si le segment existe
#         segment = db.query(Segment).filter(Segment.id == segment_id).first()
#         if not segment:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Segment avec l'ID {segment_id} introuvable"
#             )

#         # Réorganisation des positions si la nouvelle position diffère de l'ancienne
#         if segment_data.position and segment_data.position != segment.position:
#             if segment_data.position > segment.position:
#                 # Si la nouvelle position est plus grande, décrémenter les positions intermédiaires
#                 db.query(Segment).filter(
#                     Segment.show_id == segment.show_id,
#                     Segment.position > segment.position,
#                     Segment.position <= segment_data.position,
#                 ).update({Segment.position: Segment.position - 1}, synchronize_session=False)
#             else:
#                 # Si la nouvelle position est plus petite, incrémenter les positions intermédiaires
#                 db.query(Segment).filter(
#                     Segment.show_id == segment.show_id,
#                     Segment.position < segment.position,
#                     Segment.position >= segment_data.position,
#                 ).update({Segment.position: Segment.position + 1}, synchronize_session=False)
#             segment.position = segment_data.position  # Mettre à jour la position du segment
            


#         # Mise à jour des invités associés
#         if segment_data.guests is not None:
#             db.query(SegmentGuest).filter(SegmentGuest.segment_id == segment_id).delete()
#             for guest_id in segment_data.guests:
#                 segment_guest = SegmentGuest(segment_id=segment_id, guest_id=guest_id)
#                 db.add(segment_guest)

#         # Mise à jour des autres champs du segment
#         for key, value in segment_data.dict(exclude_unset=True).items():
#             setattr(segment, key, value)  # Modifier les attributs du segment

#         db.commit()  # Confirmer les modifications dans la base de données
#         db.refresh(segment)  # Actualiser l'objet pour récupérer les modifications
#         return segment

#     except SQLAlchemyError as e:  # Gestion des erreurs SQLAlchemy
#         db.rollback()  # Annuler les modifications en cas d'erreur
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la mise à jour du segment : {str(e)}"
#         )





# def delete_segment(db: Session, segment_id: int) -> None:
#     """
#     Supprime un segment existant.
    
#     - Vérifie si le segment existe avant de le supprimer.
#     - Réorganise les positions des autres segments après la suppression.
#     """
#     try:
#         # Vérifier si le segment existe
#         segment = db.query(Segment).filter(Segment.id == segment_id).first()
#         if not segment:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Segment avec l'ID {segment_id} introuvable"
#             )

#         # Réorganiser les positions des segments restants
#         db.query(Segment).filter(
#             Segment.show_id == segment.show_id,
#             Segment.position > segment.position  # Affecte les segments après celui supprimé
#         ).update({Segment.position: Segment.position - 1}, synchronize_session=False)

#         db.delete(segment)  # Supprimer le segment
#         db.commit()  # Confirmer les modifications dans la base de données

#     except SQLAlchemyError as e:  # Gestion des erreurs SQLAlchemy
#         db.rollback()  # Annuler les modifications en cas d'erreur
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la suppression du segment : {str(e)}"
#         )




# def get_segments_by_show(db: Session, show_id: int) -> List[SegmentCreate]:
#     """
#     Récupère tous les segments d'une émission donnée, triés par position.
    
#     - Renvoie une erreur 404 si aucun segment n'est trouvé.
#     """
#     try:
#         # Récupérer tous les segments pour une émission spécifique
#         segments = (
#             db.query(Segment)
#             .filter(Segment.show_id == show_id)
#             .order_by(Segment.position.asc())  # Trier par position ascendante
#             .all()
#         )
#         if not segments:  # Si aucun segment n'est trouvé, lever une erreur
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Aucun segment trouvé pour l'émission avec l'ID {show_id}"
#             )
#         return segments

#     except SQLAlchemyError as e:  # Gestion des erreurs SQLAlchemy
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la récupération des segments : {str(e)}"
#         )





# def get_segment_by_id(db: Session, segment_id: int) -> Segment:
#     """
#     Récupère un segment spécifique par son ID.
    
#     - Renvoie une erreur 404 si aucun segment n'est trouvé.
#     """
#     try:
#         # Récupérer le segment spécifique par son ID
#         segment = db.query(Segment).filter(Segment.id == segment_id).first()
        
#         # Si aucun segment n'est trouvé, lever une erreur 404
#         if not segment:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Segment avec l'ID {segment_id} introuvable"
#             )
#         return segment
    
#     except SQLAlchemyError as e:  # Gestion des erreurs SQLAlchemy
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la récupération du segment : {str(e)}"
#         )
    


# def get_all_segments(db: Session) -> List[Segment]:
#     """
#     Récupère tous les segments présents dans la base de données.
    
#     - Renvoie une erreur 404 si aucun segment n'est trouvé.
#     """
#     try:
#         # Récupérer tous les segments
#         segments = db.query(Segment).all()
        
#         # Vérifier si des segments ont été trouvés
#         if not segments:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Aucun segment trouvé dans la base de données"
#             )
#         return segments

#     except SQLAlchemyError as e:  # Gestion des erreurs SQLAlchemy
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la récupération des segments : {str(e)}"
#         )



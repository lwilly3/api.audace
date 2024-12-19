# from datetime import datetime
# from typing import List, Optional
# from sqlalchemy.orm import Session
# from app.models.model_presenter_history import PresenterHistory
# from app.schemas.schema_presenter_history import PresenterHistoryCreate
# from fastapi import HTTPException, status, Depends
# from app.db.database import get_db
# from core.auth import oauth2

# def create_presenter_history(db: Session, history: PresenterHistoryCreate):
#     """
#     Créer un nouvel historique de présentateur dans la base de données.
    
#     Args:
#     - db (Session): La session de la base de données.
#     - history (PresenterHistoryCreate): Les données de l'historique du présentateur à ajouter.
    
#     Returns:
#     - PresenterHistory: Le nouvel historique du présentateur créé.
#     """
#     try:
#         # Création d'un nouvel objet PresenterHistory à partir des données de l'historique
#         new_history = PresenterHistory(**history.model_dump())
        
#         # Ajout de l'objet à la session de la base de données
#         db.add(new_history)
        
#         # Validation des changements dans la base de données
#         db.commit()
        
#         # Récupération des données actualisées de l'historique du présentateur après commit
#         db.refresh(new_history)
        
#         # Retour de l'objet PresenterHistory nouvellement créé
#         return new_history
    
#     except Exception as e:
#         # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error creating presenter history: {str(e)}"
#         )




# # Fonction pour rechercher l'historique d'un présentateur
# def search_presenter_history(
#     presenter_id: Optional[int] = None,  # ID du présentateur (optionnel)
#     updated_by: Optional[int] = None,  # ID de l'utilisateur ayant effectué la modification (optionnel)
#     date: Optional[datetime] = None,  # Date spécifique pour filtrer l'historique (optionnel)
#     db: Session = Depends(get_db)  # Session de base de données
# ) -> List[PresenterHistory]:
#     """Rechercher l'historique des modifications d'un présentateur"""
#     try:
#         # Construire la requête de base
#         query = db.query(PresenterHistory)

#         # Ajouter des filtres optionnels
#         if presenter_id:
#             query = query.filter(PresenterHistory.presenter_id == presenter_id)
#         if updated_by:
#             query = query.filter(PresenterHistory.updated_by == updated_by)
#         if date:
#             query = query.filter(PresenterHistory.updated_at.date() == date.date())

#         # Exécuter la requête
#         history = query.all()

#         # Retourner les résultats
#         return history
#     except Exception as e:
#         # En cas d'erreur, lever une exception 500
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching presenter history: {str(e)}"
#         )







# # from sqlalchemy.orm import Session
# # from app.models.model_presenter_history import PresenterHistory
# # from app.schemas.schema_presenter_history import PresenterHistoryCreate

# # def create_presenter_history(db: Session, history: PresenterHistoryCreate):
# #     new_history = PresenterHistory(**history.model_dump())
# #     db.add(new_history)
# #     db.commit()
# #     db.refresh(new_history)
# #     return new_history

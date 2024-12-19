
# # routes.py
# from fastapi import APIRouter, HTTPException, Depends
# from typing import List, Optional
# from datetime import datetime
# from app.schemas import PresenterHistory
# from app.db.crud.crud_presenter_history import search_presenter_history
# from app.db.database import get_db
# from sqlalchemy.orm import Session


# router = APIRouter()

# # Route pour rechercher l'historique des présentateurs
# @router.get("/presenter-history/search", response_model=List[PresenterHistory])
# def search_presenter_history_route(
#     presenter_id: Optional[int] = None,
#     updated_by: Optional[int] = None,
#     date: Optional[datetime] = None,
#     db: Session = Depends(get_db)
# ):
#     """
#     Rechercher l'historique des modifications d'un présentateur par ID, utilisateur, ou date.
#     """
#     filtered_history = search_presenter_history(presenter_id, updated_by, date, db=db)

#     if not filtered_history:
#         raise HTTPException(status_code=404, detail="No presenter history found matching the search criteria")

#     return filtered_history

















# # from fastapi import FastAPI, HTTPException, Query
# # from typing import List, Optional
# # from pydantic import BaseModel
# # from datetime import datetime

# # app = FastAPI()

# # # Simulated database of presenter history (modifications)
# # presenter_history_db = [
# #     {"id": 1, "presenter_id": 1, "updated_by": 101, "update_date": datetime(2024, 5, 10), "changes": "Updated biography."},
# #     {"id": 2, "presenter_id": 2, "updated_by": 102, "update_date": datetime(2024, 5, 12), "changes": "Updated contact details."},
# #     {"id": 3, "presenter_id": 1, "updated_by": 101, "update_date": datetime(2024, 6, 5), "changes": "Changed profile picture."},
# # ]

# # # Models
# # class PresenterHistory(BaseModel):
# #     """
# #     Modèle pour représenter l'historique des modifications d'un présentateur.
# #     """
# #     id: int
# #     presenter_id: int
# #     updated_by: int
# #     update_date: datetime
# #     changes: str

# # # Route pour rechercher l'historique des modifications d'un présentateur
# # @app.get("/presenter-history/search", response_model=List[PresenterHistory])
# # def search_presenter_history(presenter_id: Optional[int] = None, updated_by: Optional[int] = None, date: Optional[datetime] = None):
# #     """
# #     Rechercher l'historique des modifications d'un présentateur par ID, utilisateur, ou date.
# #     """
# #     filtered_history = []

# #     for history in presenter_history_db:
# #         if (presenter_id is None or presenter_id == history["presenter_id"]) and \
# #            (updated_by is None or updated_by == history["updated_by"]) and \
# #            (date is None or date.date() == history["update_date"].date()):
# #             filtered_history.append(history)

# #     # Si aucun historique n'est trouvé
# #     if not filtered_history:
# #         raise HTTPException(status_code=404, detail="No presenter history found matching the search criteria")

# #     # Retourner les résultats
# #     return filtered_history


# routes.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db.crud.crud_search_user import search_users
from app.schemas import UserRead
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/users/search", response_model=List[UserRead])
def search_users_route(name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None):
    """
    Rechercher des utilisateurs par nom, email ou rôle.
    La recherche peut être effectuée sur un ou plusieurs critères à la fois.
    """
    filtered_users = search_users(name, email, role)

    if not filtered_users:
        raise HTTPException(status_code=404, detail="No users found matching the search criteria")
    
    return filtered_users






# from fastapi import FastAPI, HTTPException, Query
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# app = FastAPI()

# # Simulated database of guests
# guests_db = [
#     {"id": 1, "name": "John Doe", "biography": "A famous presenter from the 90s.", "dob": datetime(1985, 5, 10)},
#     {"id": 2, "name": "Jane Smith", "biography": "A renowned scientist and guest speaker.", "dob": datetime(1990, 7, 22)},
#     {"id": 3, "name": "Alice Johnson", "biography": "A well-known celebrity with a rich history in television.", "dob": datetime(1980, 3, 15)},
# ]

# # Models
# class Guest(BaseModel):
#     """
#     Modèle pour représenter un invité.
#     """
#     id: int
#     name: str
#     biography: str
#     dob: datetime

# # Route pour rechercher des invités par nom ou biographie
# @app.get("/guests/search", response_model=List[Guest])
# def search_guests(name: Optional[str] = None, biography: Optional[str] = None):
#     """
#     Rechercher des invités par nom ou biographie.
#     La recherche peut être effectuée sur un ou plusieurs critères à la fois.
#     """
#     filtered_guests = []

#     for guest in guests_db:
#         if (name is None or name.lower() in guest["name"].lower()) and \
#            (biography is None or biography.lower() in guest["biography"].lower()):
#             filtered_guests.append(guest)

#     # Si aucun invité n'est trouvé
#     if not filtered_guests:
#         raise HTTPException(status_code=404, detail="No guests found matching the search criteria")

#     # Retourner les résultats
#     return filtered_guests

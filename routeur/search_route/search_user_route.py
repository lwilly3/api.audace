
# routes.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.schemas import UserRead
from app.db.crud.crud_search_user import search_users

router = APIRouter()

@router.get("/users/search", response_model=List[UserRead])
def search_users_route(name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None):
    """
    Rechercher des utilisateurs par nom, email ou rôle.
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

# # Simulated database of users
# users_db = [
#     {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "created_at": datetime.now()},
#     {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "created_at": datetime.now()},
#     {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "moderator", "created_at": datetime.now()},
# ]

# # Models
# class User(BaseModel):
#     """
#     Modèle pour représenter un utilisateur.
#     """
#     id: int
#     name: str
#     email: str
#     role: str
#     created_at: datetime


# # Route pour rechercher des utilisateurs
# @app.get("/users/search", response_model=List[User])
# def search_users(name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None):
#     """
#     Rechercher des utilisateurs par nom, email ou rôle.
#     La recherche peut être effectuée sur un ou plusieurs critères à la fois.
#     """
#     filtered_users = []
    
#     for user in users_db:
#         if (name and name.lower() in user["name"].lower()) or \
#            (email and email.lower() in user["email"].lower()) or \
#            (role and role.lower() in user["role"].lower()):
#             filtered_users.append(user)

#     # Si aucun utilisateur n'est trouvé
#     if not filtered_users:
#         raise HTTPException(status_code=404, detail="No users found matching the search criteria")

#     # Retourner les résultats
#     return filtered_users

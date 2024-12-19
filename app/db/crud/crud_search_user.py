
from typing import List, Optional
from app.models import User
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base




def search_users(db: Session, name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None) -> List[User]:
    """
    Rechercher des utilisateurs par nom, email ou rôle dans la base de données.
    La recherche peut être effectuée sur un ou plusieurs critères à la fois.
    """
    try:
        query = db.query(User)  # Commencez avec une requête pour récupérer des utilisateurs
        if name:
            query = query.filter(User.username.ilike(f"%{name}%"))  # Recherche insensible à la casse pour le nom
        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))  # Recherche insensible à la casse pour l'email
        if role:
            query = query.filter(User.role == role)  # Filtre sur le rôle exact

        return query.all()  # Exécute la requête et retourne la liste des utilisateurs trouvés
    except exc.SQLAlchemyError as e:
        # Gestion des erreurs liées à SQLAlchemy
        print(f"Erreur lors de la recherche des utilisateurs : {e}")
        db.rollback()  # Annule la transaction en cas d'erreur
        return []

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Récupère un utilisateur par son ID.
    """
    try:
        return db.query(User).filter(User.id == user_id).first()
    except exc.SQLAlchemyError as e:
        # Gestion des erreurs liées à SQLAlchemy
        print(f"Erreur lors de la récupération de l'utilisateur avec l'ID {user_id}: {e}")
        db.rollback()  # Annule la transaction en cas d'erreur
        return None

def create_user(db: Session, username: str, email: str, password_hash: str, role: str) -> Optional[User]:
    """
    Crée un nouvel utilisateur dans la base de données.
    """
    try:
        db_user = User(username=username, email=email, password_hash=password_hash, role=role, created_at=datetime.now())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # Rafraîchit l'instance de l'utilisateur pour y inclure l'ID généré
        return db_user
    except exc.SQLAlchemyError as e:
        # Gestion des erreurs liées à SQLAlchemy
        print(f"Erreur lors de la création de l'utilisateur : {e}")
        db.rollback()  # Annule la transaction en cas d'erreur
        return None

# # Exemple d'initialisation de la session SQLAlchemy
# def get_db():
#     db = Session(bind=engine)
#     try:
#         yield db
#     finally:
#         db.close()
















# # database.py
# from typing import List, Optional
# from models import User
# from datetime import datetime

# # Base de données simulée des utilisateurs
# users_db = [
#     {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "created_at": datetime.now()},
#     {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "created_at": datetime.now()},
#     {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "moderator", "created_at": datetime.now()},
# ]

# def search_users(name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None) -> List[dict]:
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
    
#     return filtered_users

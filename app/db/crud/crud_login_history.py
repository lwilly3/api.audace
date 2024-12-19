# from sqlalchemy.orm import Session
from app.models.model_login_history import LoginHistory
from app.schemas.schema_login_history import LoginHistoryCreate
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import  HTTPException,  status, Depends



# CRUD pour l'historique des connexions
def create_login_history(db: Session, login: LoginHistoryCreate) -> LoginHistory:
    """Créer un enregistrement dans l'historique des connexions"""
    try:
        new_login = LoginHistory(**login.model_dump())  # Conversion du schéma en modèle
        db.add(new_login)
        db.commit()
        db.refresh(new_login)
        return new_login
    except SQLAlchemyError as e:
        db.rollback()  # Annule la transaction en cas d'erreur
        raise Exception(f"Erreur lors de la création de l'historique des connexions : {str(e)}")

def get_user_login_history(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> list:
    """Récupérer l'historique des connexions d'un utilisateur"""
    try:
        return db.query(LoginHistory).filter(LoginHistory.user_id == user_id).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération de l'historique des connexions pour l'utilisateur {user_id} : {str(e)}")





# from sqlalchemy.orm import Session
# from app.models.model_login_history import LoginHistory
# from app.schemas.schema_login_history import LoginHistoryCreate

# def create_login_history(db: Session, login: LoginHistoryCreate):
#     new_login = LoginHistory(**login.model_dump())
#     db.add(new_login)
#     db.commit()
#     db.refresh(new_login)
#     return new_login

# def get_user_login_history(db: Session, user_id: int, skip: int = 0, limit: int = 10):
#     return db.query(LoginHistory).filter(LoginHistory.user_id == user_id).offset(skip).limit(limit).all()

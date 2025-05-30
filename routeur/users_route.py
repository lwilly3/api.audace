import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
# from app.models import UserInDB, LoginLog, Notification, AuditLog
from app.schemas import UserRead, UserInDB, LoginHistoryRead, NotificationRead, AuditLog,UserLogin,UserBase,UserCreate, UserWithPermissionsResponse,UserUpdate,UserSrearchResponse
from app.models import Role, UserRole, Permission,RolePermission
from app.utils import utils
from core.auth import oauth2
from fastapi import Response


from app.db.crud.crud_users import (
    get_user_or_404,
    get_all_users,
    create_user,
    update_user,
    delete_user,
    get_user_logins,
    get_user_notifications,
    get_user_audit_logs,
    get_user_or_404_with_permissions,
    get_non_presenters
)
from app.db.database import get_db
# from app.db.init_db_rolePermissions import create_default_role_and_permission

router = APIRouter(
        prefix="/users",
     tags=['USERS']
)

logger = logging.getLogger(__name__)


@router.get("/non-presenters")
def get_non_presenters_route(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Récupérer la liste des utilisateurs qui ne sont pas des présentateurs.

    Args:
        db (Session): Session de la base de données.
        current_user (int): ID de l'utilisateur authentifié (via OAuth2).

    Returns:
        dict: Liste des utilisateurs non présentateurs avec leurs détails.

    Raises:
        HTTPException: 500 en cas d'erreur serveur.
    """
    try:
        non_presenters = get_non_presenters(db)
        return {
            "total": len(non_presenters),
            "users": non_presenters
        }
    except Exception as e:
        logger.error(f"Error in route get_non_presenters: {e}")
        raise HTTPException(status_code=500, detail="Error fetching non-presenters")
    

#//////////////////////////// Fonstions pour ajouter les roles par defaut //////////////////////////////

def create_default_role_and_permission(db: Session):
    """
    Vérifie si le rôle "public" existe, sinon le crée avec des permissions par défaut.
    """
    default_role_name = "public"

    # Vérifier si le rôle existe déjà
    existing_role = db.query(Role).filter(Role.name == default_role_name).first()
    if not existing_role:
        # Créer le rôle "public"
        new_role = Role(name=default_role_name)
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        # Ajouter des permissions par défaut au rôle "public"
        default_permissions = ["view_profile", "read_notifications"]
        for permission_name in default_permissions:
            # Vérifier si la permission existe déjà
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            if not permission:
                permission = Permission(name=permission_name)
                db.add(permission)
                db.commit()
                db.refresh(permission)

            # Créer l'association entre le rôle et la permission
            role_permission = RolePermission(role_id=new_role.id, permission_id=permission.id)
            db.add(role_permission)
        db.commit()

def assign_default_role_to_user(user_id: int, db: Session):
    """
    Assigne le rôle "public" à un utilisateur donné. Crée le rôle s'il n'existe pas.
    """
    create_default_role_and_permission(db)  # S'assurer que le rôle "public" existe

    # Récupérer le rôle "public"
    public_role = db.query(Role).filter(Role.name == "public").first()
    if not public_role:
        raise HTTPException(status_code=500, detail="Failed to create or retrieve the default role")

    # Vérifier si l'utilisateur a déjà le rôle
    existing_user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id, UserRole.role_id == public_role.id
    ).first()

    if not existing_user_role:
        # Assigner le rôle "public" à l'utilisateur
        user_role = UserRole(user_id=user_id, role_id=public_role.id)
        db.add(user_role)
        db.commit()



#////////////////////// fin des fonctions pour ajouter les roles par defaut /////////////////////////////

# , response_model=List[UserRead]   response_model=UserSrearchResponse


@router.get("/users",response_model=List[UserSrearchResponse] )
def get_users(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer tous les utilisateurs actifs.
    """
    return get_all_users(db)

@router.get("/users/{id}")
def get_user(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer un utilisateur spécifique par son ID.
    """
    # user = get_user_or_404(db, id)
    user=get_user_or_404_with_permissions(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserBase)

#####################
###  a restituer la necessiter de se loguer pour cree un user
###  aprest avoir fait les test.     
##    , current_user: int = Depends(oauth2.get_current_user)
#################
def create_new_user(user_to_create: UserCreate, db: Session = Depends(get_db)):
    # hachage du mot de passe
    hashed_password=utils.hash(user_to_create.password)
    user_to_create.password=hashed_password

    """
    Créer un nouvel utilisateur et lui assigner le rôle "public" par défaut.
    """
    # create_default_role_and_permission(db)

    # Créer l'utilisateur
    created_user = create_user(db, user_to_create.dict())
    if created_user:
        # Assigner le rôle "public"
        assign_default_role_to_user(created_user.id, db)

        return JSONResponse(
            status_code=201,
            content={
                "user_id": created_user.id,
                "email": created_user.email,
                "username": created_user.username,
                "name": created_user.name,
                "family_name": created_user.family_name,
            }
        )
    return JSONResponse(status_code=400, content={"detail": "User creation failed"})
    # # Assigner le rôle "public"
    # assign_default_role_to_user(created_user.id, db)

    # return created_user


# Route pour mettre à jour un utilisateur
@router.put("/updte/{user_id}", response_model=UserSrearchResponse)
def update_user_route(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Mettre à jour un utilisateur par son ID.
    
    Args:
        user_id (int): ID de l'utilisateur à mettre à jour.
        user_update (UserUpdate): Données de mise à jour.
        db (Session): Session SQLAlchemy.
    
    Returns:
        UserRead: Utilisateur mis à jour.
    
    Raises:
        HTTPException: 404 si l'utilisateur n'est pas trouvé.
    """
    updated_user = update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user




@router.put("/upd_date/{id}", response_model=UserInDB)
def update_user_info(id: int, user: UserInDB, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Mettre à jour un utilisateur existant.
    """
    updated_user = update_user(db, id, user.dict())
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/del/{id}")
def delete_user_info(id: int, db: Session = Depends(get_db)):
    """
    Supprimer un utilisateur (soft delete).
    """
    if not delete_user(db, id):
        return JSONResponse(
            status_code=404,
            content={"detail": "User non trouvé"}
        )
        # raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(
            status_code=204,
            content={"detail": "User soft-deleted successfully"}
        )

@router.get("/users/{id}/logins", response_model=List[LoginHistoryRead])
def get_logins(id: int, db: Session = Depends(get_db)):
    """
    Récupérer l'historique des connexions d'un utilisateur.
    """
    return get_user_logins(db, id)

@router.get("/users/{id}/notifications", response_model=List[NotificationRead])
def get_notifications(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer les notifications d'un utilisateur.
    """
    return get_user_notifications(db, id)

@router.get("/users/{id}/audit-logs", response_model=List[AuditLog])
def get_audit_logs(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    """
    Récupérer les logs d'audit d'un utilisateur.
    """
    return get_user_audit_logs(db, id)











# from fastapi import FastAPI, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime

# # Base de données simulée
# users_db = {}  # Dictionnaire pour stocker les utilisateurs actifs/inactifs
# logins_db = {}  # Dictionnaire pour stocker l'historique des connexions
# notifications_db = {}  # Dictionnaire pour stocker les notifications
# audit_logs_db = {}  # Dictionnaire pour stocker les logs d'audit


# # Modèles pour les données des utilisateurs
# class User(BaseModel):
#     """
#     Modèle de base pour créer ou mettre à jour un utilisateur.
#     """
#     username: str
#     email: str
#     is_active: bool = True


# class UserInDB(User):
#     """
#     Modèle étendu pour inclure des informations supplémentaires stockées en base.
#     """
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime] = None


# class LoginLog(BaseModel):
#     """
#     Modèle pour représenter une connexion utilisateur.
#     """
#     user_id: int
#     timestamp: datetime
#     ip_address: str


# class Notification(BaseModel):
#     """
#     Modèle pour représenter une notification.
#     """
#     user_id: int
#     message: str
#     created_at: datetime


# class AuditLog(BaseModel):
#     """
#     Modèle pour représenter un log d'audit.
#     """
#     user_id: int
#     action: str
#     timestamp: datetime


# # Fonction utilitaire pour récupérer un utilisateur ou lever une erreur 404
# def get_user_or_404(user_id: int) -> UserInDB:
#     if user_id not in users_db or not users_db[user_id].is_active:
#         raise HTTPException(status_code=404, detail="User not found")
#     return users_db[user_id]


# # Routes pour la gestion des utilisateurs
# @app.get("/users", response_model=List[UserInDB])
# def get_all_users():
#     """
#     Récupérer tous les utilisateurs actifs.
#     """
#     return [u for u in users_db.values() if u.is_active]


# @app.get("/users/{id}", response_model=UserInDB)
# def get_user(id: int):
#     """
#     Récupérer un utilisateur spécifique par son ID.
#     """
#     return get_user_or_404(id)


# @app.post("/users", response_model=UserInDB)
# def create_user(user: User):
#     """
#     Créer un nouvel utilisateur.
#     """
#     user_id = len(users_db) + 1  # Génération d'un nouvel ID
#     new_user = UserInDB(
#         **user.dict(), id=user_id, created_at=datetime.utcnow()
#     )
#     users_db[user_id] = new_user
#     return new_user


# @app.put("/users/{id}", response_model=UserInDB)
# def update_user(id: int, user: User):
#     """
#     Mettre à jour un utilisateur existant.
#     """
#     existing_user = get_user_or_404(id)
#     updated_user = existing_user.copy(
#         update={**user.dict(), "updated_at": datetime.utcnow()}
#     )
#     users_db[id] = updated_user
#     return updated_user


# @app.delete("/users/{id}")
# def delete_user(id: int):
#     """
#     Supprimer (soft delete) un utilisateur.
#     """
#     user = get_user_or_404(id)
#     user.is_active = False
#     user.updated_at = datetime.utcnow()
#     users_db[id] = user
#     return {"detail": "User soft-deleted successfully"}


# # Routes supplémentaires
# @app.get("/users/{id}/logins", response_model=List[LoginLog])
# def get_user_logins(id: int):
#     """
#     Récupérer l'historique des connexions d'un utilisateur.
#     """
#     get_user_or_404(id)
#     return [log for log in logins_db.values() if log.user_id == id]


# @app.get("/users/{id}/notifications", response_model=List[Notification])
# def get_user_notifications(id: int):
#     """
#     Récupérer les notifications d'un utilisateur.
#     """
#     get_user_or_404(id)
#     return [n for n in notifications_db.values() if n.user_id == id]


# @app.get("/users/{id}/audit-logs", response_model=List[AuditLog])
# def get_user_audit_logs(id: int):
#     """
#     Récupérer les logs d'audit d'un utilisateur.
#     """
#     get_user_or_404(id)
#     return [log for log in audit_logs_db.values() if log.user_id == id]
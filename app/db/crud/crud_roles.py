from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.model_role import Role
from app.models.model_user import User
from app.schemas.schema_roles import RoleCreate, RoleUpdate

def create_role(db: Session, role: RoleCreate):
    """
    Créer un nouveau rôle dans la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role (RoleCreate): Les données du rôle à créer.
    
    Returns:
    - Role: Le rôle créé.
    """
    try:
        # Création du nouvel objet Role à partir des données fournies
        new_role = Role(**role.model_dump())
        
        # Ajout du rôle à la session de la base de données
        db.add(new_role)
        
        # Validation des changements dans la base de données
        db.commit()
        
        # Rafraîchissement du rôle pour récupérer les informations mises à jour
        db.refresh(new_role)
        
        # Retour du rôle nouvellement créé
        return new_role
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating role: {str(e)}"
        )


def get_role(db: Session, role_id: int):
    """
    Récupérer un rôle spécifique à partir de la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_id (int): L'ID du rôle à récupérer.
    
    Returns:
    - Role: Le rôle avec l'ID spécifié, ou None si non trouvé.
    """
    try:
        # Recherche du rôle par son ID
        role = db.query(Role).filter(Role.id == role_id).first()
        
        # Si le rôle n'existe pas, une exception est levée
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Retour du rôle trouvé
        return role
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching role: {str(e)}"
        )


def get_roles(db: Session, skip: int = 0, limit: int = 10):
    """
    Récupérer une liste de rôles, avec option de pagination.
    
    Args:
    - db (Session): La session de la base de données.
    - skip (int): Nombre d'éléments à ignorer pour la pagination (par défaut 0).
    - limit (int): Nombre maximum d'éléments à récupérer pour la pagination (par défaut 10).
    
    Returns:
    - list[Role]: Liste des rôles récupérés.
    """
    try:
        # Récupération des rôles avec pagination
        roles = db.query(Role).offset(skip).limit(limit).all()
        
        # Retour de la liste des rôles
        return roles
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching roles: {str(e)}"
        )


def update_role(db: Session, role_id: int, role_update: RoleUpdate):
    """
    Mettre à jour un rôle existant dans la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_id (int): L'ID du rôle à mettre à jour.
    - role_update (RoleUpdate): Les données de mise à jour pour le rôle.
    
    Returns:
    - Role: Le rôle mis à jour.
    """
    try:
        # Recherche du rôle à mettre à jour
        role = db.query(Role).filter(Role.id == role_id).first()
        
        # Si le rôle n'existe pas, une exception est levée
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Mise à jour des attributs du rôle avec les nouvelles données
        for key, value in role_update.dict(exclude_unset=True).items():
            setattr(role, key, value)
        
        # Validation des changements dans la base de données
        db.commit()
        
        # Rafraîchissement du rôle pour récupérer les informations mises à jour
        db.refresh(role)
        
        # Retour du rôle mis à jour
        return role
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating role: {str(e)}"
        )


def delete_role(db: Session, role_id: int):
    """
    Supprimer un rôle de la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_id (int): L'ID du rôle à supprimer.
    
    Returns:
    - Role: Le rôle supprimé.
    """
    try:
        # Recherche du rôle à supprimer
        role = db.query(Role).filter(Role.id == role_id).first()
        
        # Si le rôle n'existe pas, une exception est levée
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Suppression du rôle
        db.delete(role)
        
        # Validation des changements dans la base de données
        db.commit()
        
        # Retour du rôle supprimé
        return role
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting role: {str(e)}"
        )


def get_all_roles(db: Session):
    """
    Récupérer tous les rôles de la base de données.

    Args:
    - db (Session): La session de la base de données.

    Returns:
    - list[Role]: Liste de tous les rôles.
    """
    try:
        # Récupération de tous les rôles
        roles = db.query(Role).all()
        
        # Retour de la liste des rôles
        return roles
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching all roles: {str(e)}"
        )



#/////////////////////////////////
# Ajouter un rôle à un utilisateur


# Ajouter un rôle à un utilisateur
def add_role_to_user(user_id: int, role_name: str, db: Session):
    try:
        # Recherche l'utilisateur dans la base de données en fonction de son ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
        
        # Recherche le rôle dans la base de données en fonction du nom du rôle
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")
        
        # Si l'utilisateur n'a pas déjà ce rôle, on l'ajoute à la liste des rôles de l'utilisateur
        if role not in user.roles:
            user.roles.append(role)
            # Sauvegarde les modifications dans la base de données
            db.commit()
            # Rafraîchit l'utilisateur pour obtenir les données mises à jour
            db.refresh(user)
        
        # Retourne l'utilisateur mis à jour
        return user
    except SQLAlchemyError as e:
        # Si une erreur de base de données se produit, on lève une exception HTTP 500
        db.rollback()  # Rollback pour annuler les transactions en cas d'erreur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de l'ajout du rôle")
    except Exception as e:
        # Si une autre erreur se produit, on lève une exception HTTP 400 avec un message générique
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


#////////////////////////////////
# Supprimer un rôle d'un utilisateur
def remove_role_from_user(user_id: int, role_name: str, db: Session):
    try:
        # Recherche l'utilisateur dans la base de données en fonction de son ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
        
        # Recherche le rôle dans la base de données en fonction du nom du rôle
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")
        
        # Si l'utilisateur a ce rôle, on le supprime de la liste des rôles de l'utilisateur
        if role in user.roles:
            user.roles.remove(role)
            # Sauvegarde les modifications dans la base de données
            db.commit()
            # Rafraîchit l'utilisateur pour obtenir les données mises à jour
            db.refresh(user)
        else:
            # Si l'utilisateur n'a pas ce rôle, on lève une exception HTTP 400
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'utilisateur n'a pas ce rôle")
        
        # Retourne l'utilisateur mis à jour
        return user
    except SQLAlchemyError as e:
        # Si une erreur de base de données se produit, on lève une exception HTTP 500
        db.rollback()  # Rollback pour annuler les transactions en cas d'erreur
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la suppression du rôle")
    except Exception as e:
        # Si une autre erreur se produit, on lève une exception HTTP 400 avec un message générique
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))





# from sqlalchemy.orm import Session
# from app.models.model_role import Role
# from app.schemas.schema_roles import RoleCreate, RoleUpdate

# def create_role(db: Session, role: RoleCreate):
#     new_role = Role(**role.model_dump())
#     db.add(new_role)
#     db.commit()
#     db.refresh(new_role)
#     return new_role

# def get_role(db: Session, role_id: int):
#     return db.query(Role).filter(Role.id == role_id).first()

# def get_roles(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(Role).offset(skip).limit(limit).all()

# def update_role(db: Session, role_id: int, role_update: RoleUpdate):
#     role = db.query(Role).filter(Role.id == role_id).first()
#     for key, value in role_update.dict(exclude_unset=True).items():
#         setattr(role, key, value)
#     db.commit()
#     db.refresh(role)
#     return role

# def delete_role(db: Session, role_id: int):
#     role = db.query(Role).filter(Role.id == role_id).first()
#     if role:
#         db.delete(role)
#         db.commit()
#     return role
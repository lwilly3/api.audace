
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.model_role_permission import RolePermission
from app.schemas.schema_role_permissions import RolePermissionCreate

def create_role_permission(db: Session, role_permission: RolePermissionCreate):
    """
    Créer une nouvelle relation de rôle et permission dans la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_permission (RolePermissionCreate): Les données du rôle et de la permission à créer.
    
    Returns:
    - RolePermission: La relation de rôle et permission créée.
    """
    try:
        # Création d'un nouvel objet RolePermission à partir des données fournies
        new_role_permission = RolePermission(**role_permission.model_dump())
        
        # Ajout de l'objet à la session de la base de données
        db.add(new_role_permission)
        
        # Validation des changements dans la base de données
        db.commit()
        
        # Retour de l'objet RolePermission nouvellement créé
        return new_role_permission
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating role permission: {str(e)}"
        )


def get_role_permissions(db: Session, role_id: int):
    """
    Récupérer toutes les permissions d'un rôle spécifique à partir de la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_id (int): L'ID du rôle pour lequel récupérer les permissions.
    
    Returns:
    - list[RolePermission]: La liste des relations de rôle et permission associées au rôle.
    """
    try:
        # Recherche des permissions associées à un rôle par son ID
        role_permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        
        # Retour de la liste des relations trouvées
        return role_permissions
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching role permissions: {str(e)}"
        )


def delete_role_permission(db: Session, role_id: int, permission_id: int):
    """
    Supprimer une relation de rôle et permission spécifique de la base de données.
    
    Args:
    - db (Session): La session de la base de données.
    - role_id (int): L'ID du rôle.
    - permission_id (int): L'ID de la permission.
    
    Returns:
    - RolePermission: La relation de rôle et permission supprimée.
    """
    try:
        # Recherche de la relation de rôle et permission par les IDs fournis
        role_permission = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        
        # Si la relation est trouvée, la supprimer
        if role_permission:
            db.delete(role_permission)
            db.commit()
        
        # Retour de l'objet supprimé ou None si non trouvé
        return role_permission
    
    except Exception as e:
        # Si une erreur survient, une exception HTTP 500 est levée pour indiquer une erreur interne du serveur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting role permission: {str(e)}"
        )












# from sqlalchemy.orm import Session
# from app.models.model_role_permission import RolePermission
# from app.schemas.schema_role_permissions import RolePermissionCreate

# def create_role_permission(db: Session, role_permission: RolePermissionCreate):
#     new_role_permission = RolePermission(**role_permission.model_dump())
#     db.add(new_role_permission)
#     db.commit()
#     return new_role_permission

# def get_role_permissions(db: Session, role_id: int):
#     return db.query(RolePermission).filter(RolePermission.role_id == role_id).all()

# def delete_role_permission(db: Session, role_id: int, permission_id: int):
#     role_permission = db.query(RolePermission).filter(
#         RolePermission.role_id == role_id,
#         RolePermission.permission_id == permission_id
#     ).first()
#     if role_permission:
#         db.delete(role_permission)
#         db.commit()
#     return role_permission

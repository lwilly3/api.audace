from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List
from app.models import RoleTemplate, UserPermissions
from app.schemas import RoleTemplateCreate, RoleTemplateUpdate, UserPermissionsSchema,RoleTemplateResponse

def create_role_template(db: Session, template: RoleTemplateCreate) -> RoleTemplateResponse:
    """
    Crée un nouveau modèle de rôle dans la base de données.
    """
    try:
        # Vérifie si le nom existe déjà
        if db.query(RoleTemplate).filter(RoleTemplate.name == template.name).first():
            raise ValueError(f"Un modèle avec le nom '{template.name}' existe déjà.")
        
        # Génération d'un ID basé sur le nom (simplifié, tu peux utiliser UUID si préféré)
        template_id = template.name.lower().replace(" ", "_")
        
        db_template = RoleTemplate(
            name=template.name,
            description=template.description,
            permissions=template.permissions
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e
    except ValueError as e:
        db.rollback()
        raise ValueError(str(e)) from e

def get_role_template(db: Session, template_id: str) -> RoleTemplate:
    """
    Récupère un modèle de rôle par son ID.
    """
    template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not template:
        raise ValueError(f"Aucun modèle de rôle trouvé avec l'ID '{template_id}'")
    return template

def get_all_role_templates(db: Session) -> List[RoleTemplate]:
    """
    Récupère tous les modèles de rôles.
    """
    return db.query(RoleTemplate).all()

def update_role_template(db: Session, template_id: str, template_update: RoleTemplateUpdate) -> RoleTemplate:
    """
    Met à jour un modèle de rôle existant.
    """
    try:
        db_template = get_role_template(db, template_id)
        
        if template_update.name:
            if (template_update.name != db_template.name and 
                db.query(RoleTemplate).filter(RoleTemplate.name == template_update.name).first()):
                raise ValueError(f"Un modèle avec le nom '{template_update.name}' existe déjà.")
            db_template.name = template_update.name
        
        if template_update.description is not None:
            db_template.description = template_update.description
        if template_update.permissions is not None:
            # Fusionne les permissions existantes avec les nouvelles
            db_template.permissions = {**db_template.permissions, **template_update.permissions}
        
        db.commit()
        db.refresh(db_template)
        return db_template
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e
    except ValueError as e:
        db.rollback()
        raise ValueError(str(e)) from e

def delete_role_template(db: Session, template_id: str) -> Dict[str, Any]:
    """
    Supprime un modèle de rôle.
    """
    try:
        db_template = get_role_template(db, template_id)
        db.delete(db_template)
        db.commit()
        return {"message": f"Modèle de rôle '{template_id}' supprimé avec succès", "success": True}
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e

def apply_role_template(db: Session, user_id: int, template_id: str) -> Dict[str, Any]:
    """
    Applique un modèle de rôle à un utilisateur.
    """
    try:
        # Récupérer le modèle
        template = get_role_template(db, template_id)
        
        # Récupérer les permissions de l'utilisateur
        user_permission = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
        if not user_permission:
            raise ValueError(f"Aucune permission trouvée pour l'utilisateur avec l'ID {user_id}")
        
        # Appliquer les permissions du modèle
        for perm, value in template.permissions.items():
            setattr(user_permission, perm, value)
        
        db.commit()
        return {"message": f"Modèle '{template.name}' appliqué à l'utilisateur {user_id}", "success": True}
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Erreur de base de données : {str(e)}") from e
    except ValueError as e:
        db.rollback()
        raise ValueError(str(e)) from e
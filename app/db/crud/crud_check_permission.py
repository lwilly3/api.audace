from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import User, Role, Permission, RolePermission

def check_permission(user: User, action: str, db: Session):
    """
    Vérifie que l'utilisateur a la permission d'effectuer une action.
    
    Args:
    - user (User): L'utilisateur effectuant l'action.
    - action (str): L'action à vérifier.
    - db (Session): La session de la base de données.
    
    Raises:
    - HTTPException: Si l'utilisateur n'a pas la permission.
    """
    # Récupérer les rôles de l'utilisateur
    roles = db.query(Role).join(Role.users).filter(User.id == user.id).all()
    
    # Vérifier si l'un des rôles a la permission correspondante
    for role in roles:
        # Rechercher les permissions associées à ce rôle via la table de liaison RolePermission
        permissions = db.query(Permission).join(RolePermission).filter(RolePermission.role_id == role.id).all()
        for permission in permissions:
            if permission.name == action:
                return True
    
    # Si aucune permission ne correspond à l'action, l'accès est refusé
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")



# Explications des modifications :
# Récupérer les rôles de l'utilisateur :

# La ligne db.query(Role).join(Role.users).filter(User.id == user.id).all()
#  permet de récupérer les rôles associés à l'utilisateur. 
# On utilise Role.users pour joindre la table de liaison UserRole,
#  qui associe les utilisateurs aux rôles.
# Récupérer les permissions de chaque rôle :

# La ligne db.query(Permission).join(RolePermission).filter(RolePermission.role_id == role.id).all() 
# permet de récupérer toutes les permissions associées au rôle actuel via 
# la table de liaison RolePermission.
# Vérification des permissions :

# Ensuite, on vérifie si une des permissions associées au rôle correspond 
# à l'action que l'utilisateur tente d'effectuer.



# Remarque supplémentaire :
# Si ton application a un nombre de rôles et de permissions 
# relativement important, tu pourrais envisager d'optimiser
#  la requête avec des jointures spécifiques et des select_from 
# pour éviter des chargements inutiles ou trop nombreux de données.






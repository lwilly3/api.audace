# 🔐 Module PERMISSIONS - Gestion des Permissions et Rôles

Documentation complète du système de contrôle d'accès (RBAC - Role-Based Access Control).

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Règles métier](#règles-métier)
5. [Relations](#relations)
6. [Contraintes](#contraintes)
7. [Exemples d'utilisation](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités du module
- Gestion des rôles (Admin, Presenter, Editor, Viewer)
- Gestion des permissions granulaires par utilisateur
- Initialisation des permissions par défaut
- Vérification des autorisations (check_permissions)
- Association rôles ↔ permissions
- Audit des modifications de permissions

### Fichiers sources
- `app/db/crud/crud_permissions.py` : Gestion des permissions utilisateur
- `app/db/crud/crud_roles.py` : Gestion des rôles
- `app/db/crud/crud_role_permissions.py` : Association rôles-permissions

### Dépendances
```python
# Modèles
from app.models import UserPermission, Role, User
from app.models import UserRole  # Table d'association

# Schémas
from app.schemas import PermissionUpdate, RoleCreate, RoleUpdate
```

---

## 🏗️ Architecture

### Modèle UserPermission (Permissions granulaires)

```python
UserPermission:
    id: int (PK)
    user_id: int (FK → User, UNIQUE)  # Une seule ligne par user
    
    # Permissions Shows
    create_show: bool = False
    update_show: bool = False
    delete_show: bool = False
    view_show: bool = False
    
    # Permissions Segments
    create_segment: bool = False
    update_segment: bool = False
    delete_segment: bool = False
    view_segment: bool = False
    
    # Permissions Presenters
    create_presenter: bool = False
    update_presenter: bool = False
    delete_presenter: bool = False
    view_presenter: bool = False
    
    # Permissions Guests
    create_guest: bool = False
    update_guest: bool = False
    delete_guest: bool = False
    view_guest: bool = False
    
    # Permissions Emissions
    create_emission: bool = False
    update_emission: bool = False
    delete_emission: bool = False
    view_emission: bool = False
    
    # Permissions Users
    create_user: bool = False
    update_user: bool = False
    delete_user: bool = False
    view_user: bool = False
    
    # Permissions Roles
    create_role: bool = False
    update_role: bool = False
    delete_role: bool = False
    view_role: bool = False
    
    # Permissions Notifications
    create_notification: bool = False
    update_notification: bool = False
    delete_notification: bool = False
    view_notification: bool = False
    
    # Permissions Permissions
    create_permission: bool = False
    update_permission: bool = False
    delete_permission: bool = False
    view_permission: bool = False
    
    # Permissions Dashboard
    view_dashboard: bool = False
    
    # Audit
    created_at: datetime
    updated_at: datetime
    
    # Relation
    user: User (One-to-One)
```

### Modèle Role

```python
Role:
    id: int (PK)
    name: str (UNIQUE)  # Ex: "Admin", "Presenter", "Editor"
    description: text
    created_at: datetime
    updated_at: datetime
    
    # Relations
    users: List[User] (Many-to-Many via user_roles)
```

### Modèle UserRole (Table d'association)

```python
UserRole:
    user_id: int (FK → User, PK)
    role_id: int (FK → Role, PK)
    assigned_at: datetime
```

### Hiérarchie des rôles

```
Admin (Super User)
  ├── Toutes les permissions
  └── Gestion des utilisateurs et rôles

Presenter (Animateur)
  ├── Créer/modifier ses shows
  ├── Voir tous les shows
  └── Gérer les invités de ses shows

Editor (Éditeur)
  ├── Créer/modifier tous les shows
  ├── Gérer tous les segments
  └── Gérer tous les invités

Viewer (Lecture seule)
  └── Voir tous les contenus (pas de modification)
```

### Flux de vérification des permissions

```
Request
   ↓
Middleware oauth2.get_current_user()
   ↓
Extraire user_id du token JWT
   ↓
crud_permissions.get_user_permissions(user_id)
   ↓
check_permissions(user, required_permission)
   ↓
   ├─→ Permission accordée → Exécuter la route
   └─→ Permission refusée → HTTPException(403)
```

---

## 🔧 Fonctions métier

### 1. initialize_user_permissions()

**Signature :**
```python
def initialize_user_permissions(db: Session, user_id: int) -> UserPermission
```

**Description :**
Initialise les permissions par défaut pour un nouvel utilisateur. Appelée automatiquement à la création d'un compte.

**Logique métier :**

#### Étape 1 : Vérifier l'existence
```python
def initialize_user_permissions(db: Session, user_id: int):
    # Vérifier que l'utilisateur n'a pas déjà des permissions
    existing = db.query(UserPermission).filter(
        UserPermission.user_id == user_id
    ).first()
    
    if existing:
        return existing  # Ne pas recréer
```

#### Étape 2 : Permissions par défaut (Viewer)
```python
    # Créer avec permissions de lecture uniquement
    default_permissions = UserPermission(
        user_id=user_id,
        # Shows
        view_show=True,          # Peut voir les shows
        create_show=False,
        update_show=False,
        delete_show=False,
        # Segments
        view_segment=True,       # Peut voir les segments
        create_segment=False,
        update_segment=False,
        delete_segment=False,
        # Guests
        view_guest=True,         # Peut voir les invités
        create_guest=False,
        update_guest=False,
        delete_guest=False,
        # Presenters
        view_presenter=True,     # Peut voir les présentateurs
        create_presenter=False,
        update_presenter=False,
        delete_presenter=False,
        # Emissions
        view_emission=True,
        create_emission=False,
        update_emission=False,
        delete_emission=False,
        # Users
        view_user=False,         # Ne peut PAS voir les autres users
        create_user=False,
        update_user=False,
        delete_user=False,
        # Roles
        view_role=False,
        create_role=False,
        update_role=False,
        delete_role=False,
        # Notifications
        view_notification=True,  # Peut voir ses notifs
        create_notification=False,
        update_notification=False,
        delete_notification=False,
        # Permissions
        view_permission=False,
        create_permission=False,
        update_permission=False,
        delete_permission=False,
        # Dashboard
        view_dashboard=False     # Pas d'accès stats par défaut
    )
    
    db.add(default_permissions)
    db.commit()
    db.refresh(default_permissions)
    
    return default_permissions
```

**Cas d'usage :**
- Appelée dans `crud_users.create_user()`
- Garantit que chaque utilisateur a une ligne de permissions

---

### 2. get_user_permissions()

**Signature :**
```python
def get_user_permissions(db: Session, user_id: int) -> UserPermission
```

**Description :**
Récupère les permissions d'un utilisateur. Crée les permissions par défaut si elles n'existent pas.

**Logique métier :**
```python
def get_user_permissions(db: Session, user_id: int):
    permissions = db.query(UserPermission).filter(
        UserPermission.user_id == user_id
    ).first()
    
    # Si pas de permissions, les initialiser
    if not permissions:
        permissions = initialize_user_permissions(db, user_id)
    
    return permissions
```

**Utilisation dans les routes :**
```python
from core.auth import oauth2

@router.get("/protected-resource")
def protected_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Récupérer les permissions
    permissions = crud_permissions.get_user_permissions(db, current_user.id)
    
    # Vérifier la permission
    if not permissions.view_show:
        raise HTTPException(403, "Permission denied")
    
    # Continuer...
```

---

### 3. check_permissions()

**Signature :**
```python
def check_permissions(
    db: Session,
    user_id: int,
    required_permission: str
) -> bool
```

**Description :**
Vérifie si un utilisateur possède une permission spécifique.

**Logique métier :**
```python
def check_permissions(db: Session, user_id: int, required_permission: str) -> bool:
    """
    Vérifie si l'utilisateur a la permission requise.
    
    Args:
        user_id: ID de l'utilisateur
        required_permission: Nom du champ de permission (ex: "create_show")
    
    Returns:
        bool: True si permission accordée, False sinon
    """
    permissions = get_user_permissions(db, user_id)
    
    # Vérifier que le champ existe
    if not hasattr(permissions, required_permission):
        raise ValueError(f"Unknown permission: {required_permission}")
    
    # Retourner la valeur du champ
    return getattr(permissions, required_permission, False)
```

**Utilisation avec décorateur :**
```python
from functools import wraps
from fastapi import HTTPException

def require_permission(permission_name: str):
    """Décorateur pour vérifier les permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraire db et current_user des kwargs
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(500, "Missing dependencies")
            
            # Vérifier la permission
            if not check_permissions(db, current_user.id, permission_name):
                raise HTTPException(
                    403,
                    f"Permission denied: {permission_name} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/shows")
@require_permission("create_show")
async def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # L'utilisateur a la permission create_show
    return crud_show.create_show(db, show, current_user.id)
```

---

### 4. update_user_permissions()

**Signature :**
```python
def update_user_permissions(
    db: Session,
    user_id: int,
    permissions_update: PermissionUpdate
) -> UserPermission
```

**Description :**
Met à jour les permissions d'un utilisateur spécifique. **Réservé aux administrateurs.**

**Logique métier :**
```python
def update_user_permissions(
    db: Session,
    user_id: int,
    permissions_update: PermissionUpdate
):
    # Récupérer les permissions existantes
    permissions = get_user_permissions(db, user_id)
    
    # Appliquer les modifications
    update_data = permissions_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if hasattr(permissions, key):
            setattr(permissions, key, value)
    
    # Mise à jour automatique
    permissions.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(permissions)
    
    return permissions
```

**Schema PermissionUpdate :**
```python
class PermissionUpdate(BaseModel):
    # Toutes les permissions sont optionnelles
    create_show: Optional[bool] = None
    update_show: Optional[bool] = None
    delete_show: Optional[bool] = None
    view_show: Optional[bool] = None
    # ... (40+ champs)
    
    class Config:
        extra = "forbid"  # Empêche les champs inconnus
```

**Exemple d'utilisation (route admin) :**
```python
@router.patch("/admin/users/{user_id}/permissions")
def update_permissions(
    user_id: int,
    permissions: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)  # Admin uniquement
):
    """Mettre à jour les permissions d'un utilisateur"""
    updated = crud_permissions.update_user_permissions(db, user_id, permissions)
    
    # Log de l'action
    crud_audit_log.create_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE_PERMISSIONS",
        resource_type="UserPermission",
        resource_id=user_id,
        details=permissions.model_dump()
    )
    
    return updated
```

---

### 5. assign_roles_to_user()

**Signature :**
```python
def assign_roles_to_user(
    db: Session,
    user_id: int,
    role_ids: List[int]
) -> User
```

**Description :**
Assigne un ou plusieurs rôles à un utilisateur et met à jour ses permissions en conséquence.

**Logique métier :**

#### Étape 1 : Récupérer utilisateur et rôles
```python
def assign_roles_to_user(db: Session, user_id: int, role_ids: List[int]):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Récupérer les rôles
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    
    if len(roles) != len(role_ids):
        raise HTTPException(400, "One or more roles not found")
```

#### Étape 2 : Assigner les rôles
```python
    # Remplacer tous les rôles existants
    user.roles = roles
    db.commit()
```

#### Étape 3 : Mettre à jour les permissions
```python
    # Appliquer les permissions correspondantes aux rôles
    permissions = get_user_permissions(db, user_id)
    
    # Réinitialiser toutes les permissions à False
    for field in permissions.__table__.columns:
        if field.name.endswith('_show') or field.name.endswith('_user') or ...:
            setattr(permissions, field.name, False)
    
    # Appliquer les permissions de chaque rôle
    for role in roles:
        if role.name == "Admin":
            # Admin : toutes les permissions
            for field in permissions.__table__.columns:
                if field.name not in ['id', 'user_id', 'created_at', 'updated_at']:
                    setattr(permissions, field.name, True)
        
        elif role.name == "Presenter":
            # Presenter : gestion des shows et invités
            permissions.create_show = True
            permissions.update_show = True
            permissions.view_show = True
            permissions.create_guest = True
            permissions.update_guest = True
            permissions.view_guest = True
            permissions.view_segment = True
            # ...
        
        elif role.name == "Editor":
            # Editor : gestion de tous les contenus
            permissions.create_show = True
            permissions.update_show = True
            permissions.delete_show = True
            permissions.view_show = True
            permissions.create_segment = True
            permissions.update_segment = True
            permissions.delete_segment = True
            permissions.view_segment = True
            # ...
        
        elif role.name == "Viewer":
            # Viewer : lecture seule
            permissions.view_show = True
            permissions.view_segment = True
            permissions.view_guest = True
            permissions.view_presenter = True
            # ...
    
    db.commit()
    db.refresh(user)
    
    return user
```

**Exemple d'utilisation :**
```python
@router.post("/admin/users/{user_id}/roles")
def assign_roles(
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)
):
    """Assigner des rôles à un utilisateur"""
    updated_user = crud_roles.assign_roles_to_user(db, user_id, role_ids)
    return {
        "user_id": updated_user.id,
        "roles": [{"id": r.id, "name": r.name} for r in updated_user.roles]
    }
```

---

### 6. get_all_roles()

**Signature :**
```python
def get_all_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]
```

**Description :**
Liste tous les rôles disponibles.

**Logique métier :**
```python
def get_all_roles(db: Session, skip: int = 0, limit: int = 100):
    roles = db.query(Role).order_by(Role.name).offset(skip).limit(limit).all()
    return roles
```

**Version avec nombre d'utilisateurs :**
```python
from sqlalchemy import func

def get_roles_with_user_count(db: Session):
    """Rôles avec nombre d'utilisateurs assignés"""
    roles = db.query(
        Role,
        func.count(UserRole.user_id).label("user_count")
    ).outerjoin(UserRole).group_by(Role.id).order_by(Role.name).all()
    
    result = []
    for role, user_count in roles:
        result.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "user_count": user_count
        })
    
    return result
```

---

### 7. create_role()

**Signature :**
```python
def create_role(db: Session, role: RoleCreate) -> Optional[Role]
```

**Description :**
Crée un nouveau rôle.

**Logique métier :**
```python
def create_role(db: Session, role: RoleCreate):
    # Vérifier l'unicité du nom
    existing = db.query(Role).filter(Role.name == role.name).first()
    if existing:
        raise HTTPException(400, f"Role '{role.name}' already exists")
    
    new_role = Role(
        name=role.name,
        description=role.description
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return new_role
```

---

## 📏 Règles métier

### 1. Permissions par défaut
- Nouvel utilisateur = rôle "Viewer" (lecture seule)
- Permissions granulaires > rôles (plus flexible)
- Une ligne UserPermission par utilisateur (1-to-1)

### 2. Hiérarchie des rôles
```
Admin > Editor > Presenter > Viewer
```

### 3. Modification de permissions
- Seuls les admins peuvent modifier les permissions
- Logs obligatoires de toutes les modifications
- Impossible de se retirer le rôle Admin (sauf si autre admin existe)

### 4. Vérification des permissions
- Toujours vérifier avant une action sensible
- Utiliser des décorateurs pour réutilisabilité
- Retourner 403 Forbidden si permission refusée

---

## 🔗 Relations

### Schéma relationnel complet
```
User (1) ───────→ (1) UserPermission  [Permissions granulaires]
  ↓
  │ (Many-to-Many)
  ↓
Role  [Admin, Presenter, Editor, Viewer]
```

---

## ⚠️ Contraintes

### Unicité
```sql
ALTER TABLE user_permissions ADD CONSTRAINT unique_user_permission UNIQUE (user_id);
ALTER TABLE roles ADD CONSTRAINT unique_role_name UNIQUE (name);
```

### Validation
```python
# Noms de rôles autorisés
ALLOWED_ROLES = ["Admin", "Presenter", "Editor", "Viewer"]

# Permissions valides (40+ champs)
VALID_PERMISSIONS = [
    "create_show", "update_show", "delete_show", "view_show",
    "create_user", "update_user", "delete_user", "view_user",
    # ...
]
```

---

## 💡 Exemples d'utilisation

### Protéger une route
```python
@router.delete("/shows/{show_id}")
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Vérifier la permission
    if not crud_permissions.check_permissions(db, current_user.id, "delete_show"):
        raise HTTPException(403, "You don't have permission to delete shows")
    
    # Exécuter la suppression
    crud_show.delete_show(db, show_id)
    return {"message": "Show deleted"}
```

### Promouvoir un utilisateur en Admin
```python
@router.post("/admin/promote/{user_id}")
def promote_to_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)
):
    # Récupérer le rôle Admin
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    
    # Assigner le rôle
    crud_roles.assign_roles_to_user(db, user_id, [admin_role.id])
    
    return {"message": f"User {user_id} promoted to Admin"}
```

---

**Navigation :**
- [← PRESENTERS.md](PRESENTERS.md)
- [→ AUTH.md](AUTH.md)
- [↑ Retour à l'index](README.md)

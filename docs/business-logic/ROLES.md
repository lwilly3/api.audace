# 👔 Module ROLES - Gestion des Rôles Utilisateurs

Documentation de la gestion des rôles (Admin, Presenter, Editor, Viewer).

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Règles métier](#règles-métier)
5. [Exemples](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités
- Gestion des rôles (CRUD)
- Association rôles ↔ utilisateurs
- Définition des permissions par rôle

### Fichier source
`app/db/crud/crud_roles.py`

---

## 🏗️ Architecture

### Modèle Role

```python
Role:
    id: int (PK)
    name: str (UNIQUE, NOT NULL)  # "Admin", "Presenter", "Editor", "Viewer"
    description: text
    created_at: datetime
    updated_at: datetime
    
    # Relations
    users: List[User] (Many-to-Many via user_roles)
```

### Table d'association UserRole

```python
UserRole:
    user_id: int (FK → User, PK)
    role_id: int (FK → Role, PK)
    assigned_at: datetime
```

### Rôles par défaut

```python
DEFAULT_ROLES = {
    "Admin": {
        "description": "Administrateur système avec tous les droits",
        "permissions": "ALL"
    },
    "Presenter": {
        "description": "Animateur pouvant gérer ses shows",
        "permissions": ["create_show", "update_show", "create_guest", "view_show"]
    },
    "Editor": {
        "description": "Éditeur pouvant gérer tous les contenus",
        "permissions": ["create_*", "update_*", "delete_*", "view_*"]
    },
    "Viewer": {
        "description": "Utilisateur en lecture seule",
        "permissions": ["view_*"]
    }
}
```

---

## 🔧 Fonctions métier

### 1. create_role()

```python
def create_role(db: Session, role: RoleCreate) -> Optional[Role]
```

**Description :** Crée un nouveau rôle.

**Logique :**
```python
from sqlalchemy import exc

def create_role(db: Session, role: RoleCreate):
    try:
        # Vérifier l'unicité du nom
        existing = db.query(Role).filter(Role.name == role.name).first()
        if existing:
            raise HTTPException(400, f"Role '{role.name}' already exists")
        
        db_role = Role(
            name=role.name,
            description=role.description
        )
        
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        
        return db_role
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(400, "Role name must be unique")
```

---

### 2. get_role_by_id()

```python
def get_role_by_id(db: Session, role_id: int) -> Optional[Role]
```

**Description :** Récupère un rôle par son ID.

**Logique :**
```python
def get_role_by_id(db: Session, role_id: int):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(404, "Role not found")
    
    return role
```

---

### 3. get_all_roles()

```python
def get_all_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]
```

**Description :** Liste tous les rôles avec pagination.

**Logique :**
```python
def get_all_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Role).order_by(Role.name).offset(skip).limit(limit).all()
```

**Version avec statistiques :**
```python
from sqlalchemy import func

def get_roles_with_user_count(db: Session):
    """Rôles avec nombre d'utilisateurs"""
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

### 4. update_role()

```python
def update_role(db: Session, role_id: int, role_update: RoleUpdate) -> Optional[Role]
```

**Description :** Met à jour un rôle existant.

**Logique :**
```python
def update_role(db: Session, role_id: int, role_update: RoleUpdate):
    db_role = get_role_by_id(db, role_id)
    
    update_data = role_update.model_dump(exclude_unset=True)
    
    # Vérifier unicité du nom si modifié
    if "name" in update_data and update_data["name"] != db_role.name:
        existing = db.query(Role).filter(Role.name == update_data["name"]).first()
        if existing:
            raise HTTPException(400, "Role name already in use")
    
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    db.commit()
    db.refresh(db_role)
    
    return db_role
```

---

### 5. delete_role()

```python
def delete_role(db: Session, role_id: int) -> bool
```

**Description :** Supprime un rôle.

**⚠️ ATTENTION :** Ne pas supprimer un rôle avec des utilisateurs assignés !

**Logique :**
```python
def delete_role(db: Session, role_id: int):
    db_role = get_role_by_id(db, role_id)
    
    # Vérifier qu'aucun utilisateur n'a ce rôle
    user_count = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    
    if user_count > 0:
        raise HTTPException(
            400,
            f"Cannot delete role with {user_count} assigned users. "
            f"Reassign users first."
        )
    
    # Interdire suppression des rôles système
    PROTECTED_ROLES = ["Admin", "Presenter", "Editor", "Viewer"]
    if db_role.name in PROTECTED_ROLES:
        raise HTTPException(400, f"Cannot delete system role '{db_role.name}'")
    
    db.delete(db_role)
    db.commit()
    
    return True
```

---

### 6. assign_roles_to_user()

```python
def assign_roles_to_user(
    db: Session,
    user_id: int,
    role_ids: List[int]
) -> User
```

**Description :** Assigne un ou plusieurs rôles à un utilisateur.

**Logique :**
```python
def assign_roles_to_user(db: Session, user_id: int, role_ids: List[int]):
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Récupérer les rôles
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    
    if len(roles) != len(role_ids):
        raise HTTPException(400, "One or more roles not found")
    
    # Remplacer tous les rôles existants
    user.roles = roles
    
    db.commit()
    db.refresh(user)
    
    # Mettre à jour les permissions correspondantes
    update_permissions_from_roles(db, user)
    
    return user
```

---

### 7. update_permissions_from_roles()

```python
def update_permissions_from_roles(db: Session, user: User)
```

**Description :** Synchronise les permissions utilisateur avec ses rôles.

**Logique :**
```python
from app.db.crud import crud_permissions

def update_permissions_from_roles(db: Session, user: User):
    """
    Applique les permissions correspondant aux rôles de l'utilisateur.
    """
    permissions = crud_permissions.get_user_permissions(db, user.id)
    
    # Réinitialiser toutes les permissions
    for field in permissions.__table__.columns:
        if field.name not in ['id', 'user_id', 'created_at', 'updated_at']:
            setattr(permissions, field.name, False)
    
    # Appliquer les permissions de chaque rôle
    for role in user.roles:
        if role.name == "Admin":
            # Admin : TOUTES les permissions
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
            permissions.view_presenter = True
        
        elif role.name == "Editor":
            # Editor : gestion de tous les contenus (sauf users/roles)
            permissions.create_show = True
            permissions.update_show = True
            permissions.delete_show = True
            permissions.view_show = True
            
            permissions.create_segment = True
            permissions.update_segment = True
            permissions.delete_segment = True
            permissions.view_segment = True
            
            permissions.create_guest = True
            permissions.update_guest = True
            permissions.delete_guest = True
            permissions.view_guest = True
            
            permissions.create_presenter = True
            permissions.update_presenter = True
            permissions.delete_presenter = True
            permissions.view_presenter = True
            
            permissions.create_emission = True
            permissions.update_emission = True
            permissions.delete_emission = True
            permissions.view_emission = True
            
            permissions.view_dashboard = True
        
        elif role.name == "Viewer":
            # Viewer : lecture seule
            permissions.view_show = True
            permissions.view_segment = True
            permissions.view_guest = True
            permissions.view_presenter = True
            permissions.view_emission = True
    
    db.commit()
```

---

## 📏 Règles métier

### 1. Rôles système protégés
- "Admin", "Presenter", "Editor", "Viewer" ne peuvent pas être supprimés
- Modification du nom déconseillée

### 2. Hiérarchie
```
Admin > Editor > Presenter > Viewer
```

### 3. Multi-rôles
- Un utilisateur peut avoir plusieurs rôles
- Permissions cumulatives (union des permissions)

### 4. Synchronisation
- Changement de rôle → mise à jour automatique des permissions

---

## 💡 Exemples d'utilisation

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
    
    # Log de l'action
    crud_audit_log.create_audit_log(
        db,
        user_id=current_user.id,
        action="PROMOTE_TO_ADMIN",
        resource_type="User",
        resource_id=user_id
    )
    
    return {"message": f"User {user_id} promoted to Admin"}
```

### Créer un rôle personnalisé
```python
@router.post("/admin/roles")
def create_custom_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)
):
    new_role = crud_roles.create_role(db, role)
    return new_role
```

---

**Navigation :**
- [← SEGMENTS.md](SEGMENTS.md)
- [→ NOTIFICATIONS.md](NOTIFICATIONS.md)
- [↑ Retour à l'index](README.md)

# 🗃️ Model Generator

> **Skill prioritaire** : Création de modèles SQLAlchemy et schémas Pydantic conformes aux standards api.audace.

---

## 📋 Contexte du Projet

### Modèles Existants (25 fichiers)
```
app/models/
├── base_model.py              # BaseModel avec soft delete
├── model_user.py              # User (central)
├── model_user_permissions.py  # 40+ permissions RBAC
├── model_user_role.py         # Association User-Role
├── model_role.py              # Rôles utilisateurs
├── model_role_permission.py   # Permissions par rôle
├── model_permission.py        # Permissions globales
├── model_show.py              # Shows (conducteurs)
├── model_segment.py           # Segments d'un show
├── model_show_segment.py      # Association Show-Segment
├── model_show_presenter.py    # Association Show-Presenter
├── model_presenter.py         # Présentateurs
├── model_presenter_history.py # Historique présentateurs
├── model_guest.py             # Invités
├── model_segment_guests.py    # Association Segment-Guest
├── model_emissions.py         # Émissions (container)
├── model_notification.py      # Notifications
├── model_audit_log.py         # Logs d'audit
├── model_archive_log_audit.py # Logs archivés
├── model_auth_token.py        # Tokens révoqués
├── model_password_reset_token.py
├── model_invite_token.py
├── model_login_history.py
└── model_RoleTemplate.py
```

### Schémas Existants (17 fichiers)
```
app/schemas/
├── schemas.py                 # Token, Login, etc.
├── schema_users.py            # UserCreate, UserUpdate, UserResponse
├── schema_permissions.py      # PermissionUpdate, etc.
├── schema_roles.py            # RoleCreate, RoleResponse
├── schema_show.py             # ShowCreate, ShowWithDetails
├── schema_segment.py          # SegmentCreate, SegmentResponse
├── schema_presenters.py       # PresenterCreate, PresenterResponse
├── schema_guests.py           # GuestCreate, GuestResponse
├── schema_emission.py         # EmissionCreate, EmissionResponse
├── schema_notifications.py    # NotificationCreate
├── schema_audit_logs.py       # AuditLogResponse
└── ...
```

### Pattern de Base (BaseModel)
```python
# app/models/base_model.py
class BaseModel(Base):
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
```

---

## 🎯 Objectif du Skill

Créer des modèles SQLAlchemy et schémas Pydantic :
1. **Cohérents** : Soft delete, timestamps, conventions de nommage
2. **Relationnels** : back_populates, cascade, indexes
3. **Validés** : Schémas Pydantic avec contraintes
4. **Migrables** : Alembic automatique

---

## ✅ Règles Obligatoires

### 1. Structure d'un Modèle SQLAlchemy

```python
# app/models/model_{entity}.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_model import BaseModel

class {Entity}(BaseModel):
    """
    Modèle {Entity} pour la gestion des {entities}.
    
    Attributes:
        id: Identifiant unique
        name: Nom de l'{entity}
        description: Description optionnelle
        created_by: ID du créateur (User)
        created_at: Date de création (auto)
        updated_at: Date de mise à jour (auto)
        is_deleted: Soft delete flag (hérité)
        deleted_at: Date de suppression (hérité)
    
    Relationships:
        user: User qui a créé (Many-to-One)
        items: Items associés (One-to-Many)
    """
    __tablename__ = "{entities}"
    
    # Colonnes
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign Keys
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="{entities}")
    items = relationship("Item", back_populates="{entity}", cascade="all, delete-orphan")
    
    # Index composites (optionnel)
    __table_args__ = (
        Index('idx_{entities}_name_created', 'name', 'created_at'),
    )
    
    def __repr__(self):
        return f"<{Entity}(id={self.id}, name='{self.name}')>"
```

### 2. Héritage BaseModel Obligatoire

```python
# ✅ CORRECT - Hérite de BaseModel
from app.models.base_model import BaseModel

class MyEntity(BaseModel):
    __tablename__ = "my_entities"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

# ❌ INTERDIT - N'hérite pas de BaseModel
from app.db.database import Base

class MyEntity(Base):  # Pas de soft delete !
    __tablename__ = "my_entities"
```

### 3. Relations SQLAlchemy

```python
# One-to-Many (Un User a plusieurs Shows)
class User(BaseModel):
    shows = relationship("Show", back_populates="user", cascade="all, delete-orphan")

class Show(BaseModel):
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="shows")


# Many-to-Many (Show <-> Presenter via ShowPresenter)
class Show(BaseModel):
    presenters = relationship(
        "Presenter",
        secondary="show_presenters",
        back_populates="shows"
    )

class Presenter(BaseModel):
    shows = relationship(
        "Show",
        secondary="show_presenters",
        back_populates="presenters"
    )

# Table d'association
class ShowPresenter(Base):
    __tablename__ = "show_presenters"
    id = Column(Integer, primary_key=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    presenter_id = Column(Integer, ForeignKey("presenters.id"), nullable=False)


# One-to-One (User <-> UserPermissions)
class User(BaseModel):
    permissions = relationship(
        "UserPermissions",
        back_populates="user",
        uselist=False,  # Important !
        cascade="all, delete-orphan"
    )
```

### 4. Structure des Schémas Pydantic

```python
# app/schemas/schema_{entity}.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Base (champs communs)
class {Entity}Base(BaseModel):
    """Champs communs pour création et lecture."""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de l'{entity}")
    description: Optional[str] = Field(None, max_length=2000, description="Description")


# Create (pour POST)
class {Entity}Create({Entity}Base):
    """Schéma pour la création d'un {entity}."""
    pass


# Update (pour PATCH - tous optionnels)
class {Entity}Update(BaseModel):
    """Schéma pour la mise à jour d'un {entity}."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


# Response (pour GET)
class {Entity}Response({Entity}Base):
    """Schéma de réponse avec métadonnées."""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# Avec relations (optionnel)
class {Entity}WithRelations({Entity}Response):
    """Schéma avec relations chargées."""
    items: List["ItemResponse"] = []
    user: Optional["UserResponse"] = None
```

### 5. Conventions de Nommage

| Type | Convention | Exemple |
|------|------------|---------|
| Table | snake_case pluriel | `shows`, `presenters` |
| Colonne | snake_case | `created_at`, `user_id` |
| Foreign Key | `{table}_id` | `user_id`, `show_id` |
| Relation | snake_case | `user`, `shows`, `permissions` |
| Index | `idx_{table}_{columns}` | `idx_shows_status` |
| Classe Model | PascalCase | `Show`, `Presenter` |
| Classe Schema | PascalCase + suffixe | `ShowCreate`, `ShowResponse` |

### 6. Types de Colonnes Standards

```python
# Identifiants
id = Column(Integer, primary_key=True, index=True)
uuid = Column(String(36), unique=True, index=True)

# Texte
name = Column(String(255), nullable=False)
description = Column(Text, nullable=True)
email = Column(String(255), unique=True, index=True)

# Dates
created_at = Column(DateTime, server_default=func.now())
updated_at = Column(DateTime, onupdate=func.now())
scheduled_at = Column(DateTime, nullable=True)

# Booléens
is_active = Column(Boolean, default=True)
is_deleted = Column(Boolean, default=False)  # Via BaseModel

# Foreign Keys
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
parent_id = Column(Integer, ForeignKey("parents.id", ondelete="SET NULL"), nullable=True)

# Énumérations (via String)
status = Column(String(50), default="draft")  # draft, published, archived
```

---

## 🚫 Interdictions Explicites

### ❌ Modèle sans BaseModel
```python
# ❌ INTERDIT
class Show(Base):  # Pas de soft delete !
    __tablename__ = "shows"

# ✅ CORRECT
class Show(BaseModel):
    __tablename__ = "shows"
```

### ❌ Relation sans back_populates
```python
# ❌ INTERDIT (orphelin)
class User(BaseModel):
    shows = relationship("Show")  # Pas de back_populates !

# ✅ CORRECT
class User(BaseModel):
    shows = relationship("Show", back_populates="user")

class Show(BaseModel):
    user = relationship("User", back_populates="shows")
```

### ❌ Foreign Key sans ondelete
```python
# ❌ INTERDIT (comportement indéfini)
user_id = Column(Integer, ForeignKey("users.id"))

# ✅ CORRECT
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
# ou
user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
```

### ❌ Schema avec dict() Pydantic v2
```python
# ❌ INTERDIT
user_data = user_schema.dict()

# ✅ CORRECT
user_data = user_schema.model_dump()
```

### ❌ Schema Response sans from_attributes
```python
# ❌ INTERDIT (ne peut pas convertir ORM)
class UserResponse(BaseModel):
    id: int
    name: str

# ✅ CORRECT
class UserResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Modèle User (Existant)
```python
# app/models/model_user.py
class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relations
    permissions = relationship("UserPermissions", back_populates="user", uselist=False)
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    shows = relationship("Show", back_populates="user")
```

### Exemple 2 : Modèle Show (Existant)
```python
# app/models/model_show.py
class Show(BaseModel):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    broadcast_date = Column(DateTime, nullable=True)
    
    # Foreign Keys
    emission_id = Column(Integer, ForeignKey("emissions.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relations
    emission = relationship("Emission", back_populates="shows")
    user = relationship("User", back_populates="shows")
    segments = relationship("Segment", back_populates="show", cascade="all, delete-orphan")
    presenters = relationship("Presenter", secondary="show_presenters", back_populates="shows")
```

### Exemple 3 : Schema Show (Existant)
```python
# app/schemas/schema_show.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ShowBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    emission_id: Optional[int] = None

class ShowCreate(ShowBase):
    pass

class ShowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ShowResponse(ShowBase):
    id: int
    status: str
    created_at: datetime
    created_by: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)
```

---

## ✅ Checklist de Validation

### Modèle SQLAlchemy

- [ ] Hérite de `BaseModel`
- [ ] `__tablename__` défini (snake_case, pluriel)
- [ ] `id` en primary key avec `index=True`
- [ ] Colonnes avec `nullable` explicite
- [ ] `server_default=func.now()` pour `created_at`
- [ ] `onupdate=func.now()` pour `updated_at`
- [ ] Foreign Keys avec `ondelete`
- [ ] Relations avec `back_populates`
- [ ] Index sur colonnes recherchées
- [ ] Docstring avec description des attributs

### Schéma Pydantic

- [ ] `{Entity}Base` pour champs communs
- [ ] `{Entity}Create` pour POST
- [ ] `{Entity}Update` avec tous optionnels pour PATCH
- [ ] `{Entity}Response` pour GET avec `from_attributes=True`
- [ ] `Field()` avec contraintes (min_length, max_length)
- [ ] Types corrects (str, int, Optional, List)

### Migration Alembic

- [ ] `alembic revision --autogenerate -m "add_{entity}"`
- [ ] Vérifier le fichier généré
- [ ] Tester `upgrade head`
- [ ] Tester `downgrade -1`
- [ ] Commiter la migration

---

## 📁 Templates

### Template Modèle Complet
```python
# app/models/model_{entity}.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_model import BaseModel


class {Entity}(BaseModel):
    """
    Modèle {Entity}.
    
    Attributes:
        id: Identifiant unique
        name: Nom
        description: Description optionnelle
        created_by: Créateur
    """
    __tablename__ = "{entities}"
    
    # Colonnes
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="{entities}")
    
    def __repr__(self):
        return f"<{Entity}(id={self.id}, name='{self.name}')>"
```

### Template Schéma Complet
```python
# app/schemas/schema_{entity}.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class {Entity}Base(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class {Entity}Create({Entity}Base):
    pass


class {Entity}Update(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class {Entity}Response({Entity}Base):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
```

---

## 📚 Ressources Associées

- [architecture-guardian](../architecture-guardian/skill.md) - Structure globale
- [endpoint-creator](../endpoint-creator/skill.md) - Routes associées
- [migration-helper](../migration-helper/skill.md) - Migrations Alembic

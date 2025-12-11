# 📊 Modèles de données détaillés

Documentation complète des modèles de données avec relations et contraintes.

---

## Table des matières

1. [Conventions](#conventions)
2. [Modèle de base](#modèle-de-base)
3. [Entités métier](#entités-métier)
4. [Sécurité et authentification](#sécurité-et-authentification)
5. [Audit et traçabilité](#audit-et-traçabilité)
6. [Relations et associations](#relations-et-associations)

---

## 📐 Conventions

### Nomenclature des tables
- Noms en **snake_case** (ex: `user_permissions`)
- Pluriel pour les tables principales (ex: `users`, `shows`)
- Préfixe pour les tables d'association (ex: `show_presenters`)

### Champs standards
Tous les modèles héritent de `BaseModel` qui fournit :
- `id` : Clé primaire auto-incrémentée
- `created_at` : Date de création (auto)
- `updated_at` : Date de dernière mise à jour (auto)
- `is_deleted` : Soft delete (false par défaut)

### Soft Delete
Aucune donnée n'est supprimée physiquement. Le champ `is_deleted` est mis à `true`.

---

## 🏗️ Modèle de base

### BaseModel

**Fichier :** `app/models/base_model.py`

```python
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, nullable=False, default=False)
```

**Utilisation :**
```python
class User(BaseModel):
    __tablename__ = "users"
    email = Column(String, unique=True, nullable=False)
    # ...
```

---

## 👥 Entités métier

### 1. User (Utilisateur)

**Fichier :** `app/models/model_user.py`

**Table :** `users`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `email` | String | Unique, Not Null | Email de connexion |
| `password` | String | Not Null | Hash bcrypt du mot de passe |
| `created_at` | DateTime | Not Null | Date de création du compte |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Un utilisateur a plusieurs permissions
permissions = relationship("UserPermission", back_populates="user")

# Un utilisateur crée plusieurs shows
shows = relationship("Show", back_populates="user")

# Un utilisateur crée plusieurs emissions
emissions = relationship("Emission", back_populates="user")

# Un utilisateur crée plusieurs presenters
presenters = relationship("Presenter", back_populates="user")
```

**Schémas Pydantic :**
- `UserCreate` : email, password
- `UserResponse` : id, email, created_at
- `UserUpdate` : email (optionnel)

---

### 2. Show (Émission)

**Fichier :** `app/models/model_show.py`

**Table :** `shows`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `name` | String | Not Null | Nom de l'émission |
| `description` | Text | Nullable | Description |
| `user_id` | Integer | FK → users.id | Créateur |
| `created_at` | DateTime | Not Null | Date de création |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Show appartient à un User
user = relationship("User", back_populates="shows")

# Show a plusieurs Presenters (Many-to-Many)
presenters = relationship(
    "Presenter",
    secondary="show_presenters",
    back_populates="shows"
)

# Show a plusieurs Emissions
emissions = relationship("Emission", back_populates="show")
```

**Schémas Pydantic :**
- `ShowCreate` : name, description, presenter_ids
- `ShowResponse` : id, name, description, created_at, presenters
- `ShowUpdate` : name, description (optionnels)

---

### 3. Presenter (Présentateur)

**Fichier :** `app/models/model_presenter.py`

**Table :** `presenters`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `name` | String | Not Null | Nom du présentateur |
| `bio` | Text | Nullable | Biographie |
| `user_id` | Integer | FK → users.id | Créateur |
| `created_at` | DateTime | Not Null | Date de création |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Presenter créé par un User
user = relationship("User", back_populates="presenters")

# Presenter anime plusieurs Shows (Many-to-Many)
shows = relationship(
    "Show",
    secondary="show_presenters",
    back_populates="presenters"
)
```

---

### 4. Guest (Invité)

**Fichier :** `app/models/model_guest.py`

**Table :** `guests`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `name` | String | Not Null | Nom de l'invité |
| `bio` | Text | Nullable | Biographie |
| `contact_info` | String | Nullable | Email/téléphone |
| `created_at` | DateTime | Not Null | Date de création |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Guest participe à plusieurs Segments (Many-to-Many)
segments = relationship(
    "Segment",
    secondary="segment_guests",
    back_populates="guests"
)
```

---

### 5. Emission

**Fichier :** `app/models/model_emission.py`

**Table :** `emissions`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `title` | String | Not Null | Titre de l'émission |
| `date` | Date | Not Null | Date de diffusion |
| `show_id` | Integer | FK → shows.id | Émission parente |
| `user_id` | Integer | FK → users.id | Créateur |
| `created_at` | DateTime | Not Null | Date de création |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Emission appartient à un Show
show = relationship("Show", back_populates="emissions")

# Emission créée par un User
user = relationship("User", back_populates="emissions")

# Emission a plusieurs Segments
segments = relationship("Segment", back_populates="emission")
```

---

### 6. Segment

**Fichier :** `app/models/model_segment.py`

**Table :** `segments`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `title` | String | Not Null | Titre du segment |
| `description` | Text | Nullable | Description |
| `start_time` | Time | Nullable | Heure de début |
| `end_time` | Time | Nullable | Heure de fin |
| `emission_id` | Integer | FK → emissions.id | Émission parente |
| `created_at` | DateTime | Not Null | Date de création |
| `updated_at` | DateTime | Not Null | Dernière mise à jour |
| `is_deleted` | Boolean | Default: False | Soft delete |

**Relations :**
```python
# Segment appartient à une Emission
emission = relationship("Emission", back_populates="segments")

# Segment a plusieurs Guests (Many-to-Many)
guests = relationship(
    "Guest",
    secondary="segment_guests",
    back_populates="segments"
)
```

---

## 🔐 Sécurité et authentification

### 7. Permission

**Fichier :** `app/models/model_permission.py`

**Table :** `permissions`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `name` | String | Unique, Not Null | Nom technique (ex: "create_show") |
| `description` | Text | Nullable | Description lisible |

**Exemples de permissions :**
- `create_show`
- `update_show`
- `delete_show`
- `create_user`
- `update_user`
- `delete_user`

---

### 8. UserPermission (Association)

**Fichier :** `app/models/model_user_permission.py`

**Table :** `user_permissions`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `user_id` | Integer | FK → users.id | Utilisateur |
| `permission_id` | Integer | FK → permissions.id | Permission |
| `granted` | Boolean | Default: True | Activée ou non |

**Relations :**
```python
user = relationship("User", back_populates="permissions")
permission = relationship("Permission", back_populates="user_permissions")
```

**Utilisation :**
```python
# Vérifier si user a la permission "delete_show"
has_permission = db.query(UserPermission).filter_by(
    user_id=user.id,
    permission_id=permission.id,
    granted=True
).first() is not None
```

---

### 9. Role

**Fichier :** `app/models/model_role.py`

**Table :** `roles`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `name` | String | Unique, Not Null | Nom du rôle (ex: "admin", "editor") |
| `description` | Text | Nullable | Description |
| `permissions` | JSON | Nullable | Liste des permissions (IDs) |

**Exemples de rôles :**
```json
{
  "name": "admin",
  "permissions": [1, 2, 3, 4, 5, ...]  // Toutes les permissions
}

{
  "name": "editor",
  "permissions": [2, 3, 6, 7]  // Seulement create/update shows
}

{
  "name": "viewer",
  "permissions": []  // Lecture seule
}
```

---

### 10. RoleTemplate

**Fichier :** `app/models/model_role.py`

**Table :** `role_templates`

Structure identique à `Role` mais pour les templates réutilisables.

---

### 11. InviteToken

**Fichier :** `app/models/model_invite_token.py`

**Table :** `invite_tokens`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `token` | String (UUID) | Unique, Not Null | Token d'invitation |
| `email` | String | Not Null | Email invité |
| `expires_at` | DateTime | Not Null | Date d'expiration |
| `used` | Boolean | Default: False | Utilisé ou non |
| `created_at` | DateTime | Not Null | Date de création |

**Flux d'utilisation :**
1. Admin crée un InviteToken pour "user@example.com"
2. Email envoyé avec lien : `/auth/signup?token=xyz`
3. User s'inscrit avec le token
4. Token marqué comme `used=True`

---

### 12. PasswordResetToken

**Fichier :** `app/models/model_password_reset_token.py`

**Table :** `password_reset_tokens`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `token` | String (UUID) | Unique, Not Null | Token de reset |
| `user_id` | Integer | FK → users.id | Utilisateur |
| `expires_at` | DateTime | Not Null | Expiration (15min) |
| `used` | Boolean | Default: False | Utilisé ou non |
| `created_at` | DateTime | Not Null | Date de création |

**Flux d'utilisation :**
1. User oublie son mot de passe
2. POST `/auth/forgot-password` avec email
3. Token créé et envoyé par email
4. User clique sur lien : `/auth/reset-password?token=xyz`
5. User entre nouveau mot de passe
6. Token marqué comme `used=True`

---

### 13. RevokedToken

**Fichier :** `app/models/model_revoked_token.py`

**Table :** `revoked_tokens`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `token` | String | Unique, Not Null | JWT token révoqué |
| `revoked_at` | DateTime | Not Null | Date de révocation |

**Utilisation :**
```python
# Lors de la vérification du JWT
is_revoked = db.query(RevokedToken).filter_by(token=jwt_token).first()
if is_revoked:
    raise HTTPException(401, "Token has been revoked")
```

---

## 📝 Audit et traçabilité

### 14. AuditLog

**Fichier :** `app/models/model_audit_log.py`

**Table :** `audit_logs`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Identifiant unique |
| `user_id` | Integer | FK → users.id | Qui a fait l'action |
| `action` | String | Not Null | Type d'action (CREATE, UPDATE, DELETE) |
| `entity_type` | String | Not Null | Type d'entité (Show, User, etc.) |
| `entity_id` | Integer | Not Null | ID de l'entité |
| `changes` | JSON | Nullable | Détails des modifications |
| `timestamp` | DateTime | Not Null | Quand |

**Exemple de log :**
```json
{
  "user_id": 1,
  "action": "UPDATE",
  "entity_type": "Show",
  "entity_id": 123,
  "changes": {
    "name": {
      "old": "Morning Show",
      "new": "Good Morning Show"
    },
    "description": {
      "old": "...",
      "new": "..."
    }
  },
  "timestamp": "2025-12-11T10:30:00"
}
```

---

### 15. ArchiveLogAudit

**Fichier :** `app/models/model_archive_log_audit.py`

**Table :** `archive_log_audits`

Structure identique à `AuditLog` mais pour l'archivage des anciens logs.

**Utilisation :**
- Logs de plus de 1 an déplacés vers `archive_log_audits`
- Table `audit_logs` reste performante
- Possibilité de purger les archives après 5 ans

---

## 🔗 Relations et associations

### Tables d'association (Many-to-Many)

#### show_presenters

**Lie :** Show ↔ Presenter

| Champ | Type | Contraintes |
|-------|------|-------------|
| `show_id` | Integer | FK → shows.id |
| `presenter_id` | Integer | FK → presenters.id |

**Contrainte unique :** `(show_id, presenter_id)`

---

#### segment_guests

**Lie :** Segment ↔ Guest

| Champ | Type | Contraintes |
|-------|------|-------------|
| `segment_id` | Integer | FK → segments.id |
| `guest_id` | Integer | FK → guests.id |

**Contrainte unique :** `(segment_id, guest_id)`

---

## 📊 Diagramme de relations

```
User (1) ──────< (N) Show
  │                   │
  │                   └──< (N) Emission
  │                            │
  │                            └──< (N) Segment
  │                                     │
  │                                     └──< (N) Guest
  │
  ├──< (N) Presenter
  │         │
  │         └──< (N) Show (via show_presenters)
  │
  └──< (N) UserPermission ──> (1) Permission
```

---

## 🔧 Bonnes pratiques

### 1. Toujours utiliser Soft Delete
```python
# ❌ Mauvais
db.delete(show)

# ✅ Bon
show.is_deleted = True
db.commit()
```

### 2. Filtrer les soft-deleted par défaut
```python
# ❌ Mauvais
shows = db.query(Show).all()

# ✅ Bon
shows = db.query(Show).filter_by(is_deleted=False).all()
```

### 3. Utiliser les relations SQLAlchemy
```python
# ❌ Mauvais
show_id = 1
user_id = db.query(Show).get(show_id).user_id
user = db.query(User).get(user_id)

# ✅ Bon
show = db.query(Show).get(1)
user = show.user  # Relation chargée automatiquement
```

### 4. Valider avec Pydantic avant l'insertion
```python
# ✅ Bon
from app.schemas.schema_show import ShowCreate

@router.post("/shows")
def create_show(show: ShowCreate, db: Session = Depends(get_db)):
    # show déjà validé par Pydantic
    new_show = Show(**show.dict())
    db.add(new_show)
    db.commit()
```

---

**Dernière mise à jour :** 11 décembre 2025

# 🏛️ Architecture Guardian

> **Skill critique** : Protège l'architecture globale du projet api.audace contre les violations structurelles.

---

## 📋 Contexte du Projet

### Stack Technique
| Technologie | Version | Rôle |
|-------------|---------|------|
| FastAPI | 0.109.0 | Framework web async |
| Python | 3.11+ | Langage principal |
| SQLAlchemy | 2.0 | ORM avec relations |
| PostgreSQL | 15 | Base de données |
| Pydantic | v2 | Validation (`model_dump()`) |
| Alembic | 1.13+ | Migrations DB |
| JWT | python-jose | Authentification |
| pytest | 8.0+ | Tests |

### Organisation Actuelle du Code

```
api.audace/
├── maintest.py              # Point d'entrée FastAPI
├── app/
│   ├── config/              # Configuration (settings)
│   ├── db/
│   │   ├── database.py      # Session DB, get_db()
│   │   └── crud/            # 26 fichiers CRUD
│   ├── models/              # 25 modèles SQLAlchemy
│   ├── schemas/             # 17 schémas Pydantic
│   ├── utils/               # Utilitaires (hash, tokens)
│   ├── middleware/          # LoggerMiddleware, APIVersionMiddleware
│   └── exceptions/          # Exceptions custom
├── core/
│   └── auth/                # OAuth2, JWT (oauth2.py)
├── routeur/                 # 14 fichiers de routes
│   └── search_route/        # Routes de recherche
├── alembic/
│   └── versions/            # 14 migrations
└── tests/                   # Tests pytest
```

### Patterns Existants
- **Soft delete** via `BaseModel` (is_deleted, deleted_at)
- **Relations SQLAlchemy** avec cascade et back_populates
- **RBAC** : 40+ permissions granulaires dans UserPermissions
- **Audit logging** : Traçabilité des actions critiques

---

## 🎯 Objectif du Skill

**Garantir que toute modification respecte la structure établie :**
1. Séparation stricte des couches (Routes → CRUD → Models → Schemas)
2. Intégrité des relations SQLAlchemy
3. Migrations Alembic pour tout changement DB
4. Soft delete obligatoire

---

## ✅ Règles Obligatoires

### 1. Séparation des Couches (STRICTEMENT RESPECTER)

```
ROUTEUR (API Endpoints)
    │ importe uniquement
    ▼
CRUD (Logique métier)
    │ utilise
    ▼
MODELS (SQLAlchemy)
    │ valide avec
    ▼
SCHEMAS (Pydantic)
```

**Règles d'import :**
```python
# ✅ Dans routeur/*.py
from app.db.crud.crud_users import get_user_or_404
from app.db.database import get_db
from core.auth.oauth2 import get_current_user

# ✅ Dans app/db/crud/*.py
from app.models.model_user import User
from app.schemas.schema_users import UserCreate

# ❌ INTERDIT
from routeur.users_route import ...  # Jamais CRUD → Routeur
from app.models.model_user import User  # Jamais Schema → Model
```

### 2. Nommage des Fichiers

| Type | Pattern | Exemple |
|------|---------|---------|
| Route | `{entity}_route.py` | `show_route.py` |
| CRUD | `crud_{entity}.py` | `crud_show.py` |
| Model | `model_{entity}.py` | `model_show.py` |
| Schema | `schema_{entity}.py` | `schema_show.py` |

### 3. Structure d'un Routeur

```python
# routeur/{entity}_route.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.crud.crud_{entity} import (
    create_{entity}, get_{entity}s, get_{entity}_by_id,
    update_{entity}, delete_{entity}
)
from app.schemas.schema_{entity} import {Entity}Create, {Entity}Update, {Entity}Response
from core.auth.oauth2 import get_current_user
from app.models.model_user import User

router = APIRouter(
    prefix="/{entities}",
    tags=['{entities}']
)

@router.get("/", response_model=List[{Entity}Response])
def get_all_{entities}(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    return get_{entity}s(db, skip=skip, limit=limit)
```

### 4. Structure d'un CRUD

```python
# app/db/crud/crud_{entity}.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from app.models.model_{entity} import {Entity}
from app.schemas.schema_{entity} import {Entity}Create, {Entity}Update

def get_{entity}s(db: Session, skip: int = 0, limit: int = 100):
    """Récupère les {entity}s non supprimés avec pagination."""
    return db.query({Entity}).filter(
        {Entity}.is_deleted == False
    ).offset(skip).limit(limit).all()

def get_{entity}_by_id(db: Session, {entity}_id: int):
    """Récupère un {entity} par ID ou lève 404."""
    {entity} = db.query({Entity}).filter(
        {Entity}.id == {entity}_id,
        {Entity}.is_deleted == False
    ).first()
    if not {entity}:
        raise HTTPException(status_code=404, detail="{Entity} not found")
    return {entity}

def soft_delete_{entity}(db: Session, {entity}_id: int, deleted_by: int):
    """Suppression logique (soft delete)."""
    {entity} = get_{entity}_by_id(db, {entity}_id)
    {entity}.is_deleted = True
    {entity}.deleted_at = datetime.utcnow()
    db.commit()
    return {entity}
```

### 5. Soft Delete Obligatoire

```python
# Tout modèle métier DOIT hériter de BaseModel
from app.models.base_model import BaseModel

class MyEntity(BaseModel):
    __tablename__ = "my_entities"
    # ... colonnes
```

```python
# BaseModel fournit automatiquement :
is_deleted = Column(Boolean, default=False)
deleted_at = Column(DateTime, nullable=True)
```

### 6. Migrations Alembic Obligatoires

**Pour TOUT changement de modèle :**
```bash
# 1. Modifier le modèle
# 2. Générer la migration
alembic revision --autogenerate -m "description_claire"

# 3. Vérifier le fichier généré
# 4. Appliquer
alembic upgrade head

# 5. Tester downgrade
alembic downgrade -1
alembic upgrade head
```

---

## 🚫 Interdictions Explicites

### ❌ Import Circulaire
```python
# routeur/show_route.py
from app.db.crud.crud_show import create_show  # ✅

# app/db/crud/crud_show.py
from routeur.show_route import router  # ❌ INTERDIT !
```

### ❌ Accès Direct DB dans Routeur
```python
# ❌ INTERDIT
@router.get("/shows")
def get_shows(db: Session = Depends(get_db)):
    return db.query(Show).all()  # ❌ Query direct !

# ✅ CORRECT
@router.get("/shows")
def get_shows(db: Session = Depends(get_db)):
    return get_shows_crud(db)  # Appel CRUD
```

### ❌ Hard Delete
```python
# ❌ INTERDIT
db.delete(entity)
db.commit()

# ✅ CORRECT
entity.is_deleted = True
entity.deleted_at = datetime.utcnow()
db.commit()
```

### ❌ Modification Modèle sans Migration
```python
# ❌ INTERDIT : Ajouter colonne sans migration
class User(BaseModel):
    new_column = Column(String)  # Sans alembic !

# ✅ CORRECT
# 1. Ajouter la colonne
# 2. alembic revision --autogenerate -m "add_new_column_to_user"
# 3. alembic upgrade head
```

### ❌ Ignorer les Exceptions
```python
# ❌ INTERDIT
try:
    result = db.query(User).first()
except:
    pass  # Silencieux !

# ✅ CORRECT
try:
    result = db.query(User).first()
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

### ❌ dict() avec Pydantic v2
```python
# ❌ INTERDIT (déprécié)
user_data = user_schema.dict()

# ✅ CORRECT
user_data = user_schema.model_dump()
user_data = user_schema.model_dump(exclude={"password"})
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Route Show (Correct)
```python
# routeur/show_route.py
router = APIRouter(prefix="/shows", tags=['shows'])

@router.post("/detail", status_code=status.HTTP_201_CREATED)
async def create_show_with_details_endpoint(
    show_data: ShowCreateWithDetail,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    show = create_show_with_details(
        db=db,
        show_data=show_data,
        curent_user_id=current_user.id
    )
    return {"message": "Show created successfully.", "show": show}
```

### Exemple 2 : CRUD Users (Correct)
```python
# app/db/crud/crud_users.py
def get_user_or_404_with_permissions(db: Session, user_id: int) -> dict:
    user = db.query(User).options(
        joinedload(User.permissions)
    ).filter(
        User.id == user_id,
        User.is_active == True
    ).first()
    
    if not user:
        raise NoResultFound("User not found or inactive")
    return user
```

### Exemple 3 : BaseModel (Pattern Soft Delete)
```python
# app/models/base_model.py
class BaseModel(Base):
    __abstract__ = True
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
```

---

## ✅ Checklist de Validation

### Avant Commit

- [ ] **Structure** : Fichier dans le bon dossier (routeur/, crud/, models/, schemas/)
- [ ] **Nommage** : Pattern respecté (`{type}_{entity}.py`)
- [ ] **Imports** : Aucun import circulaire (CRUD ↛ Routeur)
- [ ] **Soft Delete** : Utilisation de `is_deleted`, pas de `db.delete()`
- [ ] **Migration** : Si modèle modifié → `alembic revision --autogenerate`
- [ ] **Pydantic** : `model_dump()` et non `dict()`

### Avant PR

- [ ] **Tests passent** : `pytest`
- [ ] **Pas de TODO/FIXME** : Code propre
- [ ] **Documentation** : Docstrings présentes
- [ ] **Logs** : Exceptions loggées, pas ignorées
- [ ] **Migration testée** : `alembic upgrade head` + `alembic downgrade -1`

### Script de Validation Rapide

```bash
# Vérifier imports circulaires
grep -r "from routeur" app/db/crud/ && echo "❌ Import circulaire détecté!"

# Vérifier hard delete
grep -rn "db.delete(" routeur/ app/db/crud/ && echo "⚠️ Hard delete détecté!"

# Vérifier dict() déprécié
grep -rn "\.dict()" app/ routeur/ && echo "⚠️ dict() déprécié détecté!"

# Vérifier migrations pending
alembic current
```

---

## 🔗 Fichiers Référence

| Fichier | Rôle | Chemin |
|---------|------|--------|
| Point d'entrée | Application FastAPI | `maintest.py` |
| Base Model | Soft delete pattern | `app/models/base_model.py` |
| Database | Session factory | `app/db/database.py` |
| Auth | OAuth2, JWT | `core/auth/oauth2.py` |
| Guide Agent | Documentation complète | `AGENT.md` |

---

## 📚 Ressources Associées

- [AGENT.md](../../../AGENT.md) - Guide complet pour agents IA
- [docs/architecture/](../../../docs/architecture/) - Documentation architecture
- [endpoint-creator](../endpoint-creator/skill.md) - Création de routes
- [model-generator](../model-generator/skill.md) - Création de modèles

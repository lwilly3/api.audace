# 🚀 Endpoint Creator

> **Skill prioritaire** : Création normalisée d'endpoints FastAPI conformes aux standards api.audace.

---

## 📋 Contexte du Projet

### Routes Existantes (14 fichiers)
```
routeur/
├── auth.py                 # POST /auth/login, /logout, /signup
├── users_route.py          # CRUD /users
├── show_route.py           # CRUD /shows (complexe, avec details)
├── presenter_route.py      # CRUD /presenters
├── guest_route.py          # CRUD /guests
├── emission_route.py       # CRUD /emissions
├── segment_route.py        # CRUD /segments
├── role_route.py           # CRUD /roles
├── permissions_route.py    # CRUD /permissions
├── notification_route.py   # CRUD /notifications
├── audit_log_route.py      # GET /audit-logs
├── dashbord_route.py       # GET /dashboard/*
├── setup_route.py          # POST /setup (sans auth)
├── version_route.py        # GET /version
└── search_route/           # Routes de recherche
```

### Pattern d'Enregistrement (maintest.py)
```python
from routeur import auth, users_route, show_route, ...

app.include_router(auth.router)
app.include_router(users_route.router)
app.include_router(show_route.router)
```

---

## 🎯 Objectif du Skill

Créer des endpoints FastAPI :
1. **Structurés** : Fichier dédié par domaine
2. **Sécurisés** : Authentification et permissions
3. **Documentés** : OpenAPI automatique
4. **Testables** : Patterns facilement mockables

---

## ✅ Règles Obligatoires

### 1. Structure d'un Fichier Route

```python
# routeur/{entity}_route.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# Database
from app.db.database import get_db

# CRUD functions
from app.db.crud.crud_{entity} import (
    create_{entity},
    get_{entity}s,
    get_{entity}_by_id,
    update_{entity},
    soft_delete_{entity}
)

# Schemas
from app.schemas.schema_{entity} import (
    {Entity}Create,
    {Entity}Update,
    {Entity}Response
)

# Auth
from core.auth.oauth2 import get_current_user
from app.models.model_user import User

# Initialisation du router
router = APIRouter(
    prefix="/{entities}",
    tags=['{entities}']
)
```

### 2. CRUD Endpoints Standards

```python
# CREATE
@router.post("/", response_model={Entity}Response, status_code=status.HTTP_201_CREATED)
def create_{entity}_endpoint(
    {entity}_data: {Entity}Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouvel {entity}."""
    return create_{entity}(db=db, {entity}_data={entity}_data, user_id=current_user.id)


# READ ALL (avec pagination)
@router.get("/", response_model=List[{Entity}Response])
def get_{entity}s_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments")
):
    """Récupérer tous les {entity}s avec pagination."""
    return get_{entity}s(db=db, skip=skip, limit=limit)


# READ ONE
@router.get("/{{{entity}_id}}", response_model={Entity}Response)
def get_{entity}_endpoint(
    {entity}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un {entity} par son ID."""
    return get_{entity}_by_id(db=db, {entity}_id={entity}_id)


# UPDATE
@router.patch("/{{{entity}_id}}", response_model={Entity}Response)
def update_{entity}_endpoint(
    {entity}_id: int,
    {entity}_data: {Entity}Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un {entity}."""
    return update_{entity}(db=db, {entity}_id={entity}_id, {entity}_data={entity}_data)


# DELETE (soft)
@router.delete("/{{{entity}_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{entity}_endpoint(
    {entity}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un {entity} (soft delete)."""
    soft_delete_{entity}(db=db, {entity}_id={entity}_id, deleted_by=current_user.id)
    return None
```

### 3. HTTP Methods et Status Codes

| Operation | Method | Route | Status Code | Response |
|-----------|--------|-------|-------------|----------|
| Create | POST | `/` | 201 | Entity créée |
| Read All | GET | `/` | 200 | Liste |
| Read One | GET | `/{id}` | 200 | Entity |
| Update | PATCH | `/{id}` | 200 | Entity mise à jour |
| Replace | PUT | `/{id}` | 200 | Entity remplacée |
| Delete | DELETE | `/{id}` | 204 | Rien |

### 4. Gestion des Erreurs

```python
from fastapi import HTTPException, status

# 404 - Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"{Entity} with id {entity_id} not found"
)

# 400 - Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid data provided"
)

# 403 - Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to perform this action"
)

# 409 - Conflict
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Entity already exists"
)

# 500 - Server Error
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="An unexpected error occurred"
)
```

### 5. Query Parameters Standards

```python
# Pagination
skip: int = Query(0, ge=0, description="Offset")
limit: int = Query(100, ge=1, le=500, description="Limit")

# Filtrage
status: Optional[str] = Query(None, description="Filter by status")
search: Optional[str] = Query(None, description="Search in name/title")

# Tri
sort_by: str = Query("created_at", description="Sort field")
sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
```

### 6. Authentification

```python
# Route publique (RARE - seulement /auth/login, /setup)
@router.get("/public")
def public_endpoint():
    pass

# Route authentifiée (STANDARD)
@router.get("/protected")
def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    pass

# Route avec vérification de permission
@router.delete("/{id}")
def admin_only_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.permissions.can_delete_shows:
        raise HTTPException(status_code=403, detail="Permission denied")
```

---

## 🚫 Interdictions Explicites

### ❌ Query DB dans le Routeur
```python
# ❌ INTERDIT
@router.get("/shows")
def get_shows(db: Session = Depends(get_db)):
    return db.query(Show).filter(Show.is_deleted == False).all()

# ✅ CORRECT
@router.get("/shows")
def get_shows(db: Session = Depends(get_db)):
    return get_shows_crud(db)
```

### ❌ Logique Métier dans le Routeur
```python
# ❌ INTERDIT
@router.post("/shows")
def create_show(show_data: ShowCreate, db: Session = Depends(get_db)):
    show = Show(**show_data.model_dump())
    show.status = "draft"
    for segment in show_data.segments:
        # Logique complexe...
    db.add(show)
    db.commit()
    return show

# ✅ CORRECT
@router.post("/shows")
def create_show(show_data: ShowCreate, db: Session = Depends(get_db)):
    return create_show_with_details(db, show_data)  # Déléguer au CRUD
```

### ❌ Route sans Authentification (sauf exception)
```python
# ❌ INTERDIT (sur routes métier)
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return get_users_crud(db)  # Pas d'auth !

# ✅ CORRECT
@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Auth obligatoire
):
    return get_users_crud(db)
```

### ❌ Réponses sans Schéma
```python
# ❌ INTERDIT
@router.get("/users/{id}")
def get_user(id: int, db: Session = Depends(get_db)):
    user = get_user_crud(db, id)
    return {"id": user.id, "email": user.email, "password": user.password}  # Password exposé !

# ✅ CORRECT
@router.get("/users/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    return get_user_crud(db, id)  # Schéma filtre automatiquement
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Route Show (Existant)
```python
# routeur/show_route.py
router = APIRouter(prefix="/shows", tags=['shows'])

@router.post("/detail", status_code=status.HTTP_201_CREATED)
async def create_show_with_details_endpoint(
    show_data: ShowCreateWithDetail,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    try:
        show = create_show_with_details(
            db=db, show_data=show_data, curent_user_id=current_user.id
        )
        return {"message": "Show created successfully.", "show": show}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
```

### Exemple 2 : Route avec Pagination (Pattern)
```python
# routeur/guest_route.py
@router.get("/", response_model=List[GuestResponse])
def get_guests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    return get_guests_crud(db, skip=skip, limit=limit)
```

### Exemple 3 : Enregistrement dans maintest.py
```python
# maintest.py
from routeur import show_route

# Dans la section des routers
app.include_router(show_route.router)
```

---

## ✅ Checklist de Validation

### Avant Création

- [ ] Vérifier qu'aucune route similaire n'existe
- [ ] Définir les endpoints nécessaires (CRUD complet ?)
- [ ] Créer le fichier CRUD correspondant d'abord
- [ ] Créer les schémas Pydantic nécessaires

### Pendant Création

- [ ] `router = APIRouter(prefix=..., tags=[...])`
- [ ] Imports dans l'ordre : fastapi → sqlalchemy → app.db → app.schemas → core.auth
- [ ] `response_model` sur tous les GET/POST/PATCH
- [ ] `status_code` explicite sur POST (201) et DELETE (204)
- [ ] `Depends(get_current_user)` sauf routes publiques
- [ ] Gestion d'erreurs avec try/except sur opérations complexes

### Après Création

- [ ] Ajouter `from routeur import {entity}_route` dans maintest.py
- [ ] Ajouter `app.include_router({entity}_route.router)` dans maintest.py
- [ ] Tester avec `/docs` (Swagger UI)
- [ ] Créer les tests dans `tests/test_{entity}.py`

---

## 📁 Template de Fichier Route

```python
# routeur/{entity}_route.py
"""
Routes pour la gestion des {Entity}s.

Endpoints:
    - POST   /{entities}      : Créer un {entity}
    - GET    /{entities}      : Liste avec pagination
    - GET    /{entities}/{id} : Détail d'un {entity}
    - PATCH  /{entities}/{id} : Mise à jour partielle
    - DELETE /{entities}/{id} : Suppression (soft)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.crud.crud_{entity} import (
    create_{entity}, get_{entity}s, get_{entity}_by_id,
    update_{entity}, soft_delete_{entity}
)
from app.schemas.schema_{entity} import {Entity}Create, {Entity}Update, {Entity}Response
from core.auth.oauth2 import get_current_user
from app.models.model_user import User

router = APIRouter(
    prefix="/{entities}",
    tags=['{entities}']
)


@router.post("/", response_model={Entity}Response, status_code=status.HTTP_201_CREATED)
def create_{entity}_endpoint(
    data: {Entity}Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouvel {entity}."""
    return create_{entity}(db=db, data=data, created_by=current_user.id)


@router.get("/", response_model=List[{Entity}Response])
def get_{entity}s_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Récupérer tous les {entity}s avec pagination."""
    return get_{entity}s(db=db, skip=skip, limit=limit)


@router.get("/{{{entity}_id}}", response_model={Entity}Response)
def get_{entity}_endpoint(
    {entity}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un {entity} par ID."""
    return get_{entity}_by_id(db=db, {entity}_id={entity}_id)


@router.patch("/{{{entity}_id}}", response_model={Entity}Response)
def update_{entity}_endpoint(
    {entity}_id: int,
    data: {Entity}Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un {entity}."""
    return update_{entity}(db=db, {entity}_id={entity}_id, data=data)


@router.delete("/{{{entity}_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{entity}_endpoint(
    {entity}_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un {entity} (soft delete)."""
    soft_delete_{entity}(db=db, {entity}_id={entity}_id, deleted_by=current_user.id)
    return None
```

---

## 📚 Ressources Associées

- [architecture-guardian](../architecture-guardian/skill.md) - Structure globale
- [model-generator](../model-generator/skill.md) - Modèles SQLAlchemy
- [security-rules](../security-rules/skill.md) - Authentification

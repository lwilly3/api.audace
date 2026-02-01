# 📚 API Documentation Standard

> **Skill recommandé** : Standards de documentation OpenAPI/Swagger pour api.audace.

---

## 📋 Contexte du Projet

### Documentation Actuelle (maintest.py)
```python
app = FastAPI(
    title="Hapson API",
    description="API de gestion radio - Shows, Emissions, Presenters",
    version=__version__,
    contact={
        "name": "Support API",
        "email": "support@hapson.com"
    },
    license_info={
        "name": "MIT",
    }
)
```

### Routes Documentées
```
/docs      → Swagger UI
/redoc     → ReDoc
/openapi.json → Schema JSON
```

---

## 🎯 Objectif du Skill

Standardiser la documentation API pour :
1. **Auto-documentation** via docstrings
2. **Exemples** clairs pour chaque endpoint
3. **Descriptions** des erreurs possibles
4. **Tags** cohérents pour regroupement

---

## ✅ Règles Obligatoires

### 1. Docstring d'Endpoint

```python
@router.post("/", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
def create_show(
    show_data: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une nouvelle émission.
    
    Crée un nouveau show dans le système avec les informations fournies.
    L'utilisateur connecté sera automatiquement défini comme créateur.
    
    - **title**: Titre de l'émission (obligatoire)
    - **type**: Type d'émission (actualité, musique, débat...)
    - **duration**: Durée en minutes
    - **broadcast_date**: Date de diffusion (optionnel)
    
    Retourne le show créé avec son ID.
    
    Permissions requises: `can_create_shows`
    """
    return crud_show.create_show(db, show_data, current_user.id)
```

### 2. Réponses Multiples

```python
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

@router.get(
    "/{show_id}",
    response_model=ShowResponse,
    responses={
        200: {
            "description": "Show trouvé",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Journal du Matin",
                        "type": "actualité",
                        "status": "Planifié",
                        "duration": 60
                    }
                }
            }
        },
        404: {
            "description": "Show non trouvé",
            "content": {
                "application/json": {
                    "example": {"detail": "Show with id 123 not found"}
                }
            }
        },
        403: {
            "description": "Permission insuffisante",
            "content": {
                "application/json": {
                    "example": {"detail": "Permission denied: cannot view shows"}
                }
            }
        }
    }
)
def get_show(show_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un show par son ID.
    
    Retourne les détails complets du show incluant ses segments 
    et présentateurs associés.
    """
    show = crud_show.get_show_by_id(db, show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found"
        )
    return show
```

### 3. Tags de Router

```python
# routeur/show_route.py
router = APIRouter(
    prefix="/shows",
    tags=["Shows"],  # Tag pour Swagger
    responses={
        401: {"description": "Non authentifié"},
        403: {"description": "Permission insuffisante"}
    }
)

# routeur/emission_route.py
router = APIRouter(
    prefix="/emissions",
    tags=["Emissions"],
    responses={
        401: {"description": "Non authentifié"}
    }
)

# routeur/segment_route.py
router = APIRouter(
    prefix="/segments",
    tags=["Segments"]
)
```

### 4. Configuration OpenAPI

```python
# maintest.py

from fastapi import FastAPI
from app.__version__ import __version__

# Tags metadata pour ordre et description
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Opérations d'authentification (login, logout, refresh token)"
    },
    {
        "name": "Users",
        "description": "Gestion des utilisateurs et permissions"
    },
    {
        "name": "Emissions",
        "description": "Programmes radio récurrents"
    },
    {
        "name": "Shows",
        "description": "Épisodes/diffusions des émissions"
    },
    {
        "name": "Segments",
        "description": "Sections des shows (interviews, chroniques...)"
    },
    {
        "name": "Presenters",
        "description": "Animateurs des émissions"
    },
    {
        "name": "Guests",
        "description": "Invités des segments"
    },
    {
        "name": "Audit",
        "description": "Logs d'audit et traçabilité"
    }
]

app = FastAPI(
    title="Hapson Radio API",
    description="""
    ## API de Gestion Radio
    
    Cette API permet de gérer :
    - 📻 **Émissions** et leurs épisodes (shows)
    - 🎙️ **Présentateurs** et leurs affectations
    - 👥 **Invités** et leur participation
    - 📊 **Segments** et leur organisation
    
    ### Authentification
    
    L'API utilise JWT Bearer tokens. Obtenir un token via `/auth/login`.
    
    ### Permissions
    
    Le système RBAC contrôle l'accès aux ressources.
    Voir la documentation des permissions pour plus de détails.
    """,
    version=__version__,
    openapi_tags=tags_metadata,
    contact={
        "name": "Support API Hapson",
        "email": "support@hapson.com",
        "url": "https://hapson.com/support"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc"
)
```

### 5. Exemples dans les Schémas

```python
# app/schemas/show_schema.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ShowBase(BaseModel):
    """Schéma de base pour les shows."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Titre de l'émission",
        json_schema_extra={"example": "Journal du Matin"}
    )
    type: str = Field(
        ...,
        description="Type d'émission",
        json_schema_extra={"example": "actualité"}
    )
    duration: int = Field(
        ...,
        gt=0,
        description="Durée en minutes",
        json_schema_extra={"example": 60}
    )
    description: Optional[str] = Field(
        None,
        description="Description détaillée",
        json_schema_extra={"example": "Actualités matinales et interviews"}
    )


class ShowCreate(ShowBase):
    """Schéma pour créer un show."""
    
    broadcast_date: Optional[datetime] = Field(
        None,
        description="Date de diffusion prévue",
        json_schema_extra={"example": "2025-01-15T07:00:00"}
    )
    emission_id: Optional[int] = Field(
        None,
        description="ID de l'émission parente",
        json_schema_extra={"example": 1}
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Journal du 15 janvier",
                "type": "actualité",
                "duration": 60,
                "description": "Actualités du jour",
                "broadcast_date": "2025-01-15T07:00:00",
                "emission_id": 1
            }
        }
    )


class ShowResponse(ShowBase):
    """Schéma de réponse pour un show."""
    
    id: int = Field(..., description="Identifiant unique")
    status: str = Field(..., description="Statut actuel")
    created_at: datetime = Field(..., description="Date de création")
    created_by: Optional[int] = Field(None, description="ID du créateur")
    
    model_config = ConfigDict(from_attributes=True)
```

### 6. Query Parameters Documentés

```python
from fastapi import Query
from typing import Optional, List

@router.get("/", response_model=List[ShowResponse])
def list_shows(
    skip: int = Query(
        default=0,
        ge=0,
        description="Nombre d'éléments à sauter (pagination)"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Nombre maximum d'éléments à retourner"
    ),
    status: Optional[str] = Query(
        default=None,
        description="Filtrer par statut (En préparation, Planifié, Terminé...)"
    ),
    type: Optional[str] = Query(
        default=None,
        description="Filtrer par type (actualité, musique, débat...)"
    ),
    search: Optional[str] = Query(
        default=None,
        min_length=2,
        description="Recherche dans le titre"
    ),
    db: Session = Depends(get_db)
):
    """
    Lister les shows avec filtres et pagination.
    
    Retourne une liste de shows correspondant aux critères.
    La pagination est obligatoire (limite max: 100).
    """
    return crud_show.get_shows(db, skip, limit, status, type, search)
```

---

## 🚫 Interdictions Explicites

### ❌ Endpoint sans Docstring
```python
# ❌ INTERDIT
@router.post("/")
def create_show(show: ShowCreate, db: Session = Depends(get_db)):
    return crud_show.create(db, show)

# ✅ CORRECT
@router.post("/")
def create_show(show: ShowCreate, db: Session = Depends(get_db)):
    """
    Créer un nouveau show.
    
    - **title**: Titre obligatoire
    - **type**: Type d'émission
    
    Retourne le show créé.
    """
    return crud_show.create(db, show)
```

### ❌ Field sans Description
```python
# ❌ INTERDIT
class ShowCreate(BaseModel):
    title: str
    duration: int

# ✅ CORRECT
class ShowCreate(BaseModel):
    title: str = Field(..., description="Titre de l'émission")
    duration: int = Field(..., gt=0, description="Durée en minutes")
```

### ❌ Router sans Tag
```python
# ❌ INTERDIT
router = APIRouter(prefix="/shows")

# ✅ CORRECT
router = APIRouter(prefix="/shows", tags=["Shows"])
```

---

## 📝 Templates

### Template Endpoint CRUD

```python
@router.post(
    "/",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Créé avec succès"},
        400: {"description": "Données invalides"},
        401: {"description": "Non authentifié"},
        403: {"description": "Permission insuffisante"},
        409: {"description": "Conflit (doublon)"}
    }
)
def create_entity(
    entity_data: EntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une nouvelle entité.
    
    Description détaillée de l'opération.
    
    - **field1**: Description du champ 1
    - **field2**: Description du champ 2
    
    Permissions requises: `can_create_entities`
    """
    return crud.create(db, entity_data)
```

---

## ✅ Checklist de Validation

### Endpoints

- [ ] Docstring présente et descriptive
- [ ] Responses documentées (200, 4xx, 5xx)
- [ ] Query params avec descriptions
- [ ] Tags assignés au router

### Schémas

- [ ] Fields avec description
- [ ] Exemples via json_schema_extra
- [ ] Contraintes documentées (min, max)

### OpenAPI

- [ ] Tags metadata configurés
- [ ] Description API complète
- [ ] Contact et licence définis

---

## 📚 Ressources Associées

- [endpoint-creator](../endpoint-creator/skill.md) - Création d'endpoints
- [model-generator](../model-generator/skill.md) - Schémas Pydantic
- [architecture-guardian](../architecture-guardian/skill.md) - Structure

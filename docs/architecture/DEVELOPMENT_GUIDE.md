# 💻 Guide de développement

Guide complet pour développer, tester et maintenir l'API Audace.

---

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation locale](#installation-locale)
3. [Structure du code](#structure-du-code)
4. [Développer une nouvelle fonctionnalité](#développer-une-nouvelle-fonctionnalité)
5. [Tests](#tests)
6. [Migrations de base de données](#migrations-de-base-de-données)
7. [Bonnes pratiques](#bonnes-pratiques)
8. [Débogage](#débogage)

---

## 🛠️ Prérequis

### Logiciels requis

| Outil | Version minimale | Installation |
|-------|------------------|--------------|
| Python | 3.11+ | `brew install python@3.11` (macOS) |
| PostgreSQL | 15+ | `brew install postgresql@15` |
| Docker | 24+ | [docker.com](https://www.docker.com/products/docker-desktop) |
| Git | 2.40+ | `brew install git` |

### Connaissances recommandées

- Python 3.11+
- FastAPI / Async Python
- SQLAlchemy ORM
- PostgreSQL
- JWT / OAuth2
- Docker / Docker Compose

---

## 🚀 Installation locale

### 1. Cloner le repository

```bash
git clone https://github.com/lwilly3/api.audace.git
cd api.audace
```

---

### 2. Créer un environnement virtuel

```bash
# Créer l'environnement
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

---

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Contenu de `requirements.txt` :**
```
fastapi==0.109.0
uvicorn[standard]==0.25.0
gunicorn==21.2.0
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.2.1
email-validator==2.1.0
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

---

### 4. Configuration de l'environnement

Créer un fichier `.env` à la racine :

```bash
# Base de données
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=votre_mot_de_passe
DATABASE_NAME=audace_db

# JWT
SECRET_KEY=votre_secret_key_très_longue_et_sécurisée
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRATION_MINUTE=30

# Email (optionnel pour reset password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre_email@gmail.com
SMTP_PASSWORD=votre_app_password
```

**Générer un SECRET_KEY sécurisé :**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

### 5. Créer la base de données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base
CREATE DATABASE audace_db;

# Quitter
\q
```

---

### 6. Exécuter les migrations Alembic

```bash
# Appliquer toutes les migrations
alembic upgrade head

# Vérifier l'état
alembic current
```

**Résultat attendu :**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 75e8b3bb0750, initial
INFO  [alembic.runtime.migration] Running upgrade 75e8b3bb0750 -> 2f97ab44d3ed, add permissions
...
```

---

### 7. Lancer l'API en développement

```bash
# Avec Uvicorn (rechargement auto)
uvicorn maintest:app --reload --host 0.0.0.0 --port 8000
```

**Résultat attendu :**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Tester l'API :**
```bash
curl http://localhost:8000/
# {"BIEBVENUE":"HAPSON API pour AMG"}

# Accéder à la doc Swagger
open http://localhost:8000/docs
```

---

## 📂 Structure du code

### Organisation des fichiers

```
app/
├── config/
│   └── config.py              # Configuration Pydantic (env vars)
├── db/
│   ├── database.py            # Session SQLAlchemy
│   └── crud/                  # CRUD operations
│       ├── crud_user.py       # Logique métier pour User
│       ├── crud_show.py       # Logique métier pour Show
│       └── ...
├── models/                    # Modèles SQLAlchemy (tables)
│   ├── model_user.py
│   ├── model_show.py
│   └── ...
├── schemas/                   # Schémas Pydantic (validation)
│   ├── schema_user.py
│   ├── schema_show.py
│   └── ...
├── utils/
│   ├── oauth2.py              # JWT, authentification
│   └── utils.py               # Hash passwords, helpers
└── exceptions/                # Exceptions personnalisées
    └── guest_exceptions.py
```

---

### Séparation des responsabilités

**1. Routes (routeur/*.py)**
- Définir les endpoints HTTP
- Valider les données (Pydantic)
- Gérer l'authentification
- Retourner les réponses

**2. CRUD (app/db/crud/*.py)**
- Logique métier
- Interactions avec la base de données
- Gestion des transactions

**3. Models (app/models/*.py)**
- Structure des tables SQL
- Relations (FK, M2M)
- Contraintes

**4. Schemas (app/schemas/*.py)**
- Validation des données entrantes
- Format des réponses
- Documentation OpenAPI

---

## ✨ Développer une nouvelle fonctionnalité

### Exemple : Ajouter une entité "Category" pour les shows

#### Étape 1 : Créer le modèle

**Fichier :** `app/models/model_category.py`

```python
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    # Relations
    shows = relationship("Show", back_populates="category")
```

---

#### Étape 2 : Mettre à jour le modèle Show

**Fichier :** `app/models/model_show.py`

```python
from sqlalchemy import Column, String, Integer, ForeignKey

class Show(BaseModel):
    __tablename__ = "shows"
    
    # ... autres colonnes ...
    
    # Ajouter la FK
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Ajouter la relation
    category = relationship("Category", back_populates="shows")
```

---

#### Étape 3 : Créer les schémas Pydantic

**Fichier :** `app/schemas/schema_category.py`

```python
from pydantic import BaseModel
from datetime import datetime

# Schéma pour créer une catégorie
class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

# Schéma de réponse
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic V2 (était orm_mode=True en V1)

# Schéma pour mise à jour
class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
```

---

#### Étape 4 : Créer les opérations CRUD

**Fichier :** `app/db/crud/crud_category.py`

```python
from sqlalchemy.orm import Session
from app.models.model_category import Category
from app.schemas.schema_category import CategoryCreate, CategoryUpdate

def create_category(db: Session, category: CategoryCreate):
    """Créer une nouvelle catégorie"""
    new_category = Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def get_category(db: Session, category_id: int):
    """Récupérer une catégorie par ID"""
    return db.query(Category).filter(
        Category.id == category_id,
        Category.is_deleted == False
    ).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Lister toutes les catégories"""
    return db.query(Category).filter(
        Category.is_deleted == False
    ).offset(skip).limit(limit).all()

def update_category(db: Session, category_id: int, category: CategoryUpdate):
    """Mettre à jour une catégorie"""
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    
    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    """Supprimer une catégorie (soft delete)"""
    db_category = get_category(db, category_id)
    if not db_category:
        return False
    
    db_category.is_deleted = True
    db.commit()
    return True
```

---

#### Étape 5 : Créer les routes

**Fichier :** `routeur/category_route.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.crud import crud_category
from app.schemas.schema_category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate
)
from app.utils import oauth2

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """Créer une nouvelle catégorie"""
    return crud_category.create_category(db, category)

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """Lister toutes les catégories"""
    return crud_category.get_categories(db, skip, limit)

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """Récupérer une catégorie par ID"""
    category = crud_category.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """Mettre à jour une catégorie"""
    updated = crud_category.update_category(db, category_id, category)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return updated

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(oauth2.get_current_user)
):
    """Supprimer une catégorie"""
    deleted = crud_category.delete_category(db, category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return None
```

---

#### Étape 6 : Enregistrer le routeur

**Fichier :** `maintest.py`

```python
from routeur import category_route

app = FastAPI(...)

# ... autres routers ...
app.include_router(category_route.router)
```

---

#### Étape 7 : Créer une migration Alembic

```bash
# Générer une migration automatique
alembic revision --autogenerate -m "add categories table"

# Vérifier la migration générée
cat alembic/versions/xxxx_add_categories_table.py

# Appliquer la migration
alembic upgrade head
```

---

#### Étape 8 : Tester

```bash
# Lancer l'API
uvicorn maintest:app --reload

# Tester avec curl
curl -X POST http://localhost:8000/categories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Actualités", "description": "Émissions d'\''actualité"}'

# Ou via Swagger UI
open http://localhost:8000/docs
```

---

## 🧪 Tests

### Structure des tests

```
tests/
├── conftest.py              # Configuration pytest (fixtures)
├── test_auth.py             # Tests authentification
├── test_users.py            # Tests utilisateurs
├── test_shows.py            # Tests shows
├── test_categories.py       # Tests catégories (nouveau)
└── ...
```

---

### Écrire un test

**Fichier :** `tests/test_categories.py`

```python
import pytest
from fastapi.testclient import TestClient

def test_create_category(client: TestClient, token_headers: dict):
    """Test de création d'une catégorie"""
    response = client.post(
        "/categories",
        json={"name": "Actualités", "description": "News"},
        headers=token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Actualités"
    assert "id" in data

def test_get_categories(client: TestClient, token_headers: dict):
    """Test de récupération des catégories"""
    response = client.get("/categories", headers=token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_category_not_found(client: TestClient, token_headers: dict):
    """Test 404 sur catégorie inexistante"""
    response = client.get("/categories/99999", headers=token_headers)
    assert response.status_code == 404

def test_update_category(client: TestClient, token_headers: dict):
    """Test de mise à jour d'une catégorie"""
    # Créer une catégorie
    create_response = client.post(
        "/categories",
        json={"name": "Test", "description": "..."},
        headers=token_headers
    )
    category_id = create_response.json()["id"]
    
    # Mettre à jour
    update_response = client.put(
        f"/categories/{category_id}",
        json={"name": "Test Updated"},
        headers=token_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Test Updated"

def test_delete_category(client: TestClient, token_headers: dict):
    """Test de suppression d'une catégorie"""
    # Créer une catégorie
    create_response = client.post(
        "/categories",
        json={"name": "To Delete"},
        headers=token_headers
    )
    category_id = create_response.json()["id"]
    
    # Supprimer
    delete_response = client.delete(
        f"/categories/{category_id}",
        headers=token_headers
    )
    assert delete_response.status_code == 204
    
    # Vérifier qu'elle n'existe plus
    get_response = client.get(
        f"/categories/{category_id}",
        headers=token_headers
    )
    assert get_response.status_code == 404
```

---

### Exécuter les tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_categories.py

# Tests avec verbose
pytest -v

# Tests avec coverage
pytest --cov=app tests/

# Tests avec sortie détaillée
pytest -vv --tb=short
```

---

## 🗄️ Migrations de base de données

### Commandes Alembic essentielles

```bash
# Voir l'historique des migrations
alembic history

# Voir la révision actuelle
alembic current

# Créer une migration manuelle
alembic revision -m "description"

# Créer une migration automatique (recommandé)
alembic revision --autogenerate -m "description"

# Appliquer toutes les migrations
alembic upgrade head

# Annuler la dernière migration
alembic downgrade -1

# Revenir à une révision spécifique
alembic downgrade <revision_id>
```

---

### Exemple de migration manuelle

**Fichier généré :** `alembic/versions/xxxx_add_category_color.py`

```python
"""add category color

Revision ID: abc123
Revises: xyz789
Create Date: 2025-12-11 10:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'

def upgrade() -> None:
    # Ajouter une colonne color
    op.add_column('categories', sa.Column('color', sa.String(), nullable=True))

def downgrade() -> None:
    # Supprimer la colonne color
    op.drop_column('categories', 'color')
```

---

## 📘 Bonnes pratiques

### 1. Nommage des variables et fonctions

```python
# ✅ Bon
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# ❌ Mauvais
def getUsrByMail(d, e):
    return d.query(User).filter(User.email == e).first()
```

---

### 2. Utiliser le soft delete systématiquement

```python
# ✅ Bon
def delete_show(db: Session, show_id: int):
    show = get_show(db, show_id)
    if show:
        show.is_deleted = True
        db.commit()
        return True
    return False

# ❌ Mauvais
def delete_show(db: Session, show_id: int):
    show = get_show(db, show_id)
    db.delete(show)  # Suppression définitive
    db.commit()
```

---

### 3. Toujours valider avec Pydantic

```python
# ✅ Bon
@router.post("/")
def create_show(show: ShowCreate, db: Session = Depends(get_db)):
    # show est déjà validé
    return crud_show.create_show(db, show)

# ❌ Mauvais
@router.post("/")
def create_show(name: str, description: str, db: Session = Depends(get_db)):
    # Validation manuelle nécessaire
    if not name or len(name) < 3:
        raise HTTPException(400, "Invalid name")
    # ...
```

---

### 4. Gérer les erreurs proprement

```python
# ✅ Bon
@router.get("/{show_id}")
def get_show(show_id: int, db: Session = Depends(get_db)):
    show = crud_show.get_show(db, show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found"
        )
    return show

# ❌ Mauvais
@router.get("/{show_id}")
def get_show(show_id: int, db: Session = Depends(get_db)):
    show = crud_show.get_show(db, show_id)
    return show  # Peut retourner None
```

---

### 5. Utiliser les transactions

```python
# ✅ Bon
def create_show_with_presenters(db: Session, show: ShowCreate):
    try:
        # Créer le show
        new_show = Show(**show.dict(exclude={"presenter_ids"}))
        db.add(new_show)
        db.flush()  # Obtenir l'ID sans commit
        
        # Ajouter les presenters
        for presenter_id in show.presenter_ids:
            presenter = get_presenter(db, presenter_id)
            if presenter:
                new_show.presenters.append(presenter)
        
        db.commit()
        db.refresh(new_show)
        return new_show
    except Exception as e:
        db.rollback()
        raise e
```

---

## 🐛 Débogage

### 1. Activer les logs SQL

**Fichier :** `app/db/database.py`

```python
from sqlalchemy import create_engine

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True  # Active les logs SQL
)
```

**Résultat :**
```sql
INFO:sqlalchemy.engine.Engine:SELECT users.id, users.email, ...
INFO:sqlalchemy.engine.Engine:FROM users WHERE users.email = %(email_1)s
INFO:sqlalchemy.engine.Engine:{'email_1': 'user@example.com'}
```

---

### 2. Utiliser le débogueur Python

```python
import pdb

@router.get("/{show_id}")
def get_show(show_id: int, db: Session = Depends(get_db)):
    pdb.set_trace()  # Point d'arrêt
    show = crud_show.get_show(db, show_id)
    return show
```

**Commandes pdb :**
- `n` : Ligne suivante
- `s` : Entrer dans la fonction
- `c` : Continuer
- `p variable` : Afficher une variable
- `q` : Quitter

---

### 3. Logs avec Python logging

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/")
def create_show(show: ShowCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating show: {show.name}")
    new_show = crud_show.create_show(db, show)
    logger.info(f"Show created with id: {new_show.id}")
    return new_show
```

---

### 4. Inspecter les requêtes avec psql

```bash
# Se connecter à la base
psql -U postgres -d audace_db

# Voir toutes les tables
\dt

# Décrire une table
\d shows

# Requête SQL
SELECT * FROM shows WHERE is_deleted = false;

# Quitter
\q
```

---

## 📦 Commandes utiles

### Développement local

```bash
# Lancer l'API
uvicorn maintest:app --reload

# Lancer les tests
pytest

# Créer une migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head
```

---

### Docker local

```bash
# Lancer avec Docker Compose
docker compose up -d

# Voir les logs
docker compose logs -f web

# Arrêter
docker compose down

# Rebuild après changement
docker compose up -d --build
```

---

**Dernière mise à jour :** 11 décembre 2025

# 🧪 Test Enforcer

> **Skill prioritaire** : Standards de tests pytest pour garantir la qualité et la non-régression.

---

## 📋 Contexte du Projet

### Structure des Tests Existants
```
tests/
├── conftest.py              # Fixtures globales
├── test_auth.py             # Tests authentification
├── test_dashboard.py        # Tests dashboard
├── test_emissions.py        # Tests émissions
├── test_guests.py           # Tests invités
├── test_notifications.py    # Tests notifications
├── test_permissions.py      # Tests permissions
├── test_presenters.py       # Tests présentateurs
├── test_roles.py            # Tests rôles
├── test_root.py             # Test endpoint racine
├── test_search_routes.py    # Tests recherche
├── test_segments.py         # Tests segments
├── test_shows.py            # Tests shows
└── test_users.py            # Tests utilisateurs
```

### Configuration (pytest.ini)
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Fixtures Globales (conftest.py)
```python
import pytest
from httpx import AsyncClient
from maintest import app

@pytest.fixture()
def anyio_backend():
    return 'asyncio'

@pytest.fixture()
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
```

---

## 🎯 Objectif du Skill

Assurer que chaque fonctionnalité est testée :
1. **Tests unitaires** : CRUD, utilitaires, services
2. **Tests d'intégration** : Endpoints API complets
3. **Tests de régression** : Avant chaque PR
4. **Couverture minimale** : 80%+

---

## ✅ Règles Obligatoires

### 1. Structure d'un Fichier de Test

```python
# tests/test_{entity}.py
"""
Tests pour les endpoints {Entity}.

Tests:
    - test_create_{entity}: Création réussie
    - test_create_{entity}_unauthorized: Sans auth (401)
    - test_get_{entity}s: Liste avec pagination
    - test_get_{entity}_by_id: Récupération par ID
    - test_get_{entity}_not_found: ID inexistant (404)
    - test_update_{entity}: Mise à jour réussie
    - test_delete_{entity}: Suppression (soft delete)
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from tests.conftest import client, get_auth_headers


class Test{Entity}Endpoints:
    """Tests pour /api/{entities}"""
    
    @pytest.mark.anyio
    async def test_create_{entity}(self, client: AsyncClient):
        """Test création d'un {entity}."""
        headers = await get_auth_headers(client)
        response = await client.post(
            "/{entities}",
            json={"name": "Test {Entity}", "description": "Test description"},
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test {Entity}"
        assert "id" in data
    
    @pytest.mark.anyio
    async def test_create_{entity}_unauthorized(self, client: AsyncClient):
        """Test création sans authentification."""
        response = await client.post(
            "/{entities}",
            json={"name": "Test"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### 2. Patterns de Tests Obligatoires

#### Test CRUD Complet
```python
class TestShowCRUD:
    """Tests CRUD complets pour Show."""
    
    @pytest.mark.anyio
    async def test_create_show(self, client, auth_headers):
        """CREATE - Création réussie."""
        response = await client.post(
            "/shows",
            json={"title": "Test Show", "emission_id": 1},
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Show"
    
    @pytest.mark.anyio
    async def test_get_shows(self, client, auth_headers):
        """READ ALL - Liste avec pagination."""
        response = await client.get(
            "/shows?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.anyio
    async def test_get_show_by_id(self, client, auth_headers, created_show):
        """READ ONE - Par ID."""
        response = await client.get(
            f"/shows/{created_show['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == created_show["id"]
    
    @pytest.mark.anyio
    async def test_update_show(self, client, auth_headers, created_show):
        """UPDATE - Mise à jour."""
        response = await client.patch(
            f"/shows/{created_show['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
    
    @pytest.mark.anyio
    async def test_delete_show(self, client, auth_headers, created_show):
        """DELETE - Soft delete."""
        response = await client.delete(
            f"/shows/{created_show['id']}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Vérifier soft delete (GET retourne 404)
        response = await client.get(
            f"/shows/{created_show['id']}",
            headers=auth_headers
        )
        assert response.status_code == 404
```

#### Tests d'Erreurs
```python
class TestShowErrors:
    """Tests des cas d'erreur."""
    
    @pytest.mark.anyio
    async def test_get_show_not_found(self, client, auth_headers):
        """404 - Show inexistant."""
        response = await client.get("/shows/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.anyio
    async def test_create_show_invalid_data(self, client, auth_headers):
        """422 - Données invalides."""
        response = await client.post(
            "/shows",
            json={"invalid_field": "value"},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.anyio
    async def test_create_show_unauthorized(self, client):
        """401 - Sans authentification."""
        response = await client.post("/shows", json={"title": "Test"})
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_delete_show_forbidden(self, client, viewer_headers, created_show):
        """403 - Permission insuffisante."""
        response = await client.delete(
            f"/shows/{created_show['id']}",
            headers=viewer_headers
        )
        assert response.status_code == 403
```

### 3. Fixtures Recommandées

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient
from maintest import app
from app.db.database import get_db, SessionLocal
from app.models import User
from app.db.crud.crud_auth import create_access_token

@pytest.fixture()
def anyio_backend():
    return 'asyncio'

@pytest.fixture()
async def client():
    """Client HTTP pour tests."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture()
def db_session():
    """Session DB pour tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
async def auth_headers(client: AsyncClient) -> dict:
    """Headers avec token JWT valide (admin)."""
    response = await client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
async def viewer_headers(client: AsyncClient) -> dict:
    """Headers avec token JWT (viewer - permissions limitées)."""
    response = await client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
async def created_show(client: AsyncClient, auth_headers: dict) -> dict:
    """Fixture: Show créé pour tests."""
    response = await client.post(
        "/shows",
        json={"title": "Test Show", "emission_id": 1},
        headers=auth_headers
    )
    return response.json()

@pytest.fixture()
async def created_user(client: AsyncClient, auth_headers: dict) -> dict:
    """Fixture: User créé pour tests."""
    response = await client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "Test123!"
        },
        headers=auth_headers
    )
    return response.json()
```

### 4. Tests Unitaires CRUD

```python
# tests/test_crud_users.py

import pytest
from sqlalchemy.orm import Session
from app.db.crud.crud_users import (
    create_user, get_user_by_id, update_user, soft_delete_user
)
from app.schemas.schema_users import UserCreate, UserUpdate


class TestCrudUsers:
    """Tests unitaires CRUD users."""
    
    def test_create_user(self, db_session: Session):
        """Test création utilisateur."""
        user_data = UserCreate(
            username="newuser",
            email="new@test.com",
            password="Test123!"
        )
        user = create_user(db_session, user_data)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@test.com"
        assert user.password != "Test123!"  # Hashé
    
    def test_get_user_by_id(self, db_session: Session, created_user_id: int):
        """Test récupération par ID."""
        user = get_user_by_id(db_session, created_user_id)
        assert user is not None
        assert user.id == created_user_id
    
    def test_get_user_not_found(self, db_session: Session):
        """Test utilisateur inexistant."""
        with pytest.raises(HTTPException) as exc:
            get_user_by_id(db_session, 99999)
        assert exc.value.status_code == 404
    
    def test_soft_delete_user(self, db_session: Session, created_user_id: int):
        """Test soft delete."""
        soft_delete_user(db_session, created_user_id, deleted_by=1)
        
        user = db_session.query(User).filter(User.id == created_user_id).first()
        assert user.is_deleted is True
        assert user.deleted_at is not None
```

### 5. Commandes pytest

```bash
# Tous les tests
pytest

# Tests avec verbose
pytest -v

# Tests spécifiques
pytest tests/test_users.py
pytest tests/test_users.py::TestUserCRUD::test_create_user

# Avec couverture
pytest --cov=app --cov-report=html --cov-report=term

# Tests marqués
pytest -m "not slow"

# Parallèle
pytest -n auto

# Stop au premier échec
pytest -x

# Avec logs
pytest --log-cli-level=INFO
```

---

## 🚫 Interdictions Explicites

### ❌ Tests sans Assert
```python
# ❌ INTERDIT
def test_create_user(client):
    response = client.post("/users", json={...})
    # Pas d'assert !

# ✅ CORRECT
def test_create_user(client):
    response = client.post("/users", json={...})
    assert response.status_code == 201
    assert "id" in response.json()
```

### ❌ Tests Dépendants
```python
# ❌ INTERDIT (dépend de test_create)
class TestUser:
    created_id = None
    
    def test_create(self, client):
        response = client.post("/users", json={...})
        TestUser.created_id = response.json()["id"]  # État partagé !
    
    def test_get(self, client):
        response = client.get(f"/users/{TestUser.created_id}")  # Dépendant !

# ✅ CORRECT (fixtures indépendantes)
class TestUser:
    def test_create(self, client, auth_headers):
        response = client.post("/users", json={...}, headers=auth_headers)
        assert response.status_code == 201
    
    def test_get(self, client, auth_headers, created_user):  # Fixture
        response = client.get(f"/users/{created_user['id']}", headers=auth_headers)
        assert response.status_code == 200
```

### ❌ Tests sans Cleanup
```python
# ❌ INTERDIT (pollution DB)
def test_create_user(db_session):
    user = User(username="test", email="test@test.com")
    db_session.add(user)
    db_session.commit()
    # Pas de cleanup !

# ✅ CORRECT (fixture avec cleanup)
@pytest.fixture()
def created_user(db_session):
    user = User(username="test", email="test@test.com")
    db_session.add(user)
    db_session.commit()
    yield user
    db_session.delete(user)
    db_session.commit()
```

### ❌ Tests Ignorant les Erreurs
```python
# ❌ INTERDIT
def test_api_endpoint(client):
    try:
        response = client.get("/endpoint")
        assert response.status_code == 200
    except:
        pass  # Test toujours vert !

# ✅ CORRECT
def test_api_endpoint(client):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

---

## 📝 Exemples Concrets du Projet

### Test Auth (Existant)
```python
# tests/test_auth.py
@pytest.mark.anyio
async def test_login_success(client: AsyncClient):
    """Test connexion réussie."""
    response = await client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test connexion échouée."""
    response = await client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
```

---

## ✅ Checklist de Validation

### Avant PR

- [ ] Tous les tests passent : `pytest`
- [ ] Couverture >= 80% : `pytest --cov=app`
- [ ] Nouveaux endpoints ont leurs tests
- [ ] Tests des cas d'erreur (401, 403, 404, 422)
- [ ] Pas de tests dépendants
- [ ] Fixtures utilisées pour données de test

### Pour Chaque Endpoint

- [ ] Test création (POST) - succès
- [ ] Test création - unauthorized (401)
- [ ] Test création - invalid data (422)
- [ ] Test lecture liste (GET) - succès
- [ ] Test lecture par ID (GET) - succès
- [ ] Test lecture - not found (404)
- [ ] Test mise à jour (PATCH) - succès
- [ ] Test suppression (DELETE) - succès
- [ ] Test permission insuffisante (403)

---

## 📁 Template Test Complet

```python
# tests/test_{entity}.py
"""Tests pour /{entities}."""

import pytest
from httpx import AsyncClient
from fastapi import status


class Test{Entity}CRUD:
    """Tests CRUD {Entity}."""
    
    @pytest.mark.anyio
    async def test_create_{entity}(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/{entities}",
            json={"name": "Test"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    @pytest.mark.anyio
    async def test_get_{entity}s(self, client: AsyncClient, auth_headers):
        response = await client.get("/{entities}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    @pytest.mark.anyio
    async def test_get_{entity}_by_id(self, client, auth_headers, created_{entity}):
        response = await client.get(
            f"/{entities}/{created_{entity}['id']}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.anyio
    async def test_update_{entity}(self, client, auth_headers, created_{entity}):
        response = await client.patch(
            f"/{entities}/{created_{entity}['id']}",
            json={"name": "Updated"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.anyio
    async def test_delete_{entity}(self, client, auth_headers, created_{entity}):
        response = await client.delete(
            f"/{entities}/{created_{entity}['id']}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


class Test{Entity}Errors:
    """Tests erreurs {Entity}."""
    
    @pytest.mark.anyio
    async def test_{entity}_not_found(self, client, auth_headers):
        response = await client.get("/{entities}/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.anyio
    async def test_{entity}_unauthorized(self, client):
        response = await client.get("/{entities}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

---

## 📚 Ressources Associées

- [endpoint-creator](../endpoint-creator/skill.md) - Endpoints à tester
- [service-pattern](../service-pattern/skill.md) - Tests de services
- [security-rules](../security-rules/skill.md) - Tests de sécurité

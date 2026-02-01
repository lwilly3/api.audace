# ⚠️ Error Handling

> **Skill important** : Gestion standardisée des erreurs et exceptions dans api.audace.

---

## 📋 Contexte du Projet

### Exceptions Existantes
```
app/exceptions/
├── __init__.py
├── guest_exceptions.py    # GuestNotFoundException, etc.
└── ...
```

### Problèmes Identifiés
1. **Inconsistance** : Différents formats d'erreur
2. **Erreurs silencieuses** : `except: pass` détectés
3. **Détails exposés** : Stack traces en production
4. **Logs manquants** : Erreurs non tracées

---

## 🎯 Objectif du Skill

Standardiser la gestion des erreurs :
1. **HTTPException** cohérentes
2. **Logging** systématique
3. **Messages** utilisateur-friendly
4. **Traçabilité** pour debug

---

## ✅ Règles Obligatoires

### 1. Structure des Erreurs HTTP

```python
from fastapi import HTTPException, status

# Structure standard
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found: User with id 123"
)

# Avec headers (authentification)
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"}
)
```

### 2. Codes HTTP Standards

| Code | Constante | Usage |
|------|-----------|-------|
| 200 | `HTTP_200_OK` | Succès GET, PATCH |
| 201 | `HTTP_201_CREATED` | Succès POST |
| 204 | `HTTP_204_NO_CONTENT` | Succès DELETE |
| 400 | `HTTP_400_BAD_REQUEST` | Données invalides |
| 401 | `HTTP_401_UNAUTHORIZED` | Non authentifié |
| 403 | `HTTP_403_FORBIDDEN` | Permission insuffisante |
| 404 | `HTTP_404_NOT_FOUND` | Ressource inexistante |
| 409 | `HTTP_409_CONFLICT` | Conflit (doublon) |
| 422 | `HTTP_422_UNPROCESSABLE_ENTITY` | Validation Pydantic |
| 500 | `HTTP_500_INTERNAL_SERVER_ERROR` | Erreur serveur |

### 3. Exceptions Personnalisées

```python
# app/exceptions/base.py

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Exception de base pour l'application."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(AppException):
    """Ressource non trouvée (404)."""
    
    def __init__(self, resource: str, identifier: any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {identifier} not found",
            error_code="RESOURCE_NOT_FOUND"
        )


class PermissionDeniedException(AppException):
    """Permission insuffisante (403)."""
    
    def __init__(self, action: str = None):
        detail = f"Permission denied"
        if action:
            detail += f": cannot {action}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED"
        )


class DuplicateException(AppException):
    """Ressource déjà existante (409)."""
    
    def __init__(self, resource: str, field: str, value: any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} with {field} '{value}' already exists",
            error_code="DUPLICATE_RESOURCE"
        )


class ValidationException(AppException):
    """Erreur de validation (400)."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
```

### 4. Utilisation dans CRUD

```python
# app/db/crud/crud_users.py

from app.exceptions import NotFoundException, DuplicateException
import logging

logger = logging.getLogger(__name__)


def get_user_by_id(db: Session, user_id: int) -> User:
    """Récupère un utilisateur ou lève 404."""
    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False
    ).first()
    
    if not user:
        logger.warning(f"User not found: id={user_id}")
        raise NotFoundException("User", user_id)
    
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """Crée un utilisateur ou lève 409 si doublon."""
    # Vérifier doublon email
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        logger.warning(f"Duplicate email: {user_data.email}")
        raise DuplicateException("User", "email", user_data.email)
    
    # Vérifier doublon username
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        logger.warning(f"Duplicate username: {user_data.username}")
        raise DuplicateException("User", "username", user_data.username)
    
    try:
        user = User(**user_data.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created: id={user.id}, email={user.email}")
        return user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
```

### 5. Gestion dans les Routes

```python
# routeur/users_route.py

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un utilisateur."""
    # Vérifier permission
    if not current_user.permissions.can_create_users:
        raise PermissionDeniedException("create users")
    
    # Déléguer au CRUD (gère les exceptions)
    return create_user(db, user_data)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un utilisateur par ID."""
    return get_user_by_id(db, user_id)  # Lève 404 si non trouvé
```

### 6. Try/Except Correct

```python
import logging
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def complex_operation(db: Session, data: dict) -> dict:
    """Opération complexe avec gestion d'erreur."""
    try:
        # Opération qui peut échouer
        result = perform_operation(db, data)
        return result
        
    except HTTPException:
        # Re-lever les HTTPException (déjà formatées)
        raise
        
    except SQLAlchemyError as e:
        # Erreur base de données
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )
        
    except ValueError as e:
        # Erreur de validation
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        # Erreur inattendue
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
```

### 7. Logging des Erreurs

```python
import logging

# Configuration
logger = logging.getLogger(__name__)

# Niveaux appropriés
logger.debug("Détail technique pour debug")
logger.info("Opération normale réussie")
logger.warning("Situation anormale mais gérée")
logger.error("Erreur qui a été récupérée")
logger.exception("Erreur avec stack trace")  # Utilise ERROR + traceback
logger.critical("Erreur système critique")

# Exemples
logger.info(f"User {user_id} logged in successfully")
logger.warning(f"User {user_id} failed login attempt")
logger.error(f"Failed to create show: {str(e)}")
logger.exception(f"Unexpected error processing request")  # Inclut traceback
```

---

## 🚫 Interdictions Explicites

### ❌ Exception Silencieuse
```python
# ❌ INTERDIT
try:
    result = dangerous_operation()
except:
    pass  # Erreur ignorée !

# ✅ CORRECT
try:
    result = dangerous_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(500, "Operation failed")
```

### ❌ Stack Trace Exposée
```python
# ❌ INTERDIT
@router.get("/data")
def get_data():
    try:
        return fetch_data()
    except Exception as e:
        raise HTTPException(500, str(e))  # Expose détails !

# ✅ CORRECT
@router.get("/data")
def get_data():
    try:
        return fetch_data()
    except Exception as e:
        logger.exception(f"Error fetching data: {e}")
        raise HTTPException(500, "Failed to fetch data")
```

### ❌ except: (bare except)
```python
# ❌ INTERDIT
try:
    operation()
except:  # Attrape TOUT, même KeyboardInterrupt !
    handle_error()

# ✅ CORRECT
try:
    operation()
except Exception as e:  # Attrape les exceptions standards
    handle_error(e)
```

### ❌ Message d'Erreur Générique
```python
# ❌ INTERDIT
raise HTTPException(404, "Not found")  # Quoi n'est pas trouvé ?

# ✅ CORRECT
raise HTTPException(404, f"User with id {user_id} not found")
```

---

## 📝 Exemples Concrets du Projet

### Exemple : Guest Exception (Existant)
```python
# app/exceptions/guest_exceptions.py

class GuestNotFoundException(Exception):
    """Exception levée quand un invité n'est pas trouvé."""
    
    def __init__(self, guest_id: int):
        self.guest_id = guest_id
        self.message = f"Guest with id {guest_id} not found"
        super().__init__(self.message)
```

### Amélioration Recommandée
```python
# app/exceptions/guest_exceptions.py (amélioré)

from app.exceptions.base import NotFoundException, DuplicateException


class GuestNotFoundException(NotFoundException):
    """Exception levée quand un invité n'est pas trouvé."""
    
    def __init__(self, guest_id: int):
        super().__init__("Guest", guest_id)


class GuestDuplicateException(DuplicateException):
    """Exception levée quand un invité existe déjà."""
    
    def __init__(self, email: str):
        super().__init__("Guest", "email", email)
```

---

## ✅ Checklist de Validation

### Dans le Code

- [ ] Pas de `except: pass`
- [ ] Pas de `except:` sans type
- [ ] Logger avant `raise`
- [ ] Messages d'erreur descriptifs
- [ ] Codes HTTP appropriés

### Dans les Logs

- [ ] Niveau approprié (info/warning/error)
- [ ] Contexte suffisant (IDs, actions)
- [ ] Pas de données sensibles
- [ ] Stack trace pour erreurs 500

### Dans les Réponses

- [ ] Pas de stack trace exposée
- [ ] Message utilisateur-friendly
- [ ] Code HTTP correct

---

## 📚 Ressources Associées

- [endpoint-creator](../endpoint-creator/skill.md) - Gestion dans routes
- [test-enforcer](../test-enforcer/skill.md) - Tests des erreurs
- [security-rules](../security-rules/skill.md) - Erreurs sécurisées

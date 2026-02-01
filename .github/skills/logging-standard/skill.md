# 📊 Logging Standard

> **Skill recommandé** : Standards de logging pour traçabilité et debugging dans api.audace.

---

## 📋 Contexte du Projet

### Configuration Actuelle (maintest.py)
```python
import logging
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler = RotatingFileHandler(
    "api_logs.log",
    maxBytes=5 * 1024 * 1024,  # 5 Mo
    backupCount=3
)
file_handler.setFormatter(log_formatter)
logging.basicConfig(level=logging.INFO, handlers=[file_handler])

logger = logging.getLogger("hapson-api")
```

### Middleware de Logging
```
app/middleware/
└── logger.py    # LoggerMiddleware pour requêtes HTTP
```

---

## 🎯 Objectif du Skill

Standardiser le logging pour :
1. **Traçabilité** des actions utilisateurs
2. **Debugging** efficace
3. **Monitoring** en production
4. **Sécurité** (pas de données sensibles)

---

## ✅ Règles Obligatoires

### 1. Niveaux de Log

| Niveau | Usage | Exemple |
|--------|-------|---------|
| DEBUG | Détails techniques dev | Requêtes SQL, valeurs variables |
| INFO | Opérations normales | "User 123 logged in" |
| WARNING | Situation anormale gérée | "Login failed for user" |
| ERROR | Erreur récupérée | "Database connection failed" |
| CRITICAL | Erreur système grave | "Cannot start application" |

### 2. Format Standard

```python
import logging

# Configuration par module
logger = logging.getLogger(__name__)

# Format recommandé
'%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Exemple de sortie
# 2025-01-15 10:30:45 - app.db.crud.crud_users - INFO - User 123 created
```

### 3. Configuration Centralisée

```python
# app/config/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    """Configure le logging pour l'application."""
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Handler fichier
    file_handler = RotatingFileHandler(
        "logs/api.log",
        maxBytes=10 * 1024 * 1024,  # 10 Mo
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Réduire verbosité des libs tierces
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### 4. Logging dans les CRUD

```python
# app/db/crud/crud_users.py

import logging
from sqlalchemy.orm import Session
from app.models import User

logger = logging.getLogger(__name__)


def create_user(db: Session, user_data: UserCreate) -> User:
    """Crée un utilisateur."""
    logger.info(f"Creating user: username={user_data.username}, email={user_data.email}")
    
    try:
        user = User(**user_data.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created successfully: id={user.id}")
        return user
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise


def get_user_by_id(db: Session, user_id: int) -> User:
    """Récupère un utilisateur par ID."""
    logger.debug(f"Fetching user: id={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"User not found: id={user_id}")
        return None
    
    logger.debug(f"User found: id={user.id}, username={user.username}")
    return user


def soft_delete_user(db: Session, user_id: int, deleted_by: int) -> User:
    """Supprime un utilisateur (soft delete)."""
    logger.info(f"Soft deleting user: id={user_id}, by={deleted_by}")
    
    user = get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"Cannot delete: user {user_id} not found")
        raise NotFoundException("User", user_id)
    
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"User soft deleted: id={user_id}")
    return user
```

### 5. Logging dans les Routes

```python
# routeur/users_route.py

import logging
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


@router.post("/", response_model=UserResponse)
def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un utilisateur."""
    logger.info(
        f"Create user request: by={current_user.id}, "
        f"username={user_data.username}"
    )
    
    user = create_user(db, user_data)
    
    logger.info(f"User created via API: id={user.id}, by={current_user.id}")
    return user


@router.delete("/{user_id}")
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un utilisateur."""
    logger.info(f"Delete user request: target={user_id}, by={current_user.id}")
    
    if not current_user.permissions.can_delete_users:
        logger.warning(
            f"Permission denied: user={current_user.id} "
            f"cannot delete user={user_id}"
        )
        raise PermissionDeniedException("delete users")
    
    soft_delete_user(db, user_id, current_user.id)
    logger.info(f"User deleted via API: id={user_id}, by={current_user.id}")
```

### 6. Logging des Authentifications

```python
# core/auth/oauth2.py

import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def verify_access_token(token: str, db: Session):
    """Vérifie un token JWT."""
    try:
        if is_token_revoked(db, token):
            logger.warning("Attempt to use revoked token")
            raise credentials_exception
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        logger.debug(f"Token verified for user_id={user_id}")
        return TokenData(id=user_id)
        
    except ExpiredSignatureError:
        logger.warning("Expired token used")
        raise credentials_exception
        
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise credentials_exception


def authenticate_user(db: Session, username: str, password: str):
    """Authentifie un utilisateur."""
    logger.info(f"Login attempt: username={username}")
    
    user = get_user_by_username(db, username)
    
    if not user:
        logger.warning(f"Login failed: user not found - {username}")
        return None
    
    if not verify_password(password, user.password):
        logger.warning(f"Login failed: wrong password - user_id={user.id}")
        return None
    
    logger.info(f"Login successful: user_id={user.id}")
    return user
```

---

## 🚫 Interdictions Explicites

### ❌ Logger des Données Sensibles
```python
# ❌ INTERDIT
logger.info(f"User login: username={username}, password={password}")
logger.debug(f"Token: {token}")
logger.info(f"Created user with email={email}, password={password}")

# ✅ CORRECT
logger.info(f"User login: username={username}")
logger.debug(f"Token validated for user_id={user_id}")
logger.info(f"Created user: id={user.id}, email={user.email}")
```

### ❌ Logger sans Contexte
```python
# ❌ INTERDIT
logger.error("Operation failed")
logger.info("User created")

# ✅ CORRECT
logger.error(f"Operation failed: action=create_show, user_id={user_id}, error={e}")
logger.info(f"User created: id={user.id}, username={user.username}, by={current_user.id}")
```

### ❌ print() au lieu de logger
```python
# ❌ INTERDIT
print(f"User created: {user.id}")
print(f"Error: {e}")

# ✅ CORRECT
logger.info(f"User created: id={user.id}")
logger.error(f"Error: {e}")
```

### ❌ Niveau de Log Inapproprié
```python
# ❌ INTERDIT
logger.error(f"User {user_id} logged in")  # Ce n'est pas une erreur !
logger.debug(f"Critical system failure!")  # Trop important pour debug !

# ✅ CORRECT
logger.info(f"User {user_id} logged in")
logger.critical(f"Critical system failure!")
```

---

## 📝 Templates de Messages

### Actions Utilisateur
```python
# Authentification
logger.info(f"Login attempt: username={username}")
logger.info(f"Login successful: user_id={user_id}")
logger.warning(f"Login failed: username={username}, reason={reason}")
logger.info(f"Logout: user_id={user_id}")

# CRUD
logger.info(f"Creating {entity}: user_id={user_id}, data={safe_data}")
logger.info(f"{Entity} created: id={entity.id}, by={user_id}")
logger.info(f"Updating {entity}: id={entity_id}, by={user_id}")
logger.info(f"Deleting {entity}: id={entity_id}, by={user_id}")

# Permissions
logger.warning(f"Permission denied: user_id={user_id}, action={action}")
logger.info(f"Permission granted: user_id={user_id}, permission={permission}")
```

### Erreurs
```python
# Validation
logger.warning(f"Validation failed: field={field}, value={value}, reason={reason}")

# Database
logger.error(f"Database error: operation={operation}, error={e}", exc_info=True)

# External services
logger.error(f"External service failed: service={service}, status={status}")

# Unexpected
logger.exception(f"Unexpected error: {e}")  # Inclut stack trace
```

---

## ✅ Checklist de Validation

### Configuration

- [ ] Logger configuré par module (`__name__`)
- [ ] Format standard avec timestamp
- [ ] Rotation des fichiers activée
- [ ] Niveau approprié par environnement

### Messages

- [ ] Contexte suffisant (IDs, actions)
- [ ] Pas de données sensibles
- [ ] Niveau approprié
- [ ] Format cohérent

### Sécurité

- [ ] Pas de passwords
- [ ] Pas de tokens
- [ ] Pas de données personnelles sensibles
- [ ] Pas de secrets/clés API

---

## 📚 Ressources Associées

- [error-handling](../error-handling/skill.md) - Gestion des erreurs
- [security-rules](../security-rules/skill.md) - Données sensibles
- [test-enforcer](../test-enforcer/skill.md) - Tests avec logs

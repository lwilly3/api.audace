# 🔐 Security Rules

> **Skill critique** : Standards de sécurité obligatoires pour api.audace (authentification, permissions, protection des données).

---

## 📋 Contexte du Projet

### Système d'Authentification
- **Type** : JWT Bearer Token
- **Implémentation** : `core/auth/oauth2.py`
- **Bibliothèque** : python-jose
- **Expiration** : Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`

### Système de Permissions (RBAC)
- **Modèle** : `UserPermissions` (40+ permissions granulaires)
- **Vérification** : `crud_check_permission.py`
- **Rôles** : Admin, Presenter, Editor, Viewer

### Fichiers Clés
```
core/auth/
└── oauth2.py              # JWT, get_current_user

app/models/
├── model_user.py          # User avec password hashé
├── model_user_permissions.py  # 40+ permissions booléennes
├── model_auth_token.py    # Tokens révoqués
└── model_password_reset_token.py

app/db/crud/
├── crud_auth.py           # Login, token révocation
├── crud_permissions.py    # Gestion permissions
└── crud_check_permission.py  # Vérification permissions
```

---

## 🎯 Objectif du Skill

Garantir la sécurité de l'API :
1. **Authentification** : JWT sur toutes les routes protégées
2. **Autorisation** : Vérification des permissions RBAC
3. **Protection des données** : Hash, validation, filtrage
4. **Audit** : Traçabilité des actions sensibles

---

## ✅ Règles Obligatoires

### 1. Authentification JWT

```python
# core/auth/oauth2.py
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Récupère l'utilisateur depuis le token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # Vérifier révocation
        if is_token_revoked(db, token):
            raise credentials_exception
        
        # Décoder token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user
```

### 2. Routes Protégées (OBLIGATOIRE)

```python
# ✅ CORRECT - Route authentifiée
@router.get("/shows")
def get_shows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Auth obligatoire
):
    return get_shows_crud(db)

# ✅ Routes publiques autorisées (EXCEPTIONS UNIQUEMENT)
# - POST /auth/login
# - POST /auth/signup (si autorisé)
# - POST /setup/* (configuration initiale)
# - GET /version
```

### 3. Vérification des Permissions

```python
# Pattern de vérification dans les routes
@router.delete("/shows/{show_id}")
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier permission
    if not current_user.permissions.can_delete_showplan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: cannot delete shows"
        )
    
    # Vérifier ownership (optionnel)
    show = get_show_by_id(db, show_id)
    if show.created_by != current_user.id and not current_user.permissions.can_edit_all:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: not owner"
        )
    
    return soft_delete_show(db, show_id, current_user.id)
```

### 4. Permissions Disponibles (40+)

```python
# app/models/model_user_permissions.py
class UserPermissions(Base):
    # Shows
    can_create_showplan = Column(Boolean, default=False)
    can_edit_showplan = Column(Boolean, default=False)
    can_delete_showplan = Column(Boolean, default=False)
    can_archive_showplan = Column(Boolean, default=False)
    can_broadcast_showplan = Column(Boolean, default=False)
    
    # Presenters
    can_create_presenters = Column(Boolean, default=False)
    can_edit_presenters = Column(Boolean, default=False)
    can_delete_presenters = Column(Boolean, default=False)
    
    # Guests
    can_create_guests = Column(Boolean, default=False)
    can_edit_guests = Column(Boolean, default=False)
    can_delete_guests = Column(Boolean, default=False)
    
    # Users
    can_create_users = Column(Boolean, default=False)
    can_edit_users = Column(Boolean, default=False)
    can_delete_users = Column(Boolean, default=False)
    
    # Admin
    can_manage_roles = Column(Boolean, default=False)
    can_manage_permissions = Column(Boolean, default=False)
    can_view_audit_logs = Column(Boolean, default=False)
    # ... etc.
```

### 5. Hash des Mots de Passe

```python
# app/utils/utils.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

```python
# Utilisation dans CRUD
def create_user(db: Session, user_data: UserCreate) -> User:
    hashed = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed  # JAMAIS stocker en clair !
    )
    db.add(user)
    db.commit()
    return user
```

### 6. Révocation des Tokens

```python
# app/db/crud/crud_auth.py
from app.models.model_auth_token import RevokedToken

def revoke_token(db: Session, token: str) -> None:
    """Révoque un token (logout)."""
    revoked = RevokedToken(token=token)
    db.add(revoked)
    db.commit()

def is_token_revoked(db: Session, token: str) -> bool:
    """Vérifie si un token est révoqué."""
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first() is not None
```

### 7. Validation des Entrées (Pydantic)

```python
# app/schemas/schema_users.py
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valide la complexité du mot de passe."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Valide le format du username."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v
```

### 8. Protection des Données Sensibles

```python
# ✅ Schéma de réponse sans password
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    # password: str  # JAMAIS exposer !
    
    model_config = ConfigDict(from_attributes=True)

# ✅ Exclure des logs
logger.info(f"User {user.id} logged in")  # ✅
logger.info(f"User logged in with password {password}")  # ❌ JAMAIS !
```

### 9. Audit des Actions Sensibles

```python
# Pour toute action sensible
from app.db.crud.crud_audit_logs import create_audit_log

@router.patch("/users/{user_id}/permissions")
def update_permissions(
    user_id: int,
    permissions: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier permission admin
    if not current_user.permissions.can_manage_permissions:
        raise HTTPException(403, "Admin only")
    
    # Audit AVANT modification
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_PERMISSIONS",
        entity_type="UserPermissions",
        entity_id=user_id,
        description=f"Permissions updated: {permissions.model_dump()}"
    )
    
    # Effectuer modification
    return update_user_permissions(db, user_id, permissions)
```

---

## 🚫 Interdictions Explicites

### ❌ Route sans Authentification
```python
# ❌ INTERDIT (sur routes métier)
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return get_users_crud(db)  # Accessible à tous !

# ✅ CORRECT
@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_users_crud(db)
```

### ❌ Password en Clair
```python
# ❌ INTERDIT
user = User(username="test", password="secret123")  # Clair !

# ✅ CORRECT
user = User(username="test", password=hash_password("secret123"))
```

### ❌ Exposer le Password
```python
# ❌ INTERDIT
@router.get("/users/{id}")
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    return user  # Expose password hashé !

# ✅ CORRECT
@router.get("/users/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    return get_user_by_id(db, id)  # Schema filtre password
```

### ❌ Ignorer la Révocation de Token
```python
# ❌ INTERDIT
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return get_user_by_id(db, payload["user_id"])  # Token révoqué accepté !

# ✅ CORRECT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if is_token_revoked(db, token):
        raise HTTPException(401, "Token revoked")
    # ... reste de la logique
```

### ❌ SQL Injection
```python
# ❌ INTERDIT
@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    return db.execute(f"SELECT * FROM users WHERE name LIKE '%{q}%'")  # Injection !

# ✅ CORRECT (ORM protège)
@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.name.ilike(f"%{q}%")).all()
```

### ❌ Logs avec Données Sensibles
```python
# ❌ INTERDIT
logger.info(f"Login attempt: {username}:{password}")
logger.debug(f"Token: {token}")

# ✅ CORRECT
logger.info(f"Login attempt for user: {username}")
logger.debug(f"Token validated for user_id: {user_id}")
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Authentification (oauth2.py)
```python
# core/auth/oauth2.py
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str, credentials_exception, db: Session):
    try:
        if is_token_revoked(db, token):
            raise credentials_exception
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if not user_id:
            raise credentials_exception
        
        return TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
```

### Exemple 2 : Permissions (crud_check_permission.py)
```python
# app/db/crud/crud_check_permission.py
def check_permission(db: Session, user_id: int, permission_name: str) -> bool:
    """Vérifie si un utilisateur a une permission spécifique."""
    permissions = db.query(UserPermissions).filter(
        UserPermissions.user_id == user_id
    ).first()
    
    if not permissions:
        return False
    
    return getattr(permissions, permission_name, False)
```

---

## ✅ Checklist de Validation

### Authentification
- [ ] JWT sur toutes routes (sauf login, setup, version)
- [ ] Token révocation vérifiée
- [ ] Expiration configurée
- [ ] Secret key en variable d'environnement

### Permissions
- [ ] Vérification permission avant action sensible
- [ ] Vérification ownership si applicable
- [ ] Retour 403 si permission insuffisante

### Données
- [ ] Passwords hashés (bcrypt)
- [ ] Schémas de réponse sans password
- [ ] Validation Pydantic stricte
- [ ] Pas de SQL brut avec input utilisateur

### Audit
- [ ] Actions sensibles loggées
- [ ] Pas de données sensibles dans logs
- [ ] AuditLog pour changements permissions

### Variables d'Environnement
- [ ] `SECRET_KEY` non versionné
- [ ] `DATABASE_URL` non versionné
- [ ] `.env` dans `.gitignore`

---

## 📁 Configuration Sécurisée

```python
# app/config/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str  # Obligatoire
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

```bash
# .env (NON VERSIONNÉ)
SECRET_KEY=your-super-secret-key-min-32-chars
DATABASE_URL=postgresql://user:pass@localhost/db
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

```gitignore
# .gitignore
.env
.env.local
.env.production
```

---

## 📚 Ressources Associées

- [architecture-guardian](../architecture-guardian/skill.md) - Structure globale
- [endpoint-creator](../endpoint-creator/skill.md) - Routes sécurisées
- [test-enforcer](../test-enforcer/skill.md) - Tests de sécurité
- [AGENT.md](../../../AGENT.md) - Guide complet permissions

# 🤖 Guide Agent IA - Audace API

> **Document de référence pour les agents IA**  
> Ce fichier contient toutes les informations critiques pour comprendre, maintenir et faire évoluer ce projet **sans casser le code existant**.

---

## 📋 Table des matières

1. [Vue d'ensemble du projet](#-vue-densemble-du-projet)
2. [Règles d'or (OBLIGATOIRES)](#-règles-dor-obligatoires)
3. [Architecture et dépendances](#-architecture-et-dépendances)
4. [Modèles de données et relations](#-modèles-de-données-et-relations)
5. [Conventions de code](#-conventions-de-code)
6. [Patterns et anti-patterns](#-patterns-et-anti-patterns)
7. [Procédures de modification](#-procédures-de-modification)
8. [Tests et validation](#-tests-et-validation)
9. [Documentation](#-documentation)
10. [Checklist avant commit](#-checklist-avant-commit)

---

## 🎯 Vue d'ensemble du projet

### Contexte métier
**Audace API** est un backend REST pour la gestion collaborative d'un média radio/TV. Il gère :
- Les shows (émissions) et leur planification
- Les présentateurs et invités
- Les permissions utilisateurs (RBAC)
- Les notifications et audits
- Les statistiques et recherche

### Stack technique
| Technologie | Version | Rôle |
|-------------|---------|------|
| **FastAPI** | 0.109.0 | Framework web asynchrone |
| **Python** | 3.11+ | Langage principal |
| **SQLAlchemy** | 2.0 | ORM avec relations complexes |
| **PostgreSQL** | 15 | Base de données relationnelle |
| **Pydantic** | v2 | Validation (utiliser `model_dump()`, pas `dict()`) |
| **Alembic** | - | Migrations de BD |
| **JWT** | - | Authentification (python-jose) |
| **Pytest** | - | Tests unitaires et d'intégration |

### Points critiques
⚠️ **Ne JAMAIS modifier sans comprendre** :
- Les relations SQLAlchemy (cascade, back_populates)
- Les permissions et rôles (système RBAC complexe)
- Les contraintes de base de données (foreign keys, unique)
- Les tokens JWT et leur révocation
- Les audit logs (traçabilité légale)

---

## 🔴 Règles d'or (OBLIGATOIRES)

### 1. 🚫 NE JAMAIS casser les relations existantes

```python
# ❌ INTERDIT : Supprimer ou renommer une relation sans migration
class User(Base):
    # permissions = relationship("UserPermission")  # NE PAS SUPPRIMER !
    pass

# ✅ CORRECT : Toujours garder les relations et créer une migration
class User(Base):
    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
```

**Pourquoi ?** Les relations sont utilisées partout dans le code (CRUD, routes, schémas).

### 2. 🚫 NE JAMAIS modifier la base de données sans migration Alembic

```bash
# ❌ INTERDIT : Modifier directement models.py sans migration
# ✅ CORRECT : Toujours créer une migration
alembic revision --autogenerate -m "description_du_changement"
alembic upgrade head
```

### 3. 🚫 NE JAMAIS supprimer de champs utilisés par l'API

**Avant de supprimer un champ** :
1. ✅ Chercher toutes ses utilisations : `grep -r "nom_du_champ" .`
2. ✅ Vérifier les schémas Pydantic
3. ✅ Vérifier les routes API
4. ✅ Vérifier les tests
5. ✅ Créer une migration Alembic
6. ✅ Marquer comme deprecated si nécessaire

### 4. 🚫 NE JAMAIS changer les permissions sans audit

```python
# ❌ INTERDIT : Ajouter/retirer une permission sans tracer
user.permissions.can_delete_shows = True

# ✅ CORRECT : Toujours créer un audit log
from app.db.crud.crud_audit_logs import create_audit_log

await create_audit_log(
    db=db,
    user_id=current_user.id,
    action="PERMISSION_CHANGE",
    entity_type="User",
    entity_id=user.id,
    description=f"Permission can_delete_shows changed to True"
)
user.permissions.can_delete_shows = True
```

### 5. 🚫 NE JAMAIS utiliser `dict()` avec Pydantic v2

```python
# ❌ INTERDIT : dict() est déprécié en Pydantic v2
user_dict = user_schema.dict()

# ✅ CORRECT : Utiliser model_dump()
user_dict = user_schema.model_dump()
user_dict_exclude = user_schema.model_dump(exclude={"password"})
```

### 6. 🚫 NE JAMAIS faire de suppression hard delete

```python
# ❌ INTERDIT : Suppression définitive
db.delete(show)

# ✅ CORRECT : Soft delete (suppression logique)
show.is_deleted = True
show.deleted_at = datetime.utcnow()
show.deleted_by = current_user.id
await db.commit()
```

**Exceptions autorisées** : Tokens révoqués, logs archivés après 90 jours.

### 7. 🚫 NE JAMAIS exposer de données sensibles

```python
# ❌ INTERDIT : Retourner le mot de passe
return {"user": user, "password": user.password}

# ✅ CORRECT : Utiliser les schémas de réponse
return UserResponse.model_validate(user)  # Exclut automatiquement le password
```

### 8. 🚫 NE JAMAIS ignorer les erreurs silencieusement

```python
# ❌ INTERDIT : Ignorer les exceptions
try:
    result = some_operation()
except:
    pass

# ✅ CORRECT : Logger et gérer proprement
try:
    result = some_operation()
except Exception as e:
    logger.error(f"Error in some_operation: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="Operation failed")
```

---

## 🏗️ Architecture et dépendances

### Structure des dossiers (RESPECTER OBLIGATOIREMENT)

```
app/
├── config/          # Configuration (DATABASE_URL, SECRET_KEY)
├── db/
│   ├── database.py  # Session DB, get_db()
│   └── crud/        # 27 fichiers CRUD (NE PAS MÉLANGER LA LOGIQUE)
├── models/          # 15 modèles SQLAlchemy (BASE DE TOUT)
├── schemas/         # Schémas Pydantic (validation)
├── utils/           # Utilitaires (hashing, tokens)
├── middleware/      # Middlewares (logging)
└── exceptions/      # Exceptions personnalisées

core/
└── auth/            # Authentification JWT (oauth2_scheme, get_current_user)

routeur/             # 14 fichiers de routes (ENDPOINTS API)
├── auth.py          # POST /auth/login, /auth/logout
├── users_route.py   # CRUD utilisateurs
├── show_route.py    # CRUD shows
└── ...

alembic/
└── versions/        # 13 migrations (HISTORIQUE DE LA BD)
```

### Graphe de dépendances critiques

```
┌─────────────────────────────────────────────────────────┐
│                    ROUTEUR (API)                        │
│  auth.py, users_route.py, show_route.py, etc.          │
└─────────────────┬───────────────────────────────────────┘
                  │ importe
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   CRUD (Logique)                        │
│  crud_users.py, crud_show.py, crud_permissions.py       │
└─────────────────┬───────────────────────────────────────┘
                  │ utilise
                  ▼
┌─────────────────────────────────────────────────────────┐
│                 MODELS (SQLAlchemy)                     │
│  User, Show, Presenter, Guest, UserPermission, etc.     │
└─────────────────┬───────────────────────────────────────┘
                  │ valide avec
                  ▼
┌─────────────────────────────────────────────────────────┐
│                 SCHEMAS (Pydantic)                      │
│  UserCreate, ShowResponse, PermissionUpdate, etc.       │
└─────────────────────────────────────────────────────────┘
```

**Règle de dépendance** : ROUTEUR → CRUD → MODELS → SCHEMAS
- ❌ Ne JAMAIS importer un routeur dans un CRUD
- ❌ Ne JAMAIS importer un modèle dans un schéma (circular import)
- ✅ Toujours respecter le sens des flèches

### Imports critiques à connaître

```python
# Session de base de données
from app.db.database import get_db

# Authentification
from core.auth.oauth2 import get_current_user, get_current_active_user

# Modèles principaux
from app.models.users import User
from app.models.permissions import UserPermission
from app.models.show import Show
from app.models.emission import Emission

# CRUD principaux
from app.db.crud.crud_users import get_user_or_404, create_user
from app.db.crud.crud_permissions import get_user_permissions
from app.db.crud.crud_audit_logs import create_audit_log

# Exceptions
from fastapi import HTTPException, Depends, status
from app.exceptions.guest_exceptions import GuestNotFoundException
```

---

## 📊 Modèles de données et relations

### 15 modèles principaux (À CONNAÎTRE PAR CŒUR)

| Modèle | Fichier | Relations clés | Cascade |
|--------|---------|----------------|---------|
| **User** | `models/users.py` | → permissions (1-1), → roles (N-N), → shows (N-N) | delete-orphan |
| **UserPermission** | `models/permissions.py` | ← user (1-1) | None |
| **Role** | `models/roles.py` | ← → users (N-N via user_roles) | None |
| **Presenter** | `models/presenters.py` | ← user (1-1), → shows (N-N) | None |
| **Guest** | `models/guests.py` | → segments (N-N via segment_guests) | None |
| **Emission** | `models/emission.py` | → shows (1-N) | None |
| **Show** | `models/show.py` | ← emission (N-1), → segments (1-N), → presenters (N-N) | delete-orphan |
| **Segment** | `models/segment.py` | ← show (N-1), → guests (N-N) | None |
| **Notification** | `models/notification.py` | ← user (N-1) | None |
| **AuditLog** | `models/audit_log.py` | ← user (N-1) | None |
| **ArchivedAuditLog** | `models/archived_audit_log.py` | Aucune | None |
| **RevokedToken** | `models/revoked_tokens.py` | Aucune | None |
| **PasswordResetToken** | `models/password_reset_token.py` | ← user (N-1) | None |
| **InviteToken** | `models/invite_token.py` | ← user (N-1) | None |
| **RoleTemplate** | `models/role_template.py` | Aucune | None |

### Relations critiques à NE JAMAIS casser

#### 1. User ↔ UserPermission (1-1)

```python
# Dans User
permissions = relationship("UserPermission", back_populates="user", uselist=False, cascade="all, delete-orphan")

# Dans UserPermission
user = relationship("User", back_populates="permissions")
```

**⚠️ ATTENTION** : Si vous supprimez un User, ses permissions sont automatiquement supprimées (cascade).

#### 2. Show ↔ Segment (1-N)

```python
# Dans Show
segments = relationship("Segment", back_populates="show", cascade="all, delete-orphan")

# Dans Segment
show = relationship("Show", back_populates="segments")
show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
```

**⚠️ ATTENTION** : Si vous supprimez un Show, tous ses Segments sont supprimés.

#### 3. User ↔ Role (N-N via user_roles)

```python
# Table d'association
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

# Dans User
roles = relationship("Role", secondary=user_roles, back_populates="users")

# Dans Role
users = relationship("User", secondary=user_roles, back_populates="roles")
```

**⚠️ ATTENTION** : Utiliser `user.roles.append(role)` pour ajouter, pas d'insertion directe dans user_roles.

### Champs obligatoires (NE PAS mettre nullable=True)

```python
# Champs qui DOIVENT toujours avoir une valeur
show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)  # ✅
user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ✅
name = Column(String, nullable=False)  # ✅
email = Column(String, unique=True, nullable=False)  # ✅

# Champs optionnels autorisés
description = Column(Text, nullable=True)  # ✅
image_url = Column(String, nullable=True)  # ✅
```

### Index de performance (À RESPECTER)

```python
# Index définis dans les modèles
__table_args__ = (
    Index('idx_shows_status', 'status'),  # Recherche par statut
    Index('idx_shows_emission', 'emission_id'),  # JOIN avec Emission
    Index('idx_users_email', 'email'),  # Login rapide
    Index('idx_audit_created', 'created_at'),  # Tri chronologique
)
```

**Règle** : Ajouter un index si le champ est utilisé dans WHERE, JOIN ou ORDER BY fréquemment.

---

## 📝 Conventions de code

### Nommage (STRICTEMENT RESPECTER)

| Type | Convention | Exemple |
|------|------------|---------|
| **Classe** | PascalCase | `User`, `ShowResponse` |
| **Fonction** | snake_case | `get_user_or_404()`, `create_show()` |
| **Variable** | snake_case | `current_user`, `db_session` |
| **Constante** | UPPER_SNAKE_CASE | `MAX_RESULTS`, `DEFAULT_LIMIT` |
| **Fichier** | snake_case | `crud_users.py`, `show_route.py` |
| **Route** | kebab-case | `/users`, `/audit-logs` |

### Structure d'une fonction CRUD (TEMPLATE À SUIVRE)

```python
async def operation_entity(
    db: AsyncSession,  # Toujours en premier
    entity_id: int,  # ID si applicable
    current_user: User,  # Utilisateur authentifié
    *,  # Forcer les kwargs après
    field1: str,
    field2: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> Entity | List[Entity]:
    """
    Description courte de l'opération.
    
    Args:
        db: Session de base de données
        entity_id: ID de l'entité
        current_user: Utilisateur authentifié
        field1: Description du champ
        skip: Nombre d'éléments à ignorer (pagination)
        limit: Nombre maximum d'éléments
    
    Returns:
        Entity ou liste d'entities
    
    Raises:
        HTTPException: Si l'entité n'existe pas (404)
        HTTPException: Si l'utilisateur n'a pas la permission (403)
    
    Example:
        >>> entity = await operation_entity(db, 1, user, field1="value")
    """
    # 1. Validation des permissions
    if not current_user.permissions.can_view_entity:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 2. Récupération des données
    query = select(Entity).where(Entity.id == entity_id, Entity.is_deleted == False)
    result = await db.execute(query)
    entity = result.scalar_one_or_none()
    
    # 3. Gestion des erreurs
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # 4. Opération métier
    entity.field1 = field1
    
    # 5. Audit log si modification
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Entity",
        entity_id=entity.id,
        description=f"Updated field1 to {field1}"
    )
    
    # 6. Sauvegarde et retour
    await db.commit()
    await db.refresh(entity)
    return entity
```

### Structure d'une route API (TEMPLATE À SUIVRE)

```python
@router.get(
    "/entities/{entity_id}",
    response_model=EntityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get entity by ID",
    description="Retrieve a single entity by its unique identifier",
    responses={
        200: {"description": "Entity retrieved successfully"},
        404: {"description": "Entity not found"},
        403: {"description": "Permission denied"}
    },
    tags=["Entities"]
)
async def get_entity(
    entity_id: int = Path(..., description="Unique entity identifier", gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> EntityResponse:
    """
    Retrieve an entity by its ID.
    
    Permissions required:
    - can_view_entities
    """
    # 1. Appeler le CRUD
    entity = await crud_entity.get_entity(
        db=db,
        entity_id=entity_id,
        current_user=current_user
    )
    
    # 2. Valider avec Pydantic et retourner
    return EntityResponse.model_validate(entity)
```

### Gestion des erreurs (STANDARDISÉE)

```python
# ❌ INTERDIT : Erreurs génériques
raise Exception("Error")
raise HTTPException(status_code=500, detail="Error")

# ✅ CORRECT : Erreurs spécifiques avec détails
from fastapi import HTTPException, status

# 404 - Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Show with id {show_id} not found"
)

# 403 - Forbidden (permissions)
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission to delete shows"
)

# 400 - Bad Request (validation)
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Email already registered"
)

# 401 - Unauthorized (authentification)
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# 409 - Conflict (état métier)
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Show already published"
)
```

### Utilisation de SQLAlchemy 2.0 (ASYNC)

```python
# ❌ INTERDIT : Syntaxe synchrone (SQLAlchemy 1.x)
user = db.query(User).filter(User.id == user_id).first()

# ✅ CORRECT : Syntaxe asynchrone (SQLAlchemy 2.0)
from sqlalchemy import select

query = select(User).where(User.id == user_id)
result = await db.execute(query)
user = result.scalar_one_or_none()

# Eager loading (éviter N+1 queries)
query = select(Show).options(
    selectinload(Show.segments),
    selectinload(Show.presenters)
).where(Show.id == show_id)
result = await db.execute(query)
show = result.scalar_one_or_none()
```

---

## ✅ Patterns et anti-patterns

### Pattern 1 : Pagination (TOUJOURS IMPLÉMENTER)

```python
# ✅ CORRECT : Pagination sur toutes les listes
async def get_all_entities(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Entity]:
    query = select(Entity).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# Route avec Query parameters
@router.get("/entities")
async def list_entities(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    db: AsyncSession = Depends(get_db)
):
    return await get_all_entities(db, skip, limit)
```

### Pattern 2 : Soft Delete (OBLIGATOIRE)

```python
# ✅ CORRECT : Toujours marquer comme supprimé, ne jamais supprimer
async def delete_show(db: AsyncSession, show_id: int, current_user: User):
    show = await get_show_or_404(db, show_id)
    
    show.is_deleted = True
    show.deleted_at = datetime.utcnow()
    show.deleted_by = current_user.id
    
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="Show",
        entity_id=show.id,
        description=f"Soft deleted show: {show.name}"
    )
    
    await db.commit()
    return {"message": "Show deleted successfully"}

# Filtrer les éléments supprimés dans les requêtes
query = select(Show).where(Show.is_deleted == False)
```

### Pattern 3 : Eager Loading (ÉVITER N+1)

```python
# ❌ ANTI-PATTERN : N+1 queries
shows = await get_all_shows(db)
for show in shows:
    # Chaque itération = 1 query supplémentaire !
    presenters = show.presenters  # Query à chaque fois
    segments = show.segments  # Query à chaque fois

# ✅ CORRECT : Eager loading
from sqlalchemy.orm import selectinload

query = select(Show).options(
    selectinload(Show.presenters),
    selectinload(Show.segments).selectinload(Segment.guests)
).where(Show.is_deleted == False)

result = await db.execute(query)
shows = result.scalars().all()

# Maintenant shows.presenters et shows.segments sont déjà chargés (1 seule query)
```

### Pattern 4 : Validation métier (DANS CRUD, PAS DANS ROUTE)

```python
# ❌ ANTI-PATTERN : Validation dans la route
@router.post("/shows")
async def create_show(show_data: ShowCreate, db: AsyncSession = Depends(get_db)):
    # Validation métier dans la route = mauvais !
    if show_data.status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    show = Show(**show_data.model_dump())
    db.add(show)
    await db.commit()
    return show

# ✅ CORRECT : Validation dans le CRUD
async def create_show(db: AsyncSession, show_data: ShowCreate, current_user: User):
    # Validation métier dans le CRUD
    valid_statuses = ["draft", "published", "archived"]
    if show_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Vérifier les contraintes métier
    if show_data.status == "published" and not show_data.published_date:
        raise HTTPException(
            status_code=400,
            detail="Published shows must have a publication date"
        )
    
    show = Show(**show_data.model_dump(), created_by=current_user.id)
    db.add(show)
    await create_audit_log(...)
    await db.commit()
    await db.refresh(show)
    return show

# Route reste simple
@router.post("/shows")
async def create_show_endpoint(
    show_data: ShowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await crud_show.create_show(db, show_data, current_user)
```

### Pattern 5 : Permissions (TOUJOURS VÉRIFIER)

```python
# ✅ CORRECT : Vérifier les permissions au début de chaque CRUD
async def update_show(
    db: AsyncSession,
    show_id: int,
    show_data: ShowUpdate,
    current_user: User
):
    # 1. Vérifier les permissions AVANT toute opération
    if not current_user.permissions.can_edit_shows:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to edit shows"
        )
    
    # 2. Récupérer l'entité
    show = await get_show_or_404(db, show_id)
    
    # 3. Vérifications supplémentaires (ownership, statut, etc.)
    if show.status == "archived" and not current_user.permissions.can_delete_shows:
        raise HTTPException(
            status_code=403,
            detail="Cannot edit archived shows without delete permission"
        )
    
    # 4. Effectuer la modification
    for key, value in show_data.model_dump(exclude_unset=True).items():
        setattr(show, key, value)
    
    await db.commit()
    return show
```

### Pattern 6 : Transactions (GESTION DES ROLLBACKS)

```python
# ✅ CORRECT : Utiliser try/except pour les transactions complexes
async def create_show_with_segments(
    db: AsyncSession,
    show_data: ShowCreate,
    segments_data: List[SegmentCreate],
    current_user: User
):
    try:
        # 1. Créer le show
        show = Show(**show_data.model_dump(), created_by=current_user.id)
        db.add(show)
        await db.flush()  # Obtenir l'ID sans commit
        
        # 2. Créer les segments
        for segment_data in segments_data:
            segment = Segment(**segment_data.model_dump(), show_id=show.id)
            db.add(segment)
        
        # 3. Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="CREATE",
            entity_type="Show",
            entity_id=show.id,
            description=f"Created show with {len(segments_data)} segments"
        )
        
        # 4. Commit si tout est OK
        await db.commit()
        await db.refresh(show)
        return show
        
    except Exception as e:
        # 5. Rollback en cas d'erreur
        await db.rollback()
        logger.error(f"Error creating show with segments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create show with segments"
        )
```

---

## 🔧 Procédures de modification

### Procédure 1 : Ajouter un nouveau champ à un modèle

**Étapes OBLIGATOIRES** :

1. **Modifier le modèle** (`app/models/entity.py`)
```python
class Entity(Base):
    __tablename__ = "entities"
    
    # Nouveau champ
    new_field = Column(String, nullable=True, default=None)  # Commencer nullable pour migration
```

2. **Créer la migration Alembic**
```bash
alembic revision --autogenerate -m "add_new_field_to_entity"
```

3. **Vérifier la migration** (`alembic/versions/xxxxx_add_new_field.py`)
```python
def upgrade():
    op.add_column('entities', sa.Column('new_field', sa.String(), nullable=True))

def downgrade():
    op.drop_column('entities', 'new_field')
```

4. **Appliquer la migration**
```bash
alembic upgrade head
```

5. **Mettre à jour le schéma Pydantic** (`app/schemas/entity_schema.py`)
```python
class EntityResponse(BaseModel):
    id: int
    name: str
    new_field: Optional[str] = None  # Ajouter ici
    
    model_config = ConfigDict(from_attributes=True)
```

6. **Mettre à jour les CRUD si nécessaire** (`app/db/crud/crud_entity.py`)
```python
async def update_entity(db: AsyncSession, entity_id: int, new_field: str):
    entity = await get_entity_or_404(db, entity_id)
    entity.new_field = new_field
    await db.commit()
    return entity
```

7. **Ajouter des tests**
```python
def test_new_field():
    entity = create_test_entity(new_field="test_value")
    assert entity.new_field == "test_value"
```

### Procédure 2 : Ajouter une nouvelle route API

**Étapes OBLIGATOIRES** :

1. **Créer la fonction CRUD** (`app/db/crud/crud_entity.py`)
```python
async def new_operation(db: AsyncSession, entity_id: int, current_user: User):
    # Implémentation
    pass
```

2. **Ajouter la route** (`routeur/entity_route.py`)
```python
@router.post(
    "/entities/{entity_id}/operation",
    response_model=OperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform operation on entity",
    tags=["Entities"]
)
async def operation_endpoint(
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await crud_entity.new_operation(db, entity_id, current_user)
```

3. **Documenter** (`docs/business-logic/ENTITIES.md`)
```markdown
### `new_operation()`
Description de l'opération...
```

4. **Ajouter des tests** (`tests/test_entities.py`)
```python
def test_new_operation(client, test_user_token):
    response = client.post(
        "/entities/1/operation",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
```

5. **Vérifier Swagger** : http://localhost:8000/docs

### Procédure 3 : Ajouter une nouvelle permission

**Étapes OBLIGATOIRES** :

1. **Modifier le modèle UserPermission** (`app/models/permissions.py`)
```python
class UserPermission(Base):
    __tablename__ = "user_permissions"
    
    # Nouvelle permission
    can_new_action = Column(Boolean, default=False, nullable=False)
```

2. **Migration Alembic**
```bash
alembic revision --autogenerate -m "add_can_new_action_permission"
alembic upgrade head
```

3. **Mettre à jour le schéma** (`app/schemas/permission_schema.py`)
```python
class PermissionResponse(BaseModel):
    can_new_action: bool = False
```

4. **Mettre à jour l'initialisation** (`app/db/init_db_rolePermissions.py`)
```python
def get_default_permissions(role_name: str) -> dict:
    permissions = {
        "Admin": {
            "can_new_action": True,
            # ...
        },
        "Editor": {
            "can_new_action": True,
            # ...
        },
        "Presenter": {
            "can_new_action": False,
            # ...
        }
    }
    return permissions.get(role_name, {})
```

5. **Utiliser dans le CRUD**
```python
async def new_action(db: AsyncSession, current_user: User):
    if not current_user.permissions.can_new_action:
        raise HTTPException(status_code=403, detail="Permission denied")
    # ...
```

6. **Documenter** (`docs/business-logic/PERMISSIONS.md`)

### Procédure 4 : Modifier une relation existante

⚠️ **ATTENTION : TRÈS DANGEREUX**

**Avant de modifier une relation** :

1. **Analyser l'impact**
```bash
# Chercher toutes les utilisations de la relation
grep -r "entity.relation_name" .
grep -r "selectinload(Entity.relation_name)" .
```

2. **Lister les dépendances**
- Modèles qui utilisent cette relation
- CRUD qui font des jointures
- Routes qui retournent ces données
- Tests qui vérifient cette relation

3. **Plan de migration**
- Créer une nouvelle relation (ne pas supprimer l'ancienne)
- Migrer les données si nécessaire
- Mettre à jour le code progressivement
- Supprimer l'ancienne relation dans une version ultérieure

4. **Migration Alembic avec données**
```python
def upgrade():
    # Ajouter nouvelle colonne
    op.add_column('entities', sa.Column('new_relation_id', sa.Integer()))
    
    # Migrer les données (si applicable)
    op.execute("""
        UPDATE entities 
        SET new_relation_id = old_relation_id 
        WHERE old_relation_id IS NOT NULL
    """)
    
    # Ajouter la foreign key
    op.create_foreign_key(
        'fk_entities_new_relation',
        'entities', 'other_table',
        ['new_relation_id'], ['id']
    )
```

---

## 🧪 Tests et validation

### Tests obligatoires avant commit

1. **Tests unitaires**
```bash
# Tester un module spécifique
pytest tests/test_users.py -v

# Tester avec couverture
pytest --cov=app --cov-report=html
```

2. **Tests d'intégration**
```bash
# Tous les tests
pytest

# Tests avec logs
pytest -v --log-cli-level=INFO
```

3. **Validation manuelle**
```bash
# Démarrer le serveur
uvicorn app.main:app --reload

# Vérifier Swagger
open http://localhost:8000/docs

# Tester un endpoint
curl -X GET "http://localhost:8000/users" -H "Authorization: Bearer YOUR_TOKEN"
```

### Écrire un test (TEMPLATE)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_operation_entity(
    async_client: AsyncClient,
    test_user_token: str,
    test_entity
):
    """
    Test de l'opération sur une entité.
    
    Vérifie :
    - Le statut 200
    - La structure de la réponse
    - Les données retournées
    """
    # Arrange
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Act
    response = await async_client.post(
        f"/entities/{test_entity.id}/operation",
        json={"field": "value"},
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["field"] == "value"
```

### Fixtures importantes (À UTILISER)

```python
# Dans conftest.py

@pytest.fixture
def test_db():
    """Session de base de données de test."""
    pass

@pytest.fixture
def test_user():
    """Utilisateur de test avec permissions."""
    pass

@pytest.fixture
def test_user_token():
    """Token JWT pour l'utilisateur de test."""
    pass

@pytest.fixture
def test_admin_token():
    """Token JWT pour un admin."""
    pass
```

---

## 📚 Documentation

### Documentation obligatoire

1. **Docstrings dans le code**
```python
async def function_name(param1: str, param2: int) -> ReturnType:
    """
    Description courte (une ligne).
    
    Description détaillée si nécessaire (plusieurs lignes).
    
    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2
    
    Returns:
        Description du retour
    
    Raises:
        HTTPException: Cas d'erreur 1
        ValueError: Cas d'erreur 2
    
    Example:
        >>> result = await function_name("test", 42)
        >>> print(result)
    """
```

2. **Documentation des routes (Swagger)**
```python
@router.post(
    "/path",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Short description",  # OBLIGATOIRE
    description="Detailed description",  # OBLIGATOIRE
    responses={  # OBLIGATOIRE
        201: {"description": "Success case"},
        400: {"description": "Bad request"},
        403: {"description": "Permission denied"},
        404: {"description": "Not found"}
    },
    tags=["Category"]  # OBLIGATOIRE
)
```

3. **Mise à jour docs/business-logic/**

Après chaque modification majeure, mettre à jour le fichier correspondant :
- `docs/business-logic/USERS.md`
- `docs/business-logic/SHOWS.md`
- `docs/business-logic/PERMISSIONS.md`
- etc.

4. **Mise à jour du CHANGELOG**

```markdown
## [Version] - Date

### Added
- Nouvelle fonctionnalité X

### Changed
- Modification du comportement de Y

### Fixed
- Correction du bug Z

### Removed
- Suppression de la fonctionnalité obsolète W
```

---

## ✅ Checklist avant commit

### Phase 1 : Vérifications automatiques

```bash
# 1. Formater le code
black app/ routeur/ tests/

# 2. Vérifier le style
flake8 app/ routeur/

# 3. Vérifier les types
mypy app/

# 4. Lancer les tests
pytest

# 5. Vérifier la couverture (minimum 80%)
pytest --cov=app --cov-report=term-missing
```

### Phase 2 : Vérifications manuelles

- [ ] **Migrations** : Migration Alembic créée et testée
- [ ] **Relations** : Aucune relation cassée ou manquante
- [ ] **Permissions** : Vérifications de permissions ajoutées
- [ ] **Audit logs** : Audit logs créés pour les modifications
- [ ] **Soft delete** : Utilisation de soft delete, pas de hard delete
- [ ] **Pydantic v2** : Utilisation de `model_dump()`, pas `dict()`
- [ ] **Eager loading** : `selectinload()` utilisé pour éviter N+1
- [ ] **Pagination** : Pagination implémentée sur les listes
- [ ] **Erreurs** : Gestion d'erreurs complète avec codes HTTP appropriés
- [ ] **Documentation** : Docstrings, Swagger, et docs/ à jour
- [ ] **Tests** : Tests unitaires et d'intégration ajoutés
- [ ] **Performance** : Pas de requêtes lourdes ou boucles infinies

### Phase 3 : Tests d'intégration

- [ ] **Swagger** : Vérifier http://localhost:8000/docs
- [ ] **Endpoints** : Tester les nouveaux endpoints manuellement
- [ ] **Cas d'erreur** : Tester les erreurs 400, 403, 404, 500
- [ ] **Permissions** : Tester avec différents rôles (Admin, Presenter, Viewer)
- [ ] **Performance** : Vérifier le temps de réponse (< 500ms pour GET simples)

### Phase 4 : Commit

```bash
# Message de commit structuré
git add .
git commit -m "feat(module): Short description

- Detailed change 1
- Detailed change 2
- Migration: description_of_migration

Closes #issue_number"

# Types de commit
# feat: Nouvelle fonctionnalité
# fix: Correction de bug
# docs: Documentation
# refactor: Refactoring
# test: Tests
# chore: Maintenance
```

---

## 🚨 Situations d'urgence

### Problème : Migration Alembic échoue

```bash
# 1. Annuler la dernière migration
alembic downgrade -1

# 2. Supprimer le fichier de migration problématique
rm alembic/versions/xxxxx_bad_migration.py

# 3. Recréer la migration correctement
alembic revision --autogenerate -m "correct_migration"

# 4. Vérifier le contenu
cat alembic/versions/xxxxx_correct_migration.py

# 5. Appliquer
alembic upgrade head
```

### Problème : Relation cassée (ImportError, AttributeError)

```bash
# 1. Identifier l'erreur exacte
python -c "from app.models.entity import Entity; print(Entity.__table__)"

# 2. Vérifier les imports circulaires
# Dans models/__init__.py, l'ordre des imports est CRITIQUE

# 3. Vérifier back_populates
# Chaque relation doit avoir son back_populates correspondant

# 4. Redémarrer le serveur
# Les modèles sont chargés au démarrage
```

### Problème : Base de données corrompue

```bash
# 1. Sauvegarder immédiatement
./scripts/backup_db.sh

# 2. Vérifier l'intégrité
psql audace_db -c "SELECT * FROM alembic_version;"

# 3. Restaurer depuis un backup
./scripts/restore_db.sh backups/backup_YYYYMMDD.sql

# 4. Réappliquer les migrations si nécessaire
alembic upgrade head
```

### Problème : Performance dégradée

```python
# 1. Identifier les requêtes lentes (activer le logging SQL)
# Dans config.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Affiche toutes les requêtes SQL
)

# 2. Analyser les requêtes
# Chercher les N+1 queries (plusieurs SELECT pour la même table)

# 3. Ajouter eager loading
query = select(Entity).options(
    selectinload(Entity.relation1),
    selectinload(Entity.relation2)
)

# 4. Ajouter des index si nécessaire
# Dans le modèle
__table_args__ = (
    Index('idx_entity_field', 'field_name'),
)

# 5. Créer la migration
alembic revision --autogenerate -m "add_performance_indexes"
```

---

## 🎓 Ressources et références

### Documentation du projet

| Document | Contenu | Lien |
|----------|---------|------|
| **README principal** | Vue d'ensemble, installation | [README.md](README.md) |
| **Index documentation** | Navigation complète | [docs/INDEX.md](docs/INDEX.md) |
| **Architecture** | Vue d'ensemble technique | [docs/architecture/](docs/architecture/) |
| **Logique métier** | Documentation par module | [docs/business-logic/](docs/business-logic/) |
| **Guide démarrage** | Pour nouveaux développeurs | [docs/business-logic/QUICKSTART.md](docs/business-logic/QUICKSTART.md) |

### Documentation externe

- **FastAPI** : https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0** : https://docs.sqlalchemy.org/en/20/
- **Pydantic v2** : https://docs.pydantic.dev/latest/
- **Alembic** : https://alembic.sqlalchemy.org/
- **PostgreSQL** : https://www.postgresql.org/docs/

### Commandes utiles

```bash
# Démarrage
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
pytest -v
pytest --cov=app --cov-report=html

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history

# Base de données
psql audace_db
\dt  # Lister les tables
\d+ table_name  # Décrire une table

# Docker
docker-compose up -d
docker-compose logs -f
docker-compose down

# Git
git status
git add .
git commit -m "feat: description"
git push origin main
```

---

## 🎯 Récapitulatif : Les 10 commandements

1. **Tu ne casseras point les relations** - Toujours vérifier les `back_populates` et `cascade`
2. **Tu migreras avec Alembic** - Jamais de modification de BD sans migration
3. **Tu soft-deleteras** - `is_deleted = True`, jamais `db.delete()`
4. **Tu auditeras** - Toujours créer un `audit_log` pour les modifications
5. **Tu vérifieras les permissions** - Contrôler `can_*` au début de chaque CRUD
6. **Tu pagineras** - `skip` et `limit` sur toutes les listes
7. **Tu eager-loaderas** - `selectinload()` pour éviter N+1 queries
8. **Tu utiliseras model_dump()** - Pydantic v2, pas `dict()`
9. **Tu gèreras les erreurs** - HTTPException avec codes et détails appropriés
10. **Tu documenteras** - Docstrings, Swagger, et docs/ à jour

---

## 🤝 Collaboration avec les agents IA

### Instructions pour les agents IA

**Avant TOUTE modification** :

1. ✅ Lire ce fichier `AGENT.md` en entier
2. ✅ Lire la documentation du module concerné dans `docs/business-logic/`
3. ✅ Chercher les usages existants avec `grep` ou `semantic_search`
4. ✅ Vérifier les relations dans les modèles
5. ✅ Proposer un plan d'action AVANT de modifier
6. ✅ Attendre la validation de l'utilisateur si la modification est complexe

**Pendant la modification** :

1. ✅ Respecter les templates de code
2. ✅ Créer les migrations Alembic nécessaires
3. ✅ Ajouter les audit logs appropriés
4. ✅ Vérifier les permissions
5. ✅ Utiliser soft delete
6. ✅ Ajouter eager loading si relations

**Après la modification** :

1. ✅ Mettre à jour la documentation
2. ✅ Ajouter des tests
3. ✅ Vérifier avec pytest
4. ✅ Tester manuellement via Swagger
5. ✅ Faire la checklist complète

### Communication avec l'utilisateur

**Toujours expliquer** :
- ✅ Ce qui va être modifié
- ✅ Les impacts sur le reste du code
- ✅ Les migrations nécessaires
- ✅ Les tests à effectuer

**Toujours demander confirmation** si :
- ⚠️ Modification d'une relation
- ⚠️ Modification d'un modèle utilisé dans > 5 fichiers
- ⚠️ Suppression de fonctionnalité existante
- ⚠️ Changement de comportement d'une API publique

---

## 📊 Métriques de qualité

### Standards à respecter

| Métrique | Minimum | Idéal | Comment vérifier |
|----------|---------|-------|------------------|
| **Couverture tests** | 80% | 90%+ | `pytest --cov=app` |
| **Temps réponse API** | < 500ms | < 200ms | Swagger + logs |
| **Lignes par fonction** | < 100 | < 50 | Revue de code |
| **Complexité cyclomatique** | < 10 | < 5 | `radon cc app/` |
| **Documentation** | 100% | 100% | Revue manuelle |
| **Migrations** | 100% | 100% | `alembic history` |

### Outils de monitoring

```bash
# Complexité du code
pip install radon
radon cc app/ -a -nb

# Sécurité
pip install bandit
bandit -r app/

# Dépendances obsolètes
pip list --outdated

# Taille du code
cloc app/ routeur/ --exclude-dir=__pycache__
```

---

## 🔄 Versioning et changelog

### Format de version : MAJOR.MINOR.PATCH

- **MAJOR** : Changements incompatibles (breaking changes)
- **MINOR** : Nouvelles fonctionnalités (backward compatible)
- **PATCH** : Corrections de bugs

### Exemples

- `1.0.0` → `1.0.1` : Bug fix
- `1.0.1` → `1.1.0` : Nouvelle fonctionnalité
- `1.1.0` → `2.0.0` : Breaking change (ex: suppression d'une route)

### Mise à jour du CHANGELOG

À chaque version, documenter dans `CHANGELOG.md` :

```markdown
## [1.2.0] - 2025-01-15

### Added
- Ajout de l'endpoint `/shows/{id}/duplicate` pour dupliquer un show
- Ajout du champ `tags` sur le modèle Show
- Nouvelle permission `can_duplicate_shows`

### Changed
- Amélioration des performances de la recherche globale (index full-text)
- Migration du champ `status` vers un ENUM PostgreSQL

### Fixed
- Correction du bug de soft delete sur les segments orphelins
- Correction de la validation des dates de publication

### Deprecated
- L'endpoint `/shows/old-search` est déprécié, utiliser `/search/shows`

### Removed
- Suppression du support de Python 3.10 (minimum 3.11)

### Security
- Correction d'une faille XSS dans les descriptions de shows
```

---

<div align="center">

---

**🤖 Ce document est votre Bible pour travailler sur Audace API**

**Lisez-le. Relisez-le. Respectez-le.**

**Questions ? Consultez d'abord :**
1. Ce fichier `AGENT.md`
2. La documentation `docs/business-logic/`
3. Le code existant (c'est la source de vérité)

**En cas de doute, DEMANDEZ avant de modifier !**

---

*Dernière mise à jour : 11 décembre 2025*  
*Version : 1.0.0*

</div>

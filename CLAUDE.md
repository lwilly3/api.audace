# CLAUDE.md

## Build & Run

```bash
# Local (virtualenv)
source venv/bin/activate
uvicorn maintest:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn maintest:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --forwarded-allow-ips='*' --timeout 120

# Docker
docker-compose up -d          # lance PostgreSQL + API
docker-compose run --rm migrate  # migration seule
```

## Tests

```bash
pytest tests/ -v
```

Configuration dans `pytest.ini` : `asyncio_mode = auto`.

## Migrations Alembic

**Toujours utiliser `--autogenerate`** :
```bash
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
alembic downgrade -1
```

Ajouter `server_default=text('false')` dans la definition `Column()` du modele SQLAlchemy pour les Boolean NOT NULL. Cela permet a `--autogenerate` de generer automatiquement le `server_default` dans la migration, sans retouche manuelle.

```python
# Bon : server_default dans le modele → autogenerate le detecte
Column(Boolean, default=False, server_default=text('false'), nullable=False)

# Mauvais : default seul → pas detecte par Alembic, erreur sur lignes existantes
Column(Boolean, default=False, nullable=False)
```

## Structure du projet

```
maintest.py                          # Point d'entree FastAPI + enregistrement des routers
app/
  config/config.py                   # Settings (Pydantic BaseSettings, lit .env)
  __version__.py                     # Version API (1.2.0), prefix /api/v1
  models/                            # Modeles SQLAlchemy (Base heritee de database.py)
  schemas/                           # Schemas Pydantic (ConfigDict from_attributes=True)
  db/
    database.py                      # engine, SessionLocal, Base, get_db()
    init_admin.py                    # Creation auto admin + roles builtin au demarrage
    crud/                            # Fonctions CRUD par entite
  middleware/                        # LoggerMiddleware, APIVersionMiddleware
  services/                          # Logique metier (ex: ovh_client.py)
  utils/utils.py                     # hash(), verify() pour mots de passe
core/auth/oauth2.py                  # JWT : create_acces_token, get_current_user
routeur/                             # Routes FastAPI (APIRouter)
  search_route/                      # Routes de recherche specialisees
alembic/versions/                    # Fichiers de migration
tests/                               # Pytest + conftest.py
```

## Architecture : ajout d'un nouveau module

1. **Modele** `app/models/model_xxx.py` — herite de `Base`, soft delete (`is_deleted`, `deleted_at`)
2. **Schema** `app/schemas/schema_xxx.py` — `Create`, `Update`, `Read` avec `model_config = ConfigDict(from_attributes=True)`
3. **CRUD** `app/db/crud/crud_xxx.py` — fonctions avec `db: Session`, try/except + HTTPException
4. **Route** `routeur/xxx_route.py` — `APIRouter(prefix="/xxx", tags=["XXX"])`, Depends(get_db) + Depends(oauth2.get_current_user)
5. **Import** dans `app/models/__init__.py`
6. **Enregistrer** dans `maintest.py` : import + `app.include_router(xxx_route.router)`
7. **Migration** : `alembic revision --autogenerate -m "add xxx"`

## Patterns cles

### Authentification JWT
Toutes les routes (sauf `/setup` et `/version`) requierent `current_user = Depends(oauth2.get_current_user)`.
Token cree avec `user_id` dans le payload. Revocation via table `RevokedToken`.

### Permissions (RBAC)
Modele `UserPermissions` : colonnes Boolean par permission (70+ champs).
Verification dans les routes :
```python
perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
if not perms or not perms.nom_permission:
    raise HTTPException(status_code=403, detail="Permission requise")
```

Roles builtin avec hierarchy_level : super_admin (100), Admin (50), public (10), invite (0).
Un utilisateur ne peut pas assigner un role de niveau >= au sien.

### Audit logging
```python
from app.db.crud.crud_audit_logs import log_action
log_action(db, current_user.id, "create", "table_name", record_id)
```
Actions : "create", "read", "update", "delete", "assign_roles", etc.

### Soft delete
```python
entity.is_deleted = True
entity.deleted_at = datetime.utcnow()
db.commit()
```
Filtrer avec `.filter(Entity.is_deleted == False)`.

### Ajout de permissions
Modifier ces 4 fichiers a chaque nouvelle permission :
1. `app/models/model_user_permissions.py` — Column Boolean
2. `app/db/init_admin.py` — `ALL_PERMISSIONS_TRUE` dict + `update_all_permissions_to_true()`
3. `app/db/crud/crud_permissions.py` — `get_user_permissions()` return dict + `initialize_user_permissions()` defaults + `valid_permissions` set dans `update_user_permissions()`
4. Migration Alembic (`--autogenerate`)

## Variables d'environnement (.env)

Requises :
```
DATABASE_HOSTNAME, DATABASE_PORT, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_USERNAME
SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRATION_MINUTE
```

Optionnelles :
```
ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL, ADMIN_NAME, ADMIN_FAMILY_NAME
OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_PORT, MAIL_SERVER
FRONTEND_URL, BACKEND_URL, ENVIRONMENT, DEBUG, WORKERS
```

## Stack technique

- FastAPI 0.109 / Python 3.9+
- SQLAlchemy 2.0 + Alembic (PostgreSQL 15)
- Pydantic 2 / pydantic-settings
- python-jose (JWT) / passlib + bcrypt
- Gunicorn + Uvicorn workers
- Traefik reverse proxy (docker-compose)
- OVH Python SDK (`ovh>=1.1.0`)

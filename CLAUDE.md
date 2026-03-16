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

## Migrations Alembic — REGLE CRITIQUE

> **INTERDICTION ABSOLUE** : Ne JAMAIS creer, ecrire ou modifier un fichier de migration Alembic manuellement.
> Toute migration DOIT etre autogeneree par `alembic revision --autogenerate`.
> Une migration ecrite a la main peut corrompre la chaine de revisions et provoquer un crash en boucle du conteneur Docker en production (erreur `Can't locate revision`).

**Processus obligatoire :**
1. Modifier le modele SQLAlchemy d'abord (`app/models/`)
2. Committer et pousser le code
3. Generer la migration **sur le serveur via Docker** (l'environnement local n'a pas les dependances) :
   ```bash
   sudo docker exec -it audace_api alembic revision --autogenerate -m "description"
   ```
4. Appliquer : `sudo docker exec -it audace_api alembic upgrade head`
5. Copier le fichier genere vers le repo local :
   ```bash
   sudo docker cp audace_api:/app/alembic/versions/<fichier>.py /tmp/
   ```
6. Ajouter au repo Git et pousser

**INTERDIT :**
- Utiliser `Write` ou `Edit` pour creer un fichier `alembic/versions/*.py`
- Inventer un `revision ID` ou `down_revision`
- Copier/adapter manuellement une migration existante
- Modifier le contenu d'un fichier de migration genere

**En cas d'erreur en production :**
- `Can't locate revision 'xxx'` → corriger via PostgreSQL : `UPDATE alembic_version SET version_num = '<derniere_revision_valide>';`
- Puis autogenerer une nouvelle migration

**Commandes de reference :**
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
    social_facebook.py               # Facebook Graph API v21.0 (pages, posts, commentaires, publication)
    social_scheduler.py              # Scheduler periodique (auto-sync, auto-optimize, auto-publish)
    ai_service.py                    # Generation IA de posts depuis URL (Mistral Small)
    firebase_cleanup.py              # Nettoyage fichiers Firebase Storage temporaires
    ovh_client.py                    # Client API OVH
    scaleway_client.py               # Client API Scaleway Dedibox
  utils/utils.py                     # hash(), verify() pour mots de passe
  utils/crypto.py                    # Chiffrement TOTP (Fernet AES) + backup codes (bcrypt)
core/auth/oauth2.py                  # JWT : create_acces_token, get_current_user, refresh avec grace, 2FA temp tokens
routeur/                             # Routes FastAPI (APIRouter)
  auth.py                            # Login, logout, refresh token
  two_factor_route.py                # 2FA TOTP (setup, verify, disable, admin reset)
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

**Renouvellement silencieux du token :**
- `POST /auth/refresh` accepte un token valide ou expire dans la fenetre de grace (5 min, configurable via `REFRESH_GRACE_MINUTES`)
- `decode_token_allow_expired()` dans `oauth2.py` decode avec `options={"verify_exp": False}` puis verifie la fenetre
- L'ancien token est revoque, un nouveau est emis avec permissions fraiches
- Rejette les tokens 2FA temporaires (claim `purpose`)

### Authentification a deux facteurs (2FA/TOTP)
Standard TOTP RFC 6238 (Google Authenticator, Authy).
- Router : `routeur/two_factor_route.py` (prefix `/auth/2fa`, 7 endpoints)
- CRUD : `app/db/crud/crud_2fa.py` (setup, verify, disable, backup codes, admin reset)
- Crypto : `app/utils/crypto.py` (Fernet AES pour secrets TOTP, bcrypt pour backup codes)
- Modele : `model_user.py` (+3 colonnes : `two_factor_enabled`, `totp_secret_encrypted`, `backup_codes_hash`)
- Permissions : `can_enforce_2fa`, `can_reset_user_2fa` dans `model_user_permissions.py`
- Token temporaire : JWT 5 min avec claim `purpose: 2fa_verify`, valide uniquement sur `/auth/2fa/verify`
- Env : `TOTP_ENCRYPTION_KEY` (cle Fernet, requise pour le chiffrement des secrets)

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
2. `app/db/crud/crud_permissions.py` — `get_user_permissions()` return dict + `initialize_user_permissions()` defaults + `valid_permissions` set dans `update_user_permissions()`
3. Migration Alembic (`--autogenerate`)
4. Frontend : `src/shared/types/permissions.ts` — interface + `permissionCategories`

**Fichiers auto-synchronises (NE PAS modifier manuellement) :**
- `app/db/init_admin.py` — `ALL_PERMISSIONS_TRUE`, `update_all_permissions_to_true()`, `sync_superadmin_permissions()` utilisent l'**introspection dynamique** du modele `UserPermissions`. Toute nouvelle colonne Boolean est detectee automatiquement. Aucune modification manuelle n'est necessaire dans ce fichier lors de l'ajout d'une permission.

### Sync automatique des permissions super_admin au demarrage — REGLE CRITIQUE

> **Au demarrage de l'application**, `create_default_admin()` appelle `sync_superadmin_permissions()` qui active automatiquement TOUTES les permissions Boolean pour chaque utilisateur ayant le role `super_admin`.

**Mecanisme :**
- `_get_all_boolean_permission_fields()` fait une introspection SQLAlchemy du modele `UserPermissions`
- Trouve dynamiquement toutes les colonnes `Boolean` (exclut `id`, `user_id`, `granted_at`)
- `update_all_permissions_to_true()` met chaque champ a `True` via `setattr()`
- `ALL_PERMISSIONS_TRUE` et les templates builtin sont aussi generes dynamiquement

**Consequence :** quand une migration Alembic ajoute une nouvelle colonne Boolean dans `UserPermissions`, au prochain demarrage :
1. La colonne est detectee automatiquement par introspection
2. Tous les super_admin recoivent `True` pour cette permission
3. Les templates builtin (`super_admin`, `Admin`, etc.) incluent aussi la nouvelle permission
4. **Aucune modification manuelle de `init_admin.py` n'est necessaire**

**Ce que l'agent DOIT faire lors de l'ajout d'une permission :**
1. Ajouter la colonne dans `model_user_permissions.py` (avec `server_default=text('false')`)
2. Ajouter dans `crud_permissions.py` (3 endroits : `get_user_permissions`, `initialize_user_permissions`, `valid_permissions`)
3. Generer la migration Alembic (`--autogenerate`)
4. Mettre a jour le frontend (`permissions.ts`)
5. **NE PAS toucher** a `init_admin.py` — la sync est automatique

## Variables d'environnement (.env)

Requises :
```
DATABASE_HOSTNAME, DATABASE_PORT, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_USERNAME
SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRATION_MINUTE
```

Optionnelles :
```
TOTP_ENCRYPTION_KEY                # Cle Fernet pour chiffrement secrets 2FA (requise si 2FA active)
REFRESH_GRACE_MINUTES              # Fenetre de grace refresh token en min (defaut: 5)
ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL, ADMIN_NAME, ADMIN_FAMILY_NAME
OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
SCW_SECRET_KEY
MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_PORT, MAIL_SERVER
FRONTEND_URL, BACKEND_URL, ENVIRONMENT, DEBUG, WORKERS
FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_CONFIG_ID
MISTRAL_API_KEY
FIREBASE_SERVICE_ACCOUNT
YOUTUBE_WORKER_URL, YOUTUBE_WORKER_SECRET
WP_AUDACEMAGAZINE_URL, WP_AUDACEMAGAZINE_USER, WP_AUDACEMAGAZINE_APP_PASSWORD
WP_RADIOAUDACE_URL, WP_RADIOAUDACE_USER, WP_RADIOAUDACE_APP_PASSWORD
```

> **Important** : toute nouvelle variable doit etre ajoutee dans `docker-compose.yml` (section `environment:` du service `api`) ET dans le `.env` du serveur de production.

## Stack technique

- FastAPI 0.109 / Python 3.9+
- SQLAlchemy 2.0 + Alembic (PostgreSQL 15)
- Pydantic 2 / pydantic-settings
- python-jose (JWT) / passlib + bcrypt
- pyotp (TOTP 2FA) / qrcode (QR generation)
- cryptography (Fernet AES pour secrets TOTP)
- Gunicorn + Uvicorn workers
- Traefik reverse proxy (docker-compose)
- OVH Python SDK (`ovh>=1.1.0`)
- httpx (client HTTP asynchrone pour Dedibox API, WordPress proxy)
- mistralai (generation IA de contenu)

## Modules API externes

Deux modules de consultation en lecture seule (pas de cache, pas de stockage BDD). Chaque module dispose de sa documentation detaillee :

### OVH — [`OVH_API.md`](docs/OVH_API.md)

Consultation des services OVH via le SDK Python OVH. 13 endpoints GET sous `/ovh/*`.
Fichiers : `app/services/ovh_client.py`, `app/schemas/schema_ovh.py`, `routeur/ovh_route.py`.
Permissions : `ovh_access_section`, `ovh_view_services`, `ovh_view_dashboard`, `ovh_view_billing`, `ovh_view_account`, `ovh_manage`.

### Scaleway Dedibox — [`SCALEWAY_API.md`](docs/SCALEWAY_API.md)

Consultation des services Scaleway Dedibox (Online.net) via API REST httpx. 10 endpoints GET sous `/scaleway/*`.
Fichiers : `app/services/scaleway_client.py`, `app/schemas/schema_scaleway.py`, `routeur/scaleway_route.py`.
Permissions : `scw_access_section`, `scw_view_instances`, `scw_view_dashboard`, `scw_view_billing`, `scw_view_domains`, `scw_view_account`, `scw_manage`.

### Module Social

Gestion des reseaux sociaux : publications, commentaires, messages, analytics, synchronisation Facebook Graph API v21.0.
43 endpoints REST sous `/social/*` (comptes, posts, inbox, analytics, scheduler, database, stockage).

Fichiers principaux :
- `app/services/social_facebook.py` — Client Facebook Graph API (pages, posts, commentaires, publication, insights)
- `app/services/social_scheduler.py` — Scheduler periodique (auto-sync, auto-optimize, auto-publish toutes les 30s)
- `app/services/ai_service.py` — Generation IA de posts depuis URL (Mistral Small)
- `app/services/firebase_cleanup.py` — Nettoyage fichiers Firebase Storage temporaires
- `app/models/model_social.py` — Modeles SQLAlchemy (SocialAccount, SocialPost, SocialPostResult, SocialComment, SocialConversation, SocialMessage, SocialPageInsight)
- `app/schemas/schema_social.py` — Schemas Pydantic
- `app/db/crud/crud_social.py` — CRUD + sync + publish + purge
- `routeur/social_route.py` — Routes FastAPI (43 endpoints)

Permissions (14) : `social_access_section`, `social_view_posts`, `social_create_posts`, `social_edit_posts`, `social_delete_posts`, `social_publish_posts`, `social_view_inbox`, `social_reply_comments`, `social_delete_comments`, `social_reply_messages`, `social_view_stats`, `social_export_stats`, `social_manage_accounts`, `social_manage_settings`.


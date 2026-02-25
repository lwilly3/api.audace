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

## Module OVH (consultation API)

Module de consultation des services OVH en lecture seule. Appels API en temps reel (pas de cache, pas de stockage BDD).

### Fichiers

```
app/config/config.py         # OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
app/services/ovh_client.py   # Client OVH : get_ovh_client(), fonctions d'appel API, gestion d'erreurs
app/schemas/schema_ovh.py    # Schemas Pydantic (OvhAccountInfo, OvhServiceSummary, OvhServiceInfo, OvhBill, OvhDashboard, OvhEmailProAccount)
routeur/ovh_route.py         # 10 endpoints GET sous /ovh/*
```

### Endpoints

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/account` | `ovh_view_account` | Infos du compte OVH (nichandle, email, organisation) |
| GET | `/ovh/services` | `ovh_view_services` | Liste de tous les services avec statut, echeances et displayName |
| GET | `/ovh/services/dashboard?days=30` | `ovh_view_dashboard` | Tableau de bord : total, par type, expirations proches, expires |
| GET | `/ovh/services/types` | `ovh_access_section` | Liste des types de services supportes |
| GET | `/ovh/services/{type}` | `ovh_view_services` | Noms des services d'un type (dedicated, vps, domain...) |
| GET | `/ovh/services/{type}/{name}` | `ovh_view_services` | Detail complet d'un service |
| GET | `/ovh/services/{type}/{name}/status` | `ovh_view_services` | Statut, expiration, renouvellement, contacts |
| GET | `/ovh/email-pro/{service_name}/accounts` | `ovh_view_services` | Comptes Email Pro avec details renouvellement |
| GET | `/ovh/billing/bills?count=20` | `ovh_view_billing` | Liste des dernieres factures (triees par date decroissante) |
| GET | `/ovh/billing/bills/{bill_id}` | `ovh_view_billing` | Detail d'une facture |

### Types de services (parametre `{type}`)

`dedicated` (serveurs dedies), `vps`, `domain` (noms de domaine), `hosting` (hebergement web), `cloud` (projets cloud), `ip` (blocs IP), `alldom` (packs domaines), `email_pro` (Email Pro), `email_exchange` (Exchange), `email_mxplan` (MXPlan), `email_domain` (Email domaine).

`get_all_services()` itere sur tous les types du `SERVICE_TYPE_MAP` pour recuperer chaque service avec ses `serviceInfos` et son `displayName` (optionnel, recupere depuis le detail du service).

### Permissions

6 permissions dediees, toutes verifient `ovh_access_section` en prealable :

| Permission | Role |
|---|---|
| `ovh_access_section` | Acces a la section OVH (prerequis pour toutes les routes) |
| `ovh_view_services` | Consulter les services et leurs details |
| `ovh_view_dashboard` | Voir le tableau de bord synthetique |
| `ovh_view_billing` | Consulter les factures |
| `ovh_view_account` | Voir les infos du compte OVH |
| `ovh_manage` | Gestion complete (reserve pour futures evolutions) |

### Gestion d'erreurs

Le client OVH (`ovh_client.py`) convertit les exceptions OVH en HTTPException :

| Situation | Code HTTP |
|---|---|
| Credentials OVH absents dans `.env` | 503 Service Unavailable |
| Credentials invalides / droits insuffisants | 502 Bad Gateway |
| Ressource OVH introuvable | 404 Not Found |
| Parametres invalides | 400 Bad Request |
| Erreur API OVH generique | 502 Bad Gateway |

### Configuration requise

Variables dans `.env` (et `docker-compose.yml`) :
```
OVH_ENDPOINT=ovh-eu
OVH_APPLICATION_KEY=votre_application_key
OVH_APPLICATION_SECRET=votre_application_secret
OVH_CONSUMER_KEY=votre_consumer_key
```

Generer les credentials :
1. Creer l'application : https://eu.api.ovh.com/createApp/
2. Generer un consumer_key en lecture seule :
```python
import ovh
client = ovh.Client(endpoint='ovh-eu', application_key='...', application_secret='...')
ck = client.new_consumer_key_request()
ck.add_rules(ovh.API_READ_ONLY, '/*')
validation = ck.request()
print(validation['consumerKey'], validation['validationUrl'])
```
3. Ouvrir `validationUrl` dans le navigateur et autoriser l'acces.


# Description des fonctionnalités de l’application

L’application back‑end développée avec FastAPI sous macOS propose les fonctionnalités suivantes :

## 1. Authentification & Sécurité
- Inscription et connexion des utilisateurs via JWT
- Gestion des tokens d’accès et de rafraîchissement
- Contrôle d’accès basé sur les rôles (RBAC) et permissions granulaire

## 2. Gestion des utilisateurs et rôles
- CRUD complet : création, lecture, mise à jour et suppression des utilisateurs
- Gestion des rôles et modèles de rôles
- Affectation et révocation de permissions aux utilisateurs et aux rôles

## 3. Entités métier
- Gestion des émissions (`emissions`) et des shows (`shows`)
- Organisation en segments (`segments`), présentateurs (`presenters`) et invités (`guests`)
- Système de notifications et de votes
- Historique des connexions et journal d’audit des actions (audit log)

## 4. Routes et API
- Routes organisées par domaine :
  - Authentification (`/auth`)
  - Utilisateurs (`/users`)
  - Shows (`/shows`), segments (`/segments`), invités (`/guests`)
  - Notifications (`/notifications`), permissions (`/permissions`)
  - Audit log (`/audit-log`)
- Recherche avancée, filtres personnalisés, pagination et tri

## 5. Infrastructure & Déploiement
- Migrations de schéma gérées par Alembic
- Logging centralisé via un middleware de journalisation
- Configuration par fichier `.env` et gestion d’erreurs personnalisées
- Déploiement avec Gunicorn (Procfile) et service systemd

## 6. Modèles de données (ORM)
- **BaseModel** (`base_model.py`)
  • Attributs : `id` (UUID PK), `created_at` (datetime), `updated_at` (datetime)
  • Relations : —

- **User** (`model_user.py`)
  • Attributs : `id`, `email` (string, unique), `hashed_password`, `is_active` (bool), `created_by` (FK → User)
  • Relations :
    - `roles` (many-to-many via `UserRole`)
    - `permissions` (many-to-many via `UserPermission`)
    - `login_history` (one-to-many → `LoginHistory`)
    - `tokens` (one-to-many → `AuthToken`)
    - `audit_logs` (one-to-many → `AuditLog`)

- **Role** (`model_role.py`)
  • Attributs : `id`, `name` (string, unique), `description`
  • Relations :
    - `users` (many-to-many via `UserRole`)
    - `permissions` (many-to-many via `RolePermission`)
    - `templates` (one-to-many → `RoleTemplate`)

- **Permission** (`model_permission.py`)
  • Attributs : `id`, `code` (string, unique), `description`
  • Relations :
    - `roles` (many-to-many via `RolePermission`)
    - `users` (many-to-many via `UserPermission`)

- **RolePermission** (`model_role_permission.py`)
  • Attributs : `role_id` (FK → Role), `permission_id` (FK → Permission)
  • Table pivot = association many-to-many

- **UserRole** (`model_user_role.py`)
  • Attributs : `user_id` (FK → User), `role_id` (FK → Role)
  • Table pivot = association many-to-many

- **UserPermission** (`model_user_permissions.py`)
  • Attributs : `user_id` (FK → User), `permission_id` (FK → Permission)
  • Table pivot = association many-to-many pour permissions directes

- **RoleTemplate** (`model_RoleTemplate.py`)
  • Attributs : `id`, `name`, `permissions` (relation many-to-many via `RolePermission`)
  • Utilisé pour dupliquer rapidement un ensemble de permissions

- **AuthToken** (`model_auth_token.py`)
  • Attributs : `id`, `token` (string unique), `expires_at` (datetime), `is_revoked` (bool), `user_id` (FK → User)
  • Relations : `user` (many-to-one)

- **Emission** (`model_emissions.py`)
  • Attributs : `id`, `title`, `description`, `start_date`, `end_date`, `creator_id` (FK → User)
  • Relations :
    - `shows` (one-to-many → `Show`)

- **Show** (`model_show.py`)
  • Attributs : `id`, `emission_id` (FK → Emission), `scheduled_at`, `status`
  • Relations :
    - `segments` (one-to-many via `ShowSegment`)
    - `presenters` (one-to-many via `ShowPresenter`)

- **Segment** (`model_segment.py`)
  • Attributs : `id`, `name`, `order`, `duration`
  • Relations :
    - `guests` (many-to-many via `SegmentGuests`)
    - `shows` (many-to-many via `ShowSegment`)

- **SegmentGuests** (`model_segment_guests.py`)
  • Attributs : `segment_id` (FK → Segment), `guest_id` (FK → Guest)
  • Table pivot = association many-to-many

- **Guest** (`model_guest.py`)
  • Attributs : `id`, `name`, `role`, `contact_info`
  • Relations : `segments` (many-to-many via `SegmentGuests`)

- **ShowSegment** (`model_show_segment.py`)
  • Attributs : `show_id` (FK → Show), `segment_id` (FK → Segment), `order`
  • Table pivot = association many-to-many

- **ShowPresenter** (`model_show_presenter.py`)
  • Attributs : `show_id` (FK → Show), `presenter_id` (FK → Presenter)
  • Table pivot = association many-to-many

- **Presenter** (`model_presenter.py`)
  • Attributs : `id`, `name`, `bio`, `contact_info`
  • Relations : `shows` (many-to-many via `ShowPresenter`), `history` (one-to-many → `PresenterHistory`)

- **PresenterHistory** (`model_presenter_history.py`)
  • Attributs : `id`, `presenter_id` (FK → Presenter), `changed_at` (datetime), `changes` (json)
  • Relations : `presenter` (many-to-one)

- **Notification** (`model_notification.py`)
  • Attributs : `id`, `message`, `user_id` (FK → User), `status`, `sent_at`
  • Relations : `user` (many-to-one)

- **LoginHistory** (`model_login_history.py`)
  • Attributs : `id`, `user_id` (FK → User), `timestamp`, `ip_address`, `success` (bool)
  • Relations : `user` (many-to-one)

- **AuditLog** (`model_audit_log.py`)
  • Attributs : `id`, `user_id` (FK → User), `action`, `resource`, `timestamp`, `details` (json)
  • Relations : `user` (many-to-one)

- **ArchivedAuditLog** (`model_archive_log_audit.py`)
  • Attributs : mêmes que `AuditLog` mais table différente pour archivage
  • Relations : `user` (many-to-one)

- **TableModels** (`table_models.py`)
  • Définitions utilitaires de tables pivot et tables annexes (ex. logs externes)

## 7. Exemples de requêtes API

### 7.1 Authentification

#### Inscription
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Secret123!"
  }'
```
**Réponse** (201 Created):
```json
{
  "id": "uuid-1234",
  "email": "user@example.com",
  "is_active": true
}
```

#### Connexion
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Secret123!"
  }'
```
**Réponse** (200 OK):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "dGh...",
  "token_type": "bearer"
}
```

#### Rafraîchissement de token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "dGh..." }'
```

### 7.2 Gestion des utilisateurs

#### Lister les utilisateurs
```bash
curl -X GET http://localhost:8000/users \
  -H "Authorization: Bearer <access_token>"
```

#### Créer un nouvel utilisateur
```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new@example.com",
    "password": "P@ssword1!",
    "is_active": true
  }'
```

### 7.3 Emissions & Shows

#### Récupérer toutes les émissions
```bash
curl -X GET http://localhost:8000/emissions \
  -H "Authorization: Bearer <access_token>"
```

#### Planifier un show
```bash
curl -X POST http://localhost:8000/shows \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "emission_id": "uuid-1234",
    "scheduled_at": "2025-04-20T15:00:00Z",
    "status": "scheduled"
  }'
```

### 7.4 Segments & Invités

#### Ajouter un segment à un show
```bash
curl -X POST http://localhost:8000/segments \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Introduction",
    "order": 1,
    "duration": 300
  }'
```

#### Associer un invité à un segment
```bash
curl -X POST http://localhost:8000/segments/{segment_id}/guests \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{ "guest_id": "uuid-guest" }'
```

### 7.5 Audit & Notifications

#### Consulter le journal d'audit
```bash
curl -X GET http://localhost:8000/audit-log \
  -H "Authorization: Bearer <access_token>"
```

#### Envoyer une notification
```bash
curl -X POST http://localhost:8000/notifications \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-1234",
    "message": "Votre émission commence bientôt",
    "status": "pending"
  }'
```

## 8. Description des routes

### 8.1 Authentification (auth.py)
- Prefixe: `/auth`
- POST `/auth/signup` : création de compte utilisateur
- POST `/auth/login` : obtention des tokens JWT
- POST `/auth/refresh` : renouvellement du token d’accès

### 8.2 Utilisateurs (users_route.py)
- Prefixe: `/users`
- GET `/users` : liste paginée des utilisateurs
- GET `/users/{user_id}` : détail d’un utilisateur
- POST `/users` : création d’un utilisateur
- PUT `/users/{user_id}` : mise à jour d’un utilisateur
- DELETE `/users/{user_id}` : suppression d’un utilisateur

### 8.3 Rôles (role_route.py)
- Prefixe: `/roles`
- GET `/roles` : liste des rôles
- GET `/roles/{role_id}` : détail d’un rôle
- POST `/roles` : création d’un rôle
- PUT `/roles/{role_id}` : mise à jour d’un rôle
- DELETE `/roles/{role_id}` : suppression d’un rôle

### 8.4 Permissions (permissions_route.py)
- Prefixe: `/permissions`
- GET `/permissions` : liste des permissions
- GET `/permissions/{permission_id}` : détail d’une permission
- POST `/permissions` : création d’une permission
- PUT `/permissions/{permission_id}` : mise à jour d’une permission
- DELETE `/permissions/{permission_id}` : suppression d’une permission

### 8.5 Émissions (emission_route.py)
- Prefixe: `/emissions`
- GET `/emissions` : liste des émissions
- GET `/emissions/{emission_id}` : détail d’une émission
- POST `/emissions` : création d’une émission
- PUT `/emissions/{emission_id}` : mise à jour d’une émission
- DELETE `/emissions/{emission_id}` : suppression d’une émission

### 8.6 Shows (show_route.py)
- Prefixe: `/shows`
- GET `/shows` : liste des shows
- GET `/shows/{show_id}` : détail d’un show
- POST `/shows` : planification d’un show
- PUT `/shows/{show_id}` : mise à jour d’un show
- DELETE `/shows/{show_id}` : suppression d’un show

### 8.7 Segments (segment_route.py)
- Prefixe: `/segments`
- GET `/segments` : liste des segments
- GET `/segments/{segment_id}` : détail d’un segment
- POST `/segments` : création d’un segment
- PUT `/segments/{segment_id}` : mise à jour d’un segment
- DELETE `/segments/{segment_id}` : suppression d’un segment

### 8.8 Invités (guest_route.py)
- Prefixe: `/guests`
- GET `/guests` : liste des invités
- GET `/guests/{guest_id}` : détail d’un invité
- POST `/guests` : création d’un invité
- PUT `/guests/{guest_id}` : mise à jour d’un invité
- DELETE `/guests/{guest_id}` : suppression d’un invité

### 8.9 Présentateurs (presenter_route.py)
- Prefixe: `/presenters`
- GET `/presenters` : liste des présentateurs
- GET `/presenters/{presenter_id}` : détail d’un présentateur
- POST `/presenters` : création d’un présentateur
- PUT `/presenters/{presenter_id}` : mise à jour d’un présentateur
- DELETE `/presenters/{presenter_id}` : suppression d’un présentateur

### 8.10 Notifications (notification_route.py)
- Prefixe: `/notifications`
- GET `/notifications` : liste des notifications
- GET `/notifications/{notification_id}` : détail d’une notification
- POST `/notifications` : envoi d’une notification
- PUT `/notifications/{notification_id}` : mise à jour du statut
- DELETE `/notifications/{notification_id}` : suppression d’une notification

### 8.11 Journal d’audit (audit_log_route.py)
- Prefixe: `/audit-log`
- GET `/audit-log` : consultation du journal d’audit
- GET `/audit-log/{log_id}` : détail d’une entrée d’audit

### 8.12 Votes (votes.py)
- Prefixe: `/votes`
- POST `/votes` : vote sur une émission/show/segment

### 8.13 Dashboard (dashbord_route.py)
- Prefixe: `/dashboard`
- GET `/dashboard/stats` : statistiques globales (utilisateurs, émissions, connexions)

### 8.14 Recherche (out_routes/search_route.py)
- Prefixe: `/search`
- GET `/search/users` : recherche d’utilisateurs par email ou nom
- GET `/search/shows` : recherche de shows par titre ou date

## 9. Spécifications techniques par endpoint

### 9.1 Authentification
- **POST /auth/signup**
  • Auth: Public
  • Body: `UserCreate` (schema_users.py)
  • Succès: 201 Created → `UserInDB`
  • Erreurs:
    - 400 Bad Request (payload invalide)
    - 422 Unprocessable Entity (validation Pydantic)

- **POST /auth/login**
  • Auth: Public
  • Body: `UserLogin` (schema_users.py)
  • Succès: 200 OK → `{ access_token: str, refresh_token: str, token_type: "bearer" }`
  • Erreurs:
    - 401 Unauthorized (identifiants invalides)
    - 422 Unprocessable Entity

- **POST /auth/refresh**
  • Auth: Public
  • Body: `{ refresh_token: str }`
  • Succès: 200 OK → même que login
  • Erreurs: 401 Unauthorized (token révoqué ou expiré)

### 9.2 Utilisateurs
- **GET /users**
  • Auth: Bearer (roles: admin, manage_users)
  • Query: `skip: int`, `limit: int` (EmissionPagination réutilisé ou pagination générique)
  • Succès: 200 OK → `List[UserRead]`
  • Erreurs: 401, 403

- **GET /users/{user_id}**
  • Auth: Bearer (self ou roles: admin)
  • Succès: 200 OK → `UserRead`
  • Erreurs: 401, 403, 404 Not Found

- **POST /users**
  • Auth: Bearer (roles: admin)
  • Body: `UserCreate`
  • Succès: 201 Created → `UserInDB`
  • Erreurs: 400, 401, 403, 422

- **PUT /users/{user_id}**
  • Auth: Bearer (roles: admin ou self)
  • Body: `UserUpdate`
  • Succès: 200 OK → `UserRead`
  • Erreurs: 400, 401, 403, 404, 422

- **DELETE /users/{user_id}**
  • Auth: Bearer (roles: admin)
  • Succès: 204 No Content
  • Erreurs: 401, 403, 404

### 9.3 Émissions
- **GET /emissions**
  • Auth: Bearer (roles: viewer, editor)
  • Query: `skip`, `limit` (`EmissionPagination`)
  • Succès: 200 OK → `List[EmissionResponse]`

- **POST /emissions**
  • Auth: Bearer (roles: editor)
  • Body: `EmissionCreate` (schema_emission.py)
  • Succès: 201 Created → `EmissionResponse`
  • Erreurs: 401, 403, 422

- **PUT /emissions/{id}**
  • Auth: Bearer (roles: editor)
  • Body: `EmissionUpdate`
  • Succès: 200 OK → `EmissionResponse`
  • Erreurs: 401, 403, 404, 422

- **DELETE /emissions/{id}**
  • Auth: Bearer (roles: admin)
  • Succès: 204 No Content

### 9.4 Shows
- **GET /shows**
  • Auth: Bearer (roles: viewer)
  • Query: `skip`, `limit`
  • Succès: 200 OK → `List[ShowResponse]` (schema_show.py)

- **POST /shows**
  • Auth: Bearer (roles: editor)
  • Body: `ShowCreate` ou payload similaire
  • Succès: 201 Created → `ShowResponse`

- **PUT /shows/{id}**, **DELETE /shows/{id}**
  • Auth: Bearer (roles: editor / admin)

### 9.5 Autres domaines
- **Segments**, **Invités**, **Présentateurs**, **Notifications**, **Journal d’audit**, **Votes**, **Dashboard**, **Recherche**
  • Chaque route suit le même pattern :
    - Auth: Bearer + rôle/permission spécifique (ex. `manage_segments`)
    - Body: schéma Pydantic dédié (schema_segment.py, schema_guests.py, etc.)
    - Succès: 200/201/204 selon l’opération
    - Erreurs: 401, 403, 404, 422

**Exemple de payload d’erreur 422 (validation)**
```json
{
  "detail": [
    { "loc": ["body","email"], "msg": "value is not a valid email", "type": "value_error.email" }
  ]
}
```

**Exemple de payload d’erreur 403 (permission)**
```json
{ "detail": "Not enough permissions" }
```

## 10. Installation et démarrage
- Installation des dépendances : `pip install -r requirements.txt`
- Configuration des variables d’environnement (.env) :
  • Copier `.env.example` en `.env` et ajuster les valeurs (DB_URL, SECRET_KEY, etc.)
- Initialisation de la base de données et migrations :
  ```bash
  alembic upgrade head
  ```
- Lancement en local :
  • Uvicorn : `uvicorn maintest:app --reload --host 0.0.0.0 --port 8000`
  • Gunicorn : `gunicorn -k uvicorn.workers.UvicornWorker maintest:app --bind 0.0.0.0:8000`

## 11. Documentation interactive et tests
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`
- Tests unitaires : `pytest --maxfail=1 --disable-warnings -q`
- Collection Postman/Insomnia : fournir un fichier `postman_collection.json` ou script d’exemples

## 12. Configuration & CI/CD
- Variables d’environnement obligatoires : `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`…
- Fichier d’exemple : `.env.example`
- Pipeline CI (GitHub Actions/GitLab CI) :
  1. Checkout, install dependencies
  2. Linter (flake8, black)
  3. Tests unitaires (pytest)
  4. Build Docker image (optionnel)
  5. Déploiement automatique (Heroku, Kubernetes, etc.)

## 13. Gestion des erreurs & codes HTTP
- Catalogue d’erreurs métier :
  • 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 500 Internal Server Error
- Format de réponse homogène :
  ```json
  {
    "detail": "Message d’erreur",
    "code": "error_code",
    "type": "error_type"
  }
  ```

## 14. Versioning de l’API
- Préfixe de version : `/api/v1/...`
- Stratégie de montée en version : nouveaux endpoints sous `/api/v2/...`, dépréciation progressive

## 15. Health checks & monitoring
- Endpoint health : GET `/health` ou `/metrics`
- Intégration monitoring : Prometheus, Sentry, DataDog…

## 16. Sécurité avancée
- CORS : configuration via `fastapi.middleware.cors.CORSMiddleware`
- Rate‑limiting : ex. `slowapi` ou middleware personnalisé
- Protection CSRF (si besoin) : tokens double-submit
- Rotation des clés JWT : planification et révocation de tokens

## 17. Schémas Pydantic restants
- Détail des schémas pour :
  • Shows : `ShowCreate`, `ShowResponse` (schema_show.py)
  • Segments : `SegmentCreate`, `SegmentResponse` (schema_segment.py)
  • Invités : `GuestCreate`, `GuestResponse` (schema_guests.py)
  • Notifications : `NotificationCreate`, `NotificationResponse` (schema_notifications.py)
  • Audit logs : `AuditLogCreate`, `AuditLogResponse` (schema_audit_logs.py)
- Exemples de payloads et réponses 200 pour chaque modèle

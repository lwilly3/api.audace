# 🔌 API Consumer

> **Skill Frontend** : Guide complet pour consommer l'API Hapson Radio depuis une application cliente.

---

## 📋 Contexte

### À Propos de ce Skill
Ce skill est destiné aux **développeurs frontend** et aux **agents IA frontend** pour :
- Connaître les endpoints disponibles
- Comprendre les formats de données et **schémas de réponse**
- Gérer l'authentification JWT
- Éviter les erreurs courantes
- **Typer correctement les données reçues**

### Base URL
```
Production : https://api.cloud.audace.ovh
Development: http://localhost:8000
```

### Documentation Interactive
```
Swagger UI : {BASE_URL}/docs
ReDoc      : {BASE_URL}/redoc
OpenAPI    : {BASE_URL}/openapi.json
```

---

## 📂 Documentation des Routes

La documentation détaillée est organisée par module :

| Fichier | Routes | Description |
|---------|--------|-------------|
| [routes/auth.md](routes/auth.md) | `/auth/*` | Authentification, JWT, invitations, reset password |
| [routes/users.md](routes/users.md) | `/users/*`, `/search_users/*` | Gestion utilisateurs, recherche |
| [routes/shows.md](routes/shows.md) | `/shows/*`, `/segments/*`, `/search_shows/*` | Shows, segments, recherche |
| [routes/emissions.md](routes/emissions.md) | `/emissions/*` | Gestion des émissions |
| [routes/presenters.md](routes/presenters.md) | `/presenters/*` | Gestion des présentateurs |
| [routes/guests.md](routes/guests.md) | `/guests/*` | Gestion des invités |
| [routes/permissions.md](routes/permissions.md) | `/permissions/*`, `/roles/*` | Permissions, rôles, templates |
| [routes/notifications.md](routes/notifications.md) | `/notifications/*` | Notifications utilisateur |
| [routes/setup-version.md](routes/setup-version.md) | `/setup/*`, `/version/*`, `/dashbord/*` | Setup, version, dashboard |
| [routes/quotes.md](routes/quotes.md) | Firebase Firestore | Citations (architecture hybride) |
| [routes/segment-contents.md](routes/segment-contents.md) | Firebase Firestore | **Contenus éditoriaux par segment** |

---

## 🗺️ Récapitulatif des Routes

> **15 routers actifs** dans l'application. Total: **~85 routes**.

| Préfixe | Nb Routes | Auth | Documentation |
|---------|-----------|------|---------------|
| `/` | 1 | ❌ | Endpoint par défaut |
| `/setup` | 4 | ❌* | [setup-version.md](routes/setup-version.md) |
| `/version` | 5 | ❌ | [setup-version.md](routes/setup-version.md) |
| `/auth` | 10 | ❌/✅ | [auth.md](routes/auth.md) |
| `/users` | 10 | ✅ | [users.md](routes/users.md) |
| `/emissions` | 6 | ✅ | [emissions.md](routes/emissions.md) |
| `/shows` | 17 | ❌/✅ | [shows.md](routes/shows.md) |
| `/segments` | 6 | ✅ | [shows.md](routes/shows.md) |
| `/presenters` | 8 | ✅ | [presenters.md](routes/presenters.md) |
| `/guests` | 7 | ❌/✅ | [guests.md](routes/guests.md) |
| `/permissions` | 17 | ✅ | [permissions.md](routes/permissions.md) |
| `/roles` | 8 | ❌/✅ | [permissions.md](routes/permissions.md) |
| `/notifications` | 5 | ✅ | [notifications.md](routes/notifications.md) |
| `/dashbord` | 1 | ✅ | [setup-version.md](routes/setup-version.md) |
| `/search_shows` | 1 | ❌ | [shows.md](routes/shows.md) |
| `/search_users` | 3 | ❌ | [users.md](routes/users.md) |

---

## ⚡ Accès Rapide par Fonctionnalité

| Besoin | Route(s) | Auth | Doc |
|--------|----------|------|-----|
| **Vérifier si setup requis** | `GET /setup/check-admin` | ❌ | [setup-version.md](routes/setup-version.md) |
| **Créer premier admin** | `POST /setup/create-admin` | ❌* | [setup-version.md](routes/setup-version.md) |
| **Se connecter** | `POST /auth/login` | ❌ | [auth.md](routes/auth.md) |
| **Récupérer ses permissions** | Login response | - | [auth.md](routes/auth.md) |
| **Lister les shows** | `GET /shows/` | ❌ | [shows.md](routes/shows.md) |
| **Créer un show complet** | `POST /shows/new` | ✅ | [shows.md](routes/shows.md) |
| **Rechercher des shows** | `GET /search_shows/` | ❌ | [shows.md](routes/shows.md) |
| **Lister émissions** | `GET /emissions/` | ✅ | [emissions.md](routes/emissions.md) |
| **Dashboard stats** | `GET /dashbord/` | ✅ | [setup-version.md](routes/setup-version.md) |
| **Health check** | `GET /version/health` | ❌ | [setup-version.md](routes/setup-version.md) |
| **Gérer citations** | Firebase Firestore | ✅ | [quotes.md](routes/quotes.md) |

---

## 🔒 Routes Sans Authentification

Ces routes sont accessibles **sans token JWT** :

```
GET  /                              # API alive check
GET  /setup/check-admin             # Vérifier si admin existe
GET  /setup/status                  # Statut système
GET  /setup/env-check               # Variables d'environnement
POST /setup/create-admin            # Créer admin (si aucun n'existe)
GET  /version/                      # Infos version
GET  /version/current               # Version actuelle
GET  /version/health                # Health check
GET  /version/breaking-changes      # Breaking changes
GET  /version/compatibility/{v}     # Compatibilité client
POST /auth/login                    # Connexion
POST /auth/signup                   # Inscription
POST /auth/signup-with-invite       # Inscription via invitation
GET  /auth/invite/validate          # Valider token invitation
GET  /auth/reset-token/validate     # Valider token reset
POST /auth/reset-password           # Reset password
GET  /shows/                        # Liste shows
GET  /shows/{id}                    # Détail show
GET  /shows/x                       # Shows avec détails
GET  /shows/x/{id}                  # Show avec détails
GET  /shows/production              # Shows en production
GET  /search_shows/                 # Recherche shows
GET  /guests/search                 # Recherche invités
GET  /search_users/                 # Recherche utilisateurs
GET  /search_users/id/{id}          # User par ID
GET  /search_users/search           # Recherche avancée
GET  /roles/all                     # Liste rôles
GET  /roles/id/{id}                 # Détail rôle
```

---

## 🔐 Authentification JWT

### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. POST /auth/login (form-data)                                │
│     ↓                                                           │
│  2. Réponse: access_token + permissions                         │
│     ↓                                                           │
│  3. Stocker token (localStorage/sessionStorage/cookie)          │
│     ↓                                                           │
│  4. Ajouter header: Authorization: Bearer {token}               │
│     ↓                                                           │
│  5. Vérifier permissions avant d'afficher UI                    │
└─────────────────────────────────────────────────────────────────┘
```

### ⚠️ Login avec form-data (pas JSON!)

```typescript
// ✅ CORRECT
const formData = new URLSearchParams();
formData.append('username', email);    // "username" pas "email"
formData.append('password', password);

const response = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData
});

const data: LoginResponse = await response.json();
// data.access_token + data.permissions
```

### Headers Authentifiés

```typescript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`
};
```

---

## 📦 Types Communs

### LoginResponse

```typescript
interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  user_id: number;
  username: string;
  email: string;
  name: string;
  family_name: string;
  phone_number: string | null;
  permissions: UserPermissionsResponse;
}
```

### UserPermissionsResponse (50+ permissions)

Voir [auth.md](routes/auth.md) pour la liste complète.

Permissions principales par catégorie :
- **Showplans** : `can_create_showplan`, `can_edit_showplan`, `can_delete_showplan`, ...
- **Users** : `can_view_users`, `can_edit_users`, `can_delete_users`, ...
- **Emissions** : `can_create_emission`, `can_edit_emission`, `can_delete_emission`, ...
- **Présentateurs** : `can_create_presenter`, `can_edit_presenter`, `can_delete_presenter`, ...
- **Invités** : `can_create_guest`, `can_edit_guest`, `can_delete_guest`, ...
- **Notifications** : `can_create_notification`, `can_read_all_notification`, ...
- **Citations** : `quotes_view`, `quotes_create`, `quotes_edit`, `quotes_delete`, `quotes_publish`, ...

---

## 🌐 Codes HTTP

| Code | Signification | Action Frontend |
|------|---------------|-----------------|
| `200` | Succès | Traiter la réponse |
| `201` | Créé avec succès | Confirmer création |
| `204` | Supprimé/Pas de contenu | Confirmer suppression |
| `400` | Mauvaise requête | Afficher erreur validation |
| `401` | Non authentifié | Rediriger vers login |
| `403` | Accès interdit | Afficher "Permission refusée" |
| `404` | Non trouvé | Afficher "Ressource introuvable" |
| `422` | Données invalides | Afficher erreurs de validation |
| `500` | Erreur serveur | Afficher erreur générique |

### Format des Erreurs

```typescript
interface ApiError {
  detail: string | ValidationError[];
}

interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}
```

---

## 🚫 Pièges à Éviter

### ❌ Login avec JSON
```typescript
// ❌ FAUX - Le login utilise form-data, pas JSON !
body: JSON.stringify({ email, password })

// ✅ CORRECT - Form-data avec "username"
body: new URLSearchParams({ username: email, password })
```

### ❌ Oublier le Bearer
```typescript
// ❌ FAUX
headers: { 'Authorization': token }

// ✅ CORRECT
headers: { 'Authorization': `Bearer ${token}` }
```

### ❌ Ignorer les Permissions
```typescript
// ✅ CORRECT - Vérifier la permission
{user.permissions.can_delete_showplan && (
  <button onClick={deleteShow}>Supprimer</button>
)}
```

### ❌ Mauvais Endpoints
```typescript
// ⚠️ ATTENTION aux URLs non standard
// Users:      PUT /users/updte/{id}      (typo dans l'URL)
// Emissions:  PUT /emissions/upd/{id}
// Presenters: PUT /presenters/update/{id}
```

### ❌ Citations sans Vérifier Permissions
```typescript
// ✅ CORRECT - Toujours vérifier via API
const permissions = await checkQuotesPermissions();
if (!permissions.quotes_create) throw new Error('Non autorisé');
```

---

## ✅ Checklist Intégration

### Configuration
- [ ] Base URL configurée (env variable)
- [ ] Token stocké de façon sécurisée
- [ ] Intercepteur pour erreurs 401
- [ ] Firebase configuré (pour module Citations)

### Authentification
- [ ] Login avec form-data (pas JSON)
- [ ] Token ajouté aux headers (Bearer)
- [ ] Permissions stockées et vérifiées

### UI/UX
- [ ] Boutons conditionnels selon permissions
- [ ] Messages d'erreur user-friendly
- [ ] Loading states pendant requêtes

### Module Citations
- [ ] Permissions quotes_* vérifiées avant Firebase
- [ ] Restriction "Siennes" implémentée
- [ ] `created_by` renseigné à la création

---

## 📚 Ressources

- **Swagger UI** : `{BASE_URL}/docs`
- **ReDoc** : `{BASE_URL}/redoc`
- **OpenAPI JSON** : `{BASE_URL}/openapi.json`
- **Guide Permissions Citations** : `QUOTES_PERMISSIONS.md`

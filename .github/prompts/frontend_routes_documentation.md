# Documentation Frontend des Routes API

Ce guide présente pour chaque route :
- Exemple de requête depuis le frontend (curl ou fetch)
- Exemple de réponse JSON
- Validation frontend (types, contraintes)

---

## 1. Authentification (auth.py)

### 1.1 Inscription (POST /auth/signup)
- Méthode : POST
- URL : `/auth/signup`
- Exemple fetch :
```js
fetch('/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'Secret123!'
  })
});
```
- Payload : `{ email: string, password: string }`
  • `email`: email valide
  • `password`: min 8 caractères (au moins une majuscule et un chiffre)
- Réponse 201 Created (`UserInDB`)
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "username": "user@example.com",
  "name": "",
  "family_name": "",
  "phone_number": "",
  "created_at": "2025-04-29T10:00:00Z"
}
```

### 1.2 Connexion (POST /auth/login)
- Méthode : POST
- URL : `/auth/login`
- En-tête : `Content-Type: application/x-www-form-urlencoded`
- Exemple fetch :
```js
const data = new URLSearchParams();
data.append('username','user@example.com');
data.append('password','Secret123!');
fetch('/auth/login', { method:'POST', body:data });
```
- Payload : form fields `username` (email), `password`
- Réponse 200 OK :
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "family_name": "",
  "name": "",
  "phone_number": "",
  "permissions": {
    "edit_users": true,
    "delete_shows": false
  }
}
```
- Validation : `username` et `password` requis

### 1.3 Déconnexion (POST /auth/logout)
- Méthode : POST
- URL : `/auth/logout`
- En-tête : `Authorization: Bearer <access_token>`
- Exemple fetch :
```js
fetch('/auth/logout', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Payload : aucun
- Réponse 204 No Content
- Validation : token JWT valide requis

---

## 2. Utilisateurs (users_route.py)

### 2.1 Utilisateurs non présentateurs
- Méthode : GET
- URL : `/users/non-presenters`
- Exemple fetch :
```js
fetch('/users/non-presenters', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK :
```json
{
  "total": 5,
  "users": [
    { "id": 3, "email": "foo@ex.com", "username": "foo@ex.com", "name": "Foo", "family_name": "Bar" },
    ...
  ]
}
```
- Validation : aucune query param, token JWT requis

### 2.2 Lister les utilisateurs actifs
- Méthode : GET
- URL : `/users/users?skip=0&limit=10`
- Exemple fetch :
```js
fetch(`/users/users?skip=${skip}&limit=${limit}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : liste de `UserSearchResponse`
```json
[
  { "user_id":1, "email":"a@b.com", "username":"a@b.com", "name":"A","family_name":"B" },
  ...
]
```
- Validation : `skip` ≥ 0, `limit` entre 1 et 100, token requis

### 2.3 Détail d’un utilisateur (+ permissions)
- Méthode : GET
- URL : `/users/users/{id}`
- Exemple fetch :
```js
fetch(`/users/users/${userId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : `UserWithPermissionsResponse`
```json
{
  "id":1,
  "email":"a@b.com",
  "username":"a@b.com",
  "name":"A",
  "family_name":"B",
  "permissions":["edit_users","view_reports"]
}
```
- Erreur 404 si non trouvé

### 2.4 Créer un utilisateur
- Méthode : POST
- URL : `/users/users`
- Exemple fetch :
```js
fetch('/users/users', {
  method:'POST',
  headers:{
    'Content-Type':'application/json'
  },
  body: JSON.stringify({
    email:'new@ex.com',
    password:'P@ssw0rd!',
    username:'new@ex.com',
    name:'New',
    family_name:'User'
  })
});
```
- Payload :
  • `email`, `username`: email valide
  • `password`: string (hachée côté backend)
  • `name`, `family_name`: string
- Réponse 201 Created :
```json
{
  "user_id":10,
  "email":"new@ex.com",
  "username":"new@ex.com",
  "name":"New",
  "family_name":"User"
}
```
- Erreur 400 si échec de création, 422 si validation échoue

### 2.5 Mettre à jour un utilisateur (endpoint updte)
- Méthode : PUT
- URL : `/users/updte/{user_id}`
- Exemple fetch :
```js
fetch(`/users/updte/${id}`, {
  method:'PUT',
  headers:{ 'Content-Type':'application/json' },
  body: JSON.stringify({ name:'Updated', family_name:'Name' })
});
```
- Payload : `UserUpdate` (champs optionnels)
- Réponse 200 OK : `UserSearchResponse`
- Erreur 404 si non trouvé

### 2.6 Mettre à jour un utilisateur (endpoint upd_date)
- Méthode : PUT
- URL : `/users/upd_date/{id}`
- Exemple fetch :
```js
fetch(`/users/upd_date/${id}`, {
  method:'PUT',
  headers:{
    'Content-Type':'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    id: id,
    email: 'new@ex.com',
    username: 'new@ex.com',
    name: 'New',
    family_name: 'User',
    phone_number: '1234567890'
  })
});
```
- Payload : `UserInDB` complet
- Réponse 200 OK : `UserInDB`
- Erreur 404 si non trouvé

### 2.7 Suppression d’un utilisateur
- Méthode : DELETE
- URL : `/users/del/{id}`
- Exemple fetch :
```js
fetch(`/users/del/${id}`, {
  method:'DELETE'
});
```
- Réponse 204 No Content ou 200 OK `{ detail: 'User soft-deleted successfully' }`
- Erreur 404 si non trouvé

### 2.8 Historique des connexions
- Méthode : GET
- URL : `/users/users/{id}/logins`
- Exemple fetch :
```js
fetch(`/users/users/${userId}/logins`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : liste de `LoginHistoryRead`
```json
[
  { "id":100, "user_id":1, "timestamp":"...", "ip_address":"...", "success":true },
  ...
]
```
- Validation : `id` integer, token requis

### 2.9 Notifications d’un utilisateur
- Méthode : GET
- URL : `/users/users/{id}/notifications`
- Exemple fetch :
```js
fetch(`/users/users/${userId}/notifications`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : liste de `NotificationRead`

### 2.10 Logs d’audit d’un utilisateur
- Méthode : GET
- URL : `/users/users/{id}/audit-logs`
- Exemple fetch :
```js
fetch(`/users/users/${userId}/audit-logs`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : liste de `AuditLog`

---


## 3. Rôles & Permissions

### 3.1 Créer un rôle (POST /roles)
```js
fetch('/roles', { method:'POST', headers:{...}, body:JSON.stringify({ name:'editor' }) });
```
Réponse 201 : `{ id:4, name:'editor', users:[] }`

### 3.2 Modifier (PUT /roles/{id})
```js
fetch(`/roles/${id}`, { method:'PUT', body:JSON.stringify({ name:'writer' }), headers:{...} });
```
Statut 200 / 404.

---

## 4. Emissions & Shows

<!-- Routes définies dans routeur/emission_route.py -->

### Émissions (emission_route.py)

#### Créer une émission
- Méthode: POST
- URL: `/emissions/`
- Exemple fetch depuis le frontend:
```js
fetch('/emissions/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: 'Journal du matin',
    description: 'Actualités matinales',
    start_date: '2025-05-01',
    end_date: '2025-05-31'
  })
});
```
- Payload attendu:
  • `title`: string non vide
  • `description`: string optionnelle
  • `start_date`, `end_date`: dates ISO (YYYY-MM-DD)
- Réponse 201 Created (`EmissionResponse`):
```json
{
  "id": 10,
  "title": "Journal du matin",
  "description": "Actualités matinales",
  "start_date": "2025-05-01",
  "end_date": "2025-05-31",
  "creator_id": 1
}
```

#### Lister les émissions
- Méthode: GET
- URL: `/emissions/?skip=0&limit=10`
- Exemple fetch:
```js
fetch(`/emissions/?skip=${skip}&limit=${limit}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK (liste de `EmissionResponse`):
```json
[
  { "id": 5, "title": "Soirée musique", "start_date": "2025-04-01", "end_date": "2025-04-30", "creator_id":2 },
  { "id": 6, "title": "Podcast tech", ... }
]
```
- Validation frontend: `skip` ≥ 0, `limit` entre 1 et 100

#### Détail d’une émission
- Méthode: GET
- URL: `/emissions/{emission_id}`
- Exemple fetch:
```js
fetch(`/emissions/${id}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK (`EmissionResponse`) ou 404 Not Found:
```json
{ "id":5, "title":"Soirée musique", "description":"...", "start_date":"2025-04-01", "end_date":"2025-04-30", "creator_id":2 }
```

#### Mettre à jour une émission
- Méthode: PUT
- URL: `/emissions/upd/{emission_id}`
- Exemple fetch:
```js
fetch(`/emissions/upd/${id}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ description: 'Nouvelles locales actualisées' })
});
```
- Payload: mêmes champs que pour la création (optionnels)
- Réponse 200 OK (`EmissionResponse`) ou 404 Not Found

#### Supprimer une émission
- Méthode: DELETE
- URL: `/emissions/del/{emission_id}`
- Exemple fetch:
```js
fetch(`/emissions/del/${id}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK: `true` ou 404 Not Found

#### Suppression douce (soft delete)
- Méthode: DELETE
- URL: `/emissions/softDel/{emission_id}`
- Exemple fetch identique à DELETE simple
- Réponse 200 OK: `true` ou 404 Not Found

<!-- Routes shows suivent -->

### 4.1 Créer un nouveau show simple
- Méthode: POST
- URL: `/shows/`
- Body: ShowCreate (schéma `ShowCreate`)
  ```json
  {
    "title": "Actualités",
    "type": "Info",
    "broadcast_date": "2025-04-28T10:00:00Z",
    "duration": 60,
    "frequency": "Hebdomadaire",
    "description": "Revues des actualités",
    "status": "scheduled",
    "emission_id": 1
  }
  ```
- Réponse 201 Created (`ShowOut`)
  ```json
  {
    "id": 42,
    "title": "Actualités",
    "type": "Info",
    "broadcast_date": "2025-04-28T10:00:00Z",
    "duration": 60,
    "frequency": "Hebdomadaire",
    "description": "Revues des actualités",
    "status": "scheduled",
    "emission_id": 1,
    "created_at": "2025-04-20T09:00:00Z",
    "updated_at": "2025-04-20T09:00:00Z"
  }
  ```

### 4.2 Lister tous les shows
- Méthode: GET
- URL: `/shows/?skip=0&limit=10`
- Query params: skip (int), limit (int)
- Réponse 200 OK (Liste `ShowOut`)
  ```json
  [
    { "id": 1, "title": "Show 1", ... },
    { "id": 2, "title": "Show 2", ... }
  ]
  ```

### 4.3 Détail d’un show
- Méthode: GET
- URL: `/shows/{show_id}`
- Réponse 200 OK (`ShowOut`) ou 404 Not Found
  ```json
  {
    "id": 42,
    "title": "Actualités",
    "type": "Info",
    ...
  }
  ```

### 4.4 Supprimer un show
- Méthode: DELETE
- URL: `/shows/del/{show_id}`
- Réponse 200 OK (`ShowOut` supprimé) ou 404

### 4.5 Mettre à jour un show
- Méthode: PUT
- URL: `/shows/upd/{show_id}`
- Body: `ShowUpdate`
- Réponse 200 OK (`ShowOut`) ou 404

---

### 4.6 Création avec détails (segments + présentateurs)
- Méthode: POST
- URL: `/shows/detail`
- Body: `ShowCreateWithDetail` incluant:
  - presenters: list of IDs
  - segments: array of { title, type, position, duration, description?, guest_ids? }
- Réponse 201 Created
  ```json
  {
    "message": "Show created successfully.",
    "show": { /* ShowWithdetailResponse.show */ }
  }
  ```

### 4.7 Mise à jour avec détails
- Méthode: PATCH
- URL: `/shows/detail/{show_id}`
- Body: `ShowUpdateWithDetails` (array de segments à modifier)
- Réponse 200 OK (`ShowWithdetailResponse`) ou 404

---

### 4.8 Création via JSON complet
- Méthode: POST
- URL: `/shows/new`
- Body: liste de `ShowBase_jsonShow` pour multiples shows
- Réponse 200 OK
  ```json
  { "message": "Émission créée avec succès", "show_id": 99 }
  ```

### 4.9 Routes utilitaires détaillées
- GET `/shows/x` : liste brute des détails SQL (response_model: dict)
- GET `/shows/x/{show_id}` : détail brut JSON
- GET `/shows/production` : shows prêts à diffuser
- GET `/shows/owned` : shows appartenant à l’utilisateur connecté

### 4.10 Mise à jour de statut partielle
- Méthode: PATCH
- URL: `/shows/status/{show_id}`
- Body: `{ "status": "live" }` (`ShowStatuslUpdate`)
- Réponse 200 OK `{ "id": show_id, "status": "live" }` ou 400 si status manquant

**Validation frontend**:
- `id`, `emission_id` : entiers
- `scheduled_at`, `broadcast_date` : ISO 8601
- `status` : enum ["scheduled","live","ended"]
- `presenters` : liste d’entiers
- `segments` : structure avec `position` ≥ 1, `duration` ≥ 0

---

## 5. Segments & Invités

### 5.1 Ajouter un segment (POST /segments)
```js
fetch('/segments', { method:'POST', body:JSON.stringify({ name:'Intro', order:1, duration:300 }), headers:{...} });
```
Validation : order ≥1, duration en secondes.

### 5.2 Associer un invité (POST /segments/{id}/guests)
```js
fetch(`/segments/${segId}/guests`, { method:'POST', body:JSON.stringify({ guest_id:5 }), headers:{...} });
```
200 / 404.

---

## 6. Notifications

### 6.1 Envoyer (POST /notifications)
```js
fetch('/notifications', { method:'POST', body:JSON.stringify({ user_id:1, message:'Hello' }), headers:{...} });
```
Validation : user_id int, message non vide.

### 6.2 Lister (GET /notifications)
```js
fetch('/notifications', { headers:{...} });
```
200 : liste d’objets `{ id, message, sent_at, status }`.

---

## 8. Dashboard

### 8.1 Statistiques (GET /dashbord)
```js
fetch('/dashbord?from_date=2025-04-01&to_date=2025-04-28', { headers:{...} });
```
Réponse 200 ou 404 si pas de données.

Validation : dates ISO.

---

## 9. Recherche

### 9.1 Utilisateurs (GET /search_users?keyword=test)
200 / 400 si keyword manquant.

### 9.2 Shows (GET /search_shows?keywords=xxx)
200 / 404 si pas de résultat.

---

> **Conseil Frontend** : utiliser une fonction utilitaire pour vérifier le code HTTP et parser proprement le `detail` en cas d’erreur.

---

## 6. Invités (guest_route.py)

#### 6.1 Créer un invité
- Méthode : POST
- URL : `/guests/`
- Body : `GuestCreate`
  ```json
  {
    "name": "John Doe",
    "role": "Speaker",
    "contact_info": "john.doe@example.com"
  }
  ```
- Réponse 201 Created (`GuestResponse`)
  ```json
  {
    "id": 7,
    "name": "John Doe",
    "role": "Speaker",
    "contact_info": "john.doe@example.com"
  }
  ```
- Validation : `name`: non vide, `role`: string, `contact_info`: email ou texte libre

#### 6.2 Recherche d’invités
- Méthode : GET
- URL : `/guests/search?query=John`
- Réponse 200 OK (liste de `GuestResponseWithAppearances` ou `GuestResponse`)
  ```json
  [
    { "id": 7, "name": "John Doe", ... }
  ]
  ```
- Validation : `query`: non vide, chaîne de recherche

#### 6.3 Détail d’un invité
- Méthode : GET
- URL : `/guests/{guest_id}`
- Réponse 200 OK (`GuestResponse`)
  ```json
  {
    "id": 7,
    "name": "John Doe",
    "role": "Speaker",
    "contact_info": "john.doe@example.com"
  }
  ```
- 404 Not Found si `guest_id` invalide

#### 6.4 Liste des invités
- Méthode : GET
- URL : `/guests/?skip=0&limit=10`
- Query params : `skip`, `limit`
- Réponse 200 OK (liste `GuestResponse`)
  ```json
  [ { "id":1, ... }, { "id":2, ... } ]
  ```

#### 6.5 Mise à jour d’un invité
- Méthode : PUT
- URL : `/guests/{guest_id}`
- Body : `GuestUpdate` (tous champs optionnels)
  ```json
  { "role": "Panelist" }
  ```
- Réponse 200 OK (`GuestResponse`) ou 404

#### 6.6 Suppression d’un invité
- Méthode : DELETE
- URL : `/guests/{guest_id}`
- Réponse 200 OK
  ```json
  { "message": "Invité supprimé avec succès" }
  ```
- 404 Not Found si absent

#### 6.7 Détails et participations
- Méthode : GET
- URL : `/guests/details/{guest_id}`
- Réponse 200 OK (`GuestResponseWithAppearances`)
  ```json
  {
    "id": 7,
    "name": "John Doe",
    "appearances": [
      { "show_id": 42, "title": "Actualités", "date": "2025-04-20T15:00:00Z" }
    ]
  }
  ```
- Validation : `guest_id`: entier

**Validation frontend** :
- `id` : entier
- `name`, `role`, `contact_info` : chaînes non vides
- `appe​arances`: liste d’objets avec `show_id`: int, `title`: string, `date`: ISO

---

## Permissions (permissions_route.py)

### 1. Récupérer les permissions d’un utilisateur
- Méthode: GET
- URL: `/permissions/users/{user_id}`
- Headers: `Authorization: Bearer <token>`
- Réponse 200 OK:
```json
{
  "edit_users": true,
  "delete_shows": false,
  "view_audit_logs": true
}
```
- 404 Not Found si utilisateur inconnu
- Validation frontend: `user_id` (integer)

### 2. Gestion des rôles

#### 2.1 Lister tous les rôles
- Méthode: GET
- URL: `/permissions/roles`
- Réponse 200 OK:
```json
[
  { "id": 1, "name": "admin", "description": "Administrateur" },
  { "id": 2, "name": "editor", "description": "Éditeur" }
]
```

#### 2.2 Détail d’un rôle
- Méthode: GET
- URL: `/permissions/roles/{role_id}`
- Réponse 200 OK:
```json
{ "id": 1, "name": "admin", "description": "Administrateur" }
```
- 404 Not Found si non trouvé

#### 2.3 Créer un rôle
- Méthode: POST
- URL: `/permissions/roles`
- Body:
```json
{ "name": "viewer", "description": "Lecteur seule" }
```
- Réponse 201 Created:
```json
{ "id": 3, "name": "viewer", "description": "Lecteur seule", "users": [] }
```
- Validation frontend: `name` (non vide), `description` (optionnel)

#### 2.4 Mettre à jour un rôle
- Méthode: PUT
- URL: `/permissions/roles/{role_id}`
- Body:
```json
{ "name": "viewer", "description": "Accès lecture" }
```
- Réponse 200 OK ou 404

#### 2.5 Supprimer un rôle
- Méthode: DELETE
- URL: `/permissions/roles/{role_id}`
- Réponse 200 OK:
```json
{ "message": "Rôle supprimé avec succès" }
```
- 404 Not Found si non trouvé

#### 2.6 Récupérer les permissions d’un rôle
- Méthode: GET
- URL: `/permissions/roles/{role_id}/permissions`
- Réponse 200 OK:
```json
[
  { "code": "edit_users", "description": "Édition des utilisateurs" },
  { "code": "delete_emissions", "description": "Suppression des émissions" }
]
```

### 3. Gestion des permissions

#### 3.1 Lister toutes les permissions
- Méthode: GET
- URL: `/permissions/permissions`
- Réponse 200 OK:
```json
[
  { "id": 1, "code": "edit_users", "description": "Édition des utilisateurs" },
  { "id": 2, "code": "view_reports", "description": "Consultation des rapports" }
]
```

#### 3.2 Détail d’une permission
- Méthode: GET
- URL: `/permissions/permissions/{permission_id}`
- Réponse 200 OK:
```json
{ "id": 1, "code": "edit_users", "description": "Édition des utilisateurs" }
```
- 404 Not Found si non trouvé

#### 3.3 Mettre à jour les permissions d’un utilisateur
- Méthode: PUT
- URL: `/permissions/update_permissions/{user_id}`
- Body (JSON):
```json
{
  "edit_users": true,
  "delete_shows": false
}
```
- Réponse 200 OK:
```json
{ "message": "Permissions mises à jour" }
```
- Validation frontend: clés string, valeurs booléennes

### 4. Modèles de rôles (Role Templates)

#### 4.1 Créer un modèle de rôle
- Méthode: POST
- URL: `/permissions/templates`
- Body:
```json
{ "name": "basic_editor", "permissions": ["edit_users", "delete_shows"] }
```
- Réponse 201 Created:
```json
{ "id": "uuid-1234", "name": "basic_editor", "permissions": ["edit_users", "delete_shows"] }
```

#### 4.2 Récupérer un modèle de rôle
- Méthode: GET
- URL: `/permissions/templates/{template_id}`
- Réponse 200 OK:
```json
{ "id": "uuid-1234", "name": "basic_editor", "permissions": ["edit_users"] }
```
- 404 Not Found si non trouvé

#### 4.3 Lister tous les modèles de rôles
- Méthode: GET
- URL: `/permissions/templates`
- Réponse 200 OK:
```json
[
  { "id": "uuid-1", "name": "basic_editor", "permissions": ["edit_users"] },
  { "id": "uuid-2", "name": "viewer_template", "permissions": ["view_reports"] }
]
```

#### 4.4 Mettre à jour un modèle de rôle
- Méthode: PUT
- URL: `/permissions/templates/{template_id}`
- Body:
```json
{ "name": "advanced_editor", "permissions": ["edit_users", "publish_emissions"] }
```
- Réponse 200 OK ou 404

#### 4.5 Supprimer un modèle de rôle
- Méthode: DELETE
- URL: `/permissions/templates/{template_id}`
- Réponse 200 OK:
```json
{ "detail": "Modèle supprimé avec succès" }
```
- 404 Not Found si non trouvé

#### 4.6 Appliquer un modèle de rôle à un utilisateur
- Méthode: POST
- URL: `/permissions/apply_template/{user_id}`
- Body:
```json
{ "template_id": "uuid-1234" }
```
- Réponse 200 OK:
```json
{ "message": "Modèle appliqué avec succès" }
```
- Validation frontend: `user_id` (integer), `template_id` (UUID string)

---

## Segments (segment_route.py)

### Créer un segment
- Méthode : POST
- URL : `/segments/`
- Headers : `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body : `SegmentCreate`
  ```json
  {
    "name": "Introduction",
    "order": 1,
    "duration": 300
  }
  ```
- Réponse 201 Created (`SegmentResponse`)
  ```json
  {
    "id": 12,
    "name": "Introduction",
    "order": 1,
    "duration": 300,
    "description": null
  }
  ```
- Validation :
  - `name`: string non vide
  - `order`: entier ≥ 1
  - `duration`: entier ≥ 0

### Lister tous les segments
- Méthode : GET
- URL : `/segments/?skip=0&limit=10`
- Headers : `Authorization: Bearer <token>`
- Réponse 200 OK (liste de `SegmentResponse`)
  ```json
  [
    { "id": 1, "name": "Intro", "order": 1, "duration": 180 },
    { "id": 2, "name": "Débat", "order": 2, "duration": 600 }
  ]
  ```
- Validation : `skip` (int ≥ 0), `limit` (int 1–100)

### Détail d’un segment
- Méthode : GET
- URL : `/segments/{segment_id}`
- Headers : `Authorization: Bearer <token>`
- Réponse 200 OK (`SegmentResponse`)
  ```json
  { "id": 12, "name": "Introduction", "order": 1, "duration": 300 }
  ```
- Erreur 404 Not Found si `segment_id` invalide

### Mettre à jour un segment
- Méthode : PUT
- URL : `/segments/{segment_id}`
- Headers : `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body : `SegmentUpdate` (tous champs optionnels)
  ```json
  { "name": "Intro modifié", "duration": 320 }
  ```
- Réponse 200 OK (`SegmentResponse`) ou 404
- Validation : mêmes contraintes que création

### Mettre à jour la position
- Méthode : PATCH
- URL : `/segments/{segment_id}/position`
- Headers : `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body :
  ```json
  { "position": 3 }
  ```
- Réponse 200 OK (`SegmentResponse`) ou 404
- Validation : `position`: entier ≥ 1

### Soft delete d’un segment
- Méthode : DELETE
- URL : `/segments/{segment_id}`
- Headers : `Authorization: Bearer <token>`
- Réponse 200 OK:
  ```json
  { "message": "Segment supprimé avec succès" }
  ```
- Erreur 404 Not Found si absent

---

## Dashboard (dashbord_route.py)

### Récupérer les statistiques générales
- Méthode : GET
- URL : `/dashbord/`
- En-têtes : `Authorization: Bearer <token>`
- Exemple fetch :
```js
fetch('/dashbord/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Payload : aucun
- Réponse 200 OK : objet `DashboardStats`
```json
{
  "emissions_du_jour": 5,
  "en_direct_et_a_venir": 2,
  "emissions_planifiees": 10,
  "membres_equipe": 12,
  "heures_direct": 4.5,
  "programme_du_jour": [
    { "id": 101, "emission_id": 7, "title": "News Morning", "broadcast_date": "2025-04-29T08:00:00Z", "status": "live", "animateur": "Alice", "segments": [] }
  ]
}
```
- Erreurs possibles :
  • 400 Bad Request (donnée invalide)
  • 500 Internal Server Error (erreur serveur ou base de données)
- Validation frontend :
  • aucune query param
  • vérifier la présence et le format du JWT dans l’en-tête

---

## Recherche d’utilisateurs (search_user_route.py)

### 9.1 Recherche par mot-clé
- Méthode : GET
- URL : `/search_users/?keyword=<mot>`
- Exemple fetch :
```js
fetch(`/search_users/?keyword=${encodeURIComponent(keyword)}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Payload : aucun body, paramètre `keyword` requis
- Réponse 200 OK : liste de `UserSearchResponse`
```json
[
  { "user_id": 1, "email": "alice@example.com", "username": "alice@example.com", "name": "Alice", "family_name": "Smith" },
  ...
]
```
- Erreurs :
  - 400 Bad Request si `keyword` manquant
  - 404 Not Found si aucun utilisateur ne correspond
- Validation front : `keyword`: string non vide

### 9.2 Récupération par ID
- Méthode : GET
- URL : `/search_users/id/{user_id}`
- Exemple fetch :
```js
fetch(`/search_users/id/${userId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK : un objet `UserSearchResponse`
```json
{ "user_id": 2, "email": "bob@example.com", "username": "bob@example.com", "name": "Bob", "family_name": "Brown" }
```
- Erreur 404 Not Found si `user_id` invalide
- Validation front : `user_id`: entier

### 9.3 Recherche multi-critères
- Méthode : GET
- URL : `/search_users/search?name=<nom>&email=<mail>&role=<role>`
- Exemple fetch :
```js
const params = new URLSearchParams({ name, email, role });
fetch(`/search_users/search?${params.toString()}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Payload : aucun body, filtres en query params (optionnels)
- Réponse 200 OK : liste de `UserRead`
```json
[
  { "id": 3, "email": "carol@example.com", "name": "Carol", "family_name": "Davis", "roles": [], "permissions": [] },
  ...
]
```
- Erreur 404 Not Found si pas de résultat
- Validation front : types string, chaîne vide omise

---

## Recherche de shows (search_show.py)

### GET /search_shows/
- Méthode : GET
- URL : `/search_shows/`
- Query params (facultatifs) :
  • `keyword` : string (mots‑clés dans titre/description)
  • `status` : string (ex : "scheduled", "live", "ended")
  • `dateFrom` : string (ISO 8601, date de début)
  • `dateTo` : string (ISO 8601, date de fin)
  • `presenter` : List<int> (IDs de présentateurs)
  • `guest` : List<int> (IDs d’invités)
  • `skip` : int ≥ 0 (pagination)
  • `limit` : int ≥ 1 (pagination)

- Exemple fetch :
```js
const params = new URLSearchParams();
params.append('keyword', keyword);
params.append('status', status);
params.append('dateFrom', dateFrom);
params.append('dateTo', dateTo);
if (presenters.length) presenters.forEach(id => params.append('presenter', id));
if (guests.length) guests.forEach(id => params.append('guest', id));
params.append('skip', skip);
params.append('limit', limit);

fetch(`/search_shows/?${params.toString()}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

- Réponse 200 OK : objet `{ total: int, items: Array<ShowSummary> }`
```json
{
  "total": 42,
  "items": [
    { "id": 101, "title": "News Morning", "broadcast_date": "2025-04-29T08:00:00Z", "status": "scheduled" },
    { "id": 102, "title": "Tech Talk", ... }
  ]
}
```

- Erreurs :
  • 400 Bad Request (paramètres invalides)
  • 404 Not Found (aucun show trouvé)
  • 500 Internal Server Error

- Validation frontend :
  • `keyword`, `status`: non vide si fourni
  • `dateFrom`, `dateTo`: format ISO YYYY-MM-DD[T]HH:mm:ssZ
  • `presenter`, `guest`: tableaux d’entiers
  • `skip`, `limit`: entiers ≥ 0

---

## Présentateurs (presenter_route.py)

### Créer un présentateur
- Méthode : POST
- URL : `/presenters/`
- Headers : `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body : `PresenterCreate`
  ```json
  {
    "name": "Alice Dupont",
    "email": "alice.dupont@example.com",
    "bio": "Journaliste spécialisée",
    "contact_info": "alice.dupont@example.com"
  }
  ```
- Réponse 201 Created (`PresenterResponse`)
  ```json
  {
    "id": 5,
    "name": "Alice Dupont",
    "email": "alice.dupont@example.com",
    "bio": "Journaliste spécialisée",
    "contact_info": "alice.dupont@example.com",
    "created_at": "2025-04-29T11:00:00Z",
    "updated_at": "2025-04-29T11:00:00Z"
  }
  ```
- Erreur 422 si payload invalide
- Validation :
  • `name`, `email` non vides
  • `email` format valid

### Lister les présentateurs
- Méthode : GET
- URL : `/presenters/all?skip=0&limit=10`
- Exemple fetch :
```js
fetch(`/presenters/all?skip=${skip}&limit=${limit}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK (`List[PresenterResponsePaged]`)
  ```json
  {
    "total": 35,
    "items": [
      { "id":1, "name":"Jean Martin", ... },
      ...
    ]
  }
  ```
- Validation : `skip` ≥0, `limit` entre 1 et 100

### Détail d’un présentateur
- Méthode : GET
- URL : `/presenters/{presenter_id}`
- Exemple fetch :
```js
fetch(`/presenters/${id}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK (`PresenterResponse`) :
  ```json
  { "id":5, "name":"Alice Dupont", "email":"...", "bio":"...", "contact_info":"..." }
  ```
- Erreur 404 Not Found si non trouvé
- Validation : `presenter_id`: entier

### Récupérer par user_id
- Méthode : GET
- URL : `/presenters/by-user/{users_id}`
- Exemple fetch :
```js
fetch(`/presenters/by-user/${userId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 200 OK (`PresenterResponse`) ou 404 si pas de présentateur

### Mettre à jour un présentateur
- Méthode : PUT
- URL : `/presenters/update/{presenter_id}`
- Body : `PresenterUpdate`
  ```json
  { "bio": "Animatrice politique", "contact_info": "alice.new@example.com" }
  ```
- Réponse 200 OK (`PresenterResponse`)
- Erreur 404 Not Found si non trouvé
- Validation : champs optionnels mais types corrects

### Supprimer un présentateur
- Méthode : DELETE
- URL : `/presenters/del/{presenter_id}`
- Exemple fetch :
```js
fetch(`/presenters/del/${id}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```
- Réponse 204 No Content ou 200 OK `{ message: "Presenter deleted successfully" }`
- Erreur 404 Not Found si non trouvé
- Validation : `presenter_id`: entier

---

## Route par défaut (Root)
- Méthode : GET
- URL : `/`
- Exemple fetch :
```js
fetch('/', { method: 'GET' });
```
- Payload : aucun
- Réponse 200 OK :
```json
{ "BIEBVENUE": "HAPSON API pour AMG" }
```
- Validation frontend : aucune authentification requise

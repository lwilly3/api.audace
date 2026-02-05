# 👤 Routes Users (`/users`)

> Gestion des utilisateurs, profils, historique de connexions.

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/users/users` | ✅ | Liste tous les utilisateurs |
| `GET` | `/users/users/{id}` | ✅ | Détails d'un utilisateur |
| `POST` | `/users/users` | ❌ | Créer un utilisateur |
| `PUT` | `/users/updte/{user_id}` | ✅ | Modifier un utilisateur |
| `PUT` | `/users/upd_date/{id}` | ✅ | Modifier un utilisateur (alt) |
| `DELETE` | `/users/del/{id}` | ❌ | Supprimer un utilisateur (soft) |
| `GET` | `/users/non-presenters` | ✅ | Utilisateurs non-présentateurs |
| `GET` | `/users/users/{id}/logins` | ✅ | Historique connexions |
| `GET` | `/users/users/{id}/notifications` | ✅ | Notifications d'un user |
| `GET` | `/users/users/{id}/audit-logs` | ✅ | Audit logs d'un user |

### Routes de Recherche (`/search_users`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/search_users/?keyword=xxx` | ❌ | Recherche par mot-clé |
| `GET` | `/search_users/id/{user_id}` | ❌ | User par ID |
| `GET` | `/search_users/search` | ❌ | Recherche avancée |

---

## 📦 Schémas de Données

### UserResponse
```typescript
/** GET /users/users/{id} - Utilisateur complet */
interface UserResponse {
  id: number;
  username: string;
  email: string;
  name: string | null;
  family_name: string | null;
  phone_number: string | null;
  is_active: boolean;
  created_at: string;           // ISO 8601
  updated_at: string | null;    // ISO 8601
  profilePicture: string | null;
  roles: RoleRead[];            // Rôles assignés
}

interface RoleRead {
  id: number;
  name: string;
}
```

### UserCreate
```typescript
/** POST /users/users - Création utilisateur */
interface UserCreate {
  username: string;
  email: string;
  name?: string | null;
  family_name?: string | null;
  phone_number?: string | null;
  password: string;
}
```

### UserUpdate
```typescript
/** PUT /users/updte/{id} - Mise à jour utilisateur */
interface UserUpdate {
  username?: string;
  email?: string;
  name?: string;
  family_name?: string;
  phone_number?: string;
  profilePicture?: string;
  password?: string;
  is_active?: boolean;
  is_deleted?: boolean;
  deleted_at?: string;
  roles?: number[];  // IDs des rôles
}
```

### Historique & Logs
```typescript
/** GET /users/users/{id}/logins - Historique connexions */
interface LoginHistoryResponse {
  id: number;
  user_id: number;
  ip_address: string | null;
  timestamp: string;  // ISO 8601
}

/** GET /users/users/{id}/notifications */
interface UserNotificationResponse {
  user_id: number;
  message: string;
  created_at: string;  // ISO 8601
}

/** GET /users/users/{id}/audit-logs */
interface UserAuditLogResponse {
  user_id: number;
  action: string;
  timestamp: string;  // ISO 8601
}
```

### Recherche
```typescript
/** GET /search_users/ - Résultat recherche */
interface UserSearchResponse {
  id: number;
  username: string;
  email: string;
  name: string | null;
  family_name: string | null;
  phone_number: string | null;
  created_at: string;
  profilePicture: string | null;
  roles: RoleRead[];
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les utilisateurs
```typescript
const users: UserResponse[] = await fetch('/users/users', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Obtenir un utilisateur
```typescript
const user: UserResponse = await fetch('/users/users/123', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "id": 1,
  "username": "john_doe",
  "email": "john@radio.com",
  "name": "John",
  "family_name": "Doe",
  "phone_number": "+33123456789",
  "is_active": true,
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z",
  "profilePicture": "https://cdn.radio.com/avatars/john.jpg",
  "roles": [
    { "id": 1, "name": "Admin" },
    { "id": 3, "name": "Presenter" }
  ]
}
```

### Créer un utilisateur
```typescript
const newUser: UserResponse = await fetch('/users/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'jane_doe',
    email: 'jane@radio.com',
    password: 'securePassword123',
    name: 'Jane',
    family_name: 'Doe'
  })
}).then(r => r.json());
```

### Modifier un utilisateur
```typescript
// ⚠️ Note: URL = /users/updte/{id} (pas /users/users/{id})
const updated: UserResponse = await fetch('/users/updte/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'John Updated',
    phone_number: '+33999999999'
  })
}).then(r => r.json());
```

### Historique de connexions
```typescript
const logins: LoginHistoryResponse[] = await fetch('/users/users/123/logins', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
[
  { "id": 1, "user_id": 123, "ip_address": "192.168.1.100", "timestamp": "2025-01-15T08:00:00Z" },
  { "id": 2, "user_id": 123, "ip_address": "10.0.0.50", "timestamp": "2025-01-14T09:30:00Z" }
]
```

### Rechercher des utilisateurs
```typescript
// Recherche simple par mot-clé
const results = await fetch('/search_users/?keyword=john')
  .then(r => r.json());

// Recherche avancée
const advancedResults = await fetch('/search_users/search?name=John&role=admin')
  .then(r => r.json());
```

### Utilisateurs non-présentateurs
```typescript
// Utile pour créer un nouveau présentateur
const nonPresenters: UserResponse[] = await fetch('/users/non-presenters', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Voir liste utilisateurs | `can_view_users` |
| Voir section utilisateurs | `can_acces_users_section` |
| Modifier utilisateur | `can_edit_users` |
| Désactiver utilisateur | `can_desable_users` |
| Supprimer utilisateur | `can_delete_users` |
| Voir historique connexions | `can_view_login_history` |
| Voir audit logs | `can_view_audit_logs` |

---

## ⚠️ Points d'Attention

1. **URL de modification** : `PUT /users/updte/{id}` (pas `/users/users/{id}`)
2. **Soft delete** : La suppression ne supprime pas vraiment, elle met `is_deleted = true`
3. **Recherche publique** : Les routes `/search_users/*` n'ont pas besoin d'authentification
4. **Rôles** : Les rôles sont retournés avec chaque utilisateur mais modifiés via `/roles/assign/{user_id}`

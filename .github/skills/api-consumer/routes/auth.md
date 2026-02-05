# 🔑 Routes Authentication (`/auth`)

> Gestion de l'authentification JWT, invitations et reset password.

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/auth/login` | ❌ | Connexion (form-data) |
| `POST` | `/auth/logout` | ✅ | Déconnexion |
| `POST` | `/auth/signup` | ❌ | Inscription |
| `POST` | `/auth/invite` | ✅ | Générer lien d'invitation |
| `GET` | `/auth/invite/validate?token=xxx` | ❌ | Valider token invitation |
| `POST` | `/auth/signup-with-invite` | ❌ | Inscription via invitation |
| `POST` | `/auth/forgot-password` | ❌ | Demander reset password |
| `POST` | `/auth/reset-password` | ❌ | Réinitialiser password |
| `POST` | `/auth/generate-reset-token` | ❌ | Générer token reset (par user_id) |
| `GET` | `/auth/reset-token/validate?token=xxx` | ❌ | Valider token reset |

---

## 📦 Schémas de Données

### LoginResponse
```typescript
/** POST /auth/login - Réponse de connexion */
interface LoginResponse {
  access_token: string;       // JWT token
  token_type: "bearer";
  user_id: number;
  username: string;
  email: string;
  name: string;
  family_name: string;
  phone_number: string | null;
  permissions: UserPermissionsResponse;  // Toutes les permissions
}
```

### UserPermissionsResponse
```typescript
/** Permissions retournées avec le login */
interface UserPermissionsResponse {
  // Showplans
  can_acces_showplan_broadcast_section: boolean;
  can_acces_showplan_section: boolean;
  can_create_showplan: boolean;
  can_edit_showplan: boolean;
  can_archive_showplan: boolean;
  can_archiveStatusChange_showplan: boolean;
  can_delete_showplan: boolean;
  can_destroy_showplan: boolean;
  can_changestatus_showplan: boolean;
  can_changestatus_owned_showplan: boolean;
  can_changestatus_archived_showplan: boolean;
  can_setOnline_showplan: boolean;
  can_viewAll_showplan: boolean;
  
  // Utilisateurs
  can_acces_users_section: boolean;
  can_view_users: boolean;
  can_edit_users: boolean;
  can_desable_users: boolean;
  can_delete_users: boolean;
  
  // Rôles
  can_manage_roles: boolean;
  can_assign_roles: boolean;
  
  // Invités
  can_acces_guests_section: boolean;
  can_view_guests: boolean;
  can_edit_guests: boolean;
  can_delete_guests: boolean;
  
  // Présentateurs
  can_acces_presenters_section: boolean;
  can_view_presenters: boolean;
  can_create_presenters: boolean;
  can_edit_presenters: boolean;
  can_delete_presenters: boolean;
  
  // Émissions
  can_acces_emissions_section: boolean;
  can_view_emissions: boolean;
  can_create_emissions: boolean;
  can_edit_emissions: boolean;
  can_delete_emissions: boolean;
  can_manage_emissions: boolean;
  
  // Notifications
  can_view_notifications: boolean;
  can_manage_notifications: boolean;
  
  // Audit & Historique
  can_view_audit_logs: boolean;
  can_view_login_history: boolean;
  
  // Global
  can_manage_settings: boolean;
  
  // Messages
  can_view_messages: boolean;
  can_send_messages: boolean;
  can_delete_messages: boolean;
  
  // Fichiers
  can_view_files: boolean;
  can_upload_files: boolean;
  can_delete_files: boolean;
  
  // Tâches
  can_view_tasks: boolean;
  can_create_tasks: boolean;
  can_edit_tasks: boolean;
  can_delete_tasks: boolean;
  can_assign_tasks: boolean;
  
  // Archives
  can_view_archives: boolean;
  can_destroy_archives: boolean;
  can_restore_archives: boolean;
  can_delete_archives: boolean;
  
  // Citations (Firebase)
  quotes_view: boolean;
  quotes_create: boolean;
  quotes_edit: boolean;
  quotes_delete: boolean;
  quotes_publish: boolean;
  stream_transcription_view: boolean;
  stream_transcription_create: boolean;
  quotes_capture_live: boolean;
}
```

### Autres Schémas Auth
```typescript
/** POST /auth/invite - Génération lien d'invitation */
interface InviteResponse {
  invite_token: string;
  invite_url: string;
  expires_at: string;  // ISO 8601
}

/** GET /auth/invite/validate - Validation invitation */
interface InviteValidationResponse {
  valid: boolean;
  email?: string;
  expires_at?: string;
}

/** POST /auth/generate-reset-token */
interface ResetTokenResponse {
  reset_token: string;
  expires_at: string;  // ISO 8601
}

/** GET /auth/reset-token/validate */
interface ResetTokenValidationResponse {
  valid: boolean;
  user_id?: number;
}
```

---

## 🔄 Exemples d'Utilisation

### Login (⚠️ form-data, pas JSON !)
```typescript
// ❌ FAUX - Ne pas utiliser JSON
await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

// ✅ CORRECT - Utiliser form-data avec "username"
const formData = new URLSearchParams();
formData.append('username', email);  // ⚠️ "username" même si c'est un email
formData.append('password', password);

const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData
});

const data: LoginResponse = await response.json();
// Stocker le token
localStorage.setItem('token', data.access_token);
// Stocker les permissions
localStorage.setItem('permissions', JSON.stringify(data.permissions));
```

### Utiliser le Token
```typescript
// Toutes les requêtes authentifiées
const response = await fetch('/users/users', {
  headers: {
    'Authorization': `Bearer ${token}`,  // ⚠️ Ne pas oublier "Bearer "
    'Content-Type': 'application/json'
  }
});
```

### Logout
```typescript
await fetch('/auth/logout', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
localStorage.removeItem('token');
localStorage.removeItem('permissions');
```

### Flow Reset Password
```typescript
// 1. Générer token (admin ou système)
const { reset_token, expires_at } = await fetch('/auth/generate-reset-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 123 })
}).then(r => r.json());

// 2. Valider token (page reset)
const { valid, user_id } = await fetch(`/auth/reset-token/validate?token=${reset_token}`)
  .then(r => r.json());

// 3. Réinitialiser mot de passe
if (valid) {
  await fetch('/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: reset_token, new_password: 'newSecret123' })
  });
}
```

### Flow Invitation
```typescript
// 1. Générer invitation (admin)
const { invite_token, invite_url } = await fetch('/auth/invite', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${adminToken}` }
}).then(r => r.json());

// 2. Valider invitation (page inscription)
const { valid, email } = await fetch(`/auth/invite/validate?token=${invite_token}`)
  .then(r => r.json());

// 3. S'inscrire avec invitation
if (valid) {
  await fetch('/auth/signup-with-invite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invite_token,
      username: 'newuser',
      email: 'new@email.com',
      password: 'password123'
    })
  });
}
```

---

## ⚠️ Points d'Attention

1. **Login = form-data** : Le login utilise `application/x-www-form-urlencoded`, pas JSON
2. **"username" pas "email"** : Le champ s'appelle `username` même si on envoie un email
3. **Bearer obligatoire** : Le header doit être `Bearer {token}` avec l'espace
4. **Permissions au login** : Toutes les permissions sont retournées au login, pas besoin d'appel supplémentaire
5. **Token JWT** : Expire après un certain temps, gérer le refresh côté frontend

# 🔒 Routes Permissions & Roles (`/permissions`, `/roles`)

> Gestion des permissions, rôles et templates de permissions.

---

## 📋 Endpoints Permissions (`/permissions`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/permissions/users/{user_id}` | ✅ | Permissions d'un utilisateur |
| `PUT` | `/permissions/update_permissions/{user_id}` | ✅ | Modifier toutes permissions |
| `PATCH` | `/permissions/users/{user_id}/patch_selected_permissions` | ✅ | Modifier permissions partielles |
| `GET` | `/permissions/roles` | ✅ | Liste des rôles |
| `GET` | `/permissions/roles/{id}` | ✅ | Détails d'un rôle |
| `POST` | `/permissions/roles` | ✅ | Créer un rôle |
| `PUT` | `/permissions/roles/{id}` | ✅ | Modifier un rôle |
| `DELETE` | `/permissions/roles/{id}` | ✅ | Supprimer un rôle |
| `GET` | `/permissions/roles/{id}/permissions` | ✅ | Permissions d'un rôle |
| `GET` | `/permissions/permissions` | ✅ | Liste toutes les permissions |
| `GET` | `/permissions/permissions/{id}` | ✅ | Détails d'une permission |

### Templates de Permissions

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/permissions/templates` | ✅ | Liste des templates |
| `GET` | `/permissions/templates/{template_id}` | ✅ | Détails d'un template |
| `POST` | `/permissions/templates` | ✅ | Créer un template |
| `PUT` | `/permissions/templates/{template_id}` | ✅ | Modifier un template |
| `DELETE` | `/permissions/templates/{template_id}` | ✅ | Supprimer un template |
| `POST` | `/permissions/apply_template/{user_id}` | ✅ | Appliquer template à user |

## 📋 Endpoints Roles (`/roles`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/roles/all` | ❌ | Liste tous les rôles |
| `GET` | `/roles/id/{role_id}` | ❌ | Détails d'un rôle |
| `POST` | `/roles/` | ❌ | Créer un rôle |
| `PUT` | `/roles/update/{role_id}` | ❌ | Modifier un rôle |
| `DELETE` | `/roles/del/{role_id}` | ❌ | Supprimer un rôle |
| `POST` | `/roles/assign/{user_id}` | ❌ | Assigner rôles à un user |
| `POST` | `/roles/unassign/{user_id}` | ❌ | Retirer rôles d'un user |
| `GET` | `/roles/all_assigned/{user_id}` | ❌ | Rôles d'un utilisateur |

---

## 📦 Schémas de Données

### Rôles
```typescript
/** Rôle simple */
interface RoleRead {
  id: number;
  name: string;
}

/** Rôle complet */
interface RoleResponse {
  id: number;
  name: string;
  description: string | null;
  permissions: number[];          // IDs des permissions
  is_deleted: boolean;
}

/** POST /roles/ - Création rôle */
interface RoleCreate {
  name: string;
}

/** PUT /roles/update/{id} */
interface RoleUpdate {
  name?: string;
}

/** POST /roles/assign/{user_id} */
interface UserRoleAssign {
  role_ids: number[];
}
```

### Permissions
```typescript
/** Permission individuelle */
interface PermissionRead {
  id: number;
  name: string;
  description: string | null;
}

/** PUT /permissions/update_permissions/{user_id} - Body */
type UserPermissionsUpdate = Partial<UserPermissionsResponse>;
```

### Templates
```typescript
/** POST /permissions/templates - Création template */
interface RoleTemplateCreate {
  name: string;
  description?: string;
  permissions: Record<string, boolean>;
}

/** GET /permissions/templates/{id} */
interface RoleTemplateResponse {
  id: number;
  name: string;
  description: string | null;
  permissions: Record<string, boolean>;
  created_at: string;
  updated_at: string;
}

/** PUT /permissions/templates/{id} */
interface RoleTemplateUpdate {
  name?: string;
  description?: string;
  permissions?: Record<string, boolean>;
}
```

### Permissions Partielles Autorisées
```typescript
/** PATCH - Seules ces permissions peuvent être modifiées via PATCH */
const ALLOWED_PARTIAL_PERMISSIONS = [
  'can_acces_showplan_section',
  'can_create_showplan',
  'can_changestatus_owned_showplan',
  'can_delete_showplan',
  'can_edit_showplan',
  'can_archive_showplan',
  'can_acces_guests_section',
  'can_view_guests',
  'can_edit_guests',
  'can_view_archives'
] as const;
```

---

## 🔄 Exemples d'Utilisation

### Obtenir les permissions d'un utilisateur
```typescript
const permissions = await fetch('/permissions/users/123', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "can_acces_showplan_section": true,
  "can_create_showplan": true,
  "can_edit_showplan": true,
  "can_archive_showplan": false,
  "can_delete_showplan": false,
  // ... toutes les permissions
}
```

### Modifier toutes les permissions
```typescript
await fetch('/permissions/update_permissions/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    can_create_showplan: true,
    can_edit_users: false,
    can_delete_guests: true
  })
});
```

### Modifier permissions partielles (PATCH)
```typescript
// ⚠️ Seules certaines permissions sont autorisées via PATCH
await fetch('/permissions/users/123/patch_selected_permissions', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    can_acces_showplan_section: true,
    can_create_showplan: true,
    can_edit_showplan: false,
    can_view_guests: true
  })
});
```

### Gérer les rôles
```typescript
// Lister les rôles (public)
const roles = await fetch('/roles/all').then(r => r.json());

// Assigner des rôles à un utilisateur
await fetch('/roles/assign/123', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ role_ids: [1, 3] })
});

// Retirer des rôles
await fetch('/roles/unassign/123', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ role_ids: [3] })
});

// Voir les rôles d'un utilisateur
const userRoles = await fetch('/roles/all_assigned/123').then(r => r.json());
```

### Utiliser les templates
```typescript
// Créer un template de permissions
const template = await fetch('/permissions/templates', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Présentateur Standard",
    description: "Permissions de base pour les présentateurs",
    permissions: {
      can_acces_showplan_section: true,
      can_create_showplan: true,
      can_edit_showplan: true,
      can_changestatus_owned_showplan: true,
      can_acces_guests_section: true,
      can_view_guests: true,
      can_edit_guests: false,
      can_delete_guests: false
    }
  })
}).then(r => r.json());

// Appliquer un template à un utilisateur
await fetch('/permissions/apply_template/123', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ template_id: 5 })
});
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Gérer les rôles | `can_manage_roles` |
| Assigner des rôles | `can_assign_roles` |

---

## 📊 Rôles Prédéfinis

| Rôle | Description |
|------|-------------|
| `Admin` | Accès complet à toutes les fonctionnalités |
| `Éditeur` | Gestion des contenus, modification générale |
| `Animateur` | Gestion de ses propres shows |
| `Community Manager` | Publication et réseaux sociaux |
| `Invité` | Accès lecture seule limité |

---

## ⚠️ Points d'Attention

1. **Routes /roles publiques** : Les routes `/roles/*` n'ont pas d'authentification
2. **PATCH limité** : Seules certaines permissions peuvent être modifiées via PATCH
3. **Templates** : Utilisez les templates pour appliquer des permissions standardisées
4. **PUT vs PATCH** : PUT modifie toutes les permissions, PATCH seulement celles autorisées
5. **Cascade** : Attention lors de la suppression de rôles - vérifier les utilisateurs associés

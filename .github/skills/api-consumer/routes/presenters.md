# 🎙️ Routes Presenters (`/presenters`)

> Gestion des présentateurs et animateurs.

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/presenters/all` | ✅ | Liste des présentateurs |
| `GET` | `/presenters/{presenter_id}` | ✅ | Détails d'un présentateur |
| `GET` | `/presenters/by-user/{users_id}` | ✅ | Présentateur par user_id |
| `GET` | `/presenters/deleted` | ✅ | Présentateurs supprimés |
| `POST` | `/presenters/` | ✅ | Créer un présentateur |
| `POST` | `/presenters/assign` | ✅ | Assigner/réactiver présentateur |
| `PUT` | `/presenters/update/{presenter_id}` | ✅ | Modifier un présentateur |
| `DELETE` | `/presenters/del/{presenter_id}` | ✅ | Supprimer (soft delete) |

---

## 📦 Schémas de Données

### PresenterResponse
```typescript
/** GET /presenters/{id} - Réponse présentateur */
interface PresenterResponse {
  id: number;
  name: string;
  contact_info: string | null;
  biography: string | null;
  profilePicture: string | null;
  users_id: number;               // ID utilisateur lié
  shows: string[];                // Titres des shows
  isMainPresenter: boolean;
}
```

### PresenterResponsePaged
```typescript
/** GET /presenters/all - Liste paginée */
interface PresenterResponsePaged {
  total: number;
  presenters: PresenterResponse[];
}
```

### PresenterCreate
```typescript
/** POST /presenters/ - Création présentateur */
interface PresenterCreate {
  name: string;                   // max 100 chars, requis
  contact_info?: string;          // max 255 chars
  biography?: string;
  users_id: number;               // ID utilisateur lié, requis
  profilePicture?: string;
  isMainPresenter?: boolean;      // défaut: false
}
```

### PresenterUpdate
```typescript
/** PUT /presenters/update/{id} */
interface PresenterUpdate {
  name?: string;
  contact_info?: string;
  biography?: string;
  profilePicture?: string;
  isMainPresenter?: boolean;
}
```

### PresenterHistory
```typescript
/** Historique des modifications */
interface PresenterHistory {
  id: number;
  presenter_id: number;
  updated_by: number;
  update_date: string;
  changes: string;                // JSON stringifié
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les présentateurs
```typescript
const { total, presenters }: PresenterResponsePaged = await fetch('/presenters/all', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "total": 8,
  "presenters": [
    {
      "id": 1,
      "name": "Marie Dupont",
      "contact_info": "marie.dupont@radio.com",
      "biography": "Journaliste expérimentée avec 15 ans d'expérience",
      "profilePicture": "https://cdn.radio.com/presenters/marie.jpg",
      "users_id": 5,
      "shows": ["Journal du Matin", "Débat du Soir"],
      "isMainPresenter": true
    },
    {
      "id": 2,
      "name": "Jean Martin",
      "contact_info": "jean.martin@radio.com",
      "biography": "Spécialiste culture et musique",
      "profilePicture": null,
      "users_id": 8,
      "shows": ["Culture Express"],
      "isMainPresenter": false
    }
  ]
}
```

### Obtenir un présentateur
```typescript
const presenter: PresenterResponse = await fetch('/presenters/123', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Trouver le présentateur d'un utilisateur
```typescript
// Trouver le profil présentateur associé à un user
const presenter: PresenterResponse = await fetch('/presenters/by-user/456', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Créer un présentateur
```typescript
// D'abord, obtenir les utilisateurs sans profil présentateur
const nonPresenters = await fetch('/users/non-presenters', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Puis créer le présentateur
const newPresenter: PresenterResponse = await fetch('/presenters/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Sophie Bernard",
    contact_info: "sophie.bernard@radio.com",
    biography: "Animatrice radio depuis 2018",
    users_id: 12,  // ID d'un utilisateur existant
    profilePicture: "https://cdn.radio.com/presenters/sophie.jpg",
    isMainPresenter: false
  })
}).then(r => r.json());
```

### Modifier un présentateur
```typescript
// ⚠️ URL = /presenters/update/{id}
const updated: PresenterResponse = await fetch('/presenters/update/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    biography: "Animatrice radio primée, spécialiste des interviews politiques",
    isMainPresenter: true
  })
}).then(r => r.json());
```

### Supprimer un présentateur
```typescript
// Soft delete
await fetch('/presenters/del/123', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});

// Voir les présentateurs supprimés
const deleted: PresenterResponse[] = await fetch('/presenters/deleted', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Réactiver un présentateur
```typescript
// Utiliser /assign pour réactiver un présentateur supprimé
await fetch('/presenters/assign', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    users_id: 12  // ID de l'utilisateur
  })
});
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Accès section présentateurs | `can_acces_presenters_section` |
| Voir les présentateurs | `can_view_presenters` |
| Créer un présentateur | `can_create_presenters` |
| Modifier un présentateur | `can_edit_presenters` |
| Supprimer un présentateur | `can_delete_presenters` |

---

## 🔗 Relations

```
User (1) ←→ (0..1) Presenter
Presenter (N) ←→ (N) Show
```

- Un utilisateur peut avoir **au plus** un profil présentateur
- Un présentateur peut être associé à **plusieurs** shows
- Un show peut avoir **plusieurs** présentateurs

---

## ⚠️ Points d'Attention

1. **URL de modification** : `PUT /presenters/update/{id}` (pas `/presenters/{id}`)
2. **users_id requis** : Un présentateur doit être lié à un utilisateur existant
3. **isMainPresenter** : Un seul présentateur principal par show recommandé
4. **Soft delete** : Les présentateurs supprimés peuvent être réactivés via `/assign`
5. **Non-présentateurs** : Utiliser `/users/non-presenters` pour trouver les users disponibles

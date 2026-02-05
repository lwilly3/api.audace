# 👥 Routes Guests (`/guests`)

> Gestion des invités des émissions.

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/guests/` | ✅ | Liste des invités (pagination) |
| `GET` | `/guests/{guest_id}` | ✅ | Détails d'un invité |
| `GET` | `/guests/details/{guest_id}` | ✅ | Invité avec participations |
| `GET` | `/guests/search?query=xxx` | ❌ | Rechercher un invité |
| `POST` | `/guests/` | ✅ | Créer un invité |
| `PUT` | `/guests/{guest_id}` | ✅ | Modifier un invité |
| `DELETE` | `/guests/{guest_id}` | ✅ | Supprimer un invité |

---

## 📦 Schémas de Données

### GuestResponse
```typescript
/** GET /guests/{id} - Réponse invité */
interface GuestResponse {
  id: number;
  name: string;
  contact_info: string | null;
  biography: string | null;
  role: string | null;
  phone: string | null;
  email: string | null;
  avart: string | null;           // ⚠️ Typo volontaire (avatar)
  segments: string[];             // Titres des segments
}
```

### GuestResponseAndDetails
```typescript
/** GET /guests/details/{id} - Avec détails contact */
interface GuestResponseAndDetails {
  id: number;
  name: string;
  role: string | null;
  avatar: string | null;
  created_at: string;
  biography: string | null;
  contact: Contact;
  contact_info: string | null;
}

interface Contact {
  email: string | null;
  phone: string | null;
}
```

### GuestResponseWithAppearances
```typescript
/** Avec liste des apparitions */
interface GuestResponseWithAppearances extends GuestResponse {
  appearances: Appearance[];
}

interface Appearance {
  show_id: number;
  show_title: string;
  broadcast_date: string;
}
```

### GuestCreate
```typescript
/** POST /guests/ - Création invité */
interface GuestCreate {
  name: string;                   // max 100 chars, requis
  contact_info?: string;          // max 255 chars
  biography?: string;
  role?: string;
  phone?: string;
  email?: string;
  avart?: string;                 // ⚠️ Typo volontaire (avatar)
}
```

### GuestUpdate
```typescript
/** PUT /guests/{id} */
interface GuestUpdate {
  name?: string;
  contact_info?: string;
  biography?: string;
  role?: string;
  phone?: string;
  email?: string;
  avart?: string;
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les invités
```typescript
const guests: GuestResponse[] = await fetch('/guests/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Rechercher un invité (sans auth)
```typescript
const results: GuestResponse[] = await fetch('/guests/search?query=durand')
  .then(r => r.json());
```

### Obtenir un invité avec ses apparitions
```typescript
const guest: GuestResponseAndDetails = await fetch('/guests/details/123', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "id": 5,
  "name": "Pierre Durand",
  "role": "Maire",
  "avatar": "https://cdn.radio.com/guests/pierre.jpg",
  "created_at": "2024-06-15T10:00:00Z",
  "biography": "Maire de Lyon depuis 2020, ancien député",
  "contact": {
    "email": "pierre.durand@mairie-lyon.fr",
    "phone": "+33456789012"
  },
  "contact_info": "Mairie de Lyon"
}
```

### Créer un invité
```typescript
const newGuest: GuestResponse = await fetch('/guests/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Marie Leroy",
    contact_info: "Université Lyon 2",
    biography: "Professeure de sociologie, spécialiste des médias",
    role: "Expert",
    phone: "+33478901234",
    email: "m.leroy@univ-lyon2.fr",
    avart: null  // ⚠️ "avart" pas "avatar"
  })
}).then(r => r.json());
```

### Modifier un invité
```typescript
const updated: GuestResponse = await fetch('/guests/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    role: "Expert économie",
    biography: "Professeure et auteure de plusieurs ouvrages"
  })
}).then(r => r.json());
```

### Supprimer un invité
```typescript
const result = await fetch('/guests/123', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Réponse: { "message": "Invité supprimé avec succès" }
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Accès section invités | `can_acces_guests_section` |
| Voir les invités | `can_view_guests` |
| Modifier un invité | `can_edit_guests` |
| Supprimer un invité | `can_delete_guests` |

---

## 🔗 Relations

```
Guest (N) ←→ (N) Segment
Segment (N) ←→ (1) Show
```

- Un invité peut participer à **plusieurs** segments
- Un segment peut avoir **plusieurs** invités
- Les invités sont liés aux shows via les segments

---

## 👤 Rôles d'Invités Courants

| Rôle | Description |
|------|-------------|
| `Expert` | Spécialiste d'un domaine |
| `Témoin` | Personne témoignant |
| `Artiste` | Musicien, acteur, etc. |
| `Politique` | Élu, responsable politique |
| `Auteur` | Écrivain, journaliste |
| `Sportif` | Athlète, entraîneur |
| `Entrepreneur` | Chef d'entreprise |

---

## ⚠️ Points d'Attention

1. **⚠️ Typo "avart"** : Le champ avatar s'appelle `avart` (typo historique conservée)
2. **Recherche publique** : `/guests/search` n'a pas besoin d'authentification
3. **URL standard** : Contrairement à d'autres routes, `PUT /guests/{id}` est standard
4. **Segments** : Le champ `segments` retourne les titres des segments, pas les IDs

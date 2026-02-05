# 🎬 Routes Shows & Segments (`/shows`, `/segments`, `/search_shows`)

> Gestion des conducteurs (shows), segments et recherche.

---

## 📋 Endpoints Shows (`/shows`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/shows/` | ❌ | Liste des shows (pagination) |
| `GET` | `/shows/{show_id}` | ❌ | Détails d'un show |
| `POST` | `/shows/` | ❌ | Créer un show simple |
| `POST` | `/shows/detail` | ✅ | Créer show avec segments/présentateurs |
| `POST` | `/shows/new` | ✅ | Créer show depuis JSON complet |
| `PATCH` | `/shows/detail/{show_id}` | ✅ | Modifier show avec détails |
| `PATCH` | `/shows/status/{show_id}` | ✅ | Modifier statut uniquement |
| `PUT` | `/shows/upd/{show_id}` | ✅ | Modifier un show |
| `DELETE` | `/shows/del/{show_id}` | ✅ | Supprimer un show |
| `GET` | `/shows/x` | ❌ | Tous les shows avec détails |
| `GET` | `/shows/x/{show_id}` | ❌ | Show avec détails par ID |
| `GET` | `/shows/getdetail/{show_id}` | ✅ | Show détaillé (auth) |
| `GET` | `/shows/production` | ❌ | Shows prêts à diffuser |
| `GET` | `/shows/owned` | ✅ | Shows de l'utilisateur connecté |
| `DELETE` | `/shows/all` | ✅ | Supprimer TOUS les shows ⚠️ |
| `DELETE` | `/shows/allofuser/{user_id}` | ✅ | Supprimer shows d'un user |

## 📋 Endpoints Segments (`/segments`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/segments/` | ✅ | Liste des segments |
| `GET` | `/segments/{segment_id}` | ✅ | Détails d'un segment |
| `POST` | `/segments/` | ✅ | Créer un segment |
| `PUT` | `/segments/{segment_id}` | ✅ | Modifier un segment |
| `PATCH` | `/segments/{segment_id}/position` | ✅ | Modifier la position |
| `DELETE` | `/segments/{segment_id}` | ✅ | Supprimer (soft delete) |

## 📋 Recherche Shows (`/search_shows`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/search_shows/` | ❌ | Recherche avancée shows |

---

## 📦 Schémas de Données

### ShowStatus (Enum)
```typescript
type ShowStatus = 
  | "En préparation"
  | "Planifié"
  | "En direct"
  | "Terminé"
  | "Annulé"
  | "Archivé";
```

### ShowOut (Réponse basique)
```typescript
/** GET /shows/{id} - Réponse basique */
interface ShowOut {
  id: number;
  title: string;
  type: string;
  broadcast_date: string | null;
  duration: number;
  frequency: string | null;
  description: string | null;
  status: ShowStatus;
  emission_id: number | null;
  created_at: string;
  updated_at: string;
}
```

### ShowDetails (Réponse complète)
```typescript
/** GET /shows/x/{id} - Show avec détails complets */
interface ShowWithDetailResponse {
  message: string;
  show: ShowDetails;
}

interface ShowDetails {
  id: number;
  title: string;
  type: string;
  duration: number;
  description: string;
  created_at: string;
  emission_id: number;
  broadcast_date: string;
  frequency: string;
  status: ShowStatus;
  updated_at: string;
  presenters?: PresenterInShow[];
  segments?: SegmentInShow[];
}

interface PresenterInShow {
  id: number;
  name: string;
  isMainPresenter: boolean;
}

interface SegmentInShow {
  id: number;
  title: string;
  type: string;
  position: number;
  duration: number;
  description?: string;
  startTime?: string;
  guests: GuestInSegment[];
}

interface GuestInSegment {
  id: number;
  name: string;
  role?: string;
}
```

### ShowCreate (Création simple)
```typescript
/** POST /shows/ - Création simple */
interface ShowCreate {
  title: string;
  type: string;
  broadcast_date?: string | null;
  duration: number;
  frequency?: string | null;
  description?: string | null;
  status: ShowStatus;
  emission_id?: number | null;
}
```

### ShowCreateWithDetail (Création complète)
```typescript
/** POST /shows/detail - Création avec détails */
interface ShowCreateWithDetail {
  title: string;
  type: string;
  broadcast_date: string;
  duration: number;
  frequency?: string;
  description?: string;
  status: ShowStatus;
  emission_id?: number;
  presenter_ids?: number[];
  segments?: SegmentDetailCreate[];
}

interface SegmentDetailCreate {
  title: string;
  type: string;
  position: number;
  duration?: number;
  description?: string;
  guest_ids?: number[];
}
```

### ShowBase_jsonShow (Format JSON complet)
```typescript
/** POST /shows/new - Format JSON complet */
interface ShowBase_jsonShow {
  emission_id: number;
  title: string;
  type: string;
  broadcast_date: string;
  duration: number;
  frequency?: string;
  description?: string;
  status?: ShowStatus;
  presenters: PresenterBase_jsonShow[];
  segments: SegmentBase_jsonShow[];
}

interface PresenterBase_jsonShow {
  id: number;
  isMainPresenter?: boolean;
}

interface SegmentBase_jsonShow {
  title: string;
  type: string;
  duration: number;
  description?: string;
  startTime?: string;
  position: number;
  guests: number[];
  technical_notes?: string;
}
```

### Segments
```typescript
/** POST /segments/ - Création segment */
interface SegmentCreate {
  title: string;
  type: string;
  duration: number;
  description?: string;
  technical_notes?: string;
  position: number;
  show_id: number;
  startTime?: string;
}

/** GET /segments/{id} - Réponse segment */
interface SegmentResponse {
  id: number;
  title: string;
  type: string;
  duration: number;
  description: string | null;
  technical_notes: string | null;
  position: number;
  show_id: number;
  startTime: string | null;
  created_at: string;
  updated_at: string;
}

/** PATCH /segments/{id}/position */
interface SegmentPositionUpdate {
  position: number;
}
```

### Recherche
```typescript
/** GET /search_shows/ - Query Parameters */
interface SearchShowFilters {
  keywords?: string;
  status?: ShowStatus;
  dateFrom?: string;    // ISO 8601
  dateTo?: string;      // ISO 8601
  presenter?: number[]; // IDs
  guest?: number[];     // IDs
  skip?: number;        // défaut: 0
  limit?: number;       // défaut: 10, max: 100
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les shows
```typescript
// Liste simple
const shows: ShowOut[] = await fetch('/shows/').then(r => r.json());

// Avec détails complets
const showsDetailed = await fetch('/shows/x').then(r => r.json());
```

### Obtenir un show avec détails
```typescript
const { show }: ShowWithDetailResponse = await fetch('/shows/x/123').then(r => r.json());

// Exemple de réponse
{
  "message": "Show récupéré avec succès",
  "show": {
    "id": 1,
    "title": "Journal du Matin",
    "type": "actualité",
    "status": "Planifié",
    "duration": 60,
    "broadcast_date": "2025-01-15T07:00:00Z",
    "presenters": [
      { "id": 1, "name": "Marie Dupont", "isMainPresenter": true }
    ],
    "segments": [
      {
        "id": 1,
        "title": "Titres du jour",
        "type": "actualité",
        "position": 0,
        "duration": 10,
        "guests": []
      },
      {
        "id": 2,
        "title": "Interview Maire",
        "type": "interview",
        "position": 1,
        "duration": 20,
        "guests": [{ "id": 5, "name": "Pierre Durand", "role": "Maire" }]
      }
    ]
  }
}
```

### Créer un show complet (POST /shows/new)
```typescript
const newShow = await fetch('/shows/new', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    emission_id: 1,
    title: "Matinale Info",
    type: "actualité",
    broadcast_date: "2025-02-15T06:00:00Z",
    duration: 180,
    frequency: "quotidien",
    status: "Planifié",
    presenters: [
      { id: 1, isMainPresenter: true },
      { id: 3, isMainPresenter: false }
    ],
    segments: [
      {
        title: "Flash info 6h",
        type: "actualité",
        duration: 5,
        position: 0,
        startTime: "06:00",
        guests: [],
        technical_notes: "Jingle d'intro obligatoire"
      },
      {
        title: "Revue de presse",
        type: "chronique",
        duration: 15,
        position: 1,
        startTime: "06:05",
        guests: [8, 9]
      }
    ]
  })
}).then(r => r.json());
```

### Modifier le statut d'un show
```typescript
const updated = await fetch('/shows/status/123', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ status: "En direct" })
}).then(r => r.json());
```

### Rechercher des shows
```typescript
// Recherche avec filtres
const results = await fetch(
  '/search_shows/?keywords=journal&status=Planifié&dateFrom=2025-01-01&limit=20'
).then(r => r.json());
```

### Gérer les segments
```typescript
// Créer un segment
const segment = await fetch('/segments/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Météo locale",
    type: "météo",
    duration: 3,
    position: 5,
    show_id: 123,
    startTime: "09:00"
  })
}).then(r => r.json());

// Réordonner un segment
await fetch('/segments/456/position', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ position: 3 })
});
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Accès section showplans | `can_acces_showplan_section` |
| Créer un show | `can_create_showplan` |
| Modifier un show | `can_edit_showplan` |
| Supprimer un show | `can_delete_showplan` |
| Détruire définitivement | `can_destroy_showplan` |
| Changer statut (tous) | `can_changestatus_showplan` |
| Changer statut (siens) | `can_changestatus_owned_showplan` |
| Archiver | `can_archive_showplan` |
| Voir tous les shows | `can_viewAll_showplan` |

---

## ⚠️ Points d'Attention

1. **Routes publiques** : `/shows/`, `/shows/{id}`, `/shows/x`, `/search_shows/` sont sans auth
2. **POST /shows/new vs /shows/detail** : Deux formats différents pour la création complète
3. **Modification** : `PUT /shows/upd/{id}` (pas `/shows/{id}`)
4. **⚠️ DELETE /shows/all** : Supprime TOUS les shows - à utiliser avec précaution
5. **Types de segments** : interview, chronique, musique, publicité, jingle, actualité, météo, débat

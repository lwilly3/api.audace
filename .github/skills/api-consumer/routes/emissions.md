# 📺 Routes Emissions (`/emissions`)

> Gestion des émissions (programmes récurrents).

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/emissions/` | ✅ | Liste des émissions |
| `GET` | `/emissions/{emission_id}` | ✅ | Détails d'une émission |
| `POST` | `/emissions/` | ✅ | Créer une émission |
| `PUT` | `/emissions/upd/{emission_id}` | ✅ | Modifier une émission |
| `DELETE` | `/emissions/del/{emission_id}` | ✅ | Supprimer (hard delete) |
| `DELETE` | `/emissions/softDel/{emission_id}` | ✅ | Supprimer (soft delete) |

---

## 📦 Schémas de Données

### EmissionResponse
```typescript
/** GET /emissions/{id} - Réponse émission */
interface EmissionResponse {
  id: number;
  title: string;
  synopsis: string | null;
  type: string | null;
  duration: number | null;       // en minutes
  frequency: string | null;
  description: string | null;
  created_at: string;            // ISO 8601
  is_deleted: boolean;
  deleted_at: string | null;     // ISO 8601
}
```

### EmissionCreate
```typescript
/** POST /emissions/ - Création émission */
interface EmissionCreate {
  title: string;                  // max 255 chars, requis
  synopsis?: string | null;       // max 1000 chars
  type?: string | null;
  duration?: number | null;       // en minutes
  frequency?: string | null;
  description?: string | null;
}
```

### EmissionUpdate
```typescript
/** PUT /emissions/upd/{id} - Mise à jour */
interface EmissionUpdate {
  title?: string;
  synopsis?: string;
  type?: string;
  duration?: number;
  frequency?: string;
  description?: string;
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les émissions
```typescript
const emissions: EmissionResponse[] = await fetch('/emissions/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Obtenir une émission
```typescript
const emission: EmissionResponse = await fetch('/emissions/123', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "id": 1,
  "title": "Le Journal du Matin",
  "synopsis": "Actualités quotidiennes de 7h à 9h",
  "type": "actualité",
  "duration": 120,
  "frequency": "quotidien",
  "description": "Revue de presse et actualités locales",
  "created_at": "2024-06-15T10:00:00Z",
  "is_deleted": false,
  "deleted_at": null
}
```

### Créer une émission
```typescript
const newEmission: EmissionResponse = await fetch('/emissions/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Culture Radio",
    synopsis: "Magazine culturel hebdomadaire",
    type: "magazine",
    duration: 60,
    frequency: "hebdomadaire",
    description: "Découverte des événements culturels"
  })
}).then(r => r.json());
```

### Modifier une émission
```typescript
// ⚠️ URL = /emissions/upd/{id}
const updated: EmissionResponse = await fetch('/emissions/upd/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    duration: 90,
    description: "Magazine culturel étendu"
  })
}).then(r => r.json());
```

### Supprimer une émission
```typescript
// Soft delete (recommandé) - conserve les données
await fetch('/emissions/softDel/123', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});

// Hard delete - suppression définitive
await fetch('/emissions/del/123', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Accès section émissions | `can_acces_emissions_section` |
| Voir les émissions | `can_view_emissions` |
| Créer une émission | `can_create_emissions` |
| Modifier une émission | `can_edit_emissions` |
| Supprimer une émission | `can_delete_emissions` |
| Gérer les émissions | `can_manage_emissions` |

---

## 📊 Types d'Émissions Courants

| Type | Description |
|------|-------------|
| `actualité` | Journaux, flash info |
| `magazine` | Émissions thématiques |
| `divertissement` | Jeux, humour |
| `musique` | Émissions musicales |
| `sport` | Actualités sportives |
| `culture` | Art, littérature, cinéma |
| `débat` | Discussions, interviews |

---

## 📅 Fréquences Courantes

| Fréquence | Description |
|-----------|-------------|
| `quotidien` | Tous les jours |
| `hebdomadaire` | Une fois par semaine |
| `bimensuel` | Deux fois par mois |
| `mensuel` | Une fois par mois |
| `ponctuel` | Occasionnel |

---

## ⚠️ Points d'Attention

1. **URL de modification** : `PUT /emissions/upd/{id}` (pas `/emissions/{id}`)
2. **Soft vs Hard delete** : Préférer `softDel` pour conserver l'historique
3. **Durée en minutes** : Le champ `duration` est en minutes, pas en secondes
4. **Relation avec Shows** : Une émission peut avoir plusieurs shows (via `emission_id` dans Show)

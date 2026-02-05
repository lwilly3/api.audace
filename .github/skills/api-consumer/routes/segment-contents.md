# 📝 Contenus Éditoriaux par Segment - Firebase Realtime

> **⚠️ ARCHITECTURE HYBRIDE** : Les contenus éditoriaux sont stockés dans **Firebase Firestore** pour le temps réel, mais les **permissions** (`quotes_*`) sont gérées par l'API backend.

---

## 📋 Vue d'ensemble

### Objectif

Créer une **base de données éditoriale** consultable et réutilisable en enrichissant chaque **segment d'un conducteur** avec :
- **Citations** (`quote`) : Phrases marquantes d'un intervenant
- **Extraits écrits** (`excerpt`) : Résumés, verbatims, points clés
- **Idées clés** (`key_idea`) : Notes éditoriales, angles, accroches

Ces contenus peuvent ensuite être **recherchés, filtrés et exportés** pour être traités/formatés manuellement en vue d'une publication.

### Quand créer des contenus ?

| Moment | Source | Horodatage |
|--------|--------|------------|
| **Pendant l'émission** | `live` | Minute dans le segment (optionnel) |
| **Après l'émission** | `replay` | Horodatage vidéo/audio (optionnel, ex: "01:23:45") |
| **Manuellement** | `manual` | Aucun ou libre |

### Cas d'usage

```
┌─────────────────────────────────────────────────────────────┐
│  CONDUCTEUR : Journal du 15/01/2026                         │
├─────────────────────────────────────────────────────────────┤
│  Segment 1: Ouverture (3 min)                               │
│  Segment 2: Interview Maire (15 min)                        │
│    ├── 💬 Citation @02:30 "La transition écolo..."          │
│    ├── 💬 Citation @08:15 "Nous investirons 50M€..."        │
│    ├── 📝 Extrait @05:00 "3 axes du plan climat..."         │
│    └── 💡 Idée clé "ANGLE: Suivi dans 1 an"                 │
│  Segment 3: Chronique Météo (5 min)                         │
│  Segment 4: Musique (4 min)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Firebase

```
Firestore
├── segment_contents/           # Collection principale
│   └── {contentId}
│       ├── segment_id          # → API /segments/{id}
│       ├── show_id             # → API /shows/{id}
│       ├── content_type        # quote | excerpt | key_idea
│       ├── content             # Le texte
│       ├── speaker             # Intervenant
│       ├── timestamp_minute    # Minute dans le segment
│       └── ...
├── content_topics/             # Sujets utilisés (autocomplete)
└── content_tags/               # Tags populaires (autocomplete)
```

---

## 🔐 Permissions

Les mêmes permissions `quotes_*` s'appliquent :

| Permission | Accès contenus segment |
|------------|------------------------|
| `quotes_view` | Voir tous les contenus |
| `quotes_create` | Créer des contenus |
| `quotes_edit` | Modifier (restriction "Siennes"*) |
| `quotes_delete` | Supprimer |

> **\* Siennes** : Éditeur/Animateur ne peuvent modifier que leurs propres contenus

---

## 📦 Schémas TypeScript

```typescript
// ════════════════════════════════════════════════════════════
// SEGMENT CONTENTS - Types Firebase Firestore
// ════════════════════════════════════════════════════════════

import { Timestamp } from 'firebase/firestore';

/** Type de contenu éditorial */
type ContentType = 'quote' | 'excerpt' | 'key_idea';

/** Type d'intervenant */
type SpeakerType = 'presenter' | 'guest' | 'external' | 'unknown';

/** Plateformes de publication */
type Platform = 'facebook' | 'twitter' | 'instagram' | 'linkedin' | 'newsletter';

// ────────────────────────────────────────────────────────────
// INTERVENANT
// ────────────────────────────────────────────────────────────

/** Informations sur l'intervenant */
interface Speaker {
  type: SpeakerType;
  id: number | null;           // presenter_id ou guest_id (API)
  name: string;                // Nom affiché
  role?: string;               // Ex: "Maire de Lyon"
  organization?: string;       // Ex: "Mairie de Lyon"
}

// ────────────────────────────────────────────────────────────
// CONTENU ÉDITORIAL
// ────────────────────────────────────────────────────────────

/** Contenu éditorial lié à un segment */
interface SegmentContent {
  // Identifiants
  id: string;                      // ID Firestore (auto)
  segment_id: number;              // → API /segments/{id}
  show_id: number;                 // → API /shows/{id}
  emission_id?: number;            // → API /emissions/{id}
  
  // Contenu
  content_type: ContentType;
  content: string;                 // Texte de la citation/extrait/idée
  
  // Intervenant
  speaker: Speaker;
  
  // Position temporelle (tous optionnels)
  timestamp_minute?: number | null;     // Minute dans le segment (ex: 2.5 = 2min30s)
  video_timestamp?: string | null;      // Horodatage dans la vidéo/replay (ex: "01:23:45")
  duration_seconds?: number;            // Durée de l'extrait (secondes)
  
  // Métadonnées
  topic: string;                   // Sujet principal
  subtopic?: string;               // Sous-thème
  tags: string[];                  // Tags pour recherche
  importance: 'low' | 'medium' | 'high' | 'viral';
  
  // Source
  source_type: 'live' | 'replay' | 'manual';
  audio_url?: string;              // Lien vers extrait audio
  
  // Audit
  created_by: number;
  created_by_name: string;
  created_at: Timestamp;
  updated_at?: Timestamp;
  updated_by?: number;
  
  // Soft delete
  is_deleted: boolean;
  deleted_at?: Timestamp;
}

// ────────────────────────────────────────────────────────────
// CRÉATION / MISE À JOUR
// ────────────────────────────────────────────────────────────

/** Création de contenu */
interface SegmentContentCreate {
  segment_id: number;
  show_id: number;
  emission_id?: number;
  content_type: ContentType;
  content: string;
  speaker: Speaker;
  timestamp_minute?: number | null;    // Optionnel: minute dans le segment
  video_timestamp?: string | null;     // Optionnel: horodatage vidéo (ex: "01:23:45")
  topic: string;
  tags?: string[];
  importance?: 'low' | 'medium' | 'high' | 'viral';
  source_type?: 'live' | 'replay' | 'manual';
}

/** Mise à jour de contenu */
interface SegmentContentUpdate {
  content?: string;
  speaker?: Partial<Speaker>;
  timestamp_minute?: number | null;
  video_timestamp?: string | null;
  topic?: string;
  tags?: string[];
  importance?: 'low' | 'medium' | 'high' | 'viral';
}

// ────────────────────────────────────────────────────────────
// RECHERCHE
// ────────────────────────────────────────────────────────────

/** Filtres de recherche */
interface ContentSearchFilter {
  segment_id?: number;
  show_id?: number;
  emission_id?: number;
  content_type?: ContentType;
  speaker_id?: number;
  speaker_type?: SpeakerType;
  topic?: string;
  tags?: string[];
  importance?: 'low' | 'medium' | 'high' | 'viral';
  date_from?: Date;
  date_to?: Date;
  search_text?: string;
}
```

---

## 🎯 Types de Contenu

### 1. Citation (`quote`)

Phrase exacte prononcée par un intervenant.

```typescript
const citation: SegmentContentCreate = {
  segment_id: 42,
  show_id: 15,
  content_type: 'quote',
  content: "La transition écologique ne se fera pas sans les citoyens.",
  speaker: {
    type: 'guest',
    id: 8,
    name: "Marie Dupont",
    role: "Maire",
    organization: "Ville de Lyon"
  },
  timestamp_minute: 2.5,         // 2min30s dans le segment
  topic: "Environnement",
  tags: ["écologie", "politique"],
  importance: 'high'
};
```

### 2. Extrait écrit (`excerpt`)

Résumé ou verbatim condensé.

```typescript
const extrait: SegmentContentCreate = {
  segment_id: 42,
  show_id: 15,
  content_type: 'excerpt',
  content: "Plan climat : 3 axes - rénovation bâtiments, transports doux, zones vertes. Budget 50M€ sur 5 ans.",
  speaker: {
    type: 'presenter',
    id: 3,
    name: "Jean Martin"
  },
  timestamp_minute: 5,
  topic: "Politique locale",
  importance: 'medium'
};
```

### 3. Idée clé (`key_idea`)

Note éditoriale, angle ou accroche.

```typescript
const idee: SegmentContentCreate = {
  segment_id: 42,
  show_id: 15,
  content_type: 'key_idea',
  content: "ANGLE: Comparer promesses vs réalisations dans 1 an. Potentiel suivi éditorial.",
  speaker: {
    type: 'unknown',
    id: null,
    name: "Rédaction"
  },
  topic: "Suivi éditorial",
  tags: ["follow-up"],
  importance: 'medium'
};
```

---

## 🔄 Opérations Firebase

### 1. Charger les contenus d'un segment (Realtime)

```typescript
import { 
  collection, query, where, orderBy, onSnapshot,
  addDoc, updateDoc, doc, Timestamp 
} from 'firebase/firestore';
import { db } from './firebase-config';

/** Écoute temps réel des contenus d'un segment */
function subscribeToSegmentContents(
  segmentId: number,
  callback: (contents: SegmentContent[]) => void
): () => void {
  const q = query(
    collection(db, 'segment_contents'),
    where('segment_id', '==', segmentId),
    where('is_deleted', '==', false),
    orderBy('timestamp_minute', 'asc')
  );
  
  return onSnapshot(q, (snapshot) => {
    const contents = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    } as SegmentContent));
    callback(contents);
  });
}

// Usage dans React
useEffect(() => {
  const unsubscribe = subscribeToSegmentContents(segmentId, setContents);
  return () => unsubscribe();
}, [segmentId]);
```

### 2. Créer un contenu

```typescript
async function createSegmentContent(
  currentUser: { id: number; name: string },
  data: SegmentContentCreate
): Promise<string> {
  // 1. Vérifier permission via API
  const permissions = await checkQuotesPermissions();
  if (!permissions.quotes_create) {
    throw new Error('Permission quotes_create requise');
  }
  
  // 2. Créer dans Firebase
  const newContent: Omit<SegmentContent, 'id'> = {
    ...data,
    tags: data.tags || [],
    importance: data.importance || 'medium',
    source_type: data.source_type || 'manual',
    is_published: false,
    published_platforms: [],
    created_by: currentUser.id,
    created_by_name: currentUser.name,
    created_at: Timestamp.now(),
    is_deleted: false
  };
  
  const docRef = await addDoc(collection(db, 'segment_contents'), newContent);
  return docRef.id;
}
```

### 3. Modifier un contenu (avec vérification propriétaire)

```typescript
async function updateSegmentContent(
  currentUser: { id: number; roles: string[] },
  contentId: string,
  existingContent: SegmentContent,
  updates: SegmentContentUpdate
): Promise<void> {
  // 1. Vérifier permission
  const permissions = await checkQuotesPermissions();
  if (!permissions.quotes_edit) {
    throw new Error('Permission quotes_edit requise');
  }
  
  // 2. Vérifier restriction "Siennes"
  const isAdmin = currentUser.roles.includes('Admin');
  const isCM = currentUser.roles.includes('Community Manager');
  const isOwner = existingContent.created_by === currentUser.id;
  
  if (!isAdmin && !isCM && !isOwner) {
    throw new Error('Vous ne pouvez modifier que vos propres contenus');
  }
  
  // 3. Mettre à jour
  const contentRef = doc(db, 'segment_contents', contentId);
  await updateDoc(contentRef, {
    ...updates,
    updated_at: Timestamp.now(),
    updated_by: currentUser.id
  });
}
```

### 4. Supprimer (soft delete)

```typescript
async function deleteSegmentContent(
  currentUser: { id: number; roles: string[] },
  contentId: string,
  existingContent: SegmentContent
): Promise<void> {
  const permissions = await checkQuotesPermissions();
  if (!permissions.quotes_delete) {
    throw new Error('Permission quotes_delete requise');
  }
  
  // Vérifier propriétaire pour non-admin
  const isAdmin = currentUser.roles.includes('Admin');
  const isOwner = existingContent.created_by === currentUser.id;
  
  if (!isAdmin && !isOwner) {
    throw new Error('Suppression non autorisée');
  }
  
  // Soft delete
  const contentRef = doc(db, 'segment_contents', contentId);
  await updateDoc(contentRef, {
    is_deleted: true,
    deleted_at: Timestamp.now()
  });
}
```

### 5. Rechercher dans la base éditoriale

```typescript
async function searchContents(
  filter: ContentSearchFilter
): Promise<SegmentContent[]> {
  let q = query(
    collection(db, 'segment_contents'),
    where('is_deleted', '==', false),
    orderBy('created_at', 'desc')
  );
  
  // Filtres Firestore
  if (filter.show_id) {
    q = query(q, where('show_id', '==', filter.show_id));
  }
  if (filter.content_type) {
    q = query(q, where('content_type', '==', filter.content_type));
  }
  if (filter.topic) {
    q = query(q, where('topic', '==', filter.topic));
  }
  if (filter.importance) {
    q = query(q, where('importance', '==', filter.importance));
  }
  if (filter.is_published !== undefined) {
    q = query(q, where('is_published', '==', filter.is_published));
  }
  
  const snapshot = await getDocs(q);
  let results = snapshot.docs.map(d => ({ id: d.id, ...d.data() } as SegmentContent));
  
  // Filtres côté client (texte, tags)
  if (filter.search_text) {
    const search = filter.search_text.toLowerCase();
    results = results.filter(c =>
      c.content.toLowerCase().includes(search) ||
      c.speaker.name.toLowerCase().includes(search)
    );
  }
  if (filter.tags?.length) {
    results = results.filter(c =>
      filter.tags!.some(tag => c.tags.includes(tag))
    );
  }
  
  return results;
}

/** Exporter les contenus (pour traitement externe) */
async function exportContents(
  filter: ContentSearchFilter,
  format: 'json' | 'csv'
): Promise<string> {
  const contents = await searchContents(filter);
  
  if (format === 'json') {
    return JSON.stringify(contents, null, 2);
  }
  
  // CSV
  const headers = ['Type', 'Contenu', 'Intervenant', 'Rôle', 'Sujet', 'Tags', 'Importance', 'Show', 'Segment', 'Minute', 'Vidéo', 'Source', 'Date'];
  const rows = contents.map(c => [
    c.content_type,
    `"${c.content.replace(/"/g, '""')}"`,
    c.speaker.name,
    c.speaker.role || '',
    c.topic,
    c.tags.join(';'),
    c.importance,
    c.show_id,
    c.segment_id,
    c.timestamp_minute ?? '',
    c.video_timestamp ?? '',
    c.source_type || 'manual',
    c.created_at.toDate().toISOString()
  ]);
  
  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
}
```

---

## 🎨 Composants UI

### Panel Segment avec Contenus

```
┌──────────────────────────────────────────────────┐
│ 📍 Segment: Interview du Maire                   │
│ Durée: 15 min | Position: 2                      │
├──────────────────────────────────────────────────┤
│ [+ Citation] [+ Extrait] [+ Idée clé]            │
├──────────────────────────────────────────────────┤
│ 💬 Citations (2)                         ▼       │
│ ┌──────────────────────────────────────────────┐ │
│ │ @02:30 "La transition écologique..."         │ │
│ │ — Marie Dupont, Maire | ⭐⭐⭐              │ │
│ │ [✏️ Modifier] [📋 Copier] [🗑️ Suppr.]       │ │
│ └──────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────┐ │
│ │ @08:15 "Nous investirons 50M€..."            │ │
│ │ — Marie Dupont, Maire | ⭐⭐                 │ │
│ │ [✏️ Modifier] [📋 Copier] [🗑️ Suppr.]       │ │
│ └──────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│ 📝 Extraits (1)                          ▼       │
│ ┌──────────────────────────────────────────────┐ │
│ │ @05:00 "3 axes du plan climat..."            │ │
│ │ [✏️ Modifier] [📋 Copier] [🗑️ Suppr.]       │ │
│ └──────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│ 💡 Idées clés (1)                        ▼       │
│ ┌──────────────────────────────────────────────┐ │
│ │ ANGLE: Suivi dans 1 an                       │ │
│ │ [✏️ Modifier] [📋 Copier] [🗑️ Suppr.]       │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Formulaire de Création

```
┌──────────────────────────────────────────────────┐
│ ➕ Nouveau contenu                               │
├──────────────────────────────────────────────────┤
│ Type: [● Citation ○ Extrait ○ Idée clé]         │
│ Source: [○ Live ● Replay ○ Manuel]              │
│                                                  │
│ Contenu:                                         │
│ ┌──────────────────────────────────────────────┐ │
│ │ "La transition écologique ne se fera pas     │ │
│ │ sans les citoyens."                          │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Intervenant:                                     │
│ Type: [Invité ▼]  Rechercher: [Marie Dup... 🔍] │
│ Rôle: [Maire____________]                        │
│ Organisation: [Ville de Lyon___]                 │
│                                                  │
│ ⏱️ Temporalité (optionnel):                      │
│ Minute segment: [02]:[30]  OU  Vidéo: [01:23:45]│
│ 💡 Utilisez "Minute" en live, "Vidéo" en replay │
│                                                  │
│ Sujet: [Environnement ▼]  (ou nouveau)          │
│ Tags: [écologie] [politique] [+]                 │
│                                                  │
│ Importance: [○ Faible ● Moyenne ○ Haute ○ Viral]│
│                                                  │
│             [Annuler]  [💾 Enregistrer]          │
└──────────────────────────────────────────────────┘
```

### Base Éditoriale

```
┌──────────────────────────────────────────────────────────┐
│ 🔍 Base Éditoriale                                       │
├──────────────────────────────────────────────────────────┤
│ Recherche: [___________________________] 🔍              │
│                                                          │
│ Type: [Tous ▼] Sujet: [Tous ▼] Importance: [Tous ▼]     │
│ Période: [Du ___] [Au ___]                               │
├──────────────────────────────────────────────────────────┤
│ 📊 147 résultats        [📋 Copier sélection] [⬇️ CSV]  │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ☐ 💬 Citation | Environnement | ⭐⭐⭐ HIGH         │ │
│ │ "La transition écologique ne se fera pas..."         │ │
│ │ — Marie Dupont, Maire | Show: Journal 15/01          │ │
│ │ Segment: Interview (min 2:30)                        │ │
│ │ [📋 Copier] [✏️ Modifier] [🔗 Voir show]             │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ☐ 📝 Extrait | Politique | ⭐⭐ MEDIUM              │ │
│ │ "Plan climat : 3 axes majeurs..."                    │ │
│ │ — Jean Martin | Show: Journal 15/01                  │ │
│ │ [📋 Copier] [✏️ Modifier] [🔗 Voir show]             │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 Collections Firebase

| Collection | Description | Index |
|------------|-------------|-------|
| `segment_contents` | Contenus éditoriaux | `segment_id`, `show_id`, `content_type`, `topic`, `created_at` |
| `content_topics` | Liste des sujets | (autocomplete) |
| `content_tags` | Tags populaires | (autocomplete) |

### Règles Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    match /segment_contents/{contentId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null
        && request.resource.data.created_by != null;
      allow update: if request.auth != null
        && (isAdmin() || resource.data.created_by == request.auth.uid);
      allow delete: if isAdmin();
    }
    
    match /content_topics/{doc} {
      allow read, write: if request.auth != null;
    }
    
    match /content_tags/{doc} {
      allow read, write: if request.auth != null;
    }
    
    function isAdmin() {
      return request.auth.token.role == 'Admin';
    }
  }
}
```

---

## 🔗 Routes API Liées

| Route | Usage |
|-------|-------|
| `GET /auth/me` | Vérifier permissions `quotes_*` |
| `GET /shows/x/{id}` | Show avec segments |
| `GET /segments/{id}` | Détails segment |
| `GET /presenters/all` | Liste présentateurs (autocomplete) |
| `GET /guests/` | Liste invités (autocomplete) |

---

## ⚠️ Points d'Attention

1. **Permissions API** : Toujours vérifier via `/auth/me` avant opération Firebase
2. **Restriction "Siennes"** : Vérifier `created_by === currentUser.id` côté frontend
3. **Soft delete** : Utiliser `is_deleted: true`, jamais `deleteDoc()`
4. **IDs synchronisés** : `segment_id`, `show_id`, `speaker.id` doivent exister dans l'API
5. **Index Firestore** : Créer les index composites pour les requêtes complexes
6. **Realtime** : Utiliser `onSnapshot` pour les mises à jour temps réel sur l'éditeur de segment

---

## 🚀 Évolutions Futures

Les fonctionnalités suivantes sont prévues pour des versions ultérieures :

### Publication automatique sur réseaux sociaux

- Génération automatique de textes formatés par plateforme (Twitter, Facebook, Instagram, LinkedIn)
- Templates personnalisables avec variables (citation, auteur, émission, hashtags)
- Publication programmée
- Historique des publications avec métriques d'engagement

### Intégrations envisagées

| Fonctionnalité | Description |
|----------------|-------------|
| **Templates par plateforme** | Formatage auto selon limites (280 car. Twitter, etc.) |
| **Buffer/Hootsuite** | API tierce pour publication multi-plateforme |
| **Meta Business API** | Publication directe Facebook/Instagram |
| **Analytics** | Suivi des performances des publications |

### Export avancé

- Export CSV/Excel de la base éditoriale
- Export formaté pour newsletter
- Génération de rapports par période/émission/intervenant

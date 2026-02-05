# 🎙️ Citations (Quotes) - Intégration Firebase

> **⚠️ ARCHITECTURE HYBRIDE** : Les données des citations sont stockées dans **Firebase Firestore**, mais les **permissions** sont gérées par l'API backend. Le frontend doit vérifier les permissions via l'API avant d'effectuer des opérations Firebase.

## 📋 Vue d'ensemble

Le module Citations permet de :
- Capturer des citations depuis les émissions radio en direct
- Transcrire automatiquement le stream audio
- Publier des citations sur les réseaux sociaux
- Gérer un historique de citations par émission/présentateur

---

## 🔐 Permissions Citations

8 permissions spécifiques contrôlent l'accès au module Citations :

| Permission | Description | Actions autorisées |
|------------|-------------|-------------------|
| `quotes_view` | Visualiser les citations | Liste, détails, recherche, historique |
| `quotes_create` | Créer de nouvelles citations | Formulaire création manuelle ou depuis stream |
| `quotes_edit` | Modifier les citations | Édition contenu, métadonnées, tags |
| `quotes_delete` | Supprimer des citations | Suppression (⚠️ définitive dans Firebase) |
| `quotes_publish` | Publier sur réseaux sociaux | Génération contenu, publication Facebook/Twitter/Instagram |
| `stream_transcription_view` | Voir transcriptions live | Accès au composant de transcription temps réel |
| `stream_transcription_create` | Démarrer une transcription | Bouton "Transcrire le stream" |
| `quotes_capture_live` | Capturer depuis transcription | Bouton capture pendant transcription active |

---

## 📊 Matrice des Permissions par Rôle

| Rôle | quotes_view | quotes_create | quotes_edit | quotes_delete | quotes_publish | stream_transcription_view | stream_transcription_create | quotes_capture_live |
|------|-------------|---------------|-------------|---------------|----------------|---------------------------|----------------------------|---------------------|
| **Admin** | ✅ | ✅ | ✅ Toutes | ✅ Toutes | ✅ | ✅ | ✅ | ✅ |
| **Éditeur** | ✅ | ✅ | ✅ Siennes* | ✅ Siennes* | ✅ | ✅ | ✅ | ✅ |
| **Animateur** | ✅ | ✅ | ✅ Siennes* | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Community Manager** | ✅ | ✅ | ✅ Toutes | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Invité** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

> **\* Siennes** = L'utilisateur ne peut modifier/supprimer que les citations qu'il a créées (`created_by === current_user.id`)

---

## 📦 Schémas TypeScript

```typescript
// ════════════════════════════════════════════════════════════
// QUOTES - Types pour Firebase Firestore
// ════════════════════════════════════════════════════════════

import { Timestamp } from 'firebase/firestore';

/** Citation stockée dans Firebase */
interface Quote {
  id: string;                      // ID Firestore (auto-généré)
  content: string;                 // Texte de la citation
  author: string;                  // Nom de l'auteur/présentateur
  author_id: number | null;        // ID du présentateur (lié à l'API)
  emission_id: number | null;      // ID de l'émission (lié à l'API)
  emission_name: string | null;    // Nom de l'émission
  show_id: number | null;          // ID du show (lié à l'API)
  created_by: number;              // ID utilisateur qui a créé (pour restriction "Siennes")
  created_by_name: string;         // Nom de l'utilisateur créateur
  created_at: Timestamp;           // Date création Firebase
  updated_at: Timestamp | null;    // Date modification
  
  // Métadonnées
  tags: string[];                  // Tags pour recherche
  context: string | null;          // Contexte de la citation
  source_type: 'manual' | 'transcription' | 'live_capture';
  
  // Publication
  is_published: boolean;
  published_at: Timestamp | null;
  published_platforms: ('facebook' | 'twitter' | 'instagram')[];
  
  // Audio/Transcription
  audio_url: string | null;        // URL fichier audio si capturé
  transcription_id: string | null; // Lien vers transcription source
  timestamp_start: number | null;  // Timestamp début dans stream (ms)
  timestamp_end: number | null;    // Timestamp fin dans stream (ms)
}

/** Création d'une citation */
interface QuoteCreate {
  content: string;                 // Requis
  author: string;                  // Requis
  author_id?: number | null;
  emission_id?: number | null;
  emission_name?: string | null;
  show_id?: number | null;
  tags?: string[];
  context?: string | null;
  source_type: 'manual' | 'transcription' | 'live_capture';
  audio_url?: string | null;
  transcription_id?: string | null;
  timestamp_start?: number | null;
  timestamp_end?: number | null;
}

/** Mise à jour d'une citation */
interface QuoteUpdate {
  content?: string;
  author?: string;
  tags?: string[];
  context?: string | null;
  is_published?: boolean;
  published_platforms?: ('facebook' | 'twitter' | 'instagram')[];
}

/** Transcription en temps réel */
interface LiveTranscription {
  id: string;                      // ID Firestore
  stream_url: string;              // URL du stream audio
  emission_id: number | null;
  show_id: number | null;
  started_by: number;              // ID utilisateur
  started_at: Timestamp;
  ended_at: Timestamp | null;
  status: 'active' | 'paused' | 'stopped';
  segments: TranscriptionSegment[];
}

/** Segment de transcription */
interface TranscriptionSegment {
  id: string;
  text: string;
  timestamp: number;               // ms depuis début
  confidence: number;              // 0-1
  speaker?: string;                // Identification locuteur
}

/** Permissions Citations (extraites de UserPermissionsResponse) */
interface QuotesPermissions {
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

---

## 🔄 Workflow Frontend

### 1. Vérification des permissions (via API)

```typescript
async function checkQuotesPermissions(): Promise<QuotesPermissions> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` }
  });
  const user = await response.json();
  
  return {
    quotes_view: user.permissions.quotes_view,
    quotes_create: user.permissions.quotes_create,
    quotes_edit: user.permissions.quotes_edit,
    quotes_delete: user.permissions.quotes_delete,
    quotes_publish: user.permissions.quotes_publish,
    stream_transcription_view: user.permissions.stream_transcription_view,
    stream_transcription_create: user.permissions.stream_transcription_create,
    quotes_capture_live: user.permissions.quotes_capture_live
  };
}
```

### 2. Opérations Firebase

```typescript
import { 
  collection, doc, getDocs, addDoc, updateDoc, deleteDoc,
  query, where, orderBy, Timestamp 
} from 'firebase/firestore';
import { db } from './firebase-config';

// Lire les citations
async function getQuotes(
  permissions: QuotesPermissions,
  filters?: { emission_id?: number; author_id?: number }
): Promise<Quote[]> {
  if (!permissions.quotes_view) {
    throw new Error('Permission quotes_view requise');
  }
  
  const quotesRef = collection(db, 'quotes');
  let q = query(quotesRef, orderBy('created_at', 'desc'));
  
  if (filters?.emission_id) {
    q = query(q, where('emission_id', '==', filters.emission_id));
  }
  
  const snapshot = await getDocs(q);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Quote));
}

// Créer une citation
async function createQuote(
  permissions: QuotesPermissions,
  currentUser: { id: number; name: string },
  data: QuoteCreate
): Promise<string> {
  if (!permissions.quotes_create) {
    throw new Error('Permission quotes_create requise');
  }
  
  const quotesRef = collection(db, 'quotes');
  const newQuote = {
    ...data,
    created_by: currentUser.id,
    created_by_name: currentUser.name,
    created_at: Timestamp.now(),
    updated_at: null,
    is_published: false,
    published_at: null,
    published_platforms: []
  };
  
  const docRef = await addDoc(quotesRef, newQuote);
  return docRef.id;
}

// Modifier une citation (avec vérification propriétaire)
async function updateQuote(
  permissions: QuotesPermissions,
  currentUser: { id: number; roles: string[] },
  quoteId: string,
  quote: Quote,
  updates: QuoteUpdate
): Promise<void> {
  if (!permissions.quotes_edit) {
    throw new Error('Permission quotes_edit requise');
  }
  
  // Vérifier restriction "Siennes" pour Éditeur/Animateur
  const isAdmin = currentUser.roles.includes('Admin');
  const isCommunityManager = currentUser.roles.includes('Community Manager');
  const isOwner = quote.created_by === currentUser.id;
  
  if (!isAdmin && !isCommunityManager && !isOwner) {
    throw new Error('Vous ne pouvez modifier que vos propres citations');
  }
  
  const quoteRef = doc(db, 'quotes', quoteId);
  await updateDoc(quoteRef, {
    ...updates,
    updated_at: Timestamp.now()
  });
}

// Supprimer une citation
async function deleteQuote(
  permissions: QuotesPermissions,
  currentUser: { id: number; roles: string[] },
  quoteId: string,
  quote: Quote
): Promise<void> {
  if (!permissions.quotes_delete) {
    throw new Error('Permission quotes_delete requise');
  }
  
  const isAdmin = currentUser.roles.includes('Admin');
  const isEditor = currentUser.roles.includes('Éditeur');
  const isOwner = quote.created_by === currentUser.id;
  
  if (!isAdmin && !(isEditor && isOwner)) {
    throw new Error('Suppression non autorisée');
  }
  
  const quoteRef = doc(db, 'quotes', quoteId);
  await deleteDoc(quoteRef);
}

// Publier une citation
async function publishQuote(
  permissions: QuotesPermissions,
  quoteId: string,
  platforms: ('facebook' | 'twitter' | 'instagram')[]
): Promise<void> {
  if (!permissions.quotes_publish) {
    throw new Error('Permission quotes_publish requise');
  }
  
  const quoteRef = doc(db, 'quotes', quoteId);
  await updateDoc(quoteRef, {
    is_published: true,
    published_at: Timestamp.now(),
    published_platforms: platforms
  });
}
```

---

## 🎯 Règles de Sécurité Firebase Firestore

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Collection Citations
    match /quotes/{quoteId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null 
        && request.resource.data.created_by == request.auth.uid;
      allow update: if request.auth != null 
        && (isAdmin() || resource.data.created_by == request.auth.uid);
      allow delete: if request.auth != null 
        && (isAdmin() || resource.data.created_by == request.auth.uid);
    }
    
    // Collection Transcriptions
    match /transcriptions/{transcriptionId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null 
        && resource.data.started_by == request.auth.uid;
      allow delete: if isAdmin();
    }
    
    function isAdmin() {
      return request.auth.token.role == 'Admin';
    }
  }
}
```

---

## 📊 Collections Firebase

| Collection | Description | Document Type |
|------------|-------------|---------------|
| `quotes` | Citations capturées (niveau émission) | `Quote` |
| `transcriptions` | Sessions de transcription | `LiveTranscription` |
| `transcription_segments` | Segments de texte transcrits | `TranscriptionSegment` |
| `segment_contents` | Contenus éditoriaux par segment | `SegmentContent` |

---

## 🔗 Module Contenus Éditoriaux par Segment

Pour ajouter des **citations, extraits et idées clés** directement sur les segments d'un conducteur :

➡️ **[segment-contents.md](segment-contents.md)**

Ce module complémentaire permet :
- Enrichir chaque segment avec des contenus (minute précise)
- Métadonnées complètes (intervenant, sujet, tags, importance)
- Recherche et filtrage dans la base éditoriale
- Export des contenus (CSV/JSON) pour traitement externe
- Temps réel via Firebase `onSnapshot`

> **💡 Note** : La publication automatique sur réseaux sociaux est prévue comme évolution future.

---

## 🔗 Routes API Liées

Bien que les données soient dans Firebase, ces routes API sont nécessaires :

| Route | Méthode | Usage |
|-------|---------|-------|
| `/auth/login` | POST | Récupère les permissions quotes_* |
| `/auth/me` | GET | Vérifie les permissions actuelles |
| `/presenters/presenters` | GET | Liste des présentateurs (pour `author_id`) |
| `/emissions/emissions` | GET | Liste des émissions (pour `emission_id`) |
| `/shows/shows` | GET | Liste des shows (pour `show_id`) |
| `/segments/{id}` | GET | Détails d'un segment |

---

## ⚠️ Points d'Attention

1. **Double vérification** : Toujours vérifier les permissions via l'API backend AVANT d'effectuer une opération Firebase
2. **Restriction "Siennes"** : Implémenter côté frontend la logique `created_by === current_user.id`
3. **Synchronisation IDs** : Les IDs d'émissions, présentateurs, shows et segments doivent correspondre à ceux de l'API backend
4. **Audit** : Logger les actions sensibles (suppression, publication) via l'API backend si nécessaire
5. **Soft delete** : Préférer `is_deleted: true` plutôt que la suppression définitive

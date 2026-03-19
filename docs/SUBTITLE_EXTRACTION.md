# Extraction de sous-titres — Documentation technique

> **Derniere mise a jour :** 2026-03-19
> **Version :** Architecture hybride (youtube-transcript-api + yt-dlp)

---

## Table des matieres

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture hybride](#2-architecture-hybride)
3. [Arborescence des fichiers](#3-arborescence-des-fichiers)
4. [Backend — Comment ca marche](#4-backend--comment-ca-marche)
5. [Frontend — Comment ca marche](#5-frontend--comment-ca-marche)
6. [Endpoints API](#6-endpoints-api)
7. [Gestion des cookies YouTube](#7-gestion-des-cookies-youtube)
8. [Formats de sortie](#8-formats-de-sortie)
9. [Gestion des erreurs](#9-gestion-des-erreurs)
10. [Configuration](#10-configuration)
11. [Depannage](#11-depannage)
12. [Historique des decisions](#12-historique-des-decisions)

---

## 1. Vue d'ensemble

### A quoi ca sert ?

Cette fonctionnalite permet d'**extraire les sous-titres** (manuels ou auto-generes) de
videos YouTube, Dailymotion, Vimeo et 1000+ autres plateformes. Le texte extrait alimente :

- **La page dediee** (`/social/subtitles`) — extraction manuelle par l'utilisateur
- **Le pipeline IA** (`ai_service.py`) — extraction automatique pour generer du contenu via Mistral

### Comment l'utilisateur s'en sert ?

1. Aller dans le module **Social** > **Sous-titres** dans la sidebar
2. Coller l'URL d'une video (YouTube, etc.)
3. Choisir la langue (francais par defaut) et le format (texte brut par defaut)
4. Cliquer sur **Extraire**
5. Attendre quelques secondes (polling automatique toutes les 2 secondes)
6. Copier le texte ou l'utiliser dans le pipeline IA

---

## 2. Architecture hybride

Le systeme utilise **deux moteurs d'extraction** avec une strategie de fallback automatique :

```
URL recue par le backend
    │
    ├── C'est une URL YouTube ?
    │       │
    │       └── OUI → youtube-transcript-api (moteur 1)
    │                       │
    │                 Succes → retourner le texte
    │                       │
    │                 Echec  → log warning + fallback vers yt-dlp (moteur 2)
    │
    └── Autre plateforme (Vimeo, Dailymotion, TED…) OU fallback YouTube
            │
            └── yt-dlp (moteur 2, universel)
                        │
                  Succes → retourner le texte
                        │
                  Echec  → retourner une erreur
```

### Pourquoi deux moteurs ?

| Critere | youtube-transcript-api | yt-dlp |
|---------|----------------------|--------|
| **Plateformes** | YouTube uniquement | 1000+ plateformes |
| **Methode** | Appel direct endpoint interne YouTube | Extraction complete (metadata + format) |
| **Detection par YouTube** | Faible (imite le client web) | Plus elevee |
| **Probleme de format** | Aucun (pas de resolution video) | Peut echouer avec `"Requested format is not available"` |
| **Dependances** | Legere (1 package) | Plus lourde (yt-dlp) |
| **Fiabilite YouTube** | Tres bonne | Variable (necessite mises a jour frequentes) |

**Regle simple :** youtube-transcript-api est le moteur principal pour YouTube. yt-dlp est le
filet de securite et le moteur pour toutes les autres plateformes.

---

## 3. Arborescence des fichiers

### Backend (FastAPI)

```
/Users/happi/App/API/FASTAPI/
├── app/
│   ├── config/
│   │   └── config.py                    # YTDLP_COOKIES_PATH, YTDLP_PROXY
│   ├── schemas/
│   │   └── schema_subtitle.py           # 7 schemas Pydantic (validation entree/sortie)
│   └── services/
│       └── subtitle_service.py          # *** FICHIER PRINCIPAL *** (toute la logique)
├── routeur/
│   └── subtitle_route.py               # 6 endpoints FastAPI
├── requirements.txt                     # youtube-transcript-api + yt-dlp
└── docker-compose.yml                   # Volumes + variables d'env
```

### Frontend (React/TypeScript)

```
/Users/happi/App/radiomanager-modular/src/modules/social/
├── types/
│   └── subtitle.ts                      # Interfaces TypeScript (miroir des schemas Pydantic)
├── api/
│   └── subtitleApi.ts                   # Client REST (6 fonctions Axios)
├── hooks/
│   └── useSubtitles.ts                  # 5 hooks TanStack Query (polling, cookies)
├── components/
│   └── subtitles/
│       └── SubtitleExtractor.tsx         # Composant UI principal
├── pages/
│   └── SubtitlesPage.tsx                # Page wrapper
└── index.ts                             # Enregistrement sidebar + route
```

---

## 4. Backend — Comment ca marche

### 4.1 Le service principal : `subtitle_service.py`

C'est le coeur de la fonctionnalite. Il contient tout : les deux moteurs, la gestion des
cookies, les conversions de format.

#### Section 1 : Gestion des cookies

| Fonction | Role |
|----------|------|
| `save_cookies_file(content, filename)` | Recoit un upload, detecte format (JSON Chrome ou Netscape), convertit, stocke |
| `get_cookies_status()` | Retourne si les cookies sont presents + infos (nombre, date, taille) |
| `_ensure_netscape_cookies()` | Convertit JSON Chrome → Netscape pour yt-dlp (resultat en cache memoire) |

**Pourquoi les cookies ?** YouTube bloque les requetes depuis les serveurs cloud. Les cookies
d'un compte YouTube connecte permettent de contourner ce blocage. Le backend accepte deux
formats et convertit automatiquement.

#### Section 2 : Moteur youtube-transcript-api (YTA)

| Fonction | Role |
|----------|------|
| `_extract_video_id(url)` | `"https://youtube.com/watch?v=abc123"` → `"abc123"` |
| `_is_youtube_url(url)` | Detecte si c'est YouTube (`youtube.com` ou `youtu.be`) |
| `_seconds_to_vtt(seconds)` | `65.5` → `"00:01:05.500"` (pour generer du VTT) |
| `_extract_via_yta(url, lang, fmt)` | **Extraction YouTube principale** |
| `_get_langs_via_yta(url)` | Liste des langues disponibles |

**Comment `_extract_via_yta` fonctionne, etape par etape :**

```
1. Extrait l'ID video depuis l'URL (regex)
2. Cree une instance YouTubeTranscriptApi()
3. Appelle ytt.list(video_id) → liste les sous-titres disponibles
4. Appelle find_transcript([lang, "en"]) → trouve la langue demandee (fallback anglais)
5. Appelle transcript.fetch() → telecharge les entrees [{text, start, duration}]
6. Convertit selon le format demande (txt, vtt, json)
7. Retourne {"status": "done", "content": "...", "format": "...", "lang": "..."}
```

Chaque entree retournee par la bibliotheque a cette structure :
```python
entry.text = "Bonjour et bienvenue"   # Le texte du sous-titre
entry.start = 0.0                      # Debut en secondes
entry.duration = 2.5                   # Duree en secondes
```

#### Section 3 : Moteur yt-dlp (universel)

| Fonction | Role |
|----------|------|
| `_build_ydl_opts(lang, output_path)` | Construit les options yt-dlp |
| `convert_vtt_to_txt(vtt_content)` | Supprime timestamps, balises HTML, doublons |
| `_cleanup_temp_files(task_id)` | Nettoie `/tmp` apres extraction |
| `_find_vtt_file(task_id)` | Trouve le fichier `.vtt` genere par yt-dlp |
| `_extract_and_convert(url, lang, fmt, task_id)` | **Extraction complete via yt-dlp** |

**Comment `_extract_and_convert` fonctionne, etape par etape :**

```
1. Construit les options yt-dlp (skip_download, cookies, proxy, etc.)
2. Lance ydl.download([url]) → telecharge uniquement les sous-titres dans /tmp/
3. Cherche le fichier .vtt genere dans /tmp/ (prefixe = task_id)
4. Lit le contenu et convertit en texte brut si format "txt"
5. Retourne {"status": "done", "content": "..."} ou {"status": "error", "message": "..."}
6. Nettoie les fichiers temporaires dans le bloc finally (toujours execute)
```

**Options yt-dlp importantes (dans `_build_ydl_opts`) :**

| Option | Valeur | Pourquoi |
|--------|--------|----------|
| `skip_download` | `True` | On ne veut que les sous-titres, pas la video |
| `writesubtitles` | `True` | Ecrit les sous-titres manuels sur le disque |
| `writeautomaticsub` | `True` | Ecrit aussi les sous-titres auto-generes |
| `subtitlesformat` | `'vtt'` | Format de sortie (Web Video Text Tracks) |
| `ignore_no_formats_error` | `True` | Ne pas planter si yt-dlp n'arrive pas a resoudre un format video |
| `extractor_args` | `player_client: ['tv', 'web']` | Contourne le blocage SABR streaming de YouTube |
| `cookiefile` | chemin vers cookies | Contourne le blocage IP des serveurs cloud |

> **ATTENTION :** Ne JAMAIS utiliser `format: 'worst'` dans les options yt-dlp.
> C'etait un alias de `youtube-dl` qui **n'existe plus dans yt-dlp** et provoque
> l'erreur `"Requested format is not available"`. Avec `skip_download: True`,
> ne pas specifier de `format` du tout.

#### Section 4 : Orchestration hybride

```python
_extract_with_fallback(url, lang, fmt, task_id)
```

C'est la fonction centrale appelee par les deux modes (async et sync). Logique :

```
1. URL est YouTube ? → tente _extract_via_yta()
2. YTA reussit ?    → retourne le resultat immediatement
3. YTA echoue ?     → log warning + continue vers yt-dlp
4. (Pas YouTube OU fallback) → tente _extract_and_convert() via yt-dlp
5. Retourne le resultat (succes ou erreur)
```

#### Section 5 : Modes d'utilisation

**Mode asynchrone** (pour l'API REST — la page Sous-titres) :

| Fonction | Role |
|----------|------|
| `create_task()` | Cree un ID unique UUID, initialise le statut a `"processing"` |
| `get_task(task_id)` | Recupere le statut actuel de la tache (pour le polling) |
| `extract_subtitles(task_id, url, lang, fmt)` | Tache de fond via `BackgroundTasks` de FastAPI |

Le stockage des taches est un **dict Python en memoire** (`_tasks`). Si le worker redemarre,
les taches en cours sont perdues. TODO : migrer vers Redis pour la persistance.

**Mode synchrone** (pour le pipeline IA) :

| Fonction | Role |
|----------|------|
| `extract_subtitles_sync(url, lang, fmt)` | Retourne directement le texte ou `raise RuntimeError` |

Utilise par `ai_service.py` → `fetch_youtube_transcript()` pour generer du contenu Mistral.

### 4.2 Les routes : `subtitle_route.py`

6 endpoints sous le prefixe `/social/subtitles` :

| Methode | Path | Role | Auth requise |
|---------|------|------|-------------|
| `POST` | `/extract` | Soumet une extraction async | JWT (tout utilisateur) |
| `GET` | `/status/{task_id}` | Poll le statut (toutes les 2s) | JWT (tout utilisateur) |
| `GET` | `/langs` | Liste les langues disponibles | JWT (tout utilisateur) |
| `POST` | `/upload-cookies` | Upload fichier cookies (.json/.txt) | JWT + role `super_admin` |
| `POST` | `/paste-cookies` | Coller cookies JSON | JWT + role `super_admin` |
| `GET` | `/cookies-status` | Statut du fichier cookies | JWT (tout utilisateur) |

**Verification super_admin (pattern standard du projet) :**
```python
is_super_admin = any(r.name == 'super_admin' for r in current_user.roles)
```

> **ATTENTION :** Ne PAS utiliser `getattr(current_user, 'is_super_admin')` — cet attribut
> n'existe pas sur le modele SQLAlchemy `User`. Toujours verifier via `current_user.roles`.

### 4.3 Les schemas : `schema_subtitle.py`

7 schemas Pydantic qui valident les entrees/sorties de l'API :

| Schema | Utilise par | Direction |
|--------|------------|-----------|
| `SubtitleExtractRequest` | `POST /extract` | Entree (body JSON) |
| `SubtitleTaskResponse` | `POST /extract` | Sortie |
| `SubtitleTaskStatus` | `GET /status/{id}` | Sortie |
| `AvailableLangsResponse` | `GET /langs` | Sortie |
| `CookiesUploadResponse` | `POST /upload-cookies` et `/paste-cookies` | Sortie |
| `CookiesStatusResponse` | `GET /cookies-status` | Sortie |
| `CookiesPasteRequest` | `POST /paste-cookies` | Entree (body JSON) |

---

## 5. Frontend — Comment ca marche

### 5.1 Types : `subtitle.ts`

Miroir TypeScript des schemas Pydantic backend. **Regle importante :** si un champ est ajoute
ou modifie dans un schema Pydantic, il faut aussi le modifier ici.

| Interface | Correspond a (backend) |
|-----------|----------------------|
| `SubtitleExtractRequest` | `SubtitleExtractRequest` |
| `SubtitleTaskResponse` | `SubtitleTaskResponse` |
| `SubtitleTaskStatus` | `SubtitleTaskStatus` |
| `AvailableLangs` | `AvailableLangsResponse` |
| `CookiesUploadResponse` | `CookiesUploadResponse` |
| `CookiesStatus` | `CookiesStatusResponse` |

### 5.2 Client API : `subtitleApi.ts`

6 fonctions qui appellent les 6 endpoints backend via l'instance Axios partagee (`@/shared/api/axios`).
L'instance Axios gere automatiquement le token JWT dans les headers et le refresh silencieux.

| Fonction | Methode HTTP | Endpoint |
|----------|-------------|----------|
| `extractSubtitles(params)` | `POST` | `/social/subtitles/extract` |
| `getExtractionStatus(taskId)` | `GET` | `/social/subtitles/status/{taskId}` |
| `getAvailableLangs(videoUrl)` | `GET` | `/social/subtitles/langs?url=...` |
| `uploadCookies(file)` | `POST` | `/social/subtitles/upload-cookies` (multipart) |
| `getCookiesStatus()` | `GET` | `/social/subtitles/cookies-status` |
| `pasteCookies(content)` | `POST` | `/social/subtitles/paste-cookies` |

### 5.3 Hooks : `useSubtitles.ts`

5 hooks TanStack Query. Tous suivent les patterns du projet :

| Hook | Role | Pattern utilise |
|------|------|----------------|
| `useSubtitleExtraction()` | Extraction complete avec polling auto | `useState` + `useQuery` + `refetchInterval` (2s) |
| `useAvailableLangs(url)` | Detection des langues | `useQuery` + `staleTime` 5min |
| `useCookiesStatus()` | Statut des cookies serveur | `useQuery` + `staleTime` 30s |
| `useCookiesUpload()` | Upload fichier cookies | `useState` + `invalidateQueries` |
| `useCookiesPaste()` | Coller cookies JSON | `useState` + `invalidateQueries` |

**Comment le polling fonctionne (`useSubtitleExtraction`), etape par etape :**

```
1. L'utilisateur clique "Extraire"
2. extract() appelle POST /extract → recoit un task_id
3. Le task_id est stocke dans un useState
4. useQuery se declenche car enabled: !!taskId devient true
5. refetchInterval fait un GET /status/{taskId} toutes les 2 secondes
6. Quand status === 'done' ou 'error' → refetchInterval retourne false → polling arrete
7. Le content est disponible dans taskStatus.content
```

**Apres upload/paste de cookies**, `queryClient.invalidateQueries({ queryKey: ['cookies-status'] })`
force le rechargement du statut des cookies dans l'UI.

### 5.4 Composant : `SubtitleExtractor.tsx`

Le composant principal de l'interface. Il affiche :

```
┌─────────────────────────────────────────────────┐
│ 🎬 Extraction de sous-titres                    │
├─────────────────────────────────────────────────┤
│ URL: [________________________________]          │
│                                                  │
│ Langue: [Francais ▾]  Format: [Texte brut ▾]   │
│ [Langues dispo]                                  │
│                                                  │
│ [🔍 Extraire]  [✕ Reinitialiser]                │
│                                                  │
│ ┌─ Resultat ──────────────────────────────────┐ │
│ │ 1234 caracteres extraits    [Copier] [Util] │ │
│ │ Bonjour et bienvenue dans cette video...    │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ─── Section admin (super_admin uniquement) ───  │
│ 🍪 Cookies actifs (16 cookies, maj 19/03/2026) │
│                                                  │
│ Coller les cookies (JSON depuis Cookie-Editor) : │
│ ┌──────────────────────────────────────────────┐│
│ │ [{"domain": ".youtube.com", ...}]            ││
│ └──────────────────────────────────────────────┘│
│ [📋 Envoyer les cookies]                        │
│                                                  │
│ ──── ou ────                                     │
│ [📤 Importer un fichier] .json ou .txt           │
└─────────────────────────────────────────────────┘
```

**Props du composant :**

| Prop | Type | Description |
|------|------|-------------|
| `onExtracted` | `(text: string) => void` | Callback quand le texte est extrait (pour integration parent) |
| `initialUrl` | `string` | URL pre-remplie |
| `defaultFormat` | `SubtitleFormat` | Format par defaut (`'txt'`) |
| `className` | `string` | Classes CSS additionnelles |

**Permission admin :** La section cookies n'est visible que si `hasPermission('can_acces_users_section')` retourne `true`. C'est la permission standard admin du projet.

### 5.5 Page et routing

- **`SubtitlesPage.tsx`** — page wrapper simple (titre + description + `<SubtitleExtractor />`)
- Enregistree dans **`social/index.ts`** :
  - Sidebar : `{ id: 'social-subtitles', label: 'Sous-titres', icon: 'Subtitles', path: '/subtitles', dividerBefore: true }`
  - Route : `{ path: 'subtitles', element: SubtitlesPage }`
- URL accessible : `/social/subtitles`

---

## 6. Endpoints API — Exemples requete/reponse

### POST /social/subtitles/extract

```bash
curl -X POST https://api.radio.audace.ovh/social/subtitles/extract \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=EfLzAJnXUrM", "lang": "fr", "format": "txt"}'
```

**Reponse :**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Extraction en cours…"
}
```

### GET /social/subtitles/status/{task_id}

```bash
curl https://api.radio.audace.ovh/social/subtitles/status/550e8400-... \
  -H "Authorization: Bearer TOKEN"
```

**Reponse (en cours) :**
```json
{ "task_id": "550e8400-...", "status": "processing" }
```

**Reponse (termine) :**
```json
{
  "task_id": "550e8400-...",
  "status": "done",
  "content": "Bonjour et bienvenue\ndans cette video\n...",
  "format": "txt",
  "lang": "fr"
}
```

**Reponse (erreur) :**
```json
{
  "task_id": "550e8400-...",
  "status": "error",
  "message": "Aucun sous-titre disponible en 'fr' pour EfLzAJnXUrM"
}
```

### GET /social/subtitles/langs?url=...

```json
{
  "manual": ["en"],
  "auto": ["fr", "en", "es", "de", "pt", "it", "ar"]
}
```

### POST /social/subtitles/upload-cookies

**Requete :** `multipart/form-data` avec champ `file` (fichier .json ou .txt, max 5 MB)

```json
{ "ok": true, "count": 16, "format_detected": "chrome_json" }
```

### POST /social/subtitles/paste-cookies

```bash
curl -X POST https://api.radio.audace.ovh/social/subtitles/paste-cookies \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "[{\"domain\": \".youtube.com\", ...}]"}'
```

```json
{ "ok": true, "count": 16, "format_detected": "chrome_json" }
```

### GET /social/subtitles/cookies-status

```json
{
  "has_cookies": true,
  "count": 16,
  "size_bytes": 2048,
  "modified_at": 1710850000.0
}
```

---

## 7. Gestion des cookies YouTube

### Pourquoi des cookies ?

YouTube bloque les requetes provenant de serveurs cloud (AWS, GCP, OVH, etc.) avec le
message "Sign in to confirm you're not a bot". Les cookies d'une session YouTube authentifiee
contournent ce blocage.

> **Note :** youtube-transcript-api n'a generalement PAS besoin de cookies car il utilise
> un endpoint interne different. Les cookies sont principalement necessaires pour yt-dlp (fallback).

### Comment obtenir les cookies ?

1. Installer l'extension **Cookie-Editor** dans Chrome ou Firefox
   - Chrome : chercher "Cookie-Editor" dans le Chrome Web Store
   - Firefox : chercher "Cookie-Editor" dans les extensions Firefox
2. Se connecter a **YouTube** dans le navigateur
3. Ouvrir une page YouTube, puis cliquer sur l'icone Cookie-Editor
4. Cliquer sur **Export** → **JSON** (les cookies sont copies dans le presse-papier)
5. Aller dans RadioManager > Social > Sous-titres
6. Ouvrir la section **Configuration cookies YouTube** (visible uniquement pour les admins)
7. Coller le JSON dans le textarea et cliquer **Envoyer les cookies**

### Formats acceptes

**1. JSON Chrome (Cookie-Editor)** — format d'entree le plus courant :
```json
[
  {
    "domain": ".youtube.com",
    "hostOnly": false,
    "path": "/",
    "secure": true,
    "expirationDate": 1742511600,
    "name": "VISITOR_INFO1_LIVE",
    "value": "abc123..."
  }
]
```

**2. Netscape TXT** — format natif yt-dlp (accepte aussi mais moins courant) :
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1742511600	VISITOR_INFO1_LIVE	abc123...
```

Le backend detecte automatiquement le format et convertit en Netscape si necessaire.

### Stockage

| Element | Valeur |
|---------|--------|
| Chemin par defaut | `/app/data/cookies.txt` (dans le container Docker) |
| Variable d'env | `YTDLP_COOKIES_PATH` |
| Persistance | Volume Docker `./data:/app/data` (survit aux redeploys) |

### Quand renouveler les cookies ?

Les cookies YouTube expirent generalement apres **quelques semaines**. Signes qu'il faut
les renouveler :
- L'extraction YouTube echoue avec le message "Sign in to confirm you're not a bot"
- L'extraction fonctionne via youtube-transcript-api (moteur 1) mais pas via yt-dlp (fallback)

---

## 8. Formats de sortie

| Format | Usage principal | Produit par | Exemple |
|--------|----------------|-------------|---------|
| `txt` | Pipeline IA / Mistral / RAG | YTA + yt-dlp | `Bonjour et bienvenue\ndans cette video` |
| `vtt` | Lecteur video web (<track>) | YTA + yt-dlp | `WEBVTT\n\n00:00:00.000 --> 00:00:02.500\nBonjour` |
| `srt` | Sous-titres classiques | yt-dlp seulement | `1\n00:00:00,000 --> 00:00:02,500\nBonjour` |
| `json` | Traitement programmatique | YTA seulement | `[{"text":"Bonjour","start":0.0,"duration":2.5}]` |

---

## 9. Gestion des erreurs

### Erreurs youtube-transcript-api

| Exception Python | Cause | Ce qui se passe |
|-----------------|-------|-----------------|
| `NoTranscriptFound` | Langue demandee absente | Message d'erreur → fallback yt-dlp |
| `TranscriptsDisabled` | Le proprietaire a desactive les sous-titres | Erreur definitive retournee |
| `VideoUnavailable` | Video privee, supprimee ou geo-bloquee | Erreur definitive retournee |
| Toute autre exception | Erreur reseau, changement API YouTube | Log warning → fallback yt-dlp |

### Erreurs yt-dlp

| Erreur | Cause | Solution |
|--------|-------|----------|
| `"Requested format is not available"` | Client YouTube bloque | Deja gere par `ignore_no_formats_error` + client `tv` |
| `"Sign in to confirm you're not a bot"` | IP serveur bloquee | Mettre a jour les cookies YouTube |
| `"No subtitles found"` | Pas de sous-titres sur la video | Essayer une autre langue |

### Prefixes de log

Les logs utilisent `logger = logging.getLogger("hapson-api")` avec des prefixes :

| Prefixe | Source |
|---------|--------|
| `[YTA]` | youtube-transcript-api |
| `[yt-dlp]` | yt-dlp |
| `[subtitles]` | Orchestration hybride (choix du moteur, fallback) |

---

## 10. Configuration

### Variables d'environnement

| Variable | Defaut | Description |
|----------|--------|-------------|
| `YTDLP_COOKIES_PATH` | `/app/data/cookies.txt` | Chemin du fichier cookies Netscape |
| `YTDLP_PROXY` | _(vide)_ | Proxy HTTP pour yt-dlp (ex: `http://user:pass@proxy:port`) |

### docker-compose.yml

```yaml
services:
  api:
    environment:
      YTDLP_COOKIES_PATH: ${YTDLP_COOKIES_PATH:-/app/data/cookies.txt}
      YTDLP_PROXY: ${YTDLP_PROXY:-}
    volumes:
      - ./data:/app/data    # Cookies YouTube persistants entre redeploys
```

### requirements.txt

```
yt-dlp
youtube-transcript-api>=1.0.0
```

---

## 11. Depannage

### L'extraction YouTube ne fonctionne pas

**Etape 1 — Verifier les logs Docker :**
```bash
sudo docker logs audace_api --tail 50 | grep -i "subtitle\|YTA\|yt-dlp"
```

**Etape 2 — Verifier le statut des cookies :**
```bash
curl -H "Authorization: Bearer TOKEN" \
  https://api.radio.audace.ovh/social/subtitles/cookies-status
```

**Etape 3 — Tester youtube-transcript-api directement :**
```bash
sudo docker exec -it audace_api python3 -c "
from youtube_transcript_api import YouTubeTranscriptApi
ytt = YouTubeTranscriptApi()
t = ytt.list('EfLzAJnXUrM')
for tr in t:
    print(f'{tr.language_code} (auto={tr.is_generated})')
"
```

**Etape 4 — Mettre a jour yt-dlp et youtube-transcript-api :**
```bash
sudo docker exec -it audace_api pip install -U yt-dlp youtube-transcript-api
```

### Les sous-titres sont vides ou incomplets

- Verifier que la video a des sous-titres (bouton "Langues dispo" dans l'UI)
- Essayer avec la langue `en` (anglais) — plus souvent disponible
- Certaines videos n'ont ni sous-titres manuels ni auto-generes

### Les cookies expirent souvent

1. Ouvrir Cookie-Editor sur YouTube (apres s'etre connecte)
2. Export → JSON → copier
3. Coller dans la section admin de la page Sous-titres
4. Les cookies durent en general quelques semaines

### Le mode async reste bloque en "processing"

Le stockage `_tasks` est un dict Python en memoire. Si le worker (container Docker)
redemarre pendant une extraction, la tache est perdue et reste a `"processing"` pour
toujours cote frontend. L'utilisateur doit relancer l'extraction.

---

## 12. Historique des decisions

### v1 : Cloudflare Worker (abandonne)

Un Worker Cloudflare appelait directement l'API YouTube pour les sous-titres.
**Abandonne** car YouTube a bloque les Workers Cloudflare.

### v2 : yt-dlp seul (problemes de format)

yt-dlp est universel mais rencontre des problemes recurrents avec YouTube :
- `"Requested format is not available"` — YouTube change regulierement son API
- Le client `android` a ete bloque par le streaming SABR
- Le client `tv` fonctionne mais necessite `ignore_no_formats_error`
- Necessite des mises a jour frequentes de yt-dlp

### v3 : Architecture hybride (actuelle)

Combine youtube-transcript-api (moteur principal YouTube) et yt-dlp (fallback + autres plateformes).
youtube-transcript-api appelle directement l'endpoint interne YouTube sans resolution de format video,
ce qui elimine la plupart des problemes de compatibilite.

### Regles yt-dlp a retenir

| Regle | Explication |
|-------|-------------|
| Ne JAMAIS utiliser `format: 'worst'` | Alias supprime de yt-dlp, cause une erreur |
| Toujours `ignore_no_formats_error: True` | Empeche le crash quand yt-dlp ne trouve pas de format |
| Utiliser `player_client: ['tv', 'web']` | Le client `android` est bloque par YouTube SABR |
| Mettre a jour yt-dlp regulierement | YouTube casse les anciennes versions |

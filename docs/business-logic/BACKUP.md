# Module BACKUP - Gestion des Sauvegardes (Google Drive)

Documentation de la gestion des sauvegardes de la base de donnees PostgreSQL vers Google Drive, avec declenchement, historique et restauration depuis l'interface utilisateur.

---

## Table des matieres

1. [Vue d'ensemble](#vue-densemble)
2. [Comment ca marche (niveau junior)](#comment-ca-marche-niveau-junior)
3. [Architecture](#architecture)
4. [Fonctions metier](#fonctions-metier)
5. [Endpoints API](#endpoints-api)
6. [Frontend (UI)](#frontend-ui)
7. [Regles metier](#regles-metier)
8. [Relations](#relations)
9. [Contraintes](#contraintes)
10. [Exemples d'utilisation](#exemples-dutilisation)
11. [Depannage](#depannage)

---

## Vue d'ensemble

### A quoi ca sert ?

Imagine que ta base de donnees est un **cahier** ou tu ecris tout : les utilisateurs, les emissions, les roles, etc. Si quelqu'un renverse du cafe sur le cahier, tout est perdu.

Le module Backup, c'est comme **photocopier le cahier** regulierement et **envoyer la copie dans un coffre-fort** (Google Drive). Si le cahier est abime, tu peux **reprendre la photocopie** pour tout recuperer.

### Ce que le super_admin peut faire depuis l'interface :

1. **Connecter Google Drive** — Lier un compte Google pour y stocker les sauvegardes
2. **Configurer** — Choisir le dossier Drive, l'heure du backup auto, combien de jours garder les copies
3. **Sauvegarder maintenant** — Declencher un backup a la demande
4. **Voir l'historique** — Consulter la liste des backups passes (succes, echecs, en cours)
5. **Restaurer** — Remettre la base de donnees a un etat anterieur depuis un backup

### Responsabilites du module

- Connexion/deconnexion du compte Google Drive (OAuth2)
- Chiffrement des tokens Google (Fernet/AES)
- Upload des fichiers de backup vers Google Drive
- Telechargement et restauration depuis Google Drive
- Suivi de progression des taches longues (backup/restore)
- Historique complet avec statuts et erreurs
- Protection par permission (`can_manage_backups`)

### Fichiers sources

```
Backend (API FastAPI) :
├── app/models/model_backup.py          # Tables backup_config + backup_history
├── app/schemas/schema_backup.py        # Validation des donnees (Pydantic)
├── app/db/crud/crud_backup.py          # Lectures/ecritures en base
├── app/services/google_drive_client.py # Communication avec Google Drive
├── routeur/backup_route.py             # Endpoints API (13 routes)
└── app/config/config.py                # GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

Frontend (React) :
├── src/shared/api/backup.ts                              # Appels API (Axios)
├── src/shared/components/settings/admin/BackupManagement.tsx  # Interface utilisateur
├── src/shared/pages/settings/AdminTab.tsx                # Onglet Administration (contient Sauvegardes)
└── src/shared/types/permissions.ts                       # Permission can_manage_backups
```

### Dependances

```python
# Backend
from app.models.model_backup import BackupConfig, BackupHistory
from app.services.google_drive_client import (
    build_google_auth_url, exchange_google_code, ensure_valid_token,
    upload_to_drive, download_from_drive, list_drive_files,
)
from app.utils.crypto import encrypt_totp_secret, decrypt_totp_secret  # Chiffrement Fernet
from app.services import sync_tasks  # Suivi de progression des taches
```

---

## Comment ca marche (niveau junior)

### Le flux complet en images

```
┌──────────────────────────────────────────────────────────────────┐
│                          SUPER ADMIN                             │
│                                                                  │
│   1. Va dans Settings > Administration > Sauvegardes             │
│   2. Clique "Connecter Google Drive"                             │
│   3. Google demande l'autorisation → Accepte                     │
│   4. Retour sur l'app → "Google Drive connecte !"                │
│   5. Clique "Sauvegarder maintenant"                             │
│   6. Voit la barre de progression : 10%... 30%... 90%... 100%   │
│   7. Le backup apparait dans l'historique                        │
└──────────────────────────────────────────────────────────────────┘
```

### Analogie : Le coffre-fort automatique

```
TON SERVEUR                    INTERNET                  GOOGLE DRIVE
┌─────────────┐                                         ┌─────────────┐
│             │                                         │             │
│  PostgreSQL │   1. pg_dump                          │   Dossier   │
│  (ta base)  │──────────────┐                          │  "Backups"  │
│             │              │                          │             │
└─────────────┘              ▼                          │  ┌───────┐  │
                    ┌─────────────┐   2. Upload via     │  │dump_  │  │
                    │ dump_2026-  │──────API Google ─────│  │2026-  │  │
                    │ 03-16.sql.gz│   Drive REST v3      │  │03-16  │  │
                    └─────────────┘                     │  └───────┘  │
                    /backups/                            │  ┌───────┐  │
                    (volume Docker)                      │  │dump_  │  │
                                                        │  │2026-  │  │
                                                        │  │03-15  │  │
                                                        │  └───────┘  │
                                                        └─────────────┘
```

### Les 3 etapes d'un backup

**Etape 1 — Le cron fabrique le fichier** (ceci existe deja sur le serveur)

Un cron job (tache automatique) sur le serveur execute toutes les nuits :
```bash
pg_dump --clean --if-exists -U postgres audace_db | gzip > /backups/dump_2026-03-16_03-00.sql.gz
```
Ca exporte la base `audace_db` avec des instructions `DROP TABLE IF EXISTS` avant chaque `CREATE TABLE`, la compresse, et la sauvegarde dans `/backups/`.

> **Note** : on utilise `pg_dump` (une seule base) et non `pg_dumpall` (cluster entier).
> `pg_dump --clean` produit un dump compatible avec `psql -d audace_db` pour la restauration.
> Les anciens dumps `pg_dumpall` restent compatibles avec la restauration (le backend gere les deux formats).

**Etape 2 — L'API envoie le fichier sur Google Drive**

Quand le super_admin clique "Sauvegarder maintenant" :
1. L'API cherche le fichier le plus recent dans `/backups/`
2. L'API verifie que le token Google est valide (le rafraichit si besoin)
3. L'API envoie le fichier sur Google Drive via l'API REST
4. L'API enregistre le resultat dans l'historique

**Etape 3 — La restauration (en cas de probleme)**

Quand le super_admin clique "Restaurer" sur un backup :
1. L'API telecharge le fichier depuis Google Drive (s'il n'est pas en local)
2. L'API decompresse le fichier (`gunzip`)
3. L'API injecte le contenu dans PostgreSQL (`psql`)
4. La base retrouve son etat au moment du backup

### La connexion Google Drive (OAuth2)

C'est comme quand tu cliques "Se connecter avec Google" sur un site, sauf qu'ici on demande l'acces a Google Drive.

```
┌─────────┐     1. Clique         ┌──────────┐
│         │    "Connecter"        │          │
│  Admin  │──────────────────────>│  Notre   │
│  (UI)   │                       │  API     │
│         │<──────────────────────│          │
└─────────┘  2. Redirige vers     └──────────┘
     │          Google
     │
     ▼
┌─────────────────────┐
│                     │
│  Google Consent     │  3. "Audace veut acceder
│  Screen             │      a votre Google Drive.
│                     │      Autoriser ?"
└─────────────────────┘
     │
     │  4. L'admin clique "Autoriser"
     ▼
┌──────────┐  5. Google renvoie    ┌──────────┐
│          │     un code secret    │          │
│  Google  │──────────────────────>│  Notre   │
│  OAuth   │                       │  API     │
│          │<──────────────────────│          │
└──────────┘  6. L'API echange     └──────────┘
                 le code contre          │
                 access_token +          │  7. Stocke les tokens
                 refresh_token           │     chiffres en base
                                         ▼
                                   ┌──────────┐
                                   │PostgreSQL │
                                   │          │
                                   │ backup_  │
                                   │ config   │
                                   └──────────┘
                                         │
                                         │  8. Redirige vers l'UI
                                         ▼
                                   ┌──────────┐
                                   │  L'UI    │
                                   │ affiche  │
                                   │"Connecte"│
                                   └──────────┘
```

**Pourquoi 2 tokens ?**
- **access_token** : Le badge d'acces, valide ~1 heure. C'est ce qu'on envoie a Google Drive pour chaque requete.
- **refresh_token** : La cle de renouvellement, valide longtemps. Quand le badge expire, on l'utilise pour obtenir un nouveau badge sans redemander a l'admin.

**Pourquoi chiffrer ?**
Les tokens sont stockes chiffres (Fernet/AES) en base de donnees. Si quelqu'un pirate la base, il ne peut rien faire avec les tokens car il n'a pas la cle de chiffrement (`TOTP_ENCRYPTION_KEY`).

---

## Architecture

### Modele BackupConfig (table `backup_config`)

C'est une table **singleton** — il n'y a qu'une seule ligne, jamais plus.

```python
BackupConfig:
    id: int (PK)

    # Tokens Google (chiffres Fernet)
    google_access_token: Text (nullable)      # Badge d'acces chiffre
    google_refresh_token: Text (nullable)     # Cle de renouvellement chiffree
    google_token_expires_at: DateTime (tz)    # Quand expire le badge

    # Configuration Google Drive
    google_drive_folder_id: String(255)       # ID du dossier Drive cible
    google_drive_folder_name: String(255)     # Nom du dossier (affichage)
    google_email: String(255)                 # Email du compte Google connecte

    # Configuration du backup automatique
    auto_backup_enabled: Boolean (default: false)  # Activer le backup auto ?
    auto_backup_hour: Integer (default: 3)         # Heure du backup auto (0-23)
    retention_days: Integer (default: 30)           # Combien de jours garder les backups

    # Metadata de connexion
    is_connected: Boolean (default: false)    # Google Drive est-il connecte ?
    connected_by: Integer (nullable)          # ID de l'admin qui a connecte
    connected_at: DateTime (tz, nullable)     # Quand la connexion a ete faite
    updated_at: DateTime (tz, auto)           # Derniere modification
```

### Modele BackupHistory (table `backup_history`)

Une ligne par backup (reussi ou echoue).

```python
BackupHistory:
    id: int (PK)
    filename: String(255)                     # Ex: "dump_2026-03-16_03-00.sql.gz"
    file_size_bytes: Integer (nullable)       # Taille du fichier en octets
    backup_type: String(20)                   # "manual" ou "scheduled"
    status: String(20)                        # "running", "completed", "failed"
    error_message: Text (nullable)            # Message d'erreur si echec
    google_drive_file_id: String(255)         # ID du fichier sur Drive (pour restore)
    uploaded_to_drive: Boolean (default: false)  # A-t-il ete envoye sur Drive ?
    started_at: DateTime (tz, auto)           # Debut du backup
    completed_at: DateTime (tz, nullable)     # Fin du backup
    duration_seconds: Integer (nullable)      # Duree en secondes
    triggered_by: Integer (nullable)          # ID de l'admin qui a declenche
```

### Schema de relations

```
┌─────────────────┐          ┌──────────────────┐
│  backup_config  │          │  backup_history   │
│  (1 seule ligne)│          │  (N lignes)       │
│                 │          │                   │
│  google_email   │          │  filename         │
│  access_token   │          │  status           │
│  refresh_token  │          │  backup_type      │
│  folder_id      │          │  triggered_by ────│──> users.id
│  connected_by ──│──> users.id                  │
│  auto_backup_*  │          │  google_drive_    │
│                 │          │    file_id        │
└─────────────────┘          └──────────────────┘

┌─────────────────┐
│ user_permissions│
│                 │
│ can_manage_     │
│   backups: bool │ ← Seuls les users avec cette permission voient la section
└─────────────────┘
```

---

## Fonctions metier

### CRUD (`app/db/crud/crud_backup.py`)

#### `get_backup_config(db) -> BackupConfig | None`

Recupere la configuration unique du backup. Retourne `None` si aucune config n'existe.

```python
config = get_backup_config(db)
if config and config.is_connected:
    print(f"Google Drive connecte via {config.google_email}")
```

#### `upsert_backup_config(db, **kwargs) -> BackupConfig`

Cree ou met a jour la configuration. "Upsert" = Update si la ligne existe, Insert sinon.

```python
# Exemple : activer le backup auto a 4h du matin
config = upsert_backup_config(db, auto_backup_enabled=True, auto_backup_hour=4)
```

#### `create_backup_history(db, filename, backup_type, triggered_by) -> BackupHistory`

Cree une nouvelle entree d'historique avec le statut "running".

```python
history = create_backup_history(db, filename="dump_2026-03-16.sql.gz", backup_type="manual", triggered_by=1)
# history.status == "running"
# history.id == 42
```

#### `update_backup_history(db, history_id, **kwargs) -> BackupHistory`

Met a jour une entree d'historique (par exemple quand le backup se termine).

```python
update_backup_history(db, 42,
    status="completed",
    file_size_bytes=15_000_000,
    google_drive_file_id="abc123",
    uploaded_to_drive=True,
    completed_at=datetime.now(timezone.utc),
    duration_seconds=12,
)
```

#### `get_backup_history(db, skip, limit) -> (list[BackupHistory], int)`

Historique pagine. Retourne un tuple (liste, total).

```python
items, total = get_backup_history(db, skip=0, limit=20)
# items = [BackupHistory, BackupHistory, ...]
# total = 47  (nombre total de backups dans l'historique)
```

#### `get_backup_by_id(db, backup_id) -> BackupHistory | None`

Recupere un backup par son ID (pour la restauration).

#### `get_last_backup(db) -> BackupHistory | None`

Recupere le dernier backup (le plus recent).

#### `get_today_backup(db) -> BackupHistory | None`

Verifie si un backup a deja ete fait aujourd'hui (pour eviter les doublons dans le scheduler).

---

### Google Drive Client (`app/services/google_drive_client.py`)

#### `build_google_auth_url(user_id) -> (auth_url, state)`

Genere l'URL de consentement Google. Le `state` est un jeton HMAC-SHA256 signe qui contient l'ID de l'utilisateur. Il sert a empecher les attaques CSRF.

```python
url, state = build_google_auth_url(user_id=1)
# url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=..."
# state = "eyJ..." (JWT signe)
```

#### `verify_google_state(state) -> dict`

Verifie et decode le state retourne par Google. Lance une exception si invalide.

#### `exchange_google_code(code) -> dict`

Echange le code d'autorisation Google contre des tokens.

```python
result = exchange_google_code("4/0AX4XfWh...")
# result = {
#     "access_token": "ya29.a0...",
#     "refresh_token": "1//0e...",
#     "expires_in": 3599,
#     "email": "admin@audace.ovh"
# }
```

#### `ensure_valid_token(db) -> str | None`

Verifie si le token est encore valide. Si expire, le rafraichit automatiquement.
Retourne le access_token pret a l'emploi, ou `None` si impossible.

C'est la fonction la plus utilisee — elle est appelee avant chaque interaction avec Google Drive.

```python
access_token = ensure_valid_token(db)
if not access_token:
    raise Exception("Google Drive non connecte ou token invalide")
# Utiliser access_token pour les appels Drive
```

#### `upload_to_drive(access_token, folder_id, filepath, filename) -> dict`

Envoie un fichier vers Google Drive. Retourne les details du fichier cree.

```python
result = upload_to_drive(token, "folder123", "/backups/dump.sql.gz", "dump.sql.gz")
# result = { "id": "abc123", "name": "dump.sql.gz" }
```

#### `download_from_drive(access_token, file_id, dest_path) -> str`

Telecharge un fichier depuis Google Drive vers le serveur.

```python
path = download_from_drive(token, "abc123", "/backups/dump_restore.sql.gz")
# path = "/backups/dump_restore.sql.gz"
```

#### `list_drive_files(access_token, folder_id) -> list[dict]`

Liste les fichiers dans un dossier Google Drive.

#### `delete_drive_file(access_token, file_id) -> bool`

Supprime un fichier sur Google Drive.

---

## Endpoints API

Tous les endpoints sont sous le prefixe `/backup` et necessitent :
- Un token JWT valide (authentification)
- La permission `can_manage_backups` (autorisation)

### Resume des endpoints

| Methode | Endpoint | Description | Corps attendu |
|---------|----------|-------------|---------------|
| GET | `/backup/config` | Lire la configuration | - |
| PUT | `/backup/config` | Modifier la configuration | `BackupConfigUpdate` |
| POST | `/backup/config/oauth/url` | Obtenir l'URL Google OAuth | - |
| GET | `/backup/config/oauth/callback` | Callback Google (redirect) | Query: `code`, `state` |
| POST | `/backup/config/disconnect` | Deconnecter Google Drive | - |
| POST | `/backup/trigger` | Lancer un backup manuel | - |
| GET | `/backup/status/{task_id}` | Statut d'une tache | - |
| GET | `/backup/history` | Historique des backups | Query: `skip`, `limit` |
| GET | `/backup/files` | Fichiers disponibles | - |
| POST | `/backup/restore/upload` | Restaurer depuis un fichier uploade | `multipart/form-data: file + confirm` |
| POST | `/backup/restore/{backup_id}` | Restaurer un backup | `{ "confirm": "RESTAURER" }` |
| GET | `/backup/drive/folders` | Lister les dossiers Google Drive | - |
| POST | `/backup/drive/folders` | Creer un dossier Google Drive | `{ "name": "..." }` |

### Detail des endpoints

#### GET `/backup/config`

Retourne la config actuelle (sans les tokens — ils sont chiffres et ne sortent jamais).

```json
{
  "is_connected": true,
  "google_email": "admin@audace.ovh",
  "google_drive_folder_id": "1abc...",
  "google_drive_folder_name": "Backups RadioManager",
  "auto_backup_enabled": true,
  "auto_backup_hour": 3,
  "retention_days": 30,
  "connected_at": "2026-03-16T10:00:00Z",
  "token_valid": true
}
```

#### PUT `/backup/config`

Modifie la configuration. Seuls les champs present dans le body sont modifies.

```json
// Request
{ "auto_backup_enabled": true, "auto_backup_hour": 4, "retention_days": 14 }

// Response : meme format que GET /config
```

#### POST `/backup/config/oauth/url`

Genere l'URL ou rediriger l'admin pour connecter Google Drive.

```json
{
  "redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "eyJ..."
}
```

Le frontend fait ensuite `window.location.href = redirect_url` pour envoyer l'admin sur Google.

#### GET `/backup/config/oauth/callback`

**Ce n'est PAS un endpoint appele par le frontend !**
C'est Google qui redirige le navigateur de l'admin ici apres autorisation.

Flux :
1. Google redirige vers `https://api.radio.audace.ovh/backup/config/oauth/callback?code=XXX&state=YYY`
2. L'API echange le code contre des tokens
3. L'API stocke les tokens chiffres en base
4. L'API redirige vers `https://app.radio.audace.ovh/settings?tab=admin&section=sauvegardes&oauth=success`

#### POST `/backup/trigger`

Declenche un backup en arriere-plan. Retourne immediatement un `task_id` pour suivre la progression.

```json
// Response
{
  "task_id": "task-abc123",
  "backup_id": 42,
  "message": "Backup de dump_2026-03-16.sql.gz lance en arriere-plan"
}
```

Le frontend poll ensuite `GET /backup/status/task-abc123` toutes les 2 secondes pour afficher la progression.

#### GET `/backup/status/{task_id}`

Retourne le statut d'une tache de backup ou restauration en cours.

```json
// En cours
{
  "id": "task-abc123",
  "label": "backup-dump_2026-03-16.sql.gz",
  "status": "running",
  "progress": "Upload vers Google Drive...",
  "percent": 30,
  "result": null,
  "error": null
}

// Termine
{
  "id": "task-abc123",
  "label": "backup-dump_2026-03-16.sql.gz",
  "status": "done",
  "progress": "Termine",
  "percent": 100,
  "result": { "backup_id": 42, "drive_file_id": "abc123" },
  "error": null
}
```

#### GET `/backup/history`

Historique pagine des backups.

```json
{
  "total": 47,
  "items": [
    {
      "id": 42,
      "filename": "dump_2026-03-16_03-00.sql.gz",
      "file_size_bytes": 15000000,
      "backup_type": "manual",
      "status": "completed",
      "error_message": null,
      "google_drive_file_id": "abc123",
      "uploaded_to_drive": true,
      "started_at": "2026-03-16T10:30:00Z",
      "completed_at": "2026-03-16T10:30:12Z",
      "duration_seconds": 12,
      "triggered_by": 1
    }
  ],
  "skip": 0,
  "limit": 20
}
```

#### GET `/backup/files`

Liste les fichiers de backup disponibles (locaux + Google Drive).

```json
[
  {
    "filename": "dump_2026-03-16_03-00.sql.gz",
    "size_bytes": 15000000,
    "source": "local",
    "google_drive_file_id": null,
    "modified_at": "2026-03-16T03:00:00Z"
  },
  {
    "filename": "dump_2026-03-10_03-00.sql.gz",
    "size_bytes": 14500000,
    "source": "drive",
    "google_drive_file_id": "xyz789",
    "modified_at": "2026-03-10T03:00:00Z"
  }
]
```

#### POST `/backup/restore/{backup_id}`

Restaure la base de donnees depuis un backup. **Action dangereuse** — necessite la confirmation `"RESTAURER"`.

```json
// Request
{ "confirm": "RESTAURER" }

// Response
{
  "task_id": "task-restore-xyz",
  "message": "Restauration de dump_2026-03-16.sql.gz lancee en arriere-plan"
}
```

**Ce qui se passe en arriere-plan :**
1. Si le fichier n'est pas en local, le telecharge depuis Google Drive
2. **Nettoie le schema** : `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` (supprime toutes les tables pour eviter les conflits)
3. Decompresse le fichier (`gunzip`)
4. Injecte dans PostgreSQL (`psql`)
5. **Resynchronise les sequences** : recalcule tous les auto-increments (`setval` sur chaque sequence)
6. Met a jour le statut de la tache

> **Pourquoi le nettoyage du schema ?** Sans `DROP SCHEMA`, les `CREATE TABLE` du dump echouent (tables existantes), les `COPY` echouent (cles primaires dupliquees), et `psql` retourne 0 sans rien restaurer. Le `DROP SCHEMA` garantit une restauration propre.

> **Pourquoi resynchroniser les sequences ?** Apres restauration, les sequences auto-increment (IDs des tables) peuvent etre desynchronisees, causant des erreurs `UniqueViolation` sur les prochains INSERT.

#### POST `/backup/restore/upload`

Restaure la base de donnees depuis un fichier backup envoye par l'admin (upload direct). Utile quand le backup n'est pas dans l'historique (ex: backup telecharge depuis Google Drive manuellement, ou backup d'un ancien serveur).

```
// Request (multipart/form-data)
file: <fichier .sql.gz>
confirm: "RESTAURER"

// Response
{
  "task_id": "task-restore-upload-xyz",
  "message": "Restauration depuis dump_20260316.sql.gz lancee en arriere-plan"
}
```

**Limitations** : taille max 500 Mo. Le fichier doit etre au format `.sql.gz` (dump PostgreSQL compresse).

**Meme processus en arriere-plan** : nettoyage schema → gunzip/psql → resync sequences.

---

## Frontend (UI)

### Ou trouver la section Sauvegardes

```
Settings (page) > Administration (onglet) > Sauvegardes (sous-onglet)
```

L'URL directe est : `/settings?tab=admin&section=sauvegardes`

### Structure du composant BackupManagement.tsx

Le composant est divise en 5 zones visuelles :

```
┌─────────────────────────────────────────────────────────┐
│  1. CONNEXION GOOGLE DRIVE                              │
│  ┌───────────────────────────────────────┐              │
│  │ Statut : Connecte                     │ [Deconnecter]│
│  │ Email : admin@audace.ovh              │              │
│  └───────────────────────────────────────┘              │
│                                    OU                   │
│  ┌───────────────────────────────────────┐              │
│  │ Statut : Non connecte                 │ [Connecter]  │
│  └───────────────────────────────────────┘              │
├─────────────────────────────────────────────────────────┤
│  2. CONFIGURATION                                       │
│  Dossier Drive : [__________________________]           │
│  Backup auto : [ON/OFF]  Heure : [03:00]               │
│  Retention : [30] jours                                 │
│                                      [Sauvegarder]      │
├─────────────────────────────────────────────────────────┤
│  3. BACKUP MANUEL                                       │
│  [Sauvegarder maintenant]                               │
│  ████████████░░░░░░░  65% — Upload vers Google Drive... │
├─────────────────────────────────────────────────────────┤
│  4. HISTORIQUE                                          │
│  ┌──────┬──────────────────────┬────────┬────────┬────┐ │
│  │ Date │ Fichier              │ Taille │ Statut │    │ │
│  ├──────┼──────────────────────┼────────┼────────┼────┤ │
│  │ 16/03│ dump_2026-03-16.sql  │ 15 MB  │ Reussi │ ↩️ │ │
│  │ 15/03│ dump_2026-03-15.sql  │ 14 MB  │ Reussi │ ↩️ │ │
│  │ 14/03│ dump_2026-03-14.sql  │ - MB   │ Echec  │    │ │
│  └──────┴──────────────────────┴────────┴────────┴────┘ │
├─────────────────────────────────────────────────────────┤
│  5. DIALOG DE RESTAURATION (si clic sur ↩️)             │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ATTENTION ! La restauration va ecraser           │    │
│  │ toutes les donnees actuelles.                    │    │
│  │                                                   │    │
│  │ Tapez RESTAURER pour confirmer :                  │    │
│  │ [________________________]                        │    │
│  │                                                   │    │
│  │              [Annuler]  [Restaurer]               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Permission requise

Seuls les utilisateurs avec `can_manage_backups = true` peuvent voir et utiliser cette section.
Cette permission se gere dans Settings > Administration > Privileges.

### Flux technique frontend

```
1. Page chargee
   └──> getBackupConfig()        GET /backup/config
   └──> getBackupHistory()       GET /backup/history

2. Connecter Google Drive
   └──> getGoogleOAuthUrl()      POST /backup/config/oauth/url
   └──> window.location.href = redirect_url
   ... (l'admin est sur Google) ...
   └──> Google redirige vers le callback API
   └──> L'API redirige vers /settings?tab=admin&section=sauvegardes&oauth=success
   └──> Le composant detecte ?oauth=success et recharge la config

3. Sauvegarder maintenant
   └──> triggerBackup()          POST /backup/trigger
   └──> setInterval toutes les 2s :
        └──> getBackupStatus(taskId)  GET /backup/status/{task_id}
        └──> Met a jour la barre de progression
        └──> Si status == "done" ou "error" : clearInterval

4. Restaurer
   └──> L'admin tape "RESTAURER" dans le dialog
   └──> triggerRestore(backupId)  POST /backup/restore/{backup_id}
   └──> Meme polling que le backup pour suivre la progression
```

---

## Regles metier

### 1. Permission obligatoire

Toutes les routes verifient `can_manage_backups` avant d'executer quoi que ce soit. Un utilisateur sans cette permission recoit une erreur 403.

```python
def _check_backup_permission(db, user):
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user.id).first()
    if not perms or not perms.can_manage_backups:
        raise HTTPException(403, "Permission 'can_manage_backups' requise")
```

### 2. Tokens toujours chiffres

Les tokens Google ne sont **jamais** stockes en clair. Ils sont chiffres avec Fernet (AES-128-CBC) avant d'etre ecrits en base, et dechiffres uniquement au moment de l'utilisation.

### 3. Rafraichissement automatique des tokens

Avant chaque appel Google Drive, `ensure_valid_token()` verifie si le token expire bientot (< 5 min). Si oui, il le rafraichit automatiquement via le `refresh_token`.

### 4. Restauration protegee

La restauration est une action **irreversible** — elle ecrase toutes les donnees actuelles. Pour eviter les erreurs :
- L'admin doit taper exactement `RESTAURER` dans un champ de confirmation
- Seuls les backups avec le statut `completed` peuvent etre restaures
- L'action est loguee dans le journal d'audit

### 5. Un seul backup par declenchement

Le trigger attend que le fichier de backup le plus recent existe dans `/backups/`. S'il n'y a aucun fichier, l'API retourne une erreur 404.

### 6. Taches en arriere-plan

Les backups et restaurations sont executes dans un thread daemon separe. L'admin ne reste pas bloque — il voit la progression en temps reel via le polling du `task_id`.

### 7. Audit systematique

Toutes les actions critiques sont loguees :
- `backup_trigger` : Backup declenche
- `backup_complete` : Backup termine
- `restore_trigger` : Restauration declenchee
- `restore_complete` : Restauration terminee
- `oauth_connect` : Google Drive connecte
- `oauth_disconnect` : Google Drive deconnecte
- `update` : Configuration modifiee

---

## Relations

### Dependances entrantes (qui utilise le module Backup ?)

- **AdminTab.tsx** — Affiche la section Sauvegardes
- **permissions.ts** — Declare `can_manage_backups`

### Dependances sortantes (de quoi depend le module Backup ?)

| Dependance | Usage |
|------------|-------|
| `app/utils/crypto.py` | Chiffrement/dechiffrement des tokens Google (Fernet) |
| `app/services/sync_tasks.py` | Suivi de progression des taches longues |
| `core/auth/oauth2.py` | Verification du JWT (get_current_user) |
| `app/models/model_user_permissions.py` | Verification de la permission `can_manage_backups` |
| `app/db/crud/crud_audit_logs.py` | Journalisation des actions (audit log) |
| `app/config/config.py` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FRONTEND_URL` |
| Volume Docker `/backups` | Acces aux fichiers pg_dump |

### Diagramme de dependances

```
                    ┌──────────────────┐
                    │  backup_route.py │ (point d'entree)
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │crud_backup.py│ │google_drive_ │ │ sync_tasks   │
    │              │ │client.py     │ │              │
    └──────┬───────┘ └──────┬───────┘ └──────────────┘
           │                │
           ▼                ▼
    ┌──────────────┐ ┌──────────────┐
    │model_backup  │ │ crypto.py    │
    │.py           │ │ (Fernet)     │
    └──────────────┘ └──────────────┘
```

---

## Contraintes

### Performances

- **Upload** : Les fichiers de backup peuvent atteindre 100+ MB. L'upload vers Google Drive utilise un timeout de 300 secondes et se fait dans un thread separe pour ne pas bloquer l'API.
- **Restauration** : Le `psql` a un timeout de 600 secondes (10 minutes). Pour les tres grosses bases, ca peut etre insuffisant.
- **Polling** : Le frontend poll toutes les 2 secondes. C'est acceptable pour 1-2 admins mais ne scale pas pour des centaines (pas un probleme ici, seul le super_admin utilise cette fonction).

### Limitations

- **Pas de backup incremental** : Chaque backup est un dump complet ("photocopie entiere du cahier"). Pas de diff entre deux backups.
- **Dependance au cron** : Si le cron `pg_dump` ne tourne pas, il n'y a aucun fichier a envoyer. L'API ne cree pas le dump elle-meme.
- **Single worker** : Si Gunicorn tourne avec 4 workers, le scheduler `auto_backup` pourrait declencher 4 fois. La verification `get_today_backup()` mitige ce risque mais une race condition reste theoriquement possible.
- **Pas de notification** : En cas d'echec du backup, l'admin doit consulter l'historique. Pas de notification push ni email.

### Securite

- Les tokens Google sont chiffres Fernet (AES-128-CBC) au repos
- Le state OAuth est signe HMAC-SHA256 (protection CSRF)
- La restauration exige une confirmation explicite ("RESTAURER")
- Tous les endpoints verifient `can_manage_backups`
- Le callback OAuth ne necessite pas de JWT (redirect navigateur), mais verifie le state signe

---

## Exemples d'utilisation

### Scenario 1 : Premier setup complet

```
1. L'admin va dans Settings > Administration > Privileges
2. Il active "can_manage_backups" pour son compte
3. Il va dans Settings > Administration > Sauvegardes
4. Il clique "Connecter Google Drive"
5. Il autorise l'application sur Google
6. Il revient sur l'app → "Connecte (admin@audace.ovh)"
7. Il renseigne le nom du dossier Drive et active le backup auto
8. Il clique "Sauvegarder" pour tester
9. La barre de progression avance → "Backup reussi !"
10. Il verifie dans son Google Drive → le fichier est la
```

### Scenario 2 : Restauration apres un probleme

```
1. Un bug a corrompu des donnees en base
2. L'admin va dans Sauvegardes > Historique
3. Il identifie le backup d'avant le bug (hier soir)
4. Il clique "Restaurer" sur ce backup
5. Il tape "RESTAURER" dans le dialog de confirmation
6. La progression s'affiche : telechargement... decompression... restauration...
7. "Restauration terminee !"
8. L'admin verifie que les donnees sont correctes
```

### Scenario 3 : Token Google expire

```
1. L'admin declenche un backup
2. En arriere-plan, ensure_valid_token() detecte que le token expire dans 2 min
3. Il appelle Google avec le refresh_token pour obtenir un nouveau access_token
4. Il stocke le nouveau token chiffre en base
5. Il continue le backup avec le nouveau token
→ L'admin ne voit rien, tout se passe en transparence
```

---

## Depannage

### "Google Drive non connecte"

**Cause** : Le super_admin n'a pas encore connecte Google Drive.
**Solution** : Cliquer sur "Connecter Google Drive" et suivre le flux OAuth.

### "Permission 'can_manage_backups' requise"

**Cause** : L'utilisateur n'a pas la permission de gerer les backups.
**Solution** : Un super_admin doit activer cette permission dans Privileges.

### "Aucun fichier de backup trouve dans /backups"

**Cause** : Le cron `pg_dump` n'a pas genere de fichier, ou le volume Docker n'est pas monte.
**Solutions** :
- Verifier que le cron tourne sur le serveur : `crontab -l | grep pg_dump`
- Verifier le volume Docker : `docker exec -it audace_api ls /backups/`
- Lancer manuellement : `pg_dump --clean --if-exists -U postgres audace_db | gzip > /backups/dump_$(date +%Y-%m-%d).sql.gz`

### "Aucun fichier de backup trouve" lors de restore/upload

**Cause** : Le fichier uploade n'est pas au format `.sql.gz`, ou depasse la limite de 500 Mo.
**Solution** : Verifier que le fichier est bien un dump PostgreSQL compresse avec gzip.

### "Token Google invalide ou expire"

**Cause** : Le refresh_token a ete revoque (l'admin a retire l'acces dans Google Account).
**Solution** : Deconnecter et reconnecter Google Drive depuis l'interface.

### "psql erreur" lors de la restauration

**Cause** : Le fichier de backup est corrompu, ou PostgreSQL rejette certaines commandes.
**Solutions** :
- Verifier les logs du conteneur : `docker logs audace_api --tail 100`
- Tester manuellement : `gunzip -c /backups/dump.sql.gz | head -20`
- Verifier que les variables d'environnement DB sont correctes

### Alembic "overlaps with other requested revisions" apres restauration

**Cause** : La table `alembic_version` contient 2 lignes au lieu d'une. Cela arrive quand une restauration est faite sans vider le schema (bug corrige en v0.22.0).
**Diagnostic** :
```bash
docker exec -i audace_db psql -U audace_user -d audace_db -c "SELECT * FROM alembic_version;"
# Si 2 lignes → c'est le probleme
```
**Solution** :
1. Identifier quelle version correspond au vrai etat de la base (celle du backup restaure)
2. Supprimer l'autre : `DELETE FROM alembic_version WHERE version_num = '<ancienne_ou_fausse>';`
3. Si les colonnes manquent (ex: `two_factor_enabled does not exist`), remettre la version au niveau du backup : `UPDATE alembic_version SET version_num = '<version_du_backup>';`
4. Redemarrer le container : `docker restart audace_api` (Alembic appliquera les migrations manquantes)

> **Depuis v0.22.0** : ce probleme ne peut plus se reproduire. La restauration fait `DROP SCHEMA CASCADE` avant d'injecter le dump, garantissant une seule ligne dans `alembic_version`.

### Le backup reste "en cours" indefiniment

**Cause** : Le thread daemon s'est arrete sans mettre a jour le statut (crash, OOM, etc).
**Solution** : Le statut en base est toujours "running" — il faut le passer a "failed" manuellement en base si necessaire.

---

## Variables d'environnement requises

| Variable | Description | Ou la configurer |
|----------|-------------|------------------|
| `GOOGLE_CLIENT_ID` | ID client OAuth Google | Google Cloud Console + `.env` + `docker-compose.yml` |
| `GOOGLE_CLIENT_SECRET` | Secret client OAuth Google | Google Cloud Console + `.env` + `docker-compose.yml` |
| `TOTP_ENCRYPTION_KEY` | Cle Fernet pour chiffrer les tokens | Deja en place (reutilisee du 2FA) |
| `FRONTEND_URL` | URL du frontend pour le redirect OAuth | Deja en place |
| `DATABASE_*` | Connexion PostgreSQL (pour la restauration) | Deja en place |

---

## Historique

| Version | Date | Description |
|---------|------|-------------|
| 0.21.0 | 2026-03-16 | Creation du module Backup Management |
| 0.22.0 | 2026-03-16 | Selecteur dossiers Drive, restauration par upload, fix restore (DROP SCHEMA + resync sequences) |

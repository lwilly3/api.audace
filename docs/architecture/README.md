# 🏗️ Architecture de l'API Audace

Documentation complète de l'architecture pour comprendre, développer et maintenir l'API.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure du projet](#structure-du-projet)
3. [Technologies utilisées](#technologies-utilisées)
4. [Modèles de données](#modèles-de-données)
5. [Architecture des couches](#architecture-des-couches)
6. [Flux de données](#flux-de-données)
7. [Sécurité et authentification](#sécurité-et-authentification)
8. [**Variables d'environnement** 🆕](ENVIRONMENT_VARIABLES.md)

---

## 🎯 Vue d'ensemble

**API Audace** est une API REST construite avec FastAPI pour gérer les émissions de radio, les présentateurs, les invités et les segments.

### Caractéristiques principales :
- 🔐 Authentification JWT
- 👥 Gestion des utilisateurs et permissions
- 📻 Gestion des émissions (shows)
- 🎤 Gestion des présentateurs et invités
- 📊 Tableaux de bord et statistiques
- 🔍 Recherche avancée
- 📝 Audit logging

---

## 📁 Structure du projet

```
api.audace/
├── app/                          # Code principal de l'application
│   ├── config/                   # Configuration
│   │   └── config.py            # Variables d'environnement (Pydantic)
│   ├── db/                      # Base de données
│   │   ├── database.py          # Connexion SQLAlchemy
│   │   ├── init_db_rolePermissions.py  # Init des rôles (commenté)
│   │   └── crud/                # Opérations CRUD
│   │       ├── crud_user.py
│   │       ├── crud_show.py
│   │       ├── crud_presenters.py
│   │       ├── crud_guests.py
│   │       ├── crud_emission.py
│   │       └── ...
│   ├── models/                  # Modèles SQLAlchemy (ORM)
│   │   ├── base_model.py        # Modèle de base (id, timestamps)
│   │   ├── model_user.py
│   │   ├── model_show.py
│   │   ├── model_presenter.py
│   │   ├── model_guest.py
│   │   ├── model_emission.py
│   │   ├── model_segment.py
│   │   ├── model_role.py
│   │   ├── model_permission.py
│   │   └── ...
│   ├── schemas/                 # Schémas Pydantic (validation)
│   │   ├── schema_user.py
│   │   ├── schema_show.py
│   │   ├── schema_presenter.py
│   │   └── ...
│   ├── utils/                   # Utilitaires
│   │   ├── oauth2.py            # JWT et authentification
│   │   └── utils.py             # Hash passwords, etc.
│   ├── exceptions/              # Exceptions personnalisées
│   │   └── guest_exceptions.py
│   └── middleware/              # Middlewares
│       └── logger.py            # Logger des requêtes
├── routeur/                     # Routes API (endpoints)
│   ├── auth.py                  # /auth/* (signup, login, reset)
│   ├── users_route.py           # /users/*
│   ├── show_route.py            # /shows/*
│   ├── presenter_route.py       # /presenters/*
│   ├── guest_route.py           # /guests/*
│   ├── emission_route.py        # /emissions/*
│   ├── segment_route.py         # /segments/*
│   ├── role_route.py            # /roles/*
│   ├── permissions_route.py     # /permissions/*
│   ├── dashbord_route.py        # /dashboard/*
│   ├── notification_route.py    # /notifications/*
│   ├── audit_log_route.py       # /audit-logs/*
│   └── search_route/            # /search/*
│       ├── search_show.py
│       ├── search_user_route.py
│       └── ...
├── core/                        # Logique métier (anciennes routes)
│   └── auth/
├── alembic/                     # Migrations de base de données
│   ├── env.py
│   └── versions/                # Fichiers de migration
├── scripts/                     # Scripts utilitaires
│   ├── backup_db.sh             # Sauvegarde PostgreSQL
│   ├── restore_db.sh            # Restauration
│   └── cleanup_docker.sh        # Nettoyage Docker
├── tests/                       # Tests unitaires et d'intégration
│   ├── conftest.py              # Configuration pytest
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_shows.py
│   └── ...
├── docs/                        # Documentation
│   ├── architecture/            # Architecture (ce dossier)
│   └── docker/                  # Documentation Docker
├── backups/                     # Dossier de sauvegarde
├── maintest.py                  # Point d'entrée de l'API
├── docker-compose.yml           # Configuration Docker
├── Dockerfile                   # Image Docker
├── requirements.txt             # Dépendances Python
├── alembic.ini                  # Configuration Alembic
└── pytest.ini                   # Configuration pytest
```

---

## 🛠️ Technologies utilisées

### Backend
| Technologie | Version | Usage |
|-------------|---------|-------|
| **Python** | 3.11 | Langage principal |
| **FastAPI** | 0.109.0 | Framework web ASGI |
| **Uvicorn** | 0.25.0 | Serveur ASGI |
| **Gunicorn** | 21.2.0 | Process manager (production) |

### Base de données
| Technologie | Version | Usage |
|-------------|---------|-------|
| **PostgreSQL** | 15-alpine | Base de données principale |
| **SQLAlchemy** | 2.0.27 | ORM |
| **Alembic** | 1.13.1 | Migrations |
| **psycopg2-binary** | 2.9.9 | Driver PostgreSQL |

### Sécurité
| Technologie | Version | Usage |
|-------------|---------|-------|
| **python-jose** | 3.3.0 | JWT tokens |
| **passlib** | 1.7.4 | Hash passwords |
| **bcrypt** | 4.2.1 | Algorithme de hashing |

### Validation
| Technologie | Version | Usage |
|-------------|---------|-------|
| **Pydantic** | 2.5.3 | Validation de données |
| **pydantic-settings** | 2.1.0 | Configuration |

### Infrastructure
| Technologie | Version | Usage |
|-------------|---------|-------|
| **Docker** | 24+ | Conteneurisation |
| **Docker Compose** | 3.8 | Orchestration |
| **Traefik** | 3.6.1 | Reverse proxy / SSL |
| **Dokploy** | Latest | Plateforme de déploiement |

---

## 📊 Modèles de données

### Modèle de base

Tous les modèles héritent de `BaseModel` :

```python
class BaseModel:
    id: int (Primary Key, Auto-increment)
    created_at: datetime (Timestamp de création)
    updated_at: datetime (Timestamp de mise à jour)
    is_deleted: bool (Soft delete)
```

### Entités principales

#### 1. User (Utilisateur)
```python
User
├── id: int
├── email: str (unique)
├── password: str (hashed)
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    ├── permissions: List[UserPermission]
    ├── shows: List[Show] (créées)
    ├── emissions: List[Emission] (créées)
    └── presenters: List[Presenter] (créés)
```

#### 2. Show (Émission)
```python
Show
├── id: int
├── name: str
├── description: str
├── user_id: int (FK → User)
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    ├── user: User (créateur)
    ├── presenters: List[Presenter] (via show_presenters)
    └── emissions: List[Emission]
```

#### 3. Presenter (Présentateur)
```python
Presenter
├── id: int
├── name: str
├── user_id: int (FK → User)
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    ├── user: User (créateur)
    └── shows: List[Show] (via show_presenters)
```

#### 4. Guest (Invité)
```python
Guest
├── id: int
├── name: str
├── bio: str
├── contact_info: str
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    └── segments: List[Segment] (via segment_guests)
```

#### 5. Emission
```python
Emission
├── id: int
├── title: str
├── date: date
├── show_id: int (FK → Show)
├── user_id: int (FK → User)
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    ├── show: Show
    ├── user: User (créateur)
    └── segments: List[Segment]
```

#### 6. Segment
```python
Segment
├── id: int
├── title: str
├── description: str
├── start_time: time
├── end_time: time
├── emission_id: int (FK → Emission)
├── created_at: datetime
├── updated_at: datetime
├── is_deleted: bool
└── Relationships:
    ├── emission: Emission
    └── guests: List[Guest] (via segment_guests)
```

### Modèles de sécurité et gestion

#### 7. Permission
```python
Permission
├── id: int
├── name: str (ex: "create_show", "delete_user")
├── description: str
└── Relationships:
    └── user_permissions: List[UserPermission]
```

#### 8. UserPermission (Association)
```python
UserPermission
├── id: int
├── user_id: int (FK → User)
├── permission_id: int (FK → Permission)
├── granted: bool (activée ou non)
└── Relationships:
    ├── user: User
    └── permission: Permission
```

#### 9. Role & RoleTemplate
```python
Role / RoleTemplate
├── id: int
├── name: str
├── description: str
└── permissions: JSON (liste des permissions)
```

#### 10. InviteToken
```python
InviteToken
├── id: int
├── token: str (UUID)
├── email: str
├── expires_at: datetime
├── used: bool
└── created_at: datetime
```

#### 11. PasswordResetToken
```python
PasswordResetToken
├── id: int
├── token: str (UUID)
├── user_id: int (FK → User)
├── expires_at: datetime
├── used: bool
└── created_at: datetime
```

#### 12. RevokedToken
```python
RevokedToken
├── id: int
├── token: str (JWT token révoqué)
└── revoked_at: datetime
```

### Modèles d'audit

#### 13. AuditLog
```python
AuditLog
├── id: int
├── user_id: int
├── action: str (ex: "CREATE", "UPDATE", "DELETE")
├── entity_type: str (ex: "Show", "User")
├── entity_id: int
├── changes: JSON (détails des modifications)
└── timestamp: datetime
```

#### 14. ArchiveLogAudit
```python
ArchiveLogAudit
├── id: int
├── (copie des données d'AuditLog archivées)
└── archived_at: datetime
```

---

## 🏛️ Architecture des couches

L'API suit une **architecture en couches** (Layered Architecture) :

```
┌─────────────────────────────────────────┐
│         CLIENT (Frontend/Mobile)        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       PRESENTATION LAYER (Routes)       │
│  routeur/auth.py, users_route.py, etc. │
│  - Validation des requêtes              │
│  - Sérialisation des réponses           │
│  - Gestion des codes HTTP               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      BUSINESS LOGIC LAYER (CRUD)        │
│  app/db/crud/*.py                       │
│  - Logique métier                       │
│  - Règles de validation                 │
│  - Orchestration des opérations         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       DATA ACCESS LAYER (Models)        │
│  app/models/*.py                        │
│  - ORM SQLAlchemy                       │
│  - Relations entre entités              │
│  - Contraintes de base de données       │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        DATABASE (PostgreSQL)            │
│  - Stockage persistant                  │
│  - Transactions ACID                    │
│  - Indexation                           │
└─────────────────────────────────────────┘
```

### Responsabilités de chaque couche :

**1. Routes (Presentation Layer)**
- Définir les endpoints HTTP
- Valider les données d'entrée (Pydantic schemas)
- Gérer l'authentification JWT
- Retourner les réponses formatées
- Gérer les erreurs HTTP

**2. CRUD (Business Logic Layer)**
- Implémenter la logique métier
- Interagir avec la base de données
- Gérer les transactions
- Appliquer les règles de soft-delete
- Vérifier les permissions

**3. Models (Data Access Layer)**
- Définir la structure des tables
- Gérer les relations (FK, M2M)
- Définir les contraintes (unique, nullable)
- Timestamps automatiques

**4. Schemas (Validation Layer)**
- Valider les données entrantes
- Définir les types de retour
- Sérialiser les objets complexes
- Documentation automatique (OpenAPI)

---

## 🔄 Flux de données

### Exemple : Créer une émission

```
1. CLIENT
   POST /shows
   {
     "name": "Morning Show",
     "description": "...",
     "presenter_ids": [1, 2]
   }
        │
        ▼
2. ROUTE (show_route.py)
   @router.post("/")
   - Valide le schema ShowCreate
   - Vérifie le token JWT
   - Récupère current_user
        │
        ▼
3. CRUD (crud_show.py)
   create_show(db, show_data, user_id)
   - Crée le Show en DB
   - Associe les presenters (show_presenters)
   - Gère les transactions
        │
        ▼
4. MODEL (model_show.py)
   Show SQLAlchemy model
   - Insert dans la table "shows"
   - Génère id, timestamps
        │
        ▼
5. DATABASE (PostgreSQL)
   INSERT INTO shows ...
   - Stockage persistant
   - Commit transaction
        │
        ▼
6. RESPONSE
   {
     "id": 123,
     "name": "Morning Show",
     "created_at": "2025-12-11T10:00:00"
   }
```

---

## 🔐 Sécurité et authentification

### Flux d'authentification

```
1. SIGNUP (/auth/signup)
   - Hash password avec bcrypt
   - Créer User en DB
   - Retourner user_id

2. LOGIN (/auth/login)
   - Vérifier email existe
   - Vérifier password avec bcrypt
   - Générer JWT token (exp: 30min)
   - Retourner access_token

3. REQUÊTES PROTÉGÉES
   Header: Authorization: Bearer <token>
   - Décoder le JWT
   - Vérifier expiration
   - Vérifier que token pas révoqué
   - Récupérer user_id depuis token
   - Charger current_user depuis DB

4. LOGOUT (/auth/logout)
   - Ajouter token dans revoked_tokens
   - Token devient invalide
```

### Protection des routes

```python
# Route protégée
@router.get("/protected")
def protected_route(
    current_user: User = Depends(oauth2.get_current_user)
):
    # current_user disponible automatiquement
    return {"user_id": current_user.id}
```

### Système de permissions

```python
# Vérifier une permission spécifique
user_permission = db.query(UserPermission).filter_by(
    user_id=user.id,
    permission_id=permission_id
).first()

if not user_permission or not user_permission.granted:
    raise HTTPException(403, "Permission denied")
```

---

## 📝 Prochains documents

- [Modèles de données détaillés](DATA_MODELS.md)
- [Guide des endpoints API](API_ENDPOINTS.md)
- [Guide de développement](DEVELOPMENT_GUIDE.md)
- [Guide de contribution](CONTRIBUTION_GUIDE.md)

---

**Dernière mise à jour :** 11 décembre 2025

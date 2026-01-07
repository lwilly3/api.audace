# 📻 Audace - API de Gestion de Média Radio/TV

**Backend API REST pour la gestion collaborative des ressources et opérations d'un média radio ou télévision.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg?style=flat)](https://www.sqlalchemy.org)

---

## 🎯 Objectif du projet

**Audace** est une API backend complète conçue pour faciliter la **gestion collaborative** et l'**organisation des ressources** d'un média (radio ou télévision). Elle permet aux équipes de production de gérer efficacement :

- 📺 **Shows et émissions** - Planification et gestion du contenu
- 🎤 **Présentateurs** - Profils et assignations
- 👥 **Invités** - Base de données des participants
- 📋 **Segments** - Découpage et organisation des émissions
- 🔐 **Permissions** - Contrôle d'accès basé sur les rôles (RBAC)
- 📊 **Statistiques** - Tableaux de bord et rapports
- 🔔 **Notifications** - Alertes en temps réel
- 📝 **Audit** - Traçabilité complète des actions

---

## 🚀 Fonctionnalités principales

### 🔐 Authentification et Sécurité
- ✅ Authentification JWT (JSON Web Tokens)
- ✅ **Admin automatique** créé au premier démarrage (configurable)
- ✅ Système de permissions granulaires (RBAC)
- ✅ Gestion des rôles (Admin, Presenter, Editor, Viewer)
- ✅ Révocation de tokens (blacklist)
- ✅ Réinitialisation de mot de passe sécurisée
- ✅ Invitations d'utilisateurs par email
- ✅ Routes de diagnostic et configuration initiale

### 📺 Gestion des Émissions
- ✅ Création et gestion de shows
- ✅ Organisation en émissions (séries)
- ✅ Découpage en segments avec invités
- ✅ Workflow de validation (draft → published → archived)
- ✅ Import/export JSON de conducteurs
- ✅ Gestion des statuts et transitions

### 👥 Gestion des Ressources Humaines
- ✅ Profils des présentateurs
- ✅ Base de données des invités
- ✅ Historique des participations
- ✅ Gestion des contacts et biographies
- ✅ Statistiques d'activité

### 🔧 Outils Collaboratifs
- ✅ Notifications en temps réel
- ✅ Journalisation des actions (audit logs)
- ✅ Recherche globale multi-critères
- ✅ Tableau de bord avec KPIs
- ✅ Exports et rapports

### 🛡️ Fiabilité et Traçabilité
- ✅ Soft delete (suppression logique)
- ✅ Historique complet des modifications
- ✅ Logs d'audit avec archivage
- ✅ Gestion des erreurs complète
- ✅ Validation des données avec Pydantic

---

## 🏗️ Architecture technique

### Stack Technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Framework** | FastAPI | 0.109.0 |
| **Langage** | Python | 3.11+ |
| **Base de données** | PostgreSQL | 15 |
| **ORM** | SQLAlchemy | 2.0 |
| **Validation** | Pydantic | v2 |
| **Authentification** | JWT (python-jose) | - |
| **Migrations** | Alembic | - |
| **Tests** | Pytest | - |
| **Déploiement** | Docker / Gunicorn | - |

### Structure du projet

```
api.audace/
├── app/                          # Code source principal
│   ├── config/                   # Configuration de l'application
│   ├── db/                       # Base de données
│   │   └── crud/                 # Opérations CRUD (27 fichiers)
│   ├── models/                   # Modèles SQLAlchemy (15 modèles)
│   ├── schemas/                  # Schémas Pydantic de validation
│   ├── utils/                    # Utilitaires
│   ├── middleware/               # Middlewares (logging, etc.)
│   └── exceptions/               # Gestions d'exceptions personnalisées
│
├── core/                         # Logique métier core
│   └── auth/                     # Authentification (JWT, OAuth2)
│
├── routeur/                      # Routes API (14 modules)
│   ├── auth.py                   # Authentification
│   ├── users_route.py            # Gestion des utilisateurs
│   ├── show_route.py             # Gestion des shows
│   ├── presenter_route.py        # Gestion des présentateurs
│   ├── guest_route.py            # Gestion des invités
│   ├── emission_route.py         # Gestion des émissions
│   ├── segment_route.py          # Gestion des segments
│   ├── role_route.py             # Gestion des rôles
│   ├── permissions_route.py      # Gestion des permissions
│   ├── notification_route.py     # Notifications
│   ├── audit_log_route.py        # Logs d'audit
│   ├── dashbord_route.py         # Tableau de bord
│   └── search_route/             # Recherche globale
│
├── alembic/                      # Migrations de base de données
│   └── versions/                 # Historique des migrations
│
├── tests/                        # Tests unitaires et d'intégration
├── scripts/                      # Scripts utilitaires
├── docs/                         # Documentation complète
│   ├── architecture/             # Documentation architecture
│   └── business-logic/           # Documentation logique métier
│
├── docker-compose.yml            # Configuration Docker
├── Dockerfile                    # Image Docker
├── requirements.txt              # Dépendances Python
├── alembic.ini                   # Configuration Alembic
├── pytest.ini                    # Configuration des tests
└── README.md                     # Ce fichier
```

---

## 📦 Installation et démarrage

### Prérequis

- Python 3.11+
- PostgreSQL 15+
- pip (gestionnaire de paquets Python)
- Docker (optionnel, recommandé)

### 🔐 Première connexion

**Un utilisateur admin est créé automatiquement au premier démarrage !**

Credentials par défaut :
- **Username**: `admin`
- **Password**: `Admin@2024!`
- **Email**: `admin@audace.local`

⚠️ **IMPORTANT** : Changez ces credentials immédiatement après la première connexion en production !

➡️ **Guide complet** : [FIRST_LOGIN.md](FIRST_LOGIN.md)

### Installation avec Docker (Recommandé)

```bash
# Cloner le repository
git clone https://github.com/lwilly3/api.audace.git
cd api.audace

# Lancer avec Docker Compose
docker-compose up -d

# L'API sera disponible sur http://localhost:8000
```

### Installation manuelle

```bash
# 1. Cloner le repository
git clone https://github.com/lwilly3/api.audace.git
cd api.audace

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres (DATABASE_URL, SECRET_KEY, etc.)

# 5. Créer la base de données
createdb audace_db

# 6. Exécuter les migrations
alembic upgrade head

# 7. Démarrer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Accès à l'API

- **API** : http://localhost:8000
- **Documentation interactive (Swagger)** : http://localhost:8000/docs
- **Documentation alternative (ReDoc)** : http://localhost:8000/redoc

---

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/audace_db

# Sécurité
SECRET_KEY=votre_clé_secrète_très_longue_et_sécurisée
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
APP_NAME=Audace API
APP_VERSION=1.0.0
DEBUG=False

# Email (pour reset password et invitations)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre_email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe

# CORS (si frontend séparé)
CORS_ORIGINS=http://localhost:3000,http://localhost:4200
```

---

## 📚 Documentation

### Documentation complète disponible

La documentation exhaustive est disponible dans le dossier `docs/` :

- **[docs/README.md](docs/README.md)** - Point d'entrée de la documentation
- **[docs/INDEX.md](docs/INDEX.md)** - Index complet de toute la documentation
- **[docs/architecture/](docs/architecture/)** - Documentation de l'architecture
- **[docs/business-logic/](docs/business-logic/)** - Documentation de la logique métier

### Guides rapides

| Guide | Description | Lien |
|-------|-------------|------|
| 🚀 Démarrage rapide | Guide pour nouveaux développeurs | [QUICKSTART.md](docs/business-logic/QUICKSTART.md) |
| 🏗️ Architecture | Vue d'ensemble de l'architecture | [architecture/README.md](docs/architecture/README.md) |
| 📊 Modèles de données | Tous les modèles (15) | [DATA_MODELS.md](docs/architecture/DATA_MODELS.md) |
| 🔌 Endpoints API | Tous les endpoints (70+) | [API_ENDPOINTS.md](docs/architecture/API_ENDPOINTS.md) |
| 💼 Logique métier | Documentation par module (12 fichiers) | [business-logic/](docs/business-logic/) |
| � **Gestion permissions** | **Ajouter/supprimer permissions (13 étapes)** | **[PERMISSIONS_MANAGEMENT_GUIDE.md](docs/PERMISSIONS_MANAGEMENT_GUIDE.md)** |
| 🐳 Docker | Déploiement et migrations | [DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md) |
| 📝 Traçabilité | Historique et changelog | [CHANGELOG.md](CHANGELOG.md) • [TRACEABILITY_GUIDE.md](docs/TRACEABILITY_GUIDE.md) |
| 🔐 Permissions Citations | Module Citations + Firebase | [QUOTES_PERMISSIONS.md](QUOTES_PERMISSIONS.md) |
| 🔄 Versioning API | Gestion des versions | [API_VERSIONING.md](docs/API_VERSIONING.md) |
| 🤖 Guide Agent IA | Pour agents IA et assistants | [AGENT.md](AGENT.md) |

### Documentation API interactive

Après démarrage du serveur :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests d'un module spécifique
pytest tests/test_users.py

# Tests en mode verbose
pytest -v
```

### Tests disponibles

- ✅ Tests d'authentification
- ✅ Tests des utilisateurs
- ✅ Tests des shows et émissions
- ✅ Tests des présentateurs
- ✅ Tests des invités
- ✅ Tests des permissions
- ✅ Tests des rôles
- ✅ Tests des notifications
- ✅ Tests de recherche
- ✅ Tests du dashboard

---

## 📊 Modèles de données

### 15 modèles principaux

| Modèle | Description | Relations |
|--------|-------------|-----------|
| **User** | Utilisateurs du système | → UserPermission, UserRole |
| **UserPermission** | Permissions granulaires | ← User |
| **Role** | Rôles (Admin, Presenter, etc.) | ← → User |
| **Presenter** | Profils des présentateurs | ← User, → Show |
| **Guest** | Invités des émissions | → Segment |
| **Emission** | Séries d'émissions | → Show |
| **Show** | Épisodes spécifiques | ← Emission, → Segment, → Presenter |
| **Segment** | Parties d'un show | ← Show, → Guest |
| **Notification** | Alertes utilisateurs | ← User |
| **AuditLog** | Journalisation active | ← User |
| **ArchivedAuditLog** | Journalisation archivée | - |
| **RevokedToken** | Tokens révoqués | - |
| **PasswordResetToken** | Tokens de reset | ← User |
| **InviteToken** | Tokens d'invitation | ← User |

➡️ **Voir la documentation complète** : [docs/architecture/DATA_MODELS.md](docs/architecture/DATA_MODELS.md)

---

## 🔌 Endpoints API

### Routes principales

| Catégorie | Prefix | Routes | Description |
|-----------|--------|--------|-------------|
| 🔐 Authentification | `/auth` | 6 | Login, logout, reset password |
| 👤 Utilisateurs | `/users` | 12 | CRUD utilisateurs + permissions |
| 📺 Shows | `/shows` | 15 | Gestion des shows et émissions |
| 🎤 Présentateurs | `/presenters` | 8 | Gestion des présentateurs |
| 👥 Invités | `/guests` | 7 | Gestion des invités |
| 📋 Segments | `/segments` | 8 | Gestion des segments |
| 📻 Émissions | `/emissions` | 6 | Gestion des séries |
| 🔐 Permissions | `/permissions` | 5 | Gestion des permissions |
| 👔 Rôles | `/roles` | 6 | Gestion des rôles |
| 🔔 Notifications | `/notifications` | 5 | Notifications utilisateurs |
| 📝 Audit | `/audit-logs` | 4 | Logs d'audit |
| 🔍 Recherche | `/search` | 5 | Recherche globale |
| 📊 Dashboard | `/dashboard` | 1 | Statistiques |

**Total : 70+ endpoints documentés**

➡️ **Voir la documentation complète** : [docs/architecture/API_ENDPOINTS.md](docs/architecture/API_ENDPOINTS.md)

---

## 🔐 Authentification

### Workflow d'authentification

```python
# 1. Login
POST /auth/login
{
  "username": "admin",
  "password": "password"
}

# Réponse
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 2. Utiliser le token dans les requêtes
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Rôles et permissions

| Rôle | Description | Permissions |
|------|-------------|-------------|
| **Admin** | Administrateur système | Toutes les permissions |
| **Editor** | Éditeur de contenu | Gestion de tous les contenus |
| **Presenter** | Présentateur/Animateur | Gestion de ses shows |
| **Viewer** | Lecture seule | Consultation uniquement |

➡️ **Voir la documentation complète** : [docs/business-logic/PERMISSIONS.md](docs/business-logic/PERMISSIONS.md)

---

## 🛠️ Scripts utilitaires

### Sauvegarde de la base de données

```bash
# Sauvegarde
./scripts/backup_db.sh

# Restauration
./scripts/restore_db.sh backup_file.sql
```

### Nettoyage Docker

```bash
./scripts/cleanup_docker.sh
```

### Mise à jour des modèles

```bash
python scripts/update_models_script.py
```

---

## 🚀 Déploiement

### Déploiement avec Gunicorn

```bash
# Production avec Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

### Configuration Systemd

Voir le fichier `gunicorn.service` pour la configuration systemd.

### Déploiement avec Docker

```bash
# Build de l'image
docker build -t audace-api .

# Lancer le conteneur
docker run -d \
  --name audace-api \
  -p 8000:8000 \
  --env-file .env \
  audace-api
```

---

## 🤝 Contribution

### Workflow de contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Standards de code

- ✅ Suivre PEP 8 (style Python)
- ✅ Ajouter des docstrings
- ✅ Écrire des tests
- ✅ Mettre à jour la documentation
- ✅ Vérifier les permissions requises
- ✅ Ajouter des audit logs

➡️ **Voir le guide complet** : [docs/architecture/CONTRIBUTION_GUIDE.md](docs/architecture/CONTRIBUTION_GUIDE.md)

---

## 📈 Roadmap

### Version actuelle : v1.0 (Décembre 2024)

- ✅ API REST complète
- ✅ Authentification JWT
- ✅ Système de permissions RBAC
- ✅ Gestion des shows et émissions
- ✅ Gestion des présentateurs et invités
- ✅ Notifications
- ✅ Audit logs
- ✅ Dashboard et statistiques
- ✅ Documentation exhaustive

### Prochaines fonctionnalités (v1.1)

- 🔄 WebSockets pour notifications en temps réel
- 🔄 API GraphQL (en complément de REST)
- 🔄 Export PDF des conducteurs
- 🔄 Intégration calendrier (Google Calendar, Outlook)
- 🔄 Gestion des fichiers média (upload audio/vidéo)
- 🔄 Module de facturation
- 🔄 Statistiques avancées (analytics)

---

## 📞 Support et Contact

### Documentation
- 📚 [Documentation complète](docs/README.md)
- 🚀 [Guide de démarrage rapide](docs/business-logic/QUICKSTART.md)
- 🏗️ [Architecture](docs/architecture/README.md)

### Issues et bugs
- GitHub Issues : https://github.com/lwilly3/api.audace/issues

### Développeur principal
- **Lwilly3** - [GitHub](https://github.com/lwilly3)

---

## 📄 Licence

Ce projet est sous licence privée. Tous droits réservés.

---

## 🙏 Remerciements

Merci à tous les contributeurs et aux utilisateurs de cette API.

Technologies utilisées :
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderne pour Python
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [PostgreSQL](https://www.postgresql.org/) - Base de données
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Validation de données
- [Alembic](https://alembic.sqlalchemy.org/) - Migrations de base de données

---

<div align="center">

**Audace API** - Gestion collaborative de média radio/TV

Fait avec ❤️ par l'équipe Audace

[Documentation](docs/README.md) • [API Docs](http://localhost:8000/docs) • [Issues](https://github.com/lwilly3/api.audace/issues)

</div>

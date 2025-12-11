# 📚 Documentation Logique Métier - Index

Bienvenue dans la documentation complète de la logique métier de l'API Audace.

---

## 📂 Organisation

Cette documentation est organisée en modules métier, chacun dans un fichier dédié :

### 🔐 Authentification et Sécurité
- **[AUTH.md](AUTH.md)** ✅ - Gestion de l'authentification, tokens JWT, reset password, invite tokens
- **[PERMISSIONS.md](PERMISSIONS.md)** ✅ - Système de permissions RBAC et contrôle d'accès granulaire
- **[ROLES.md](ROLES.md)** ✅ - Gestion des rôles (Admin, Presenter, Editor, Viewer)

### 👥 Gestion des Entités
- **[USERS.md](USERS.md)** ✅ - Gestion des utilisateurs (CRUD, permissions, login history, audit)
- **[PRESENTERS.md](PRESENTERS.md)** ✅ - Gestion des présentateurs (profils, association users, shows)
- **[GUESTS.md](GUESTS.md)** ✅ - Gestion des invités (participants, statistiques d'apparition)
- **[SHOWS.md](SHOWS.md)** ✅ - Gestion des shows (création JSON complexe, statuts, workflow)
- **[EMISSIONS.md](EMISSIONS.md)** ✅ - Gestion des séries d'émissions (CRUD, archivage)
- **[SEGMENTS.md](SEGMENTS.md)** ✅ - Gestion des segments (positions, invités par segment)

### 🔧 Fonctionnalités Transverses
- **[NOTIFICATIONS.md](NOTIFICATIONS.md)** ✅ - Système de notifications utilisateurs (lu/non lu)
- **[AUDIT.md](AUDIT.md)** ✅ - Logs d'audit et traçabilité (logs actifs/archivés)
- **[UTILITIES.md](UTILITIES.md)** ✅ - Recherche globale et tableau de bord avec statistiques

---

## 🎯 Structure de chaque document

Chaque fichier de documentation contient :

### 1. Vue d'ensemble
- Description du module
- Responsabilités
- Dépendances

### 2. Architecture
- Modèles de données utilisés
- Relations avec autres modules
- Flux de données

### 3. Fonctions métier
- Signature complète
- Paramètres et types
- Valeur de retour
- Logique métier détaillée
- Contraintes et validations
- Gestion des erreurs

### 4. Règles métier
- Contraintes d'intégrité
- Validations
- Règles de soft delete
- Permissions requises

### 5. Exemples d'utilisation
- Cas d'usage courants
- Code d'exemple
- Scénarios complexes

### 6. Relations
- Dépendances entrantes
- Dépendances sortantes
- Impact des modifications

### 7. Contraintes techniques
- Performances
- Limitations
- Optimisations possibles

---

## 🔄 Flux de données globaux

### Flux d'authentification
```
User → auth.py → crud_auth.py → JWT Token → oauth2.py → Protected Routes
```

### Flux de création d'entité
```
Route → Schema Validation → CRUD Function → Model → Database
                                ↓
                          Audit Log Creation
                                ↓
                          Permission Check
```

### Flux de soft delete
```
Delete Request → Permission Check → Set is_deleted=True → Audit Log → Response
```

---

## 📊 Diagramme de dépendances

```
┌─────────────────────────────────────────────────────────────┐
│                      API Routes Layer                        │
│  auth.py | users_route.py | show_route.py | ...             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ crud_users   │  │ crud_show    │  │ crud_guests  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ crud_auth    │  │ crud_perms   │  │ crud_audit   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Models Layer                           │
│  User | Show | Presenter | Guest | Permission | AuditLog    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Index des fonctions par module

### USERS (15 fonctions)
- `get_non_presenters()` - Liste utilisateurs non-présentateurs
- `get_user_or_404()` - Récupération avec gestion d'erreur
- `get_user_or_404_with_permissions()` - Récupération avec permissions
- `get_all_users()` - Liste complète
- `create_user()` - Création
- `update_user()` - Mise à jour
- `delete_user()` - Soft delete
- `get_user_logins()` - Historique connexions
- `get_user_notifications()` - Notifications
- `get_user_audit_logs()` - Logs d'audit
- `archive_audit_log()` - Archivage
- `add_permission_to_role()` - Association permission/rôle
- `create_role()` - Création de rôle
- `create_guest()` - Création d'invité (legacy)

### SHOWS (12 fonctions)
- `update_show_status()` - Mise à jour statut
- `create_show_with_elements_from_json()` - Création complète depuis JSON
- `get_show_details_all()` - Liste détaillée avec relations
- `create_show()` - Création simple
- `get_show()` - Récupération par ID
- `get_shows()` - Liste avec pagination
- `update_show()` - Mise à jour
- `delete_show()` - Soft delete
- `get_show_with_segments()` - Show avec segments
- `get_show_with_presenters()` - Show avec présentateurs

### PRESENTERS (8 fonctions)
- `create_presenter()` - Création avec validations
- `get_presenter()` - Récupération avec user associé
- `get_presenters()` - Liste paginée
- `update_presenter()` - Mise à jour
- `delete_presenter()` - Soft delete
- `search_presenters()` - Recherche par nom
- `get_presenter_shows()` - Shows d'un présentateur

### PERMISSIONS (20+ fonctions)
- `check_permissions()` - Vérification middleware
- `get_user_permissions()` - Récupération permissions user
- `initialize_user_permissions()` - Initialisation par défaut
- `update_user_permissions()` - Mise à jour permissions
- `get_all_permissions()` - Liste complète
- `get_permission()` - Récupération par ID
- `get_all_roles()` - Liste des rôles
- `get_role()` - Rôle par ID
- `create_role()` - Création de rôle
- `update_role()` - Mise à jour de rôle
- `delete_role()` - Suppression de rôle
- `get_role_permissions()` - Permissions d'un rôle

---

## 🎨 Conventions de nommage

### Fonctions CRUD
- `create_*()` - Création
- `get_*()` - Récupération (un ou plusieurs)
- `get_all_*()` - Liste complète
- `update_*()` - Mise à jour
- `delete_*()` - Soft delete
- `destroy_*()` - Suppression physique (rare)

### Fonctions de recherche
- `search_*()` - Recherche par critères
- `filter_*()` - Filtrage avancé

### Fonctions de validation
- `check_*()` - Vérification
- `validate_*()` - Validation
- `verify_*()` - Vérification (auth)

### Fonctions d'association
- `add_*_to_*()` - Association Many-to-Many
- `remove_*_from_*()` - Dissociation

---

## 📝 Règles métier globales

### 1. Soft Delete Universel
Toutes les entités utilisent le soft delete :
- Champ `is_deleted` mis à `True`
- Champ `deleted_at` avec timestamp
- Les données ne sont jamais supprimées physiquement

### 2. Audit Systématique
Toutes les actions importantes sont loguées :
- Création : `action="CREATE"`
- Modification : `action="UPDATE"` avec changements
- Suppression : `action="DELETE"`

### 3. Permissions Obligatoires
Routes protégées nécessitent :
- Token JWT valide
- Permission spécifique activée
- Utilisateur actif (`is_active=True`)

### 4. Validation Pydantic
Toutes les données entrantes passent par :
- Schémas Pydantic pour validation
- Type checking automatique
- Contraintes de format

### 5. Relations Préservées
Lors d'un soft delete :
- Relations Many-to-Many préservées
- Foreign keys restent valides
- Filtrage automatique dans les queries

---

## 🔗 Relations inter-modules

### Module USERS dépend de :
- `crud_permissions` - Initialisation permissions
- `crud_audit_logs` - Logging actions
- `utils.hash` - Hash passwords

### Module SHOWS dépend de :
- `crud_presenters` - Association présentateurs
- `crud_segments` - Gestion segments
- `crud_guests` - Association invités (via segments)
- `crud_audit_logs` - Logging

### Module PERMISSIONS dépend de :
- `crud_users` - Vérification utilisateur
- `crud_roles` - Gestion rôles
- `oauth2` - Authentification

### Module AUDIT dépend de :
- Tous les modules (logging universel)

---

## 🚀 Performances

### Optimisations appliquées
- `joinedload()` pour eager loading des relations
- `selectinload()` pour collections
- Index sur colonnes de recherche fréquente
- Pagination par défaut

### Points d'attention
- Éviter les N+1 queries
- Utiliser `options()` pour charger relations
- Limiter les `.all()` sans pagination
- Fermer les sessions explicitement

---

## 🛡️ Sécurité

### Authentification
- JWT avec expiration (30 min par défaut)
- Tokens révoqués en base
- Vérification à chaque requête

### Autorisation
- Permissions granulaires par entité
- Vérification avant chaque action
- Logs de toutes les tentatives

### Validation
- Schémas Pydantic stricts
- Validation des emails
- Contraintes de longueur

---

## 📖 Comment utiliser cette documentation

### Pour un nouveau développeur
1. Commencer par [USERS.md](USERS.md) et [AUTH.md](AUTH.md)
2. Comprendre le système de [PERMISSIONS.md](PERMISSIONS.md)
3. Explorer les modules métier selon les besoins

### Pour ajouter une fonctionnalité
1. Identifier le module concerné
2. Lire les règles métier et contraintes
3. Suivre les patterns existants
4. Ajouter les logs d'audit

### Pour déboguer
1. Vérifier les logs d'audit
2. Consulter les contraintes du module
3. Vérifier les relations avec autres modules
4. Tester les permissions

---

## 🔄 Maintenance

### Mise à jour de la documentation
Lors de l'ajout/modification de fonctions :
1. Mettre à jour le fichier module concerné
2. Mettre à jour cet index si nouveau module
3. Mettre à jour les diagrammes de relations
4. Ajouter des exemples d'utilisation

### Versioning
Cette documentation suit la version de l'API :
- Version actuelle : **1.0.0**
- Dernière mise à jour : **11 décembre 2025**

---

**Navigation rapide :**
- [AUTH.md](AUTH.md) - Authentification
- [USERS.md](USERS.md) - Utilisateurs
- [SHOWS.md](SHOWS.md) - Shows
- [PERMISSIONS.md](PERMISSIONS.md) - Permissions

**Documentation générale :**
- [Architecture](../architecture/README.md)
- [Endpoints API](../architecture/API_ENDPOINTS.md)
- [Guide de développement](../architecture/DEVELOPMENT_GUIDE.md)

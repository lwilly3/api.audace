# 📚 Documentation Complète de l'API Audace

Bienvenue dans la documentation complète de l'API Audace Radio Management System.

---

## 🗂️ Organisation de la documentation

### 1. 🏗️ [Architecture](architecture/)
Documentation de l'architecture générale de l'application.

**Fichiers disponibles :**
- **[README.md](architecture/README.md)** - Vue d'ensemble de l'architecture
- **[DATA_MODELS.md](architecture/DATA_MODELS.md)** - Tous les modèles de données (15 modèles)
- **[API_ENDPOINTS.md](architecture/API_ENDPOINTS.md)** - Tous les endpoints API (70+)
- **[DEVELOPMENT_GUIDE.md](architecture/DEVELOPMENT_GUIDE.md)** - Guide de développement
- **[CONTRIBUTION_GUIDE.md](architecture/CONTRIBUTION_GUIDE.md)** - Guide de contribution
- **[FUNCTIONS_REFERENCE.md](architecture/FUNCTIONS_REFERENCE.md)** - Référence alphabétique (80+ fonctions)
- **[ENVIRONMENT_VARIABLES.md](architecture/ENVIRONMENT_VARIABLES.md)** 🆕 - Variables d'environnement et configuration

**Utilisez cette section pour :**
- Comprendre la structure globale du projet
- Voir tous les endpoints disponibles
- Consulter les modèles de données
- Démarrer le développement local

---

### 2. 💼 [Business Logic](business-logic/)
Documentation détaillée de la logique métier par module.

**Fichiers disponibles :**

#### 🚀 Démarrage
- **[README.md](business-logic/README.md)** - Index de la documentation métier
- **[QUICKSTART.md](business-logic/QUICKSTART.md)** - Guide de démarrage rapide
- **[SUMMARY.md](business-logic/SUMMARY.md)** - Récapitulatif complet de livraison

#### 🔐 Authentification & Sécurité
- **[AUTH.md](business-logic/AUTH.md)** - JWT, reset password, invite tokens (6 fonctions)
- **[PERMISSIONS.md](business-logic/PERMISSIONS.md)** - RBAC complet (7 fonctions, 40+ permissions)
- **[ROLES.md](business-logic/ROLES.md)** - Gestion des rôles (7 fonctions)
- **🆕 [PERMISSIONS_MANAGEMENT_GUIDE.md](PERMISSIONS_MANAGEMENT_GUIDE.md)** - Guide pour ajouter/supprimer des permissions (13 étapes)

#### 👥 Gestion des Entités
- **[USERS.md](business-logic/USERS.md)** - Gestion utilisateurs (10 fonctions, 720 lignes)
- **[PRESENTERS.md](business-logic/PRESENTERS.md)** - Gestion présentateurs (6 fonctions)
- **[GUESTS.md](business-logic/GUESTS.md)** - Gestion invités (7 fonctions)
- **[SHOWS.md](business-logic/SHOWS.md)** - Gestion shows (3 fonctions complexes, 600 lignes)
- **[EMISSIONS.md](business-logic/EMISSIONS.md)** - Gestion émissions (6 fonctions)
- **[SEGMENTS.md](business-logic/SEGMENTS.md)** - Gestion segments (7 fonctions)

#### 🔧 Fonctionnalités Transverses
- **[NOTIFICATIONS.md](business-logic/NOTIFICATIONS.md)** - Système de notifications (7 fonctions)
- **[AUDIT.md](business-logic/AUDIT.md)** - Logs d'audit (7 fonctions)
- **[UTILITIES.md](business-logic/UTILITIES.md)** - Recherche + Dashboard (6 fonctions)
- **🆕 [BACKUP.md](business-logic/BACKUP.md)** - Sauvegardes Google Drive (backup, restore, OAuth2)

**Utilisez cette section pour :**
- Comprendre la logique métier de chaque module
- Voir les fonctions disponibles avec exemples
- Comprendre les relations entre modules
- Implémenter de nouvelles fonctionnalités

---

## 📊 Statistiques de la documentation

| Section | Fichiers | Lignes | Fonctions | Exemples |
|---------|----------|--------|-----------|----------|
| Architecture | 6 | ~8,000 | 80+ | 50+ |
| Business Logic | 14 | ~6,300 | 79 | 99 |
| **TOTAL** | **20** | **~14,300** | **159+** | **149+** |

---

## 🎯 Par où commencer ?

### Pour un nouveau développeur
1. 📖 Lire [architecture/README.md](architecture/README.md) pour comprendre la structure
2. 🚀 Lire [business-logic/QUICKSTART.md](business-logic/QUICKSTART.md) pour démarrer rapidement
3. 🔐 Lire [business-logic/AUTH.md](business-logic/AUTH.md) et [business-logic/PERMISSIONS.md](business-logic/PERMISSIONS.md) (essentiel)
4. 👤 Consulter les modules selon vos besoins

### Pour implémenter une fonctionnalité
1. 🔍 Identifier le module concerné dans [business-logic/README.md](business-logic/README.md)
2. 📄 Lire la documentation du module
3. 💻 Copier/adapter les exemples fournis
4. ✅ Vérifier la checklist dans [business-logic/QUICKSTART.md](business-logic/QUICKSTART.md)

### Pour débugger
1. 🐛 Consulter la section "Erreurs" du module concerné
2. 📏 Vérifier les contraintes dans "Règles métier"
3. 🔗 Consulter les relations dans "Relations"

---

## 🔍 Recherche rapide

### Authentification
- Login/Logout → [AUTH.md](business-logic/AUTH.md)
- Permissions → [PERMISSIONS.md](business-logic/PERMISSIONS.md)
- Rôles → [ROLES.md](business-logic/ROLES.md)

### Entités principales
- Utilisateurs → [USERS.md](business-logic/USERS.md)
- Shows → [SHOWS.md](business-logic/SHOWS.md)
- Présentateurs → [PRESENTERS.md](business-logic/PRESENTERS.md)
- Invités → [GUESTS.md](business-logic/GUESTS.md)

### Fonctionnalités
- Recherche → [UTILITIES.md](business-logic/UTILITIES.md#module-search)
- Statistiques → [UTILITIES.md](business-logic/UTILITIES.md#module-dashboard)
- Notifications → [NOTIFICATIONS.md](business-logic/NOTIFICATIONS.md)
- Audit → [AUDIT.md](business-logic/AUDIT.md)

---

## 📖 Conventions de documentation

### Structure des fichiers business-logic
Chaque module contient :
1. **Vue d'ensemble** - Responsabilités et dépendances
2. **Architecture** - Modèles et relations
3. **Fonctions métier** - Documentation détaillée avec exemples
4. **Règles métier** - Contraintes et validations
5. **Relations** - Dépendances inter-modules
6. **Contraintes** - Limitations et performances
7. **Exemples** - Cas d'usage concrets

### Format des fonctions
```python
# Signature complète
def fonction_name(param1: Type, param2: Type) -> ReturnType

# Description
Explication de ce que fait la fonction

# Logique métier
Étapes détaillées du traitement

# Paramètres
- param1: Description et contraintes
- param2: Description et contraintes

# Retour
Description de la valeur de retour

# Erreurs
- HTTPException(404): Cas d'erreur 1
- HTTPException(400): Cas d'erreur 2

# Exemples
Code complet d'utilisation
```

---

## 🛠️ Technologies documentées

- **Backend** : FastAPI 0.109.0
- **ORM** : SQLAlchemy 2.0
- **Base de données** : PostgreSQL 15
- **Authentification** : JWT (python-jose)
- **Validation** : Pydantic v2
- **Tests** : Pytest
- **Migrations** : Alembic

---

## 🔗 Liens utiles

### Repositories
- Code source : `/Users/happi/App/API/FASTAPI/`
- Documentation : `/Users/happi/App/API/FASTAPI/docs/`

### Fichiers de configuration
- `alembic.ini` - Configuration des migrations
- `requirements.txt` - Dépendances Python
- `pytest.ini` - Configuration des tests
- `app/config/config.py` - Configuration de l'application

### Scripts utiles
- `scripts/backup_db.sh` - Sauvegarde de la base de données
- `scripts/restore_db.sh` - Restauration de la base de données
- `scripts/cleanup_docker.sh` - Nettoyage Docker

---

## 📝 Glossaire

| Terme | Définition | Documentation |
|-------|------------|---------------|
| **CRUD** | Create, Read, Update, Delete | Tous les modules |
| **Soft Delete** | Suppression logique (is_deleted=True) | Tous les modules |
| **RBAC** | Role-Based Access Control | [PERMISSIONS.md](business-logic/PERMISSIONS.md) |
| **JWT** | JSON Web Token | [AUTH.md](business-logic/AUTH.md) |
| **Eager Loading** | Chargement anticipé des relations | [SHOWS.md](business-logic/SHOWS.md) |
| **N+1 Problem** | Problème de performance (queries multiples) | [SHOWS.md](business-logic/SHOWS.md) |
| **Audit Log** | Journal de traçabilité | [AUDIT.md](business-logic/AUDIT.md) |

---

## 🎯 Bonnes pratiques

✅ **Toujours** utiliser les fonctions CRUD existantes  
✅ **Toujours** vérifier les permissions  
✅ **Toujours** utiliser soft delete  
✅ **Toujours** logger les actions critiques  
✅ **Toujours** utiliser eager loading pour les relations  
✅ **Toujours** gérer les erreurs avec HTTPException  

❌ **Jamais** faire de queries SQL directes  
❌ **Jamais** supprimer physiquement (hard delete)  
❌ **Jamais** oublier les permissions  
❌ **Jamais** utiliser lazy loading (N+1 problem)  

---

## 🆘 Support

### Questions ?
1. Cherchez dans la documentation (Ctrl+F)
2. Consultez les exemples dans chaque module
3. Vérifiez le [QUICKSTART.md](business-logic/QUICKSTART.md)

### Besoin d'aide ?
- Consultez les FAQ dans [QUICKSTART.md](business-logic/QUICKSTART.md)
- Vérifiez les exemples de code
- Lisez la section "Contraintes" de chaque module

---

## 📈 Évolution de la documentation

### Version actuelle : v1.0 (Décembre 2024)
- ✅ Documentation architecture complète (6 fichiers)
- ✅ Documentation business logic complète (14 fichiers)
- ✅ 159+ fonctions documentées
- ✅ 149+ exemples de code
- ✅ 20+ diagrammes

### Prochaines évolutions
- [ ] Documentation des tests
- [ ] Documentation du déploiement
- [ ] Tutoriels vidéo
- [ ] FAQ étendue

---

## 🎉 Prêt à commencer ?

**Commencez par :**
1. [architecture/README.md](architecture/README.md) - Architecture globale
2. [business-logic/QUICKSTART.md](business-logic/QUICKSTART.md) - Démarrage rapide
3. Consultez les modules selon vos besoins !

**Bonne documentation ! 📚**

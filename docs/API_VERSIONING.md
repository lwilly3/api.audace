# Guide de Gestion des Versions de l'API

Ce document explique comment gérer les versions de l'API Audace.

## 📌 Vue d'ensemble

L'API utilise un système de versioning basé sur :
- **Semantic Versioning** (SemVer) pour les versions logicielles : `X.Y.Z`
- **URL Versioning** pour l'API : `/api/v1`, `/api/v2`, etc.
- **Headers de version** dans toutes les réponses

## 🔢 Semantic Versioning

Format : `MAJOR.MINOR.PATCH` (ex: `1.2.0`)

- **MAJOR** : Changements incompatibles (breaking changes)
- **MINOR** : Nouvelles fonctionnalités compatibles
- **PATCH** : Corrections de bugs compatibles

### Exemples
```
1.0.0 → 1.0.1  # Correction de bug
1.0.1 → 1.1.0  # Nouvelle fonctionnalité
1.1.0 → 2.0.0  # Breaking change
```

## 📁 Fichiers de Version

### app/__version__.py
Fichier centralisé contenant toutes les informations de version :

```python
__version__ = "1.2.0"  # Version actuelle

VERSION_INFO = {
    "version": "1.2.0",
    "release_date": "2026-01-07",
    "api_version": "v1",  # Pour le routing
    "min_client_version": "1.0.0",  # Compatibilité
    "deprecated_versions": [],  # Versions obsolètes
    "breaking_changes": {
        "1.2.0": ["Description des changements"]
    }
}
```

**⚠️ Toujours mettre à jour ce fichier lors d'une nouvelle version !**

## 🛣️ Versioning d'URL (Futur)

Actuellement, l'API utilise une seule version (`v1`) sans préfixe.

Pour une évolution future avec plusieurs versions :

```python
# Structure recommandée
/api/v1/users      # Version 1 (actuelle)
/api/v2/users      # Version 2 (future)
/version           # Info de version (sans préfixe)
```

### Migration vers URL versioning

1. **Créer un nouveau dossier de routeurs** :
   ```
   routeur/
   ├── v1/              # Routes version 1
   │   ├── users.py
   │   ├── auth.py
   │   └── ...
   └── v2/              # Routes version 2 (future)
       └── ...
   ```

2. **Monter les routeurs avec préfixe** :
   ```python
   from routeur.v1 import users_route
   app.include_router(users_route.router, prefix="/api/v1")
   ```

3. **Maintenir v1 pendant la transition** :
   - Les anciennes URLs continuent de fonctionner
   - Ajouter un warning header pour encourager la migration

## 📡 Headers de Version

Chaque réponse de l'API inclut automatiquement :

```http
X-API-Version: 1.2.0
X-Min-Client-Version: 1.0.0
X-API-Path-Version: v1
```

### Middleware de Version

Le middleware `APIVersionMiddleware` :
- ✅ Ajoute automatiquement les headers
- ✅ Détecte les versions dépréciées
- ✅ Retourne 410 Gone pour les versions obsolètes
- ✅ Ajoute des warnings pour les versions anciennes

## 🔌 Endpoints de Version

### GET /version
Informations complètes sur la version :
```json
{
  "version": "1.2.0",
  "release_date": "2026-01-07",
  "api_version": "v1",
  "min_client_version": "1.0.0",
  "breaking_changes": {...},
  "changelog_url": "https://...",
  "documentation_url": "https://..."
}
```

### GET /version/current
Version actuelle uniquement :
```json
{
  "version": "1.2.0"
}
```

### GET /version/health
Health check avec version :
```json
{
  "status": "healthy",
  "version": "1.2.0",
  "api_version": "v1"
}
```

### GET /version/compatibility/{client_version}
Vérifier la compatibilité :
```bash
curl /version/compatibility/1.0.0
```

```json
{
  "compatible": true,
  "outdated": true,
  "recommendation": "Update your client to the latest version"
}
```

## 🔄 Processus de Mise à Jour

### 1. Déterminer le Type de Version

**PATCH (1.2.0 → 1.2.1)** :
- Corrections de bugs
- Améliorations de performance
- Pas de nouveaux endpoints
- 100% compatible

**MINOR (1.2.1 → 1.3.0)** :
- Nouvelles fonctionnalités
- Nouveaux endpoints
- Nouveaux champs optionnels
- Compatible backward

**MAJOR (1.3.0 → 2.0.0)** :
- Breaking changes
- Suppression d'endpoints
- Modification de schémas existants
- Changements incompatibles

### 2. Mettre à Jour les Fichiers

```bash
# 1. Modifier app/__version__.py
vim app/__version__.py
# Changer __version__ = "1.3.0"
# Ajouter les breaking_changes si MAJOR

# 2. Mettre à jour CHANGELOG.md
python scripts/add_changelog_entry.py
# ou modifier manuellement

# 3. Créer une migration si nécessaire
alembic revision -m "description"
alembic upgrade head
```

### 3. Tester

```bash
# Démarrer l'API
uvicorn maintest:app --reload

# Vérifier la version
curl http://localhost:8000/version

# Vérifier les headers
curl -I http://localhost:8000/version
```

### 4. Commit et Tag

```bash
# Commit
git add .
git commit -m "chore: bump version to 1.3.0"

# Tag
git tag -a v1.3.0 -m "Version 1.3.0 - Description"
git push origin v1.3.0
```

## 📋 Checklist de Release

### Avant la Release

- [ ] Vérifier que tous les tests passent
- [ ] Mettre à jour `app/__version__.py`
- [ ] Documenter les breaking changes dans `VERSION_INFO`
- [ ] Mettre à jour `CHANGELOG.md`
- [ ] Mettre à jour la documentation API
- [ ] Créer/appliquer les migrations Alembic
- [ ] Tester en local
- [ ] Vérifier les endpoints `/version`

### Pendant la Release

- [ ] Créer un tag Git : `v1.3.0`
- [ ] Pousser le tag : `git push origin v1.3.0`
- [ ] Créer une release GitHub (optionnel)
- [ ] Déployer en production
- [ ] Vérifier que l'API répond avec la bonne version

### Après la Release

- [ ] Annoncer la nouvelle version
- [ ] Mettre à jour la documentation externe
- [ ] Archiver le CHANGELOG si > 300 lignes
- [ ] Planifier la dépréciation des anciennes versions (si MAJOR)

## 🚫 Dépréciation de Versions

### Processus de Dépréciation

1. **Annoncer** (N versions avant) :
   ```python
   # app/__version__.py
   VERSION_INFO["deprecated_versions"] = ["v0"]  # v0 sera supprimé
   ```

2. **Warning Period** (3-6 mois) :
   - Les clients reçoivent un warning header
   - Documentation mise à jour
   - Communications aux utilisateurs

3. **Retrait** :
   ```python
   # Le middleware retourne 410 Gone
   VERSION_INFO["deprecated_versions"] = ["v0"]
   ```

### Exemple de Timeline

```
Mois 0:  Release v2, annonce dépréciation v1
Mois 1:  Warning headers activés pour v1
Mois 3:  Rappels aux utilisateurs encore sur v1
Mois 6:  v1 retournée en 410 Gone
```

## 🔍 Monitoring des Versions

### Logs

Le middleware log automatiquement :
```
WARNING - Deprecated API version v0 accessed from 192.168.1.1
```

### Métriques Recommandées

- Nombre de requêtes par version d'API
- Nombre de clients sur anciennes versions
- Temps de réponse par version

## 💡 Bonnes Pratiques

### ✅ À faire

- Toujours incrémenter la version selon SemVer
- Documenter tous les breaking changes
- Maintenir `CHANGELOG.md` à jour
- Tester avant de taguer
- Garder les anciennes versions un certain temps
- Communiquer les changements aux utilisateurs

### ❌ À éviter

- Changer la version sans raison
- Oublier de mettre à jour `__version__.py`
- Breaking changes sans incrémenter MAJOR
- Supprimer brutalement une version
- Déployer sans tagger

## 🛠️ Commandes Utiles

```bash
# Voir la version actuelle
python -c "from app.__version__ import get_version; print(get_version())"

# Tester les endpoints de version
curl http://localhost:8000/version
curl http://localhost:8000/version/current
curl http://localhost:8000/version/health

# Vérifier compatibilité
curl http://localhost:8000/version/compatibility/1.0.0

# Créer une nouvelle version
# 1. Modifier __version__.py
# 2. python scripts/add_changelog_entry.py
# 3. git tag -a v1.3.0 -m "Version 1.3.0"
# 4. git push origin v1.3.0
```

## 📚 Ressources

- [Semantic Versioning](https://semver.org/)
- [API Versioning Best Practices](https://www.troyhunt.com/your-api-versioning-is-wrong-which-is/)
- [CHANGELOG.md](../../CHANGELOG.md)
- [Documentation API](https://api.cloud.audace.ovh/docs)

## 🤖 Pour les Agents IA

Lors de modifications du code :

1. **Déterminer l'impact** :
   - Bug fix → PATCH
   - Nouvelle feature → MINOR
   - Breaking change → MAJOR

2. **Mettre à jour `app/__version__.py`** :
   ```python
   __version__ = "X.Y.Z"  # Nouvelle version
   VERSION_INFO["release_date"] = "YYYY-MM-DD"
   VERSION_INFO["breaking_changes"]["X.Y.Z"] = [...]  # Si MAJOR
   ```

3. **Mettre à jour `CHANGELOG.md`** :
   ```bash
   python scripts/add_changelog_entry.py
   ```

4. **Suggérer de créer un tag Git**

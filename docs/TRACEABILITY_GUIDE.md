# Guide de Traçabilité des Changements

Ce document explique comment maintenir la traçabilité des changements dans le projet.

## Système de Traçabilité

Le projet utilise plusieurs niveaux de traçabilité :

### 1. CHANGELOG.md
**Fichier principal** : [CHANGELOG.md](../../CHANGELOG.md)

Document lisible par l'humain qui suit le format [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

**Caractéristiques spéciales** :
- ✅ Instructions explicites pour les agents IA en début de fichier
- ✅ Archivage automatique quand le fichier dépasse 300 lignes
- ✅ Organisation par année dans `docs/changelog/`
- ✅ Section `[Non publié]` pour les changements en cours

**Quand l'utiliser** :
- À chaque nouvelle fonctionnalité
- À chaque correction de bug
- À chaque changement d'API
- À chaque release

**Structure** :
```markdown
## [Version] - Date

### Ajouté
- Nouvelles fonctionnalités

### Modifié
- Changements dans l'existant

### Corrigé
- Corrections de bugs

### Base de données
- Migrations Alembic
```

**Archivage automatique** :
```bash
# Vérifier si l'archivage est nécessaire (simulation)
python scripts/archive_changelog.py --dry-run

# Archiver automatiquement les anciennes versions
python scripts/archive_changelog.py
```

### 2. Migrations Alembic
**Répertoire** : `alembic/versions/`

Traçabilité automatique des changements de schéma de base de données.

**Consulter l'historique** :
```bash
# Voir toutes les migrations
python scripts/show_migrations_history.py

# Générer une entrée changelog pour la dernière migration
python scripts/show_migrations_history.py --changelog

# Voir l'état actuel de la base de données
alembic current

# Voir l'historique des migrations
alembic history
```

### 3. Git Commits
**Historique Git** : `.git/`

Traçabilité fine de tous les changements de code.

**Bonnes pratiques** :
```bash
# Commits descriptifs
git commit -m "feat: ajout des permissions Citations"
git commit -m "fix: correction du bug de suppression en cascade"
git commit -m "docs: mise à jour de la documentation des permissions"

# Format de commit recommandé
<type>(<scope>): <description>

Types : feat, fix, docs, style, refactor, test, chore
```

### 4. Documentation spécifique
**Fichiers** : `QUOTES_PERMISSIONS.md`, `version_description.md`, etc.

Documentation détaillée pour des fonctionnalités spécifiques.

## Processus de Mise à Jour

### Lors de l'ajout d'une fonctionnalité

1. **Développement**
   ```bash
   git checkout -b feature/nouvelle-fonctionnalite
   # ... développement ...
   ```

2. **Migration de base de données** (si nécessaire)
   ```bash
   alembic revision -m "description_du_changement"
   # Éditer le fichier de migration
   alembic upgrade head
   ```

3. **Mise à jour du CHANGELOG**
   ```bash
   # Générer l'entrée automatiquement
   python scripts/show_migrations_history.py --changelog
   
   # Copier dans CHANGELOG.md section [Non publié]
   ```
   
   Ajouter manuellement les autres changements :
   ```markdown
   ## [Non publié]
   
   ### Ajouté
   - Nouvelle fonctionnalité X
   - Script Y pour Z
   
   ### Base de données
   - Migration `75574b12` : add_quotes_permissions
   ```

4. **Documentation spécifique** (si nécessaire)
   ```bash
   # Créer un fichier MD dédié pour les fonctionnalités complexes
   vim FEATURE_NAME.md
   ```

5. **Commit et Push**
   ```bash
   git add .
   git commit -m "feat: ajout de la nouvelle fonctionnalité"
   git push origin feature/nouvelle-fonctionnalite
   ```

### Lors d'une Release

1. **Mettre à jour le CHANGELOG**
   ```markdown
   ## [1.2.0] - 2026-01-07
   
   ### Ajouté
   - (déplacer depuis [Non publié])
   
   ### Modifié
   - (déplacer depuis [Non publié])
   ```

2. **Créer un tag Git**
   ```bash
   git tag -a v1.2.0 -m "Version 1.2.0 - Module Citations"
   git push origin v1.2.0
   ```

3. **Créer une release GitHub** (si applicable)
   - Utiliser le contenu du CHANGELOG pour la description
   - Attacher les binaires/artifacts si nécessaire

4. **Mettre à jour version_description.md** (optionnel)
   ```bash
   # Pour des descriptions détaillées de version
   vim version_description.md
   ```

## Outils Disponibles

### Script de visualisation des migrations
```bash
# Afficher toutes les migrations
python scripts/show_migrations_history.py

# Générer une entrée changelog
python scripts/show_migrations_history.py --changelog
```

### Commandes Alembic utiles
```bash
# État actuel
alembic current

# Historique complet
alembic history --verbose

# Voir une migration spécifique
alembic show <revision_id>

# Revenir en arrière
alembic downgrade -1

# Aller à une révision spécifique
alembic upgrade <revision_id>
```

### Commandes Git utiles
```bash
# Voir l'historique
git log --oneline --graph --all

# Voir les changements d'un fichier
git log -p <fichier>

# Chercher dans l'historique
git log --grep="permissions"

# Voir qui a modifié une ligne
git blame <fichier>
```

## Exemple Complet : Ajout des Permissions Citations

Voici comment la traçabilité a été maintenue pour les permissions Citations :

### 1. Migration Alembic
```
Fichier : alembic/versions/75574b1232db_add_quotes_permissions.py
Date    : 07/01/2026
Changes : 8 nouvelles colonnes dans user_permissions
```

### 2. CHANGELOG.md
```markdown
## [Non publié]

### Ajouté
- Nouvelles permissions pour le module Citations
  - 8 permissions : quotes_view, quotes_create, etc.
  - Script d'initialisation
  - Documentation complète

### Modifié
- Modèle UserPermissions : 8 colonnes ajoutées
- init_admin.py : permissions Citations pour admin

### Base de données
- Migration `75574b12` : add_quotes_permissions
```

### 3. Documentation
```
Fichier : QUOTES_PERMISSIONS.md
Contenu : Guide complet d'utilisation des permissions
```

### 4. Scripts
```
Fichiers :
- app/db/init_quotes_permissions.py : Logique métier
- scripts/init_quotes_permissions.py : Script d'initialisation
```

## Bonnes Pratiques

### ✅ À faire
- Mettre à jour le CHANGELOG à chaque changement significatif
- Écrire des descriptions de migration claires et descriptives
- Documenter les breaking changes avec ⚠️
- Référencer les issues/tickets (#123)
- Garder le format cohérent

### ❌ À éviter
- Oublier de mettre à jour le CHANGELOG
- Descriptions vagues ("fix bug", "update code")
- Mélanger plusieurs types de changements dans un commit
- Oublier de documenter les breaking changes
- Ne pas tester les migrations (upgrade/downgrade)

## Commandes Rapides

```bash
# Workflow complet d'ajout de fonctionnalité
git checkout -b feature/ma-fonctionnalite
# ... développement ...
alembic revision -m "add_my_feature"
# ... éditer migration ...
alembic upgrade head
python scripts/show_migrations_history.py --changelog
# ... copier dans CHANGELOG.md ...
git add .
git commit -m "feat: ajout de ma fonctionnalité"
git push origin feature/ma-fonctionnalite
```

## Support

Pour toute question sur la traçabilité :
1. Consulter [CHANGELOG.md](CHANGELOG.md)
2. Utiliser `python scripts/show_migrations_history.py`
3. Consulter l'historique Git : `git log`
4. Vérifier les migrations Alembic : `alembic history`

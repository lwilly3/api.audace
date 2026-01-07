# Aide-Mémoire : Traçabilité des Changements

## 📋 Commandes Rapides

### Version de l'API

```bash
# Voir la version actuelle
python -c "from app.__version__ import get_version; print(get_version())"

# Informations complètes
curl http://localhost:8000/version

# Bumper la version
python scripts/bump_version.py patch      # 1.2.0 → 1.2.1
python scripts/bump_version.py minor      # 1.2.1 → 1.3.0
python scripts/bump_version.py major      # 1.3.0 → 2.0.0
```

### Consulter l'historique

```bash
# Voir toutes les migrations Alembic
python scripts/show_migrations_history.py

# Générer une entrée changelog pour la dernière migration
python scripts/show_migrations_history.py --changelog

# État actuel de la base de données
source venv/bin/activate && alembic current

# Historique des migrations Alembic
source venv/bin/activate && alembic history

# Historique Git
git log --oneline --graph --all
```

### Ajouter une entrée au CHANGELOG

```bash
# Assistant interactif (recommandé)
python scripts/add_changelog_entry.py

# Manuellement : éditer CHANGELOG.md section [Non publié]
```

### Archiver le CHANGELOG

```bash
# Vérifier si archivage nécessaire (simulation)
python scripts/archive_changelog.py --dry-run

# Archiver automatiquement (quand > 300 lignes)
python scripts/archive_changelog.py
```

### Créer une migration

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Créer une nouvelle migration
alembic revision -m "description_claire"

# Éditer le fichier dans alembic/versions/

# Appliquer la migration
alembic upgrade head

# Vérifier que tout fonctionne
alembic downgrade -1
alembic upgrade head
```

## 📝 Templates

### Template d'entrée CHANGELOG

```markdown
## [Non publié]

### Ajouté
- Nouvelle fonctionnalité X permettant Y
  - Détail 1
  - Détail 2

### Modifié
- Amélioration de Z pour optimiser les performances

### Corrigé
- Correction du bug #123 causant X

### Base de données
- Migration `75574b12` : description du changement

### Sécurité
- Correction de la vulnérabilité CVE-2024-XXXX
```

### Template de commit Git

```bash
# Format recommandé
git commit -m "type(scope): description courte"

# Types :
# - feat: nouvelle fonctionnalité
# - fix: correction de bug
# - docs: documentation
# - style: formatage
# - refactor: refactoring
# - test: ajout de tests
# - chore: tâches de maintenance

# Exemples :
git commit -m "feat(permissions): ajout des permissions Citations"
git commit -m "fix(auth): correction du bug de révocation de token"
git commit -m "docs: mise à jour du guide de traçabilité"
```

### Template de migration Alembic

```python
"""description_claire

Revision ID: xxxxxxxxx
Revises: yyyyyyyyy
Create Date: 2026-01-07 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'xxxxxxxxx'
down_revision: Union[str, None] = 'yyyyyyyyy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Ajouter vos changements ici
    op.add_column('table_name', sa.Column('column_name', sa.String(), nullable=True))

def downgrade() -> None:
    # Toujours implémenter le downgrade !
    op.drop_column('table_name', 'column_name')
```

## 🔄 Workflow Complet

### Nouvelle fonctionnalité

```bash
# 1. Créer une branche
git checkout -b feature/ma-fonctionnalite

# 2. Développer
# ... codage ...

# 3. Migration de base de données (si nécessaire)
source venv/bin/activate
alembic revision -m "add_my_feature"
# Éditer le fichier de migration
alembic upgrade head

# 4. Tests
pytest

# 5. Ajouter au CHANGELOG
python scripts/add_changelog_entry.py
# ou
python scripts/show_migrations_history.py --changelog
# puis copier dans CHANGELOG.md

# 6. Commit
git add .
git commit -m "feat(module): ajout de ma fonctionnalité"

# 7. Push
git push origin feature/ma-fonctionnalite
```

### Correction de bug

```bash
# 1. Créer une branche
git checkout -b fix/bug-description

# 2. Corriger
# ... correction ...

# 3. Tests
pytest

# 4. CHANGELOG
python scripts/add_changelog_entry.py
# Sélectionner "Corrigé"

# 5. Commit
git commit -m "fix(module): correction du bug #123"

# 6. Push
git push origin fix/bug-description
```

### Préparer une release

```bash
# 1. Mettre à jour le CHANGELOG
# Déplacer [Non publié] vers [X.Y.Z] - DATE

# 2. Créer un tag
git tag -a v1.2.0 -m "Version 1.2.0 - Description"
git push origin v1.2.0

# 3. Créer une release GitHub (optionnel)
# Copier le contenu du CHANGELOG pour la description
```

## 🎯 Bonnes Pratiques

### ✅ À faire
- [x] Mettre à jour le CHANGELOG immédiatement après chaque changement
- [x] Écrire des descriptions claires et complètes
- [x] Tester les migrations (upgrade + downgrade)
- [x] Utiliser des commits atomiques (un changement = un commit)
- [x] Référencer les issues/tickets
- [x] Marquer les breaking changes avec ⚠️

### ❌ À éviter
- [ ] Oublier de mettre à jour le CHANGELOG
- [ ] Descriptions vagues ("fix", "update")
- [ ] Oublier d'implémenter downgrade()
- [ ] Commits multiples pour une seule fonctionnalité
- [ ] Ne pas tester avant de push

## 📊 Vérifications Avant Release

- [ ] CHANGELOG.md à jour avec tous les changements
- [ ] Toutes les migrations testées (upgrade + downgrade)
- [ ] Tests passent (pytest)
- [ ] Documentation à jour
- [ ] Version mise à jour dans les fichiers appropriés
- [ ] Tag Git créé
- [ ] Release notes préparées

## 🆘 Problèmes Courants

### Migration ne s'applique pas

```bash
# Vérifier l'état
alembic current

# Voir l'historique
alembic history

# Forcer à une révision spécifique
alembic stamp head

# Réappliquer
alembic upgrade head
```

### Conflit de migration

```bash
# Voir les branches
alembic branches

# Fusionner manuellement
alembic merge <rev1> <rev2> -m "merge description"
```

### CHANGELOG mal formaté

```bash
# Valider avec un linter Markdown
npx markdownlint CHANGELOG.md

# Ou utiliser l'assistant
python scripts/add_changelog_entry.py
```

## 📚 Ressources

- [Keep a Changelog](https://keepachangelog.com/fr/)
- [Semantic Versioning](https://semver.org/lang/fr/)
- [Conventional Commits](https://www.conventionalcommits.org/fr/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Guide complet](docs/TRACEABILITY_GUIDE.md)

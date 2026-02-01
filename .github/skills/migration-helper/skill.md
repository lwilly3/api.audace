# 📋 Migration Helper

> **Skill critique** : Guide complet pour les migrations Alembic sans perte de données.

---

## 📋 Contexte du Projet

### Migrations Existantes (14 fichiers)
```
alembic/versions/
├── 75e8b3bb0750_initial.py
├── 728d86904477_add_created_by_on_show_and_index.py
├── 93c6f091bafb_update_user_model_and_schemas.py
├── 75574b1232db_add_quotes_permissions.py
├── b314bb576ceb_add_revoked_tokens_table.py
├── 03c857d562d1_fix_last_update.py
├── 2aa8889d4cd1_add_on_db_user_permissions.py
├── 2f97ab44d3ed_add_permissions.py
├── 38dddbddd7a3_fix_last_update2_add_all_relationship.py
├── 9eea8fc12e70_create_password_reset_tokens_table.py
├── b035c931cdf8_add_roletemplate_db_and_route.py
├── bfdc86d253c7_update_user_permission_model.py
├── c2a6f1769b7f_create_invite_tokens_table.py
└── e141f13156c7_add_inverst_relationship_on_user_whith_.py
```

### Configuration (alembic.ini)
```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname
```

---

## 🎯 Objectif du Skill

Maîtriser les migrations Alembic pour :
1. **Créer** des migrations correctes
2. **Vérifier** avant application
3. **Tester** upgrade ET downgrade
4. **Éviter** les pertes de données

---

## ✅ Règles Obligatoires

### 1. Workflow de Migration

```bash
# 1. Modifier le modèle SQLAlchemy
# app/models/model_entity.py

# 2. Générer la migration automatique
alembic revision --autogenerate -m "description_claire"

# 3. VÉRIFIER le fichier généré (OBLIGATOIRE !)
# alembic/versions/xxx_description_claire.py

# 4. Tester l'upgrade
alembic upgrade head

# 5. Tester le downgrade
alembic downgrade -1

# 6. Re-upgrade pour état final
alembic upgrade head

# 7. Committer
git add alembic/versions/xxx_description_claire.py
git commit -m "migration: description_claire"
```

### 2. Structure d'une Migration

```python
# alembic/versions/xxx_description.py
"""Description claire du changement.

Revision ID: abc123
Revises: xyz789
Create Date: 2025-01-01 12:00:00.000000

Changes:
    - Add column 'new_column' to 'users' table
    - Create index on 'email' column
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'abc123'
down_revision: Union[str, None] = 'xyz789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    # Ajout de colonne
    op.add_column('users', sa.Column('new_column', sa.String(255), nullable=True))
    
    # Création d'index
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    """Rollback migration."""
    # Suppression dans l'ordre inverse
    op.drop_index('ix_users_email', 'users')
    op.drop_column('users', 'new_column')
```

### 3. Opérations Courantes

```python
# === TABLES ===

# Créer table
op.create_table(
    'entities',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    sa.Column('is_deleted', sa.Boolean(), default=False)
)

# Supprimer table
op.drop_table('entities')


# === COLONNES ===

# Ajouter colonne
op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

# Supprimer colonne
op.drop_column('users', 'phone')

# Modifier colonne
op.alter_column('users', 'name',
    existing_type=sa.String(100),
    type_=sa.String(255),
    nullable=False
)


# === INDEX ===

# Créer index simple
op.create_index('ix_users_email', 'users', ['email'])

# Créer index unique
op.create_index('ix_users_email', 'users', ['email'], unique=True)

# Créer index composite
op.create_index('ix_shows_status_date', 'shows', ['status', 'broadcast_date'])

# Supprimer index
op.drop_index('ix_users_email', 'users')


# === FOREIGN KEYS ===

# Ajouter FK
op.create_foreign_key(
    'fk_shows_user',
    'shows', 'users',
    ['created_by'], ['id'],
    ondelete='SET NULL'
)

# Supprimer FK
op.drop_constraint('fk_shows_user', 'shows', type_='foreignkey')


# === CONTRAINTES ===

# Ajouter contrainte unique
op.create_unique_constraint('uq_users_email', 'users', ['email'])

# Supprimer contrainte
op.drop_constraint('uq_users_email', 'users', type_='unique')
```

### 4. Migration de Données

```python
def upgrade() -> None:
    # 1. Ajouter nouvelle colonne
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    
    # 2. Migrer données existantes
    op.execute("""
        UPDATE users 
        SET full_name = CONCAT(name, ' ', family_name)
        WHERE name IS NOT NULL
    """)
    
    # 3. Rendre non-nullable (optionnel)
    # op.alter_column('users', 'full_name', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

### 5. Migration NOT NULL avec Données Existantes

```python
def upgrade() -> None:
    # ❌ ÉCHOUE si données existantes ont NULL
    # op.add_column('users', sa.Column('status', sa.String(20), nullable=False))
    
    # ✅ CORRECT : 3 étapes
    # 1. Ajouter nullable
    op.add_column('users', sa.Column('status', sa.String(20), nullable=True))
    
    # 2. Peupler avec valeur par défaut
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    
    # 3. Rendre NOT NULL
    op.alter_column('users', 'status', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'status')
```

### 6. Commandes Alembic Essentielles

```bash
# Voir état actuel
alembic current

# Voir historique
alembic history

# Voir historique détaillé
alembic history --verbose

# Appliquer toutes migrations
alembic upgrade head

# Appliquer migration spécifique
alembic upgrade abc123

# Rollback une migration
alembic downgrade -1

# Rollback à révision spécifique
alembic downgrade abc123

# Rollback tout
alembic downgrade base

# Créer migration vide
alembic revision -m "description"

# Créer migration auto-générée
alembic revision --autogenerate -m "description"

# Voir SQL sans exécuter
alembic upgrade head --sql

# Marquer comme appliqué (DANGER)
alembic stamp head
```

---

## 🚫 Interdictions Explicites

### ❌ Migration sans Vérification
```bash
# ❌ INTERDIT
alembic revision --autogenerate -m "changes"
alembic upgrade head  # Sans vérifier le fichier !

# ✅ CORRECT
alembic revision --autogenerate -m "changes"
# VÉRIFIER le fichier généré !
cat alembic/versions/xxx_changes.py
# Puis appliquer
alembic upgrade head
```

### ❌ Supprimer Colonne avec Données
```python
# ❌ INTERDIT - Perte de données !
def upgrade():
    op.drop_column('users', 'important_data')

# ✅ CORRECT - Backup d'abord
def upgrade():
    # Documenter la migration de données si nécessaire
    # Les données de 'important_data' ont été migrées vers 'new_table'
    op.drop_column('users', 'important_data')
```

### ❌ Migration sans Downgrade
```python
# ❌ INTERDIT
def upgrade():
    op.add_column('users', sa.Column('new_col', sa.String()))

def downgrade():
    pass  # Vide !

# ✅ CORRECT
def upgrade():
    op.add_column('users', sa.Column('new_col', sa.String()))

def downgrade():
    op.drop_column('users', 'new_col')
```

### ❌ Modifier Migration Appliquée
```python
# ❌ INTERDIT - Migration déjà en production !
# Fichier: 75e8b3bb0750_initial.py
# NE JAMAIS modifier ce fichier !

# ✅ CORRECT - Créer nouvelle migration
alembic revision --autogenerate -m "fix_initial_issue"
```

### ❌ Renommer Table/Colonne Directement
```python
# ❌ INTERDIT - Perte de données
def upgrade():
    op.drop_table('old_name')
    op.create_table('new_name', ...)

# ✅ CORRECT - Renommer
def upgrade():
    op.rename_table('old_name', 'new_name')
    # ou pour colonne
    op.alter_column('table', 'old_col', new_column_name='new_col')
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Ajout de Colonne (Existant)
```python
# alembic/versions/728d86904477_add_created_by_on_show_and_index.py
def upgrade() -> None:
    op.add_column('shows', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_index('idx_shows_created_by', 'shows', ['created_by'])
    op.create_foreign_key(
        'fk_shows_created_by',
        'shows', 'users',
        ['created_by'], ['id']
    )

def downgrade() -> None:
    op.drop_constraint('fk_shows_created_by', 'shows', type_='foreignkey')
    op.drop_index('idx_shows_created_by', 'shows')
    op.drop_column('shows', 'created_by')
```

### Exemple 2 : Nouvelle Table (Existant)
```python
# alembic/versions/b314bb576ceb_add_revoked_tokens_table.py
def upgrade() -> None:
    op.create_table('revoked_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('ix_revoked_tokens_token', 'revoked_tokens', ['token'])

def downgrade() -> None:
    op.drop_index('ix_revoked_tokens_token', 'revoked_tokens')
    op.drop_table('revoked_tokens')
```

---

## ✅ Checklist de Validation

### Avant Création

- [ ] Modèle SQLAlchemy modifié correctement
- [ ] Héritage de BaseModel si nouvelle table
- [ ] Relations avec back_populates

### Après Génération

- [ ] Vérifier le fichier migration généré
- [ ] upgrade() contient les bonnes opérations
- [ ] downgrade() est l'inverse exact de upgrade()
- [ ] Pas d'opérations dangereuses (drop sans backup)

### Avant Application

- [ ] Tests passent avec modèle modifié
- [ ] `alembic upgrade head` réussit
- [ ] `alembic downgrade -1` réussit
- [ ] `alembic upgrade head` réussit encore

### Avant Commit

- [ ] Migration documentée (docstring)
- [ ] Tests de régression passent
- [ ] Pas de données perdues

---

## 📁 Template Migration

```python
"""Description claire du changement.

Revision ID: [auto-generated]
Revises: [auto-generated]
Create Date: [auto-generated]

Changes:
    - Lister les changements ici
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '[auto]'
down_revision: Union[str, None] = '[auto]'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    pass


def downgrade() -> None:
    """Rollback migration."""
    pass
```

---

## 📚 Ressources Associées

- [model-generator](../model-generator/skill.md) - Modèles SQLAlchemy
- [refactor-safe](../refactor-safe/skill.md) - Modifications sûres
- [architecture-guardian](../architecture-guardian/skill.md) - Structure projet

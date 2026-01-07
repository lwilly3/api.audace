# Guide de Gestion des Permissions

## 📋 Vue d'ensemble

Ce guide explique **étape par étape** comment ajouter ou supprimer des permissions dans l'API Audace.

**⚠️ IMPORTANT** : Suivez TOUTES les étapes dans l'ordre pour éviter les incohérences.

---

## ➕ Ajouter une ou plusieurs nouvelles permissions

### Étape 1 : Créer la migration Alembic

**Fichier** : `alembic/versions/XXXXXX_add_new_permissions.py`

```bash
# Créer la migration
alembic revision -m "add_new_permissions"
```

**Contenu de la migration** :

```python
from alembic import op
import sqlalchemy as sa

# Identifiants de révision
revision = 'xxxxx'  # Généré automatiquement
down_revision = 'yyyyy'  # Version précédente
branch_labels = None
depends_on = None

def upgrade():
    # Ajouter les nouvelles colonnes
    op.add_column('user_permissions', 
        sa.Column('nouvelle_permission_1', sa.Boolean(), 
                  server_default='false', nullable=False))
    op.add_column('user_permissions', 
        sa.Column('nouvelle_permission_2', sa.Boolean(), 
                  server_default='false', nullable=False))

def downgrade():
    # Supprimer les colonnes en cas de rollback
    op.drop_column('user_permissions', 'nouvelle_permission_2')
    op.drop_column('user_permissions', 'nouvelle_permission_1')
```

**📝 Règles de nommage** :
- Format snake_case : `can_action_resource` ou `resource_action`
- Exemples : `can_view_reports`, `quotes_create`, `stream_transcription_view`

---

### Étape 2 : Mettre à jour le modèle SQLAlchemy

**Fichier** : `app/models/model_user_permissions.py`

Ajouter les colonnes dans la classe `UserPermissions` :

```python
class UserPermissions(Base):
    __tablename__ = "user_permissions"
    
    # ... existing columns ...
    
    # Nouvelles permissions (ajouter à la fin)
    nouvelle_permission_1 = Column(Boolean, default=False, nullable=False, 
                                   comment="Description de la permission 1")
    nouvelle_permission_2 = Column(Boolean, default=False, nullable=False, 
                                   comment="Description de la permission 2")
```

**⚠️ Important** : Le nom de la colonne doit correspondre EXACTEMENT au nom dans la migration.

---

### Étape 3 : Mettre à jour le CRUD `get_user_permissions`

**Fichier** : `app/db/crud/crud_permissions.py`

**Fonction** : `get_user_permissions()`

Ajouter les nouvelles permissions dans le dictionnaire retourné :

```python
def get_user_permissions(db: Session, user_id: int) -> Dict[str, Any]:
    # ... code existant ...
    
    return {
        "user_id": permissions.user_id,
        
        # ... existing permissions ...
        
        # Section pour votre nouveau module
        "nouvelle_permission_1": permissions.nouvelle_permission_1,
        "nouvelle_permission_2": permissions.nouvelle_permission_2,
        
        "granted_at": permissions.granted_at.isoformat() if permissions.granted_at else None
    }
```

---

### Étape 4 : Mettre à jour le CRUD `initialize_user_permissions`

**Fichier** : `app/db/crud/crud_permissions.py`

**Fonction** : `initialize_user_permissions()`

Ajouter les permissions avec valeur par défaut `False` :

```python
def initialize_user_permissions(db: Session, user_id: int):
    # ... code existant ...
    
    new_permissions = UserPermissions(
        user_id=user_id,
        
        # ... existing permissions ...
        
        # Nouvelles permissions
        nouvelle_permission_1=False,
        nouvelle_permission_2=False
    )
    
    # ... reste du code ...
```

---

### Étape 5 : Mettre à jour le CRUD `update_user_permissions`

**Fichier** : `app/db/crud/crud_permissions.py`

**Fonction** : `update_user_permissions()`

Ajouter les permissions dans l'ensemble `valid_permissions` :

```python
def update_user_permissions(db: Session, user_id: int, permissions: Dict[str, bool], user_connected_id: int):
    # ... code existant ...
    
    valid_permissions = {
        # ... existing permissions ...
        
        # Nouvelles permissions
        'nouvelle_permission_1',
        'nouvelle_permission_2',
    }
    
    # ... reste du code ...
```

---

### Étape 6 : Mettre à jour `init_admin.py`

**Fichier** : `app/db/init_admin.py`

**Fonction** : `initialize_default_admin()`

Activer les permissions pour l'admin (si applicable) :

```python
# Mettre à jour les permissions de l'admin
admin_permissions.nouvelle_permission_1 = True
admin_permissions.nouvelle_permission_2 = True

db.commit()
```

---

### Étape 7 : Créer le script d'initialisation (optionnel)

**Fichier** : `app/db/init_nouvelles_permissions.py`

Pour appliquer les permissions aux rôles existants :

```python
from sqlalchemy.orm import Session
from app.models import User, UserPermissions

# Matrice de permissions par rôle
ROLE_PERMISSIONS_MATRIX = {
    "Admin": {
        "nouvelle_permission_1": True,
        "nouvelle_permission_2": True,
    },
    "Éditeur": {
        "nouvelle_permission_1": True,
        "nouvelle_permission_2": False,
    },
    # ... autres rôles ...
}

def initialize_nouvelles_permissions_for_role(db: Session, role_name: str) -> int:
    """
    Initialise les nouvelles permissions pour tous les utilisateurs d'un rôle.
    """
    permissions_config = ROLE_PERMISSIONS_MATRIX.get(role_name)
    if not permissions_config:
        return 0
    
    users = db.query(User).filter(User.role == role_name).all()
    updated_count = 0
    
    for user in users:
        user_permissions = db.query(UserPermissions).filter(
            UserPermissions.user_id == user.id
        ).first()
        
        if user_permissions:
            for perm_name, perm_value in permissions_config.items():
                setattr(user_permissions, perm_name, perm_value)
            updated_count += 1
    
    db.commit()
    return updated_count
```

**Fichier** : `scripts/init_nouvelles_permissions.py`

Script standalone pour exécution manuelle :

```python
#!/usr/bin/env python3
from app.db.database import SessionLocal
from app.db.init_nouvelles_permissions import initialize_nouvelles_permissions_for_role

def main():
    db = SessionLocal()
    try:
        roles = ["Admin", "Éditeur", "Animateur", "Community Manager", "Invité"]
        
        for role in roles:
            count = initialize_nouvelles_permissions_for_role(db, role)
            print(f"✅ {count} utilisateur(s) mis à jour pour le rôle {role}")
        
        print("\n✅ Initialisation terminée avec succès!")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

---

### Étape 8 : Appliquer la migration

```bash
# Vérifier la migration avant de l'appliquer
alembic current

# Voir le SQL qui sera exécuté (dry-run)
alembic upgrade head --sql

# Appliquer la migration
alembic upgrade head

# Vérifier que tout est OK
alembic current
```

---

### Étape 9 : Exécuter le script d'initialisation

```bash
# Rendre le script exécutable
chmod +x scripts/init_nouvelles_permissions.py

# Exécuter
python scripts/init_nouvelles_permissions.py
```

---

### Étape 10 : Tester

```bash
# Démarrer l'API
uvicorn maintest:app --reload

# Tester l'endpoint de permissions
curl http://localhost:8000/users/me/permissions

# Vérifier que les nouvelles permissions apparaissent
```

---

### Étape 11 : Documenter

**Fichier** : Créer `NOUVELLES_PERMISSIONS.md`

```markdown
# Permissions [Nom du Module]

## Permissions ajoutées

1. **nouvelle_permission_1** : Description de la permission
2. **nouvelle_permission_2** : Description de la permission

## Matrice de permissions par rôle

| Permission | Admin | Éditeur | Animateur | CM | Invité |
|-----------|-------|---------|-----------|-----|--------|
| nouvelle_permission_1 | ✅ | ✅ | ❌ | ❌ | ❌ |
| nouvelle_permission_2 | ✅ | ❌ | ❌ | ❌ | ❌ |

## Scripts d'initialisation

- `app/db/init_nouvelles_permissions.py` - Logique métier
- `scripts/init_nouvelles_permissions.py` - Script standalone

## Utilisation

\`\`\`bash
python scripts/init_nouvelles_permissions.py
\`\`\`
```

---

### Étape 12 : Mettre à jour le CHANGELOG

**Fichier** : `CHANGELOG.md`

```markdown
## [1.3.0] - 2026-01-07

### Added
- Ajout de 2 nouvelles permissions pour le module [Nom]
  - `nouvelle_permission_1` : Description
  - `nouvelle_permission_2` : Description
- Script d'initialisation `scripts/init_nouvelles_permissions.py`
- Documentation `NOUVELLES_PERMISSIONS.md`

### Changed
- Migration Alembic `xxxxx_add_new_permissions`
- Mise à jour du modèle `UserPermissions`
- Mise à jour du CRUD permissions
```

---

### Étape 13 : Commit et push

```bash
# Vérifier les changements
git status

# Ajouter tous les fichiers
git add -A

# Commit avec message conventionnel
git commit -m "feat: Add [Module] permissions

- Add 2 new permissions: nouvelle_permission_1, nouvelle_permission_2
- Create migration xxxxx_add_new_permissions
- Update UserPermissions model and CRUD
- Add initialization scripts
- Add documentation"

# Push
git push origin main
```

---

## ➖ Supprimer des permissions

### ⚠️ ATTENTION : Opération délicate

La suppression de permissions peut casser l'API si :
- Elles sont utilisées dans le code frontend
- Elles sont référencées dans la logique métier

### Processus recommandé

#### Option 1 : Dépréciation (recommandé)

1. **Marquer comme obsolète** dans le code
2. **Documenter** la dépréciation dans le CHANGELOG
3. **Attendre** plusieurs versions avant suppression
4. **Communiquer** avec l'équipe frontend

```python
# app/models/model_user_permissions.py
ancienne_permission = Column(Boolean, default=False, nullable=False, 
                            comment="DEPRECATED: Ne plus utiliser, sera supprimée en v2.0")
```

#### Option 2 : Suppression immédiate (risqué)

Suivre les étapes dans l'ordre inverse de l'ajout :

### Étape 1 : Créer la migration de suppression

```bash
alembic revision -m "remove_old_permissions"
```

```python
def upgrade():
    op.drop_column('user_permissions', 'ancienne_permission')

def downgrade():
    op.add_column('user_permissions', 
        sa.Column('ancienne_permission', sa.Boolean(), 
                  server_default='false', nullable=False))
```

### Étape 2 : Supprimer du modèle

**Fichier** : `app/models/model_user_permissions.py`

Supprimer la ligne de la colonne.

### Étape 3 : Supprimer du CRUD

**Fichiers** :
- `app/db/crud/crud_permissions.py` : 
  - Fonction `get_user_permissions()` - Retirer du dictionnaire
  - Fonction `initialize_user_permissions()` - Retirer du constructeur
  - Fonction `update_user_permissions()` - Retirer de `valid_permissions`

### Étape 4 : Supprimer de `init_admin.py`

**Fichier** : `app/db/init_admin.py`

Retirer les lignes qui assignent cette permission.

### Étape 5 : Appliquer la migration

```bash
# ⚠️ BACKUP de la base avant !
pg_dump -U audace_user audace_db > backup_before_drop_permissions.sql

# Appliquer
alembic upgrade head
```

### Étape 6 : Tester

Vérifier que l'API démarre sans erreur et que les endpoints fonctionnent.

---

## 📋 Checklist complète - Ajout de permissions

Utilisez cette checklist pour vous assurer que rien n'est oublié :

### Base de données
- [ ] Migration Alembic créée avec `upgrade()` et `downgrade()`
- [ ] Noms de colonnes en snake_case
- [ ] `server_default='false'` sur chaque colonne
- [ ] Migration testée avec `alembic upgrade head --sql`
- [ ] Migration appliquée avec `alembic upgrade head`

### Modèle
- [ ] Colonnes ajoutées dans `app/models/model_user_permissions.py`
- [ ] Type `Column(Boolean, default=False, nullable=False)`
- [ ] Commentaires ajoutés pour documentation

### CRUD
- [ ] Permissions ajoutées dans `get_user_permissions()` - dictionnaire retourné
- [ ] Permissions ajoutées dans `initialize_user_permissions()` - avec `False`
- [ ] Permissions ajoutées dans `update_user_permissions()` - set `valid_permissions`

### Initialisation
- [ ] Permissions activées dans `app/db/init_admin.py` pour l'admin
- [ ] Script d'initialisation créé `app/db/init_nouvelles_permissions.py`
- [ ] Script standalone créé `scripts/init_nouvelles_permissions.py`
- [ ] Script rendu exécutable `chmod +x`
- [ ] Script exécuté et testé

### Documentation
- [ ] Fichier `NOUVELLES_PERMISSIONS.md` créé avec matrice de rôles
- [ ] `CHANGELOG.md` mis à jour avec section `Added`
- [ ] Version incrémentée dans `app/__version__.py`

### Tests
- [ ] API démarre sans erreur
- [ ] Endpoint `/users/me/permissions` retourne les nouvelles permissions
- [ ] Tests manuels avec Postman/curl effectués
- [ ] Vérification dans la base de données

### Git
- [ ] `git status` vérifié
- [ ] `git add -A` exécuté
- [ ] Commit avec message conventionnel (`feat:` pour ajout)
- [ ] Push vers le repository

---

## 🎯 Cas d'usage courants

### Ajouter des permissions pour un nouveau module

**Exemple : Module "Rapports"**

1. Définir les permissions nécessaires :
   - `reports_view` - Voir les rapports
   - `reports_create` - Créer des rapports
   - `reports_export` - Exporter des rapports
   - `reports_delete` - Supprimer des rapports

2. Créer la matrice de rôles :

| Permission | Admin | Éditeur | Animateur | CM | Invité |
|-----------|-------|---------|-----------|-----|--------|
| reports_view | ✅ | ✅ | ✅ | ❌ | ❌ |
| reports_create | ✅ | ✅ | ❌ | ❌ | ❌ |
| reports_export | ✅ | ✅ | ❌ | ❌ | ❌ |
| reports_delete | ✅ | ❌ | ❌ | ❌ | ❌ |

3. Suivre toutes les étapes 1 à 13 du guide

---

### Modifier les permissions d'un rôle existant

**Ne nécessite PAS de migration** si vous modifiez juste les valeurs.

1. Modifier le fichier `app/db/init_[module]_permissions.py`
2. Mettre à jour la matrice `ROLE_PERMISSIONS_MATRIX`
3. Relancer le script d'initialisation
4. Documenter le changement dans le CHANGELOG

---

## 🚨 Erreurs courantes et solutions

### Erreur : "Permission invalide"

**Cause** : Permission non ajoutée dans `valid_permissions` du CRUD

**Solution** : Ajouter dans `update_user_permissions()` ligne ~470

### Erreur : "Column does not exist"

**Cause** : Migration non appliquée

**Solution** : 
```bash
alembic upgrade head
```

### Erreur : "Permission not found in response"

**Cause** : Permission non ajoutée dans `get_user_permissions()`

**Solution** : Ajouter dans le dictionnaire retourné

### Base de données et modèle désynchronisés

**Cause** : Migration appliquée mais modèle non mis à jour (ou inverse)

**Solution** :
```bash
# Voir l'état actuel
alembic current

# Voir les migrations en attente
alembic history

# Rollback si nécessaire
alembic downgrade -1

# Réappliquer
alembic upgrade head
```

---

## 📚 Ressources

- [Modèle UserPermissions](../app/models/model_user_permissions.py)
- [CRUD Permissions](../app/db/crud/crud_permissions.py)
- [Init Admin](../app/db/init_admin.py)
- [Exemple - Permissions Citations](../QUOTES_PERMISSIONS.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

## 🤖 Pour les agents IA

### Prompt pour ajouter des permissions

```
Ajoute les permissions suivantes au système :
- nom_permission_1 : Description
- nom_permission_2 : Description

Matrice de rôles :
- Admin: toutes les permissions
- Éditeur: permission_1 uniquement
- Autres: aucune permission

Suis le guide docs/PERMISSIONS_MANAGEMENT_GUIDE.md étape par étape.
```

### Validation automatique

Après ajout, vérifier que :

```bash
# 1. Migration existe
ls alembic/versions/ | grep add_new_permissions

# 2. Modèle contient les colonnes
grep "nouvelle_permission_1" app/models/model_user_permissions.py

# 3. CRUD contient les permissions
grep "nouvelle_permission_1" app/db/crud/crud_permissions.py | wc -l
# Doit retourner 3 (une occurrence dans chaque fonction)

# 4. L'API démarre
uvicorn maintest:app --reload

# 5. Les permissions sont retournées
curl http://localhost:8000/users/me/permissions | grep "nouvelle_permission_1"
```

---

**Version du guide** : 1.0.0  
**Dernière mise à jour** : 7 janvier 2026  
**Auteur** : Documentation Audace API

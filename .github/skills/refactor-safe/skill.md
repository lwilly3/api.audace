# 🔄 Refactor Safe

> **Skill important** : Méthodologie pour modifier le code existant sans introduire de régressions.

---

## 📋 Contexte du Projet

### État Actuel
- **14 migrations Alembic** : Historique DB à préserver
- **26 fichiers CRUD** : Logique métier critique
- **14 fichiers routes** : API publique (contrats)
- **25 modèles SQLAlchemy** : Relations interdépendantes
- **40+ permissions** : Système RBAC complexe

### Zones à Risque
| Zone | Risque | Impact |
|------|--------|--------|
| Relations SQLAlchemy | 🔴 Critique | Cascade, orphelins |
| UserPermissions | 🔴 Critique | Accès utilisateurs |
| Endpoints publics | 🟠 Élevé | Breaking API |
| Schémas Pydantic | 🟠 Élevé | Validation frontend |
| CRUD functions | 🟡 Moyen | Logique métier |

---

## 🎯 Objectif du Skill

Modifier le code existant en :
1. **Préservant** la compatibilité ascendante
2. **Testant** avant/après modification
3. **Migrant** les données si nécessaire
4. **Documentant** les changements

---

## ✅ Règles Obligatoires

### 1. Processus de Refactoring

```
┌─────────────────────────────────────────────────────────┐
│ 1. ANALYSER                                             │
│    - Identifier toutes les utilisations                 │
│    - Lister les dépendances                            │
│    - Évaluer l'impact                                  │
└─────────────────┬───────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 2. PRÉPARER                                             │
│    - Écrire tests de régression                        │
│    - Créer branche feature                             │
│    - Backup si nécessaire                              │
└─────────────────┬───────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 3. IMPLÉMENTER                                          │
│    - Modifications incrémentales                        │
│    - Compatibilité ascendante                          │
│    - Migration Alembic si DB                           │
└─────────────────┬───────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 4. VALIDER                                              │
│    - Tests passent                                      │
│    - Review code                                       │
│    - Test en staging                                   │
└─────────────────┬───────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 5. DÉPLOYER                                             │
│    - Migration si nécessaire                           │
│    - Monitoring post-déploiement                       │
│    - Plan de rollback prêt                             │
└─────────────────────────────────────────────────────────┘
```

### 2. Recherche d'Utilisations

```bash
# Avant toute modification, chercher TOUTES les utilisations

# Dans le code Python
grep -rn "function_name" app/ routeur/ tests/
grep -rn "ClassName" app/ routeur/ tests/
grep -rn "column_name" app/ routeur/ tests/

# Dans les imports
grep -rn "from app.models.model_user import" .
grep -rn "from app.db.crud.crud_users import" .

# Relations SQLAlchemy
grep -rn "relationship.*User" app/models/
grep -rn "ForeignKey.*users.id" app/models/

# Schémas Pydantic
grep -rn "class.*User.*BaseModel" app/schemas/
```

### 3. Renommer une Fonction

```python
# ❌ INTERDIT - Renommer directement
# def old_function():  # Supprimé
#     pass

def new_function():
    pass

# ✅ CORRECT - Wrapper de compatibilité
def new_function():
    """Nouvelle implémentation."""
    pass

def old_function():
    """
    Deprecated: Utiliser new_function() à la place.
    Sera supprimé en version 2.0.
    """
    import warnings
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

### 4. Renommer une Colonne DB

```python
# Étape 1 : Ajouter nouvelle colonne (migration)
# alembic revision --autogenerate -m "add_new_column"

def upgrade():
    op.add_column('users', sa.Column('new_name', sa.String()))
    # Copier données
    op.execute("UPDATE users SET new_name = old_name")

def downgrade():
    op.drop_column('users', 'new_name')


# Étape 2 : Mettre à jour le modèle (utiliser les deux)
class User(BaseModel):
    old_name = Column(String)  # Garder temporairement
    new_name = Column(String)
    
    @property
    def name(self):
        """Compatibilité ascendante."""
        return self.new_name or self.old_name


# Étape 3 : Migrer le code (une PR séparée)
# Remplacer old_name par new_name dans tout le code


# Étape 4 : Supprimer ancienne colonne (migration finale)
def upgrade():
    op.drop_column('users', 'old_name')
```

### 5. Modifier un Schéma Pydantic

```python
# ❌ INTERDIT - Changer le type directement
class UserResponse(BaseModel):
    # name: str  # Était string
    name: dict  # Breaking change !

# ✅ CORRECT - Ajouter nouveau champ
class UserResponse(BaseModel):
    name: str  # Garder l'ancien
    name_details: Optional[dict] = None  # Nouveau champ
    
    @computed_field
    @property
    def full_name(self) -> str:
        """Compatibilité avec ancien format."""
        if self.name_details:
            return f"{self.name_details['first']} {self.name_details['last']}"
        return self.name
```

### 6. Supprimer un Endpoint

```python
# ❌ INTERDIT - Supprimer directement
# @router.delete("/old-endpoint")  # Supprimé sans avertissement

# ✅ CORRECT - Déprécier d'abord
@router.delete("/old-endpoint", deprecated=True)
def old_endpoint():
    """
    DEPRECATED: Utiliser /new-endpoint à la place.
    Sera supprimé le 2025-06-01.
    """
    import warnings
    warnings.warn("Deprecated endpoint", DeprecationWarning)
    return new_endpoint()  # Rediriger vers nouveau

# Version 2.0+ : Supprimer après période de grâce
```

### 7. Modifier une Relation SQLAlchemy

```python
# ❌ INTERDIT - Supprimer relation directement
class User(BaseModel):
    # shows = relationship("Show", ...)  # Supprimé !
    pass

# ✅ CORRECT - Vérifier cascade d'abord
# 1. Chercher utilisations
#    grep -rn "user.shows" app/ routeur/
#    grep -rn "back_populates=\"user\"" app/models/

# 2. Modifier les dépendances d'abord

# 3. Supprimer la relation seulement si plus utilisée
```

### 8. Tests de Régression

```python
# tests/test_regression.py
"""
Tests de régression pour modifications.
À exécuter AVANT et APRÈS le refactoring.
"""

import pytest
from httpx import AsyncClient


class TestRegressionUsers:
    """Tests de régression pour users."""
    
    @pytest.mark.anyio
    async def test_user_creation_still_works(self, client, auth_headers):
        """Vérifier que la création fonctionne toujours."""
        response = await client.post(
            "/users",
            json={"username": "regtest", "email": "reg@test.com", "password": "Test123!"},
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Vérifier format de réponse inchangé
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "password" not in data  # Jamais exposé
    
    @pytest.mark.anyio
    async def test_user_permissions_structure(self, client, auth_headers):
        """Vérifier structure permissions inchangée."""
        response = await client.get("/users/1/permissions", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Vérifier champs critiques présents
        assert "can_create_showplan" in data
        assert "can_edit_showplan" in data
        assert "can_delete_showplan" in data
```

---

## 🚫 Interdictions Explicites

### ❌ Modifier DB sans Migration
```python
# ❌ INTERDIT
class User(BaseModel):
    new_column = Column(String)  # Ajouté sans migration !

# ✅ CORRECT
# 1. Modifier modèle
# 2. alembic revision --autogenerate -m "add_new_column"
# 3. Vérifier migration générée
# 4. alembic upgrade head
```

### ❌ Supprimer Endpoint Utilisé
```python
# ❌ INTERDIT - Supprimer sans vérifier
# Le frontend utilise peut-être cet endpoint !

# ✅ CORRECT
# 1. Vérifier logs d'utilisation
# 2. Communiquer avec équipe frontend
# 3. Déprécier pendant X semaines
# 4. Supprimer
```

### ❌ Casser Relation Sans Vérifier
```python
# ❌ INTERDIT
class Show(BaseModel):
    # user = relationship("User", ...)  # Supprimé sans vérifier !

# ✅ CORRECT
# 1. grep -rn "show.user" app/ routeur/
# 2. grep -rn "back_populates=\"shows\"" app/models/
# 3. Modifier tous les usages d'abord
# 4. Créer migration pour supprimer FK si nécessaire
```

### ❌ Changer Type de Retour API
```python
# ❌ INTERDIT - Breaking change
# Avant
@router.get("/users")
def get_users() -> List[UserResponse]:
    return users

# Après (CASSÉ !)
@router.get("/users")
def get_users() -> dict:  # Type changé !
    return {"users": users}

# ✅ CORRECT - Nouveau endpoint
@router.get("/users", response_model=List[UserResponse])
def get_users() -> List[UserResponse]:
    return users

@router.get("/v2/users", response_model=UsersPageResponse)
def get_users_v2() -> UsersPageResponse:
    return {"users": users, "total": count, "page": page}
```

---

## 📝 Exemples Concrets du Projet

### Exemple 1 : Ajouter Champ à User
```python
# 1. Modifier modèle
# app/models/model_user.py
class User(BaseModel):
    # ... existant
    phone_number = Column(String(20), nullable=True)  # Nouveau

# 2. Créer migration
# alembic revision --autogenerate -m "add_phone_to_user"

# 3. Vérifier migration
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')

# 4. Mettre à jour schémas
# app/schemas/schema_users.py
class UserUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=20)

class UserResponse(BaseModel):
    phone_number: Optional[str] = None

# 5. Mettre à jour CRUD si nécessaire
# 6. Tests
# 7. alembic upgrade head
```

### Exemple 2 : Renommer Permission
```python
# ATTENTION : Impact sur 40+ permissions !

# 1. Ajouter nouvelle permission (migration)
def upgrade():
    op.add_column('user_permissions', 
        sa.Column('can_manage_shows', sa.Boolean(), default=False))
    # Copier valeur
    op.execute("""
        UPDATE user_permissions 
        SET can_manage_shows = can_create_showplan
    """)

# 2. Mettre à jour modèle (garder les deux temporairement)
class UserPermissions(Base):
    can_create_showplan = Column(Boolean, default=False)  # Ancien
    can_manage_shows = Column(Boolean, default=False)  # Nouveau

# 3. Mettre à jour code (utiliser nouveau)
if current_user.permissions.can_manage_shows:
    # ...

# 4. Supprimer ancien (migration finale, version suivante)
def upgrade():
    op.drop_column('user_permissions', 'can_create_showplan')
```

---

## ✅ Checklist de Validation

### Avant Modification

- [ ] Rechercher TOUTES les utilisations (grep)
- [ ] Identifier les dépendances (imports, relations)
- [ ] Créer branche feature
- [ ] Écrire tests de régression
- [ ] Documenter le changement prévu

### Pendant Modification

- [ ] Modifications incrémentales
- [ ] Migration Alembic si DB modifiée
- [ ] Compatibilité ascendante si possible
- [ ] Wrapper de dépréciation si breaking change

### Après Modification

- [ ] Tests de régression passent
- [ ] Nouveaux tests ajoutés
- [ ] Documentation mise à jour
- [ ] CHANGELOG mis à jour
- [ ] Review code demandée

### Avant Déploiement

- [ ] Migration testée (upgrade + downgrade)
- [ ] Test en staging
- [ ] Plan de rollback prêt
- [ ] Communication équipe si breaking change

---

## 📁 Script de Recherche d'Utilisations

```bash
#!/bin/bash
# scripts/find_usages.sh

# Usage: ./find_usages.sh "pattern"

PATTERN=$1

echo "=== Recherche dans le code Python ==="
grep -rn "$PATTERN" app/ routeur/ tests/ --include="*.py"

echo ""
echo "=== Recherche dans les imports ==="
grep -rn "import.*$PATTERN\|from.*$PATTERN" . --include="*.py"

echo ""
echo "=== Recherche dans les migrations ==="
grep -rn "$PATTERN" alembic/versions/ --include="*.py"

echo ""
echo "=== Compte des occurrences ==="
grep -rc "$PATTERN" app/ routeur/ tests/ --include="*.py" | grep -v ":0$"
```

---

## 📚 Ressources Associées

- [architecture-guardian](../architecture-guardian/skill.md) - Structure à préserver
- [model-generator](../model-generator/skill.md) - Migrations DB
- [test-enforcer](../test-enforcer/skill.md) - Tests de régression
- [AGENT.md](../../../AGENT.md) - Règles d'or

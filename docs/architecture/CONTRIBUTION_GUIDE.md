# 🤝 Guide de contribution

Guide pour contribuer au projet API Audace.

---

## Table des matières

1. [Introduction](#introduction)
2. [Code de conduite](#code-de-conduite)
3. [Avant de commencer](#avant-de-commencer)
4. [Workflow de contribution](#workflow-de-contribution)
5. [Standards de code](#standards-de-code)
6. [Commits et messages](#commits-et-messages)
7. [Pull Requests](#pull-requests)
8. [Review process](#review-process)

---

## 👋 Introduction

Merci de votre intérêt pour contribuer à l'API Audace ! Ce guide vous aidera à soumettre des contributions de qualité.

### Types de contributions acceptées

- 🐛 Corrections de bugs
- ✨ Nouvelles fonctionnalités
- 📝 Améliorations de documentation
- ⚡ Optimisations de performance
- 🧪 Ajout de tests
- ♻️ Refactoring de code

---

## 📜 Code de conduite

### Principes

- **Respectueux** : Soyez courtois envers tous les contributeurs
- **Constructif** : Fournissez des retours utiles et bienveillants
- **Inclusif** : Accueillez les nouveaux contributeurs
- **Professionnel** : Gardez les discussions centrées sur le code

### Comportements inacceptables

- Langage offensant ou discriminatoire
- Harcèlement sous toute forme
- Publication d'informations privées sans consentement
- Trolling ou comportement perturbateur

---

## 🚀 Avant de commencer

### 1. Fork et clone

```bash
# Fork sur GitHub (bouton "Fork")

# Clone de votre fork
git clone https://github.com/votre-username/api.audace.git
cd api.audace

# Ajouter le repo original comme remote
git remote add upstream https://github.com/lwilly3/api.audace.git
```

---

### 2. Configuration de l'environnement

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Installer les outils de développement
pip install black flake8 mypy pytest-cov
```

---

### 3. Créer une base de données de test

```bash
psql -U postgres
CREATE DATABASE audace_db_test;
\q

# Copier .env en .env.test
cp .env .env.test

# Modifier DATABASE_NAME dans .env.test
# DATABASE_NAME=audace_db_test
```

---

### 4. Vérifier que tout fonctionne

```bash
# Lancer les migrations
alembic upgrade head

# Lancer l'API
uvicorn maintest:app --reload

# Lancer les tests
pytest
```

---

## 🔄 Workflow de contribution

### 1. Créer une branche

```bash
# Synchroniser avec upstream
git fetch upstream
git checkout main
git merge upstream/main

# Créer une branche pour votre feature/fix
git checkout -b feature/add-categories
# ou
git checkout -b fix/auth-token-expiration
# ou
git checkout -b docs/update-api-endpoints
```

**Convention de nommage des branches :**
- `feature/nom-de-la-feature` : Nouvelle fonctionnalité
- `fix/nom-du-bug` : Correction de bug
- `docs/nom-de-la-doc` : Documentation
- `refactor/nom-du-refactor` : Refactoring
- `test/nom-du-test` : Ajout de tests

---

### 2. Développer votre contribution

```bash
# Faire vos modifications
# ... coder ...

# Formater le code
black app/ routeur/ tests/

# Vérifier le linting
flake8 app/ routeur/ tests/

# Vérifier les types
mypy app/ routeur/

# Lancer les tests
pytest -v
```

---

### 3. Commiter vos changements

```bash
# Ajouter les fichiers modifiés
git add .

# Commit avec message descriptif
git commit -m "feat: add categories endpoint with CRUD operations"

# Push vers votre fork
git push origin feature/add-categories
```

---

### 4. Créer une Pull Request

1. Aller sur GitHub : `https://github.com/lwilly3/api.audace`
2. Cliquer sur "Pull Requests" > "New Pull Request"
3. Sélectionner votre branche
4. Remplir le template de PR (voir ci-dessous)
5. Soumettre la PR

---

## 🎨 Standards de code

### 1. Style Python (PEP 8)

```python
# ✅ Bon
def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Récupère un utilisateur par email.
    
    Args:
        db: Session de base de données SQLAlchemy
        email: Email de l'utilisateur
        
    Returns:
        User ou None si introuvable
    """
    return db.query(User).filter(
        User.email == email,
        User.is_deleted == False
    ).first()

# ❌ Mauvais
def getUsrByMail(d,e):
    return d.query(User).filter(User.email==e).first()
```

---

### 2. Type hints

```python
# ✅ Bon - Type hints explicites
from typing import List, Optional
from sqlalchemy.orm import Session

def get_shows(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Show]:
    """Lister les shows avec pagination"""
    return db.query(Show).offset(skip).limit(limit).all()

# ❌ Mauvais - Pas de type hints
def get_shows(db, skip=0, limit=100):
    return db.query(Show).offset(skip).limit(limit).all()
```

---

### 3. Docstrings

```python
# ✅ Bon - Docstring Google style
def create_show(db: Session, show: ShowCreate, user_id: int) -> Show:
    """
    Crée un nouveau show.
    
    Args:
        db: Session de base de données
        show: Données du show à créer
        user_id: ID de l'utilisateur créateur
        
    Returns:
        Le show créé
        
    Raises:
        ValueError: Si le nom du show est vide
        IntegrityError: Si un show avec le même nom existe déjà
    """
    if not show.name:
        raise ValueError("Show name cannot be empty")
    
    new_show = Show(**show.dict(), user_id=user_id)
    db.add(new_show)
    db.commit()
    db.refresh(new_show)
    return new_show

# ❌ Mauvais - Pas de docstring
def create_show(db, show, user_id):
    new_show = Show(**show.dict(), user_id=user_id)
    db.add(new_show)
    db.commit()
    return new_show
```

---

### 4. Gestion des erreurs

```python
# ✅ Bon - Erreurs explicites
from fastapi import HTTPException, status

@router.get("/{show_id}", response_model=ShowResponse)
def get_show(show_id: int, db: Session = Depends(get_db)):
    show = crud_show.get_show(db, show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found"
        )
    return show

# ❌ Mauvais - Pas de gestion d'erreur
@router.get("/{show_id}")
def get_show(show_id: int, db: Session = Depends(get_db)):
    return crud_show.get_show(db, show_id)  # Peut retourner None
```

---

### 5. Tests obligatoires

Pour chaque nouvelle fonctionnalité, ajouter des tests :

```python
# tests/test_categories.py
def test_create_category(client, token_headers):
    """Test de création d'une catégorie"""
    response = client.post(
        "/categories",
        json={"name": "Actualités"},
        headers=token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Actualités"
    assert "id" in data

def test_get_category_not_found(client, token_headers):
    """Test 404 sur catégorie inexistante"""
    response = client.get("/categories/99999", headers=token_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

**Coverage minimum requis : 80%**

```bash
# Vérifier la couverture
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 📝 Commits et messages

### Convention Conventional Commits

```
<type>(<scope>): <description>

[corps optionnel]

[footer optionnel]
```

**Types autorisés :**
- `feat` : Nouvelle fonctionnalité
- `fix` : Correction de bug
- `docs` : Documentation
- `style` : Formatage (pas de changement de logique)
- `refactor` : Refactoring
- `test` : Ajout de tests
- `chore` : Maintenance (dépendances, config)
- `perf` : Amélioration de performance

---

### Exemples de bons messages

```bash
# Feature
git commit -m "feat(shows): add categories endpoint with CRUD operations"

# Fix
git commit -m "fix(auth): prevent token expiration during active session"

# Docs
git commit -m "docs(api): add categories section to API_ENDPOINTS.md"

# Test
git commit -m "test(categories): add integration tests for CRUD operations"

# Refactor
git commit -m "refactor(crud): extract common pagination logic to base class"

# Breaking change
git commit -m "feat(auth)!: change JWT token structure

BREAKING CHANGE: JWT tokens now include user roles.
Clients must update to handle new token format."
```

---

### Exemples de mauvais messages

```bash
# ❌ Trop vague
git commit -m "fix bug"
git commit -m "update code"
git commit -m "changes"

# ❌ Pas de type
git commit -m "add categories"

# ❌ Trop long dans le titre
git commit -m "feat: add categories endpoint with full CRUD operations and validation and tests and documentation"
```

---

## 🔍 Pull Requests

### Template de PR

```markdown
## Description
Brève description des changements.

## Type de changement
- [ ] 🐛 Bug fix (changement non-breaking qui corrige un problème)
- [ ] ✨ Nouvelle fonctionnalité (changement non-breaking qui ajoute une feature)
- [ ] 💥 Breaking change (fix ou feature qui modifie le comportement existant)
- [ ] 📝 Documentation

## Checklist
- [ ] Mon code suit les standards du projet
- [ ] J'ai ajouté des tests qui prouvent mon fix/feature
- [ ] Tous les tests passent (`pytest`)
- [ ] J'ai mis à jour la documentation si nécessaire
- [ ] J'ai formaté mon code avec `black`
- [ ] J'ai vérifié le linting avec `flake8`
- [ ] J'ai créé/mis à jour les migrations Alembic si nécessaire

## Tests
Décrivez les tests ajoutés.

## Screenshots (si applicable)
Ajoutez des captures d'écran pour les changements UI.

## Notes supplémentaires
Informations contextuelles supplémentaires.
```

---

### Exemple de PR complète

```markdown
## Description
Ajoute un système de catégories pour les shows avec CRUD complet.

## Type de changement
- [x] ✨ Nouvelle fonctionnalité

## Checklist
- [x] Mon code suit les standards du projet
- [x] J'ai ajouté des tests (couverture 95%)
- [x] Tous les tests passent
- [x] Documentation mise à jour (DATA_MODELS.md, API_ENDPOINTS.md)
- [x] Code formaté avec black
- [x] Linting OK
- [x] Migration Alembic créée (abc123_add_categories_table.py)

## Tests
- `test_create_category` : Création de catégorie
- `test_get_categories` : Liste des catégories
- `test_get_category_not_found` : 404 sur catégorie inexistante
- `test_update_category` : Mise à jour
- `test_delete_category` : Soft delete
- `test_show_with_category` : Relation Show ↔ Category

## Notes supplémentaires
Les shows peuvent désormais avoir une catégorie optionnelle.
API backward-compatible (category_id nullable).
```

---

## 👀 Review process

### Ce que les reviewers vérifient

1. **Fonctionnalité**
   - Le code fait-il ce qu'il est censé faire ?
   - Y a-t-il des edge cases non gérés ?

2. **Tests**
   - Les tests couvrent-ils tous les cas ?
   - Les tests passent-ils ?

3. **Code quality**
   - Le code est-il lisible et maintenable ?
   - Y a-t-il de la duplication ?
   - Les noms de variables sont-ils clairs ?

4. **Performance**
   - Y a-t-il des requêtes N+1 ?
   - Les opérations sont-elles optimisées ?

5. **Sécurité**
   - Y a-t-il des failles de sécurité ?
   - Les permissions sont-elles vérifiées ?

6. **Documentation**
   - La documentation est-elle à jour ?
   - Les docstrings sont-elles présentes ?

---

### Répondre aux commentaires

```markdown
# ✅ Bon
> Reviewer: Cette fonction devrait gérer le cas où show est None

Bonne remarque ! J'ai ajouté une vérification et un test dans abc123.

# ❌ Mauvais
> Reviewer: Cette fonction devrait gérer le cas où show est None

Non, ça marche comme ça.
```

---

### Résoudre les conflits

```bash
# Synchroniser avec upstream
git fetch upstream
git checkout main
git merge upstream/main

# Rebaser votre branche
git checkout feature/add-categories
git rebase main

# Résoudre les conflits
# ... éditer les fichiers ...
git add .
git rebase --continue

# Force push (votre branche uniquement !)
git push origin feature/add-categories --force
```

---

## 🏆 Bonnes pratiques

### 1. Commits atomiques

Chaque commit doit représenter un changement logique unique.

```bash
# ✅ Bon
git commit -m "feat(categories): add Category model"
git commit -m "feat(categories): add CRUD operations"
git commit -m "feat(categories): add API routes"
git commit -m "test(categories): add integration tests"
git commit -m "docs(categories): update documentation"

# ❌ Mauvais
git commit -m "add categories feature" # Tout en un seul commit
```

---

### 2. Garder les PRs petites

- **Idéal :** < 400 lignes changées
- **Acceptable :** 400-800 lignes
- **Trop gros :** > 800 lignes (diviser en plusieurs PRs)

```bash
# Voir le nombre de lignes changées
git diff --stat main
```

---

### 3. Tester localement avant de push

```bash
# Checklist avant push
black app/ routeur/ tests/          # Formatter
flake8 app/ routeur/ tests/         # Linter
mypy app/ routeur/                  # Type checker
pytest -v                           # Tests
alembic upgrade head                # Migrations
uvicorn maintest:app --reload       # Lancer l'API
```

---

### 4. Répondre rapidement aux reviews

- Répondre dans les 24-48h
- Si vous êtes bloqué, demandez de l'aide
- N'hésitez pas à discuter

---

## 🎓 Ressources

### Documentation externe

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Documentation interne

- [Architecture](README.md)
- [Modèles de données](DATA_MODELS.md)
- [Endpoints API](API_ENDPOINTS.md)
- [Guide de développement](DEVELOPMENT_GUIDE.md)

---

## ❓ Questions ?

- **Email :** hapson@audace.ovh
- **GitHub Issues :** https://github.com/lwilly3/api.audace/issues
- **Documentation :** [docs/architecture/](.)

---

**Merci de contribuer à l'API Audace ! 🚀**

**Dernière mise à jour :** 11 décembre 2025

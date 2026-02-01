# ✅ Architecture Guardian - Checklist de Validation

## 🔍 Validation Pré-Commit

### Structure des Fichiers
- [ ] Le fichier est dans le bon dossier selon son type
- [ ] Le nom suit la convention : `{type}_{entity}.py`
- [ ] Pas de fichier orphelin (non importé)

### Imports
- [ ] Aucun import de `routeur/` dans `app/db/crud/`
- [ ] Aucun import de `app/models/` dans `app/schemas/`
- [ ] Les imports sont triés (stdlib → third-party → local)

### Modèles SQLAlchemy
- [ ] Hérite de `BaseModel` (soft delete)
- [ ] `__tablename__` défini
- [ ] Relations avec `back_populates`
- [ ] Foreign keys avec `nullable` explicite
- [ ] Index sur colonnes fréquemment requêtées

### CRUD Functions
- [ ] Filtre `is_deleted == False` par défaut
- [ ] Pagination avec `skip` et `limit`
- [ ] HTTPException 404 si non trouvé
- [ ] Docstring avec Args/Returns/Raises

### Routes
- [ ] `router = APIRouter(prefix=..., tags=[...])`
- [ ] Dépendance `get_db` via `Depends()`
- [ ] Authentification via `get_current_user` si nécessaire
- [ ] Response model défini
- [ ] Status codes appropriés (201, 204, etc.)

---

## 🔍 Validation Pré-PR

### Database
- [ ] Migration Alembic créée si modèle modifié
- [ ] Migration testée : `upgrade` + `downgrade`
- [ ] Pas de perte de données

### Tests
- [ ] Tests unitaires pour nouveau CRUD
- [ ] Tests d'intégration pour nouvelles routes
- [ ] `pytest` passe sans erreur

### Code Quality
- [ ] Pas de `# TODO` ou `# FIXME` non résolu
- [ ] Pas de code commenté
- [ ] Exceptions loggées (pas de `except: pass`)
- [ ] `model_dump()` au lieu de `dict()`

### Documentation
- [ ] Docstrings complètes
- [ ] CHANGELOG mis à jour si changement notable
- [ ] AGENT.md mis à jour si nouveau pattern

---

## 🛠️ Commandes de Validation

```bash
# Structure
find . -name "*.py" -path "*/routeur/*" | head

# Imports circulaires
grep -r "from routeur" app/db/crud/

# Hard delete
grep -rn "db.delete(" routeur/ app/db/crud/

# dict() déprécié  
grep -rn "\.dict()" app/ routeur/

# Migrations
alembic current
alembic history --verbose

# Tests
pytest -v
pytest --cov=app
```

---

## 🚨 Red Flags (Blocage Automatique)

| Problème | Gravité | Action |
|----------|---------|--------|
| Import circulaire | 🔴 Critique | Refactorer immédiatement |
| Hard delete sur modèle métier | 🔴 Critique | Convertir en soft delete |
| Modèle sans migration | 🔴 Critique | Créer migration |
| Exception ignorée | 🟠 Important | Logger et gérer |
| dict() Pydantic v2 | 🟡 Warning | Remplacer par model_dump() |

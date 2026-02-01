# 🔧 Service Pattern

> **Skill recommandé** : Séparation de la logique métier complexe dans des services dédiés.

---

## 📋 Contexte du Projet

### Organisation Actuelle

Le projet api.audace utilise actuellement une architecture **Routes → CRUD** :

```
routeur/show_route.py → app/db/crud/crud_show.py → app/models/model_show.py
```

**Constat** : Certains fichiers CRUD contiennent de la logique métier complexe :
- `crud_show.py` : `create_show_with_details()` (création + segments + présentateurs)
- `crud_users.py` : `get_user_or_404_with_permissions()` (user + permissions + rôles)
- `crud_permissions.py` : `initialize_user_permissions()` (création + 40 permissions)

### Problèmes Identifiés

1. **CRUD trop complexes** : Mélange opérations simples et orchestration
2. **Logique dupliquée** : Validation métier répétée
3. **Tests difficiles** : Fonctions CRUD avec trop de responsabilités
4. **Maintenance complexe** : Modifications risquées

---

## 🎯 Objectif du Skill

Introduire une couche **Services** optionnelle pour :
1. **Isoler** la logique métier complexe
2. **Simplifier** les CRUD (opérations atomiques)
3. **Faciliter** les tests
4. **Centraliser** les validations métier

---

## ✅ Règles Obligatoires

### 1. Quand Utiliser un Service

| Situation | CRUD | Service |
|-----------|------|---------|
| CRUD simple (create, get, update, delete) | ✅ | ❌ |
| Opération sur une seule entité | ✅ | ❌ |
| Orchestration multi-entités | ❌ | ✅ |
| Validation métier complexe | ❌ | ✅ |
| Transactions avec rollback | ❌ | ✅ |
| Appels API externes | ❌ | ✅ |
| Notifications/Events | ❌ | ✅ |

### 2. Structure Proposée

```
app/
├── db/
│   └── crud/           # Opérations atomiques simples
├── services/           # Logique métier complexe (NOUVEAU)
│   ├── __init__.py
│   ├── show_service.py
│   ├── user_service.py
│   └── permission_service.py
├── models/
└── schemas/
```

### 3. Architecture avec Services

```
ROUTEUR (API)
    │
    ▼
SERVICE (Logique métier)  ← NOUVEAU
    │
    ▼
CRUD (Opérations atomiques)
    │
    ▼
MODELS (SQLAlchemy)
```

### 4. Structure d'un Service

```python
# app/services/show_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional
import logging

from app.db.crud import crud_show, crud_segment, crud_presenter
from app.schemas.schema_show import ShowCreateWithDetail, ShowResponse
from app.models.model_user import User

logger = logging.getLogger(__name__)


class ShowService:
    """
    Service pour la gestion des shows.
    
    Responsabilités:
        - Création de show avec détails (segments, présentateurs)
        - Validation des règles métier
        - Orchestration des opérations CRUD
        - Gestion des transactions
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_show_with_details(
        self,
        show_data: ShowCreateWithDetail,
        current_user: User
    ) -> ShowResponse:
        """
        Crée un show complet avec segments et présentateurs.
        
        Args:
            show_data: Données du show avec détails
            current_user: Utilisateur créateur
        
        Returns:
            ShowResponse avec toutes les relations
        
        Raises:
            HTTPException 400: Données invalides
            HTTPException 403: Permission insuffisante
            HTTPException 500: Erreur lors de la création
        """
        try:
            # 1. Validation métier
            self._validate_show_creation(show_data, current_user)
            
            # 2. Création du show
            show = crud_show.create_show(
                self.db,
                show_data=show_data,
                created_by=current_user.id
            )
            
            # 3. Création des segments
            for segment_data in show_data.segments:
                segment = crud_segment.create_segment(
                    self.db,
                    segment_data=segment_data,
                    show_id=show.id
                )
                
                # 4. Association des invités
                for guest_id in segment_data.guest_ids:
                    crud_segment.add_guest(self.db, segment.id, guest_id)
            
            # 5. Association des présentateurs
            for presenter_id in show_data.presenter_ids:
                crud_show.add_presenter(self.db, show.id, presenter_id)
            
            # 6. Commit transaction
            self.db.commit()
            self.db.refresh(show)
            
            logger.info(f"Show {show.id} created by user {current_user.id}")
            return show
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating show: {e}")
            raise HTTPException(status_code=500, detail="Show creation failed")
    
    def _validate_show_creation(
        self,
        show_data: ShowCreateWithDetail,
        current_user: User
    ) -> None:
        """Valide les règles métier pour la création d'un show."""
        
        # Vérifier permission
        if not current_user.permissions.can_create_showplan:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Vérifier que les présentateurs existent
        for presenter_id in show_data.presenter_ids:
            if not crud_presenter.exists(self.db, presenter_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Presenter {presenter_id} not found"
                )
        
        # Autres validations métier...
```

### 5. Utilisation dans les Routes

```python
# routeur/show_route.py

from app.services.show_service import ShowService

@router.post("/detail", status_code=status.HTTP_201_CREATED)
def create_show_with_details(
    show_data: ShowCreateWithDetail,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un show avec segments et présentateurs."""
    service = ShowService(db)
    show = service.create_show_with_details(show_data, current_user)
    return {"message": "Show created successfully", "show": show}
```

### 6. CRUD Simplifiés

```python
# app/db/crud/crud_show.py (simplifié)

def create_show(db: Session, show_data: ShowCreate, created_by: int) -> Show:
    """Crée un show simple (sans relations)."""
    show = Show(**show_data.model_dump(), created_by=created_by)
    db.add(show)
    db.flush()
    return show


def add_presenter(db: Session, show_id: int, presenter_id: int) -> None:
    """Ajoute un présentateur à un show."""
    assoc = ShowPresenter(show_id=show_id, presenter_id=presenter_id)
    db.add(assoc)
    db.flush()


def get_show_by_id(db: Session, show_id: int) -> Show:
    """Récupère un show par ID."""
    show = db.query(Show).filter(
        Show.id == show_id,
        Show.is_deleted == False
    ).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show
```

---

## 🚫 Interdictions Explicites

### ❌ Logique Métier dans Route
```python
# ❌ INTERDIT
@router.post("/shows")
def create_show(show_data, db, current_user):
    # Validation métier dans route !
    if not current_user.permissions.can_create_showplan:
        raise HTTPException(403)
    
    show = Show(**show_data.dict())
    db.add(show)
    # Création segments...
    db.commit()
    return show

# ✅ CORRECT
@router.post("/shows")
def create_show(show_data, db, current_user):
    service = ShowService(db)
    return service.create_show_with_details(show_data, current_user)
```

### ❌ Service sans Gestion Transaction
```python
# ❌ INTERDIT (pas de rollback)
class ShowService:
    def create_show_with_details(self, data):
        show = crud_show.create(self.db, data)
        for segment in data.segments:
            crud_segment.create(self.db, segment)  # Erreur ici = show orphelin !
        self.db.commit()

# ✅ CORRECT
class ShowService:
    def create_show_with_details(self, data):
        try:
            show = crud_show.create(self.db, data)
            for segment in data.segments:
                crud_segment.create(self.db, segment)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
```

### ❌ CRUD avec Logique Métier
```python
# ❌ INTERDIT (CRUD trop complexe)
def create_show_with_details(db, show_data, user_id):
    # Validation métier
    if user_id not in get_allowed_users():
        raise HTTPException(403)
    
    # Création + relations + notifications...
    show = Show(...)
    for segment in show_data.segments:
        # 50 lignes de logique...
    
    send_notification(user_id, "Show created")
    return show

# ✅ CORRECT - Séparer en Service
# CRUD : opérations atomiques
def create_show(db, show_data): ...
def add_segment(db, show_id, segment_data): ...

# Service : orchestration
class ShowService:
    def create_show_with_details(self, show_data, user):
        self._validate(show_data, user)
        show = crud_show.create_show(self.db, show_data)
        for segment in show_data.segments:
            crud_show.add_segment(self.db, show.id, segment)
        self._notify(user, show)
        return show
```

---

## 📝 Exemples Concrets du Projet

### Avant : CRUD Complexe (Actuel)
```python
# app/db/crud/crud_show.py (ACTUEL - trop complexe)
def create_show_with_details(db, show_data, curent_user_id):
    try:
        # Création show
        show = Show(**show_data.model_dump(...))
        show.created_by = curent_user_id
        db.add(show)
        db.flush()
        
        # Création segments (50+ lignes)
        for segment_data in show_data.segments:
            segment = Segment(...)
            db.add(segment)
            db.flush()
            
            # Invités
            for guest_id in segment_data.guests:
                assoc = SegmentGuest(...)
                db.add(assoc)
        
        # Présentateurs
        for presenter_id in show_data.presenters:
            assoc = ShowPresenter(...)
            db.add(assoc)
        
        db.commit()
        return show
    except Exception as e:
        db.rollback()
        raise
```

### Après : Service + CRUD Simples (Recommandé)
```python
# app/services/show_service.py
class ShowService:
    def create_show_with_details(self, show_data, current_user):
        self._validate_permissions(current_user)
        
        try:
            show = crud_show.create_show(self.db, show_data, current_user.id)
            self._create_segments(show.id, show_data.segments)
            self._assign_presenters(show.id, show_data.presenter_ids)
            self.db.commit()
            return show
        except Exception:
            self.db.rollback()
            raise

# app/db/crud/crud_show.py (simplifié)
def create_show(db, show_data, created_by):
    show = Show(**show_data.model_dump(exclude={'segments', 'presenter_ids'}))
    show.created_by = created_by
    db.add(show)
    db.flush()
    return show
```

---

## ✅ Checklist de Validation

### Avant de Créer un Service

- [ ] La logique implique plusieurs entités ?
- [ ] Il y a des validations métier complexes ?
- [ ] Le CRUD actuel dépasse 30 lignes ?
- [ ] Il y a des effets de bord (notifications, logs) ?

### Structure du Service

- [ ] Classe avec `__init__(self, db: Session)`
- [ ] Méthodes publiques avec docstrings
- [ ] Gestion des transactions (try/rollback)
- [ ] Logging des opérations importantes
- [ ] Validation métier centralisée

### Tests

- [ ] Tests unitaires pour chaque méthode
- [ ] Mock des dépendances CRUD
- [ ] Tests des cas d'erreur
- [ ] Tests des rollbacks

---

## 📁 Template Service

```python
# app/services/{entity}_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

from app.db.crud import crud_{entity}
from app.schemas.schema_{entity} import {Entity}Create
from app.models.model_user import User

logger = logging.getLogger(__name__)


class {Entity}Service:
    """
    Service pour la gestion des {entity}s.
    
    Responsabilités:
        - Orchestration des opérations CRUD
        - Validation des règles métier
        - Gestion des transactions
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_with_details(
        self,
        data: {Entity}Create,
        current_user: User
    ):
        """Crée un {entity} avec toutes ses relations."""
        try:
            self._validate(data, current_user)
            
            entity = crud_{entity}.create(self.db, data)
            # ... opérations supplémentaires
            
            self.db.commit()
            self.db.refresh(entity)
            
            logger.info(f"{Entity} {entity.id} created by {current_user.id}")
            return entity
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {entity}: {e}")
            raise HTTPException(status_code=500, detail="Creation failed")
    
    def _validate(self, data, current_user):
        """Valide les règles métier."""
        # Implémentation...
        pass
```

---

## 📚 Ressources Associées

- [architecture-guardian](../architecture-guardian/skill.md) - Structure globale
- [endpoint-creator](../endpoint-creator/skill.md) - Utilisation dans routes
- [test-enforcer](../test-enforcer/skill.md) - Tests de services

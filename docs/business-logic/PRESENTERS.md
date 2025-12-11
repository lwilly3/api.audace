# 🎤 Module PRESENTERS - Gestion des Présentateurs

Documentation complète de la logique métier pour la gestion des présentateurs radio.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Règles métier](#règles-métier)
5. [Relations](#relations)
6. [Contraintes](#contraintes)
7. [Exemples d'utilisation](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités du module
- Gestion des profils de présentateurs (CRUD)
- Association des présentateurs avec les utilisateurs du système
- Gestion des photos de profil
- Récupération des shows animés par un présentateur
- Recherche de présentateurs
- Statistiques d'activité

### Fichier source
`app/db/crud/crud_presenters.py`

### Dépendances
```python
# Modèles
from app.models import Presenter, User, Show
from app.models import ShowPresenter  # Table d'association

# Schémas
from app.schemas import PresenterCreate, PresenterUpdate
```

---

## 🏗️ Architecture

### Modèle Presenter

```python
Presenter:
    id: int (PK)
    name: str (NOT NULL)
    biography: text
    contact_info: text
    profile_picture: str (URL ou chemin)
    user_id: int (FK → User, UNIQUE)  # Lien avec compte utilisateur
    is_deleted: bool (default: False)
    created_at: datetime
    updated_at: datetime
    
    # Relations
    user: User (One-to-One)  # Un présentateur = un compte utilisateur
    shows: List[Show] (Many-to-Many via show_presenters)
```

### Relation Presenter ↔ User

**Principe :** Un présentateur est un utilisateur avec un profil public enrichi.

```python
User (compte système)
  ↓ (One-to-One)
Presenter (profil public)
  ↓ (Many-to-Many)
Shows (émissions animées)
```

**Contrainte d'unicité :**
```sql
ALTER TABLE presenters ADD CONSTRAINT unique_user_id UNIQUE (user_id);
```

Un utilisateur ne peut être lié qu'à un seul profil présentateur.

### Flux de création

```
1. Créer d'abord le User (si pas existant)
     ↓
2. Créer le Presenter avec user_id
     ↓
3. Validation : user_id existe et n'est pas déjà utilisé
     ↓
4. Assignation automatique des permissions "Presenter"
```

---

## 🔧 Fonctions métier

### 1. create_presenter()

**Signature :**
```python
def create_presenter(
    db: Session,
    presenter: PresenterCreate,
    current_user_id: int
) -> Presenter
```

**Description :**
Crée un nouveau profil présentateur et l'associe à un utilisateur existant.

**Logique métier :**

#### Étape 1 : Validation de l'utilisateur
```python
def create_presenter(db: Session, presenter: PresenterCreate, current_user_id: int):
    # Vérifier que user_id est fourni
    if not presenter.user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id is required to create a presenter"
        )
    
    # Vérifier que l'utilisateur existe
    user = db.query(User).filter(User.id == presenter.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {presenter.user_id} not found"
        )
    
    # Vérifier que l'utilisateur n'est pas déjà présentateur
    existing_presenter = db.query(Presenter).filter(
        Presenter.user_id == presenter.user_id
    ).first()
    
    if existing_presenter:
        raise HTTPException(
            status_code=400,
            detail=f"User {user.username} is already a presenter"
        )
```

#### Étape 2 : Création du profil
```python
    # Créer le profil présentateur
    new_presenter = Presenter(
        name=presenter.name,
        biography=presenter.biography,
        contact_info=presenter.contact_info,
        profile_picture=presenter.profile_picture,
        user_id=presenter.user_id
    )
    
    db.add(new_presenter)
    db.flush()  # Obtenir l'ID sans commit
```

#### Étape 3 : Assignation des permissions
```python
    # Assigner le rôle "Presenter"
    presenter_role = db.query(Role).filter(Role.name == "Presenter").first()
    
    if presenter_role:
        # Ajouter le rôle à l'utilisateur
        if presenter_role not in user.roles:
            user.roles.append(presenter_role)
    
    # Mettre à jour les permissions utilisateur
    user_permissions = db.query(UserPermission).filter(
        UserPermission.user_id == user.id
    ).first()
    
    if user_permissions:
        # Activer les permissions liées aux présentateurs
        user_permissions.create_show = True
        user_permissions.update_show = True
        user_permissions.view_show = True
        # ... autres permissions pertinentes
    
    db.commit()
    db.refresh(new_presenter)
    
    return new_presenter
```

**Paramètres :**
- `db` (Session) : Session SQLAlchemy
- `presenter` (PresenterCreate) : Données du présentateur
- `current_user_id` (int) : ID de l'utilisateur créateur (pour audit)

**PresenterCreate Schema :**
```python
class PresenterCreate(BaseModel):
    name: str  # Nom public (peut différer du username)
    biography: Optional[str] = None
    contact_info: Optional[str] = None
    profile_picture: Optional[str] = None
    user_id: int  # OBLIGATOIRE
```

**Erreurs :**
- `HTTPException(400)` : user_id manquant ou utilisateur déjà présentateur
- `HTTPException(404)` : user_id inexistant

**Cas d'usage :**
- Promotion d'un utilisateur en présentateur
- Onboarding de nouveaux animateurs radio

---

### 2. get_presenter()

**Signature :**
```python
def get_presenter(db: Session, presenter_id: int) -> Presenter
```

**Description :**
Récupère un présentateur par son ID avec toutes ses informations.

**Logique métier :**
```python
def get_presenter(db: Session, presenter_id: int):
    presenter = db.query(Presenter).filter(
        Presenter.id == presenter_id,
        Presenter.is_deleted == False  # Exclure les supprimés
    ).first()
    
    if not presenter:
        raise HTTPException(
            status_code=404,
            detail=f"Presenter with ID {presenter_id} not found"
        )
    
    return presenter
```

**Optimisation avec relations :**
```python
from sqlalchemy.orm import joinedload

def get_presenter_with_user(db: Session, presenter_id: int):
    """Version optimisée avec données utilisateur"""
    presenter = db.query(Presenter).options(
        joinedload(Presenter.user)  # Charge l'utilisateur associé
    ).filter(
        Presenter.id == presenter_id,
        Presenter.is_deleted == False
    ).first()
    
    if not presenter:
        raise HTTPException(404, "Presenter not found")
    
    return presenter
```

**Format de retour enrichi :**
```python
def get_presenter_details(db: Session, presenter_id: int) -> dict:
    """Retourne le présentateur avec statistiques"""
    presenter = get_presenter(db, presenter_id)
    
    # Compter les shows animés
    show_count = db.query(ShowPresenter).filter(
        ShowPresenter.presenter_id == presenter_id
    ).count()
    
    # Shows actifs (non archivés)
    active_shows = db.query(ShowPresenter).join(Show).filter(
        ShowPresenter.presenter_id == presenter_id,
        Show.status.in_(["published", "live", "approved"])
    ).count()
    
    return {
        "id": presenter.id,
        "name": presenter.name,
        "biography": presenter.biography,
        "contact_info": presenter.contact_info,
        "profile_picture": presenter.profile_picture,
        "user": {
            "id": presenter.user.id,
            "username": presenter.user.username,
            "email": presenter.user.email
        } if presenter.user else None,
        "statistics": {
            "total_shows": show_count,
            "active_shows": active_shows
        }
    }
```

---

### 3. get_presenters()

**Signature :**
```python
def get_presenters(
    db: Session,
    skip: int = 0,
    limit: int = 10
) -> List[Presenter]
```

**Description :**
Liste tous les présentateurs actifs avec pagination.

**Logique métier :**
```python
def get_presenters(db: Session, skip: int = 0, limit: int = 10):
    presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False
    ).order_by(
        Presenter.created_at.desc()  # Plus récents en premier
    ).offset(skip).limit(limit).all()
    
    return presenters
```

**Version avec statistiques :**
```python
from sqlalchemy import func

def get_presenters_with_stats(db: Session, skip: int = 0, limit: int = 10):
    """Liste avec nombre de shows par présentateur"""
    presenters = db.query(
        Presenter,
        func.count(ShowPresenter.show_id).label("show_count")
    ).outerjoin(ShowPresenter).filter(
        Presenter.is_deleted == False
    ).group_by(Presenter.id).order_by(
        Presenter.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Sérialiser
    result = []
    for presenter, show_count in presenters:
        result.append({
            "id": presenter.id,
            "name": presenter.name,
            "biography": presenter.biography,
            "profile_picture": presenter.profile_picture,
            "show_count": show_count
        })
    
    return result
```

---

### 4. update_presenter()

**Signature :**
```python
def update_presenter(
    db: Session,
    presenter_id: int,
    presenter_update: PresenterUpdate
) -> Presenter
```

**Description :**
Met à jour les informations d'un présentateur.

**Logique métier :**
```python
def update_presenter(db: Session, presenter_id: int, presenter_update: PresenterUpdate):
    # Récupérer le présentateur
    presenter = get_presenter(db, presenter_id)
    
    # Appliquer les modifications
    update_data = presenter_update.model_dump(exclude_unset=True)
    
    # user_id ne peut pas être modifié après création
    if "user_id" in update_data:
        raise HTTPException(
            status_code=400,
            detail="user_id cannot be changed after creation"
        )
    
    for key, value in update_data.items():
        setattr(presenter, key, value)
    
    # Mise à jour automatique de updated_at (si défini dans le modèle)
    presenter.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(presenter)
    
    return presenter
```

**Champs modifiables :**
```python
class PresenterUpdate(BaseModel):
    name: Optional[str] = None
    biography: Optional[str] = None
    contact_info: Optional[str] = None
    profile_picture: Optional[str] = None
    # user_id: INTERDIT (relation immuable)
```

**Upload de photo de profil :**
```python
from fastapi import UploadFile

async def update_profile_picture(
    db: Session,
    presenter_id: int,
    file: UploadFile
) -> Presenter:
    """Upload et mise à jour de la photo"""
    presenter = get_presenter(db, presenter_id)
    
    # Sauvegarder le fichier
    file_path = f"uploads/presenters/{presenter_id}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Mettre à jour le chemin dans la DB
    presenter.profile_picture = file_path
    db.commit()
    db.refresh(presenter)
    
    return presenter
```

---

### 5. delete_presenter()

**Signature :**
```python
def delete_presenter(db: Session, presenter_id: int) -> dict
```

**Description :**
Suppression logique (soft delete) d'un présentateur.

**Logique métier :**
```python
def delete_presenter(db: Session, presenter_id: int):
    presenter = get_presenter(db, presenter_id)
    
    # Vérifier qu'il n'a pas de shows actifs
    active_shows = db.query(ShowPresenter).join(Show).filter(
        ShowPresenter.presenter_id == presenter_id,
        Show.status.in_(["published", "live", "approved"])
    ).count()
    
    if active_shows > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete presenter with {active_shows} active shows. "
                   f"Please archive or reassign shows first."
        )
    
    # Soft delete
    presenter.is_deleted = True
    presenter.updated_at = datetime.utcnow()
    
    # Optionnel : retirer le rôle "Presenter" de l'utilisateur
    if presenter.user:
        presenter_role = db.query(Role).filter(Role.name == "Presenter").first()
        if presenter_role and presenter_role in presenter.user.roles:
            presenter.user.roles.remove(presenter_role)
    
    db.commit()
    
    return {
        "message": f"Presenter {presenter.name} successfully deleted",
        "id": presenter_id
    }
```

**Suppression physique (hard delete) :**
```python
def hard_delete_presenter(db: Session, presenter_id: int):
    """⚠️ Suppression définitive - À utiliser avec prudence"""
    presenter = get_presenter(db, presenter_id)
    
    # Vérifier qu'il n'a AUCUN show (même archivé)
    any_shows = db.query(ShowPresenter).filter(
        ShowPresenter.presenter_id == presenter_id
    ).count()
    
    if any_shows > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot permanently delete presenter with associated shows"
        )
    
    db.delete(presenter)
    db.commit()
    
    return {"message": "Presenter permanently deleted"}
```

---

### 6. search_presenters()

**Signature :**
```python
def search_presenters(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 10
) -> List[Presenter]
```

**Description :**
Recherche de présentateurs par nom ou biographie.

**Logique métier :**
```python
def search_presenters(db: Session, query: str, skip: int = 0, limit: int = 10):
    if not query or len(query.strip()) == 0:
        raise HTTPException(400, "Search query cannot be empty")
    
    search_term = f"%{query}%"
    
    presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False,
        or_(
            Presenter.name.ilike(search_term),
            Presenter.biography.ilike(search_term),
            Presenter.contact_info.ilike(search_term)
        )
    ).order_by(
        Presenter.name.asc()
    ).offset(skip).limit(limit).all()
    
    return presenters
```

**Recherche avancée avec score de pertinence :**
```python
from sqlalchemy import case

def search_presenters_ranked(db: Session, query: str):
    """Recherche avec classement par pertinence"""
    search_term = f"%{query}%"
    
    # Score de pertinence
    relevance = case(
        (Presenter.name.ilike(query), 3),  # Correspondance exacte
        (Presenter.name.ilike(f"{query}%"), 2),  # Commence par
        else_=1  # Contient
    )
    
    presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False,
        or_(
            Presenter.name.ilike(search_term),
            Presenter.biography.ilike(search_term)
        )
    ).order_by(
        relevance.desc(),
        Presenter.name.asc()
    ).all()
    
    return presenters
```

---

## 📏 Règles métier

### 1. Relation User-Presenter
- Un utilisateur peut devenir présentateur (1-to-1)
- Un présentateur doit avoir un user_id valide
- `user_id` immuable après création
- Suppression du présentateur ne supprime pas l'utilisateur

### 2. Permissions automatiques
Quand un utilisateur devient présentateur :
- Rôle "Presenter" assigné
- Permissions `create_show`, `update_show`, `view_show` activées
- Peut gérer ses propres shows

### 3. Suppression
- Soft delete par défaut (`is_deleted = True`)
- Impossible si shows actifs
- Préserver les associations passées

### 4. Profile Picture
- Format recommandé : JPG/PNG
- Taille max : 5 MB
- Stockage : `/uploads/presenters/{id}/`
- URL publique accessible

---

## 🔗 Relations

### Dépendances entrantes
- **crud_users.py** : Création d'utilisateurs associés
- **crud_permissions.py** : Gestion des rôles et permissions
- **presenter_route.py** : Routes API

### Dépendances sortantes
- **crud_show.py** : Association aux shows
- **crud_audit_logs.py** : Logging des actions

### Diagramme de relations
```
User (1) ───────→ (1) Presenter
                     │
                     │ (Many-to-Many)
                     ↓
                   Show
                     │
                     └───→ Segments → Guests
```

---

## ⚠️ Contraintes

### Base de données
```sql
-- user_id unique et obligatoire
ALTER TABLE presenters ADD CONSTRAINT unique_user_id UNIQUE (user_id);
ALTER TABLE presenters ALTER COLUMN user_id SET NOT NULL;

-- Index pour performances
CREATE INDEX idx_presenter_user_id ON presenters(user_id);
CREATE INDEX idx_presenter_name ON presenters(name);
CREATE INDEX idx_presenter_is_deleted ON presenters(is_deleted);
```

### Validation des données
```python
class PresenterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    biography: Optional[str] = Field(None, max_length=2000)
    contact_info: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[HttpUrl] = None  # URL valide
    user_id: int = Field(..., gt=0)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
```

---

## 💡 Exemples d'utilisation

### Créer un présentateur depuis un utilisateur
```python
@router.post("/presenters", response_model=PresenterResponse)
def create_new_presenter(
    presenter: PresenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)  # Admin seulement
):
    """Créer un nouveau profil présentateur"""
    return crud_presenters.create_presenter(db, presenter, current_user.id)
```

### Récupérer un présentateur avec ses shows
```python
@router.get("/presenters/{presenter_id}/shows")
def get_presenter_shows(
    presenter_id: int,
    db: Session = Depends(get_db)
):
    """Liste des shows animés par un présentateur"""
    presenter = crud_presenters.get_presenter(db, presenter_id)
    
    shows = db.query(Show).join(ShowPresenter).filter(
        ShowPresenter.presenter_id == presenter_id,
        Show.is_deleted == False
    ).order_by(Show.broadcast_date.desc()).all()
    
    return {
        "presenter": presenter,
        "shows": shows
    }
```

### Rechercher des présentateurs
```python
@router.get("/presenters/search")
def search(
    q: str = Query(..., min_length=2),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Rechercher des présentateurs"""
    return crud_presenters.search_presenters(db, q, skip, limit)
```

---

**Navigation :**
- [← SHOWS.md](SHOWS.md)
- [→ PERMISSIONS.md](PERMISSIONS.md)
- [↑ Retour à l'index](README.md)

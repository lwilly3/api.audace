# 📺 Module EMISSIONS - Gestion des Séries d'Émissions

Documentation de la gestion des émissions (séries de shows réguliers).

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Relations](#relations)
5. [Exemples](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités
- Gestion des émissions (séries de shows)
- CRUD complet (Create, Read, Update, Delete)
- Soft delete et hard delete
- Récupération avec shows associés

### Fichier source
`app/db/crud/crud_emission.py`

---

## 🏗️ Architecture

### Modèle Emission

```python
Emission:
    id: int (PK)
    title: str (NOT NULL, UNIQUE)
    description: text
    frequency: str  # "Daily", "Weekly", "Monthly"
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime (optional)
    
    # Relations
    shows: List[Show] (One-to-Many)  # Épisodes de l'émission
```

**Hiérarchie :**
```
Emission (série) → "Morning Show"
  ├── Show 1 → "Morning Show - 11 Dec 2025"
  ├── Show 2 → "Morning Show - 12 Dec 2025"
  └── Show 3 → "Morning Show - 13 Dec 2025"
```

---

## 🔧 Fonctions métier

### 1. create_emission()

```python
def create_emission(db: Session, emission_create: EmissionCreate) -> Emission
```

**Description :** Crée une nouvelle série d'émission.

**Logique :**
```python
def create_emission(db: Session, emission_create: EmissionCreate):
    # Vérifier unicité du titre
    existing = db.query(Emission).filter(
        Emission.title == emission_create.title
    ).first()
    
    if existing:
        raise HTTPException(400, f"Emission '{emission_create.title}' already exists")
    
    new_emission = Emission(
        title=emission_create.title,
        description=emission_create.description,
        frequency=emission_create.frequency
    )
    
    db.add(new_emission)
    db.commit()
    db.refresh(new_emission)
    
    return new_emission
```

---

### 2. get_emissions()

```python
def get_emissions(db: Session, skip: int = 0, limit: int = 10) -> List[Emission]
```

**Description :** Liste toutes les émissions actives avec pagination.

**Logique :**
```python
def get_emissions(db: Session, skip: int = 0, limit: int = 10):
    emissions = db.query(Emission).filter(
        Emission.is_deleted == False
    ).order_by(Emission.title).offset(skip).limit(limit).all()
    
    return emissions
```

---

### 3. get_emission_by_id()

```python
def get_emission_by_id(db: Session, emission_id: int) -> Emission
```

**Description :** Récupère une émission avec tous ses shows.

**Logique :**
```python
from sqlalchemy.orm import joinedload

def get_emission_by_id(db: Session, emission_id: int):
    emission = db.query(Emission).options(
        joinedload(Emission.shows)  # Eager loading des shows
    ).filter(
        Emission.id == emission_id,
        Emission.is_deleted == False
    ).first()
    
    if not emission:
        raise HTTPException(404, "Emission not found")
    
    return emission
```

---

### 4. update_emission()

```python
def update_emission(
    db: Session,
    emission_id: int,
    emission_update: EmissionUpdate
) -> Emission
```

**Description :** Met à jour une émission existante.

**Logique :**
```python
def update_emission(db: Session, emission_id: int, emission_update: EmissionUpdate):
    emission = get_emission_by_id(db, emission_id)
    
    update_data = emission_update.model_dump(exclude_unset=True)
    
    # Vérifier unicité du titre si modifié
    if "title" in update_data and update_data["title"] != emission.title:
        existing = db.query(Emission).filter(
            Emission.title == update_data["title"]
        ).first()
        if existing:
            raise HTTPException(400, "Emission title already in use")
    
    for key, value in update_data.items():
        setattr(emission, key, value)
    
    db.commit()
    db.refresh(emission)
    
    return emission
```

---

### 5. soft_delete_emission()

```python
def soft_delete_emission(db: Session, emission_id: int) -> bool
```

**Description :** Suppression logique d'une émission.

**Logique :**
```python
def soft_delete_emission(db: Session, emission_id: int):
    emission = get_emission_by_id(db, emission_id)
    
    # Vérifier s'il y a des shows actifs
    active_shows = db.query(Show).filter(
        Show.emission_id == emission_id,
        Show.status.in_(["published", "live", "approved"])
    ).count()
    
    if active_shows > 0:
        raise HTTPException(
            400,
            f"Cannot delete emission with {active_shows} active shows"
        )
    
    # Soft delete
    emission.is_deleted = True
    emission.deleted_at = datetime.utcnow()
    
    db.commit()
    
    return True
```

---

### 6. delete_emission() - Hard Delete

```python
def delete_emission(db: Session, emission_id: int) -> bool
```

**Description :** Suppression physique (définitive).

**⚠️ ATTENTION :** Supprime toutes les relations en cascade !

**Logique :**
```python
def delete_emission(db: Session, emission_id: int):
    emission = get_emission_by_id(db, emission_id)
    
    # Vérifier qu'il n'y a AUCUN show
    show_count = db.query(Show).filter(Show.emission_id == emission_id).count()
    
    if show_count > 0:
        raise HTTPException(
            400,
            f"Cannot permanently delete emission with {show_count} shows. "
            f"Delete shows first or use soft delete."
        )
    
    # Suppression définitive
    db.delete(emission)
    db.commit()
    
    return True
```

---

## 🔗 Relations

### Schéma
```
Emission (1) ────< (N) Show
                     │
                     ├── Segments
                     ├── Presenters
                     └── Guests
```

### Cascade Delete
- Soft delete Emission → Shows préservés mais cachés
- Hard delete Emission → ⚠️ Shows supprimés si cascade activée

---

## 📏 Règles métier

### 1. Unicité
- `title` doit être unique
- Fréquence recommandée : "Daily", "Weekly", "Monthly"

### 2. Suppression
- Soft delete par défaut
- Hard delete uniquement si aucun show

### 3. Statistiques
```python
def get_emission_stats(db: Session, emission_id: int) -> dict:
    emission = get_emission_by_id(db, emission_id)
    
    total_shows = db.query(Show).filter(Show.emission_id == emission_id).count()
    published_shows = db.query(Show).filter(
        Show.emission_id == emission_id,
        Show.status == "published"
    ).count()
    
    return {
        "emission": emission,
        "total_shows": total_shows,
        "published_shows": published_shows
    }
```

---

## 💡 Exemples d'utilisation

### Créer une émission
```python
@router.post("/emissions")
def create_emission_route(
    emission: EmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    return crud_emission.create_emission(db, emission)
```

### Récupérer avec statistiques
```python
@router.get("/emissions/{emission_id}/details")
def get_emission_details(emission_id: int, db: Session = Depends(get_db)):
    emission = crud_emission.get_emission_by_id(db, emission_id)
    
    return {
        "id": emission.id,
        "title": emission.title,
        "description": emission.description,
        "frequency": emission.frequency,
        "show_count": len(emission.shows),
        "shows": [
            {
                "id": show.id,
                "title": show.title,
                "status": show.status,
                "broadcast_date": show.broadcast_date
            }
            for show in emission.shows
        ]
    }
```

---

**Navigation :**
- [← GUESTS.md](GUESTS.md)
- [→ SEGMENTS.md](SEGMENTS.md)
- [↑ Retour à l'index](README.md)

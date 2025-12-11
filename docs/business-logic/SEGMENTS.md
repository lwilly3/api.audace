# 🎬 Module SEGMENTS - Gestion des Segments de Shows

Documentation de la gestion des segments (parties d'un show avec invités spécifiques).

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
- Gestion des segments d'un show
- Gestion des positions (ordre des segments)
- Association invités ↔ segments
- Soft delete

### Fichier source
`app/db/crud/crud_segments.py`

---

## 🏗️ Architecture

### Modèle Segment

```python
Segment:
    id: int (PK)
    title: str (NOT NULL)
    type: str  # "Interview", "News", "Music", etc.
    duration: int (minutes)
    description: text
    technical_notes: text  # Notes régie
    position: int (ordre dans le show)
    startTime: time
    show_id: int (FK → Show, NOT NULL)
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Relations
    show: Show (Many-to-One)
    guests: List[Guest] (Many-to-Many via segment_guests)
```

### Hiérarchie
```
Show: "Morning Show - 11 Dec"
  ├── Segment 1 (pos=1): "Actualités" (08:00-08:15)
  │   ├── Guest A
  │   └── Guest B
  ├── Segment 2 (pos=2): "Interview" (08:15-08:45)
  │   └── Guest C
  └── Segment 3 (pos=3): "Musique" (08:45-09:00)
```

---

## 🔧 Fonctions métier

### 1. create_segment()

```python
def create_segment(db: Session, segment: SegmentCreate) -> Segment
```

**Description :** Crée un segment et calcule automatiquement sa position.

**Logique :**
```python
from sqlalchemy import func

def create_segment(db: Session, segment: SegmentCreate):
    # Calculer la prochaine position automatiquement
    max_position_result = db.query(func.max(Segment.position)).filter(
        Segment.show_id == segment.show_id
    ).scalar()
    
    new_position = (max_position_result + 1) if max_position_result is not None else 1
    
    # Préparer les données (exclure position si présente)
    segment_data = segment.model_dump()
    segment_data.pop('position', None)
    
    # Créer le segment
    new_segment = Segment(**segment_data, position=new_position)
    
    db.add(new_segment)
    db.commit()
    db.refresh(new_segment)
    
    return new_segment
```

---

### 2. get_segments()

```python
def get_segments(db: Session) -> List[Segment]
```

**Description :** Récupère tous les segments triés par position.

**Logique :**
```python
def get_segments(db: Session):
    return db.query(Segment).filter(
        Segment.is_deleted == False
    ).order_by(Segment.position).all()
```

---

### 3. get_segment_by_id()

```python
def get_segment_by_id(db: Session, segment_id: int) -> Segment
```

**Description :** Récupère un segment actif par son ID.

**Logique :**
```python
def get_segment_by_id(db: Session, segment_id: int):
    segment = db.query(Segment).filter(
        Segment.id == segment_id,
        Segment.is_deleted == False  # IMPORTANT
    ).first()
    
    if not segment:
        raise HTTPException(404, "Segment not found")
    
    return segment
```

---

### 4. update_segment()

```python
def update_segment(
    db: Session,
    db_segment: Segment,
    segment: SegmentUpdate
) -> Segment
```

**Description :** Met à jour un segment existant.

**Logique :**
```python
def update_segment(db: Session, db_segment: Segment, segment: SegmentUpdate):
    update_data = segment.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_segment, key, value)
    
    db.commit()
    db.refresh(db_segment)
    
    return db_segment
```

---

### 5. update_segment_position()

```python
def update_segment_position(
    db: Session,
    db_segment: Segment,
    position: int
) -> Segment
```

**Description :** Change la position d'un segment et réorganise les autres.

**Logique :**
```python
def update_segment_position(db: Session, db_segment: Segment, position: int):
    # Si position inchangée, rien à faire
    if db_segment.position == position:
        return db_segment
    
    # Réorganiser les positions
    reorganize_positions(db, db_segment, position)
    
    # Mettre à jour la position
    db_segment.position = position
    db.commit()
    db.refresh(db_segment)
    
    return db_segment
```

---

### 6. reorganize_positions()

```python
def reorganize_positions(db: Session, db_segment: Segment, new_position: int)
```

**Description :** Réorganise les positions pour maintenir la continuité.

**Logique :**
```python
def reorganize_positions(db: Session, db_segment: Segment, new_position: int):
    """
    Réattribue les positions séquentiellement pour éviter les trous.
    
    Exemple :
    Avant : [1, 2, 3, 4, 5]
    Déplacer segment 2 vers position 4
    Après : [1, 3, 4, 2, 5] → [1, 2, 3, 4, 5]
    """
    active_segments = db.query(Segment).filter(
        Segment.show_id == db_segment.show_id,
        Segment.is_deleted == False
    ).order_by(Segment.position).all()
    
    # Retirer le segment déplacé de la liste
    active_segments = [s for s in active_segments if s.id != db_segment.id]
    
    # Insérer à la nouvelle position
    active_segments.insert(new_position - 1, db_segment)
    
    # Réattribuer les positions
    for index, segment in enumerate(active_segments, start=1):
        segment.position = index
    
    db.commit()
```

---

### 7. delete_segment() - Soft Delete

```python
def delete_segment(db: Session, db_segment: Segment) -> bool
```

**Description :** Suppression logique et réorganisation des positions.

**Logique :**
```python
def delete_segment(db: Session, db_segment: Segment):
    # Soft delete
    db_segment.is_deleted = True
    db.commit()
    
    # Réorganiser les positions restantes
    remaining_segments = db.query(Segment).filter(
        Segment.show_id == db_segment.show_id,
        Segment.is_deleted == False
    ).order_by(Segment.position).all()
    
    # Réattribuer les positions sans trous
    for index, segment in enumerate(remaining_segments, start=1):
        segment.position = index
    
    db.commit()
    
    return True
```

---

## 📏 Règles métier

### 1. Positions
- Commence toujours à 1
- Pas de trous (1, 2, 3... pas 1, 3, 5)
- Réorganisation automatique à la suppression

### 2. Durées
- `duration` en minutes
- Somme des durées ≤ durée totale du show

### 3. startTime
- Format : HH:MM:SS
- Doit être chronologique (segment 1 < segment 2 < segment 3)

### 4. Invités
- Un segment peut avoir 0, 1 ou plusieurs invités
- Association via table `segment_guests`

---

## 🔗 Relations

### Schéma
```
Show (1) ────< (N) Segment
                     │
                     │ (Many-to-Many)
                     ↓
                   Guest
```

---

## 💡 Exemples d'utilisation

### Créer un segment avec invités
```python
@router.post("/segments")
def create_segment_route(
    segment: SegmentCreate,
    guest_ids: List[int],
    db: Session = Depends(get_db)
):
    # Créer le segment
    new_segment = crud_segments.create_segment(db, segment)
    
    # Associer les invités
    for guest_id in guest_ids:
        guest = db.query(Guest).filter(Guest.id == guest_id).first()
        if guest:
            new_segment.guests.append(guest)
    
    db.commit()
    db.refresh(new_segment)
    
    return new_segment
```

### Réorganiser les segments d'un show
```python
@router.patch("/shows/{show_id}/segments/reorder")
def reorder_segments(
    show_id: int,
    segment_orders: List[dict],  # [{"id": 1, "position": 2}, ...]
    db: Session = Depends(get_db)
):
    for order in segment_orders:
        segment = crud_segments.get_segment_by_id(db, order["id"])
        crud_segments.update_segment_position(db, segment, order["position"])
    
    return {"message": "Segments reordered successfully"}
```

---

**Navigation :**
- [← EMISSIONS.md](EMISSIONS.md)
- [→ ROLES.md](ROLES.md)
- [↑ Retour à l'index](README.md)

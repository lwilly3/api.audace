# 👥 Module GUESTS - Gestion des Invités

Documentation de la gestion des invités (personnalités, experts) participant aux segments.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Règles métier](#règles-métier)
5. [Relations](#relations)
6. [Exemples d'utilisation](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités
- Gestion des profils d'invités (CRUD)
- Association invités ↔ segments
- Statistiques de participation
- Recherche et filtrage

### Fichier source
`app/db/crud/crud_guests.py`

---

## 🏗️ Architecture

### Modèle Guest

```python
Guest:
    id: int (PK)
    name: str (NOT NULL)
    email: str (UNIQUE, optional)
    phone: str (optional)
    role: str  # Ex: "Expert", "Artiste", "Politique"
    biography: text
    contact_info: text
    avatar: str (URL)
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Relations
    segments: List[Segment] (Many-to-Many via segment_guests)
```

### Table d'association SegmentGuest

```python
SegmentGuest:
    segment_id: int (FK → Segment, PK)
    guest_id: int (FK → Guest, PK)
    added_at: datetime
```

---

## 🔧 Fonctions métier

### 1. create_guest()

```python
def create_guest(db: Session, guest: GuestCreate) -> Guest
```

**Description :** Crée un nouveau profil d'invité.

**Logique :**
```python
def create_guest(db: Session, guest: GuestCreate):
    # Vérifier unicité email si fourni
    if guest.email:
        existing = db.query(Guest).filter(Guest.email == guest.email).first()
        if existing:
            raise HTTPException(400, "Guest with this email already exists")
    
    db_guest = Guest(
        name=guest.name,
        contact_info=guest.contact_info,
        biography=guest.biography,
        role=guest.role,
        email=guest.email,
        phone=guest.phone
    )
    
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    
    return db_guest
```

---

### 2. get_guest_by_id()

```python
def get_guest_by_id(db: Session, guest_id: int) -> Optional[Guest]
```

**Description :** Récupère un invité avec ses informations complètes.

**Logique :**
```python
def get_guest_by_id(db: Session, guest_id: int):
    guest = db.query(Guest).filter(
        Guest.id == guest_id,
        Guest.is_deleted == False
    ).first()
    
    if not guest:
        raise HTTPException(404, "Guest not found")
    
    return guest
```

---

### 3. get_guests() - Avec statistiques

```python
def get_guests(db: Session, skip: int = 0, limit: int = 10) -> List[dict]
```

**Description :** Liste tous les invités avec leur nombre d'apparitions.

**Logique :**
```python
def get_guests(db: Session, skip: int = 0, limit: int = 10):
    guests = db.query(Guest).filter(
        Guest.is_deleted == False
    ).order_by(Guest.id.desc()).offset(skip).limit(limit).all()
    
    serialized_guests = []
    for guest in guests:
        guests_data = {
            "id": guest.id,
            "name": guest.name,
            "email": guest.email,
            "phone": guest.phone,
            "role": guest.role,
            "biography": guest.biography,
            "avatar": guest.avatar,
            "contact_info": guest.contact_info,
            "showSegment_participation": len(guest.segments)  # Nombre d'apparitions
        }
        serialized_guests.append(guests_data)
    
    return serialized_guests
```

**Optimisation :**
```python
from sqlalchemy import func

def get_guests_with_appearances(db: Session, skip: int = 0, limit: int = 10):
    """Version optimisée avec une seule requête"""
    guests = db.query(
        Guest,
        func.count(SegmentGuest.segment_id).label("appearance_count")
    ).outerjoin(SegmentGuest).filter(
        Guest.is_deleted == False
    ).group_by(Guest.id).order_by(
        Guest.id.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for guest, appearance_count in guests:
        result.append({
            "id": guest.id,
            "name": guest.name,
            "email": guest.email,
            "phone": guest.phone,
            "role": guest.role,
            "biography": guest.biography,
            "avatar": guest.avatar,
            "contact_info": guest.contact_info,
            "showSegment_participation": appearance_count
        })
    
    return result
```

---

### 4. update_guest()

```python
def update_guest(db: Session, guest_id: int, guest_update: GuestUpdate) -> Guest
```

**Description :** Met à jour les informations d'un invité.

**Logique :**
```python
def update_guest(db: Session, guest_id: int, guest_update: GuestUpdate):
    db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
    
    if not db_guest:
        raise HTTPException(404, "Guest not found")
    
    # Appliquer les modifications
    update_data = guest_update.model_dump(exclude_unset=True)
    
    # Vérifier unicité email si modifié
    if "email" in update_data and update_data["email"] != db_guest.email:
        existing = db.query(Guest).filter(Guest.email == update_data["email"]).first()
        if existing:
            raise HTTPException(400, "Email already in use")
    
    for key, value in update_data.items():
        setattr(db_guest, key, value)
    
    db.commit()
    db.refresh(db_guest)
    
    return db_guest
```

---

### 5. delete_guest()

```python
def delete_guest(db: Session, guest_id: int) -> bool
```

**Description :** Suppression logique d'un invité.

**Logique :**
```python
def delete_guest(db: Session, guest_id: int):
    db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
    
    if not db_guest:
        raise HTTPException(404, "Guest not found")
    
    # Soft delete
    db_guest.is_deleted = True
    db.commit()
    
    return True
```

---

### 6. search_guest()

```python
def search_guest(session: Session, query: str) -> Dict[str, Any]
```

**Description :** Recherche d'invités par nom, email, rôle ou biographie.

**Logique :**
```python
from sqlalchemy import or_

def search_guest(session: Session, query: str):
    # Validation
    if not query.strip():
        return {
            "status_code": 400,
            "message": "Le mot-clé de recherche ne peut pas être vide."
        }
    
    # Recherche multi-critères
    search_term = f"%{query}%"
    results = session.query(Guest).filter(
        Guest.is_deleted == False,
        or_(
            Guest.name.ilike(search_term),
            Guest.email.ilike(search_term),
            Guest.phone.ilike(search_term),
            Guest.role.ilike(search_term),
            Guest.contact_info.ilike(search_term),
            Guest.biography.ilike(search_term)
        )
    ).all()
    
    if not results:
        return {
            "status_code": 404,
            "message": f"Aucun invité trouvé pour '{query}'"
        }
    
    # Sérialiser
    guests_data = []
    for guest in results:
        guests_data.append({
            "id": guest.id,
            "name": guest.name,
            "email": guest.email,
            "phone": guest.phone,
            "role": guest.role,
            "biography": guest.biography,
            "avatar": guest.avatar,
            "contact_info": guest.contact_info
        })
    
    return {
        "status_code": 200,
        "count": len(results),
        "guests": guests_data
    }
```

---

### 7. get_guest_with_appearances()

```python
def get_guest_with_appearances(db: Session, guest_id: int) -> dict
```

**Description :** Récupère un invité avec l'historique complet de ses apparitions.

**Logique :**
```python
from sqlalchemy.orm import joinedload

def get_guest_with_appearances(db: Session, guest_id: int):
    guest = db.query(Guest).options(
        joinedload(Guest.segments).joinedload(Segment.show)
    ).filter(
        Guest.id == guest_id,
        Guest.is_deleted == False
    ).first()
    
    if not guest:
        raise HTTPException(404, "Guest not found")
    
    # Construire l'historique
    appearances = []
    for segment in guest.segments:
        if segment.show:
            appearances.append({
                "segment_id": segment.id,
                "segment_title": segment.title,
                "show_id": segment.show.id,
                "show_title": segment.show.title,
                "broadcast_date": segment.show.broadcast_date.isoformat() if segment.show.broadcast_date else None
            })
    
    return {
        "id": guest.id,
        "name": guest.name,
        "email": guest.email,
        "role": guest.role,
        "biography": guest.biography,
        "total_appearances": len(appearances),
        "appearances": sorted(appearances, key=lambda x: x["broadcast_date"], reverse=True)
    }
```

---

## 📏 Règles métier

### 1. Unicité
- Email unique (si fourni)
- Nom non unique (homonymes possibles)

### 2. Soft Delete
- Jamais supprimer physiquement
- Préserver les associations avec segments

### 3. Statistiques
- Compter les apparitions via `segment_guests`
- Trier les invités par popularité

### 4. Validation
```python
class GuestCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = Field(None, max_length=50)
    biography: Optional[str] = Field(None, max_length=2000)
    contact_info: Optional[str] = Field(None, max_length=500)
```

---

## 🔗 Relations

### Schéma
```
Guest (N) ←──→ (M) Segment (via segment_guests)
                     │
                     └──→ Show
```

### Dépendances
- **crud_segments.py** : Association aux segments
- **crud_show.py** : Statistiques par show
- **guest_route.py** : Routes API

---

## 💡 Exemples d'utilisation

### Ajouter un invité
```python
@router.post("/guests", response_model=GuestResponse)
def create_guest_route(
    guest: GuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Vérifier permission
    if not crud_permissions.check_permissions(db, current_user.id, "create_guest"):
        raise HTTPException(403, "Permission denied")
    
    return crud_guests.create_guest(db, guest)
```

### Récupérer les invités les plus actifs
```python
@router.get("/guests/top-participants")
def get_top_guests(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Top 10 des invités avec le plus d'apparitions"""
    guests = db.query(
        Guest,
        func.count(SegmentGuest.segment_id).label("count")
    ).join(SegmentGuest).filter(
        Guest.is_deleted == False
    ).group_by(Guest.id).order_by(
        desc("count")
    ).limit(limit).all()
    
    return [
        {
            "guest": guest,
            "appearances": count
        }
        for guest, count in guests
    ]
```

---

**Navigation :**
- [← AUTH.md](AUTH.md)
- [→ EMISSIONS.md](EMISSIONS.md)
- [↑ Retour à l'index](README.md)

# 📻 Module SHOWS - Gestion des Shows et Émissions

Documentation complète de la logique métier pour la gestion des shows.

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
- Gestion du cycle de vie des shows (CRUD)
- Création de shows complexes avec segments et invités depuis JSON
- Association des présentateurs aux shows
- Gestion du statut des shows (draft, published, archived, etc.)
- Récupération enrichie avec relations (segments, présentateurs, invités)
- Soft delete et archivage

### Fichier source
`app/db/crud/crud_show.py`

### Dépendances
```python
# Modèles
from app.models import Show, Segment, Presenter, Guest
from app.models import ShowPresenter, SegmentGuest  # Tables d'association

# Schémas
from app.schemas import ShowCreateWithDetail, ShowUpdate, ShowCreate, ShowBase_jsonShow

# CRUD externes
from app.db.crud import crud_presenters, crud_guests, crud_segments
```

---

## 🏗️ Architecture

### Modèle Show

```python
Show:
    id: int (PK)
    title: str
    type: str (ex: "Talk Show", "News", "Music")
    broadcast_date: date
    duration: int (minutes)
    frequency: str (ex: "Daily", "Weekly")
    description: text
    status: str (ex: "draft", "published", "archived")
    emission_id: int (FK → Emission) [relation parent]
    created_by: int (FK → User)
    is_deleted: bool (default: False)
    created_at: datetime
    updated_at: datetime
    
    # Relations
    emission: Emission (Many-to-One)
    presenters: List[Presenter] (Many-to-Many via show_presenters)
    segments: List[Segment] (One-to-Many)
    created_by_user: User (Many-to-One)
```

### Statuts possibles

```python
STATUS = {
    "draft": "Brouillon, en préparation",
    "pending": "En attente de validation",
    "approved": "Validé, prêt à diffuser",
    "published": "Publié, en ligne",
    "live": "En direct actuellement",
    "completed": "Diffusion terminée",
    "archived": "Archivé",
    "cancelled": "Annulé"
}
```

### Hiérarchie des entités

```
Emission (série)
    └── Show (épisode spécifique)
        ├── Segment 1
        │   ├── Guest A
        │   └── Guest B
        ├── Segment 2
        │   └── Guest C
        └── Segment 3
```

### Flux de données

```
Client Request
      ↓
Route (show_route.py)
      ↓
Schema Validation (ShowCreate / ShowBase_jsonShow)
      ↓
CRUD Function (crud_show.py)
      ↓
├─→ Create Show
├─→ Associate Presenters (Many-to-Many)
├─→ Create Segments
│   └─→ Associate Guests per Segment
└─→ Create Audit Log
      ↓
Response to Client
```

---

## 🔧 Fonctions métier

### 1. update_show_status()

**Signature :**
```python
def update_show_status(db: Session, show_id: int, status: str) -> dict
```

**Description :**
Met à jour uniquement le statut d'un show. Fonction optimisée pour les changements d'état fréquents.

**Logique métier :**
1. Récupération du show par ID
2. Validation que le show existe
3. Mise à jour du champ `status`
4. Commit immédiat
5. Retour ID + nouveau statut

**Paramètres :**
- `db` (Session) : Session SQLAlchemy
- `show_id` (int) : ID du show
- `status` (str) : Nouveau statut (voir enum STATUS)

**Retour :**
```python
{
    "id": 1,
    "status": "published"
}
```

**Validations :**
```python
VALID_STATUSES = [
    "draft", "pending", "approved", "published", 
    "live", "completed", "archived", "cancelled"
]

def update_show_status(db: Session, show_id: int, status: str):
    # Validation du statut
    if status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of {VALID_STATUSES}")
    
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(404, f"Show with ID {show_id} not found")
    
    # Vérifier transitions autorisées
    if not is_valid_transition(show.status, status):
        raise HTTPException(
            400, 
            f"Cannot change status from '{show.status}' to '{status}'"
        )
    
    show.status = status
    db.commit()
    db.refresh(show)
    
    return {"id": show.id, "status": show.status}
```

**Transitions autorisées :**
```python
TRANSITIONS = {
    "draft": ["pending", "cancelled"],
    "pending": ["approved", "draft", "cancelled"],
    "approved": ["published", "draft"],
    "published": ["live", "archived"],
    "live": ["completed"],
    "completed": ["archived"],
    "archived": [],  # État final
    "cancelled": []  # État final
}

def is_valid_transition(current: str, new: str) -> bool:
    return new in TRANSITIONS.get(current, [])
```

**Erreurs :**
- `HTTPException(404)` : Show introuvable
- `HTTPException(400)` : Statut invalide ou transition non autorisée

**Cas d'usage :**
- Workflow de validation (draft → pending → approved → published)
- Passage en direct (published → live → completed)
- Archivage (completed → archived)

---

### 2. create_show_with_elements_from_json()

**Signature :**
```python
def create_show_with_elements_from_json(
    db: Session,
    shows_data: List[ShowBase_jsonShow],
    current_user_id: int
) -> Show
```

**Description :**
Fonction complexe pour créer un ou plusieurs shows complets avec segments, invités et présentateurs depuis un JSON structuré.

**Logique métier détaillée :**

#### Étape 1 : Création du Show
```python
for show_data in shows_data:
    # Créer l'objet Show
    new_show = Show(
        title=show_data.title,
        type=show_data.type,
        broadcast_date=show_data.broadcast_date,
        duration=show_data.duration,
        frequency=show_data.frequency,
        description=show_data.description,
        status=show_data.status,
        emission_id=show_data.emission_id,
        created_by=current_user_id
    )
    db.add(new_show)
    db.flush()  # IMPORTANT : obtenir l'ID sans commit
```

#### Étape 2 : Création des Segments
```python
    for segment_data in show_data.segments:
        new_segment = Segment(
            title=segment_data.title,
            type=segment_data.type,
            duration=segment_data.duration,
            description=segment_data.description,
            technical_notes=segment_data.technical_notes,
            position=segment_data.position,
            startTime=segment_data.startTime,
            show_id=new_show.id  # Utilise l'ID du show créé
        )
        db.add(new_segment)
        db.flush()  # Obtenir l'ID du segment
```

#### Étape 3 : Association des Invités aux Segments
```python
        # Pour chaque segment, associer ses invités spécifiques
        for guest_id in segment_data.guests:
            guest = db.query(Guest).filter(Guest.id == guest_id).one_or_none()
            if guest:
                new_segment.guests.append(guest)
                # Crée automatiquement l'entrée dans segment_guests
```

#### Étape 4 : Association des Présentateurs au Show
```python
    # Après tous les segments
    for presenter_data in show_data.presenters:
        presenter = db.query(Presenter).filter(
            Presenter.id == presenter_data.id
        ).one_or_none()
        
        if presenter:
            new_show.presenters.append(presenter)
            # Crée automatiquement l'entrée dans show_presenters
            
            # Gérer le présentateur principal
            if presenter_data.isMainPresenter:
                # Logique pour marquer comme présentateur principal
                # (peut nécessiter un champ supplémentaire dans show_presenters)
                pass
```

#### Étape 5 : Commit final
```python
    db.commit()

return new_show  # Retourne le dernier show créé
```

**Structure JSON attendue :**
```json
[
  {
    "title": "Morning Show - 11 Dec 2025",
    "type": "Talk Show",
    "broadcast_date": "2025-12-11",
    "duration": 120,
    "frequency": "Daily",
    "description": "Émission matinale",
    "status": "draft",
    "emission_id": 1,
    "presenters": [
      {
        "id": 1,
        "isMainPresenter": true
      },
      {
        "id": 2,
        "isMainPresenter": false
      }
    ],
    "segments": [
      {
        "title": "Actualités",
        "type": "News",
        "duration": 15,
        "description": "Tour d'horizon",
        "technical_notes": "Jingle intro",
        "position": 1,
        "startTime": "08:00:00",
        "guests": [1, 2]
      },
      {
        "title": "Interview",
        "type": "Interview",
        "duration": 30,
        "description": "Interview expert climat",
        "technical_notes": "Micro casque",
        "position": 2,
        "startTime": "08:15:00",
        "guests": [3]
      }
    ]
  }
]
```

**Gestion des erreurs :**
```python
try:
    # ... création ...
    db.commit()
    return new_show
    
except IntegrityError as e:
    db.rollback()
    # Violation de contrainte (FK invalide, etc.)
    raise ValueError(f"Integrity error: {str(e)}")
    
except Exception as e:
    db.rollback()
    # Erreur inattendue
    logger.error(f"Unexpected error creating show: {e}")
    raise ValueError(f"Unexpected error: {str(e)}")
```

**Validations nécessaires :**
1. `emission_id` doit exister
2. Tous les `presenter_id` doivent exister
3. Tous les `guest_id` doivent exister
4. `position` des segments doit être unique par show
5. `startTime` des segments doit être cohérent (pas de chevauchement)

**Contraintes :**
- Tous les segments doivent tenir dans la durée du show
- Au moins un présentateur requis
- Les invités peuvent être vides (certains segments sans invités)

**Optimisations :**
```python
# Précharger tous les présentateurs et invités en une seule query
presenter_ids = [p.id for show in shows_data for p in show.presenters]
guest_ids = [g for show in shows_data for seg in show.segments for g in seg.guests]

presenters_map = {
    p.id: p 
    for p in db.query(Presenter).filter(Presenter.id.in_(presenter_ids)).all()
}
guests_map = {
    g.id: g 
    for g in db.query(Guest).filter(Guest.id.in_(guest_ids)).all()
}

# Utiliser les maps au lieu de queries individuelles
for presenter_data in show_data.presenters:
    presenter = presenters_map.get(presenter_data.id)
    if presenter:
        new_show.presenters.append(presenter)
```

**Cas d'usage :**
- Import de conducteurs depuis fichier JSON
- Création de shows templates
- API bulk creation
- Duplication de show existant

---

### 3. get_show_details_all()

**Signature :**
```python
def get_show_details_all(db: Session) -> List[dict]
```

**Description :**
Récupère TOUS les shows avec leurs relations complètes chargées (emission, présentateurs, segments, invités).

**Logique métier :**

#### Étape 1 : Query avec eager loading
```python
shows = db.query(Show).options(
    joinedload(Show.emission),                              # 1-to-1
    joinedload(Show.presenters),                           # Many-to-Many
    joinedload(Show.segments).joinedload(Segment.guests)   # 1-to-Many → Many-to-Many
).all()
```

**Pourquoi l'eager loading ?**
Sans `joinedload()`, SQLAlchemy ferait des queries lazy :
```python
# Sans eager loading : N+1 problem !
shows = db.query(Show).all()  # 1 query

for show in shows:  # N itérations
    emission = show.emission      # +1 query par show
    presenters = show.presenters  # +1 query par show
    for segment in show.segments: # +1 query par show
        guests = segment.guests   # +1 query par segment
# Total : 1 + N + N + M queries (très lent !)

# Avec eager loading : queries optimisées
shows = db.query(Show).options(
    joinedload(Show.emission),
    joinedload(Show.presenters),
    joinedload(Show.segments).joinedload(Segment.guests)
).all()
# Total : 3-4 queries seulement (rapide)
```

#### Étape 2 : Sérialisation
```python
show_details = []

for show in shows:
    show_info = {
        "id": show.id,
        "emission": show.emission.title if show.emission else "No Emission Linked",
        "emission_id": show.emission_id,
        "title": show.title,
        "type": show.type,
        "broadcast_date": show.broadcast_date.isoformat() if show.broadcast_date else None,
        "duration": show.duration,
        "frequency": show.frequency,
        "description": show.description,
        "status": show.status,
        "presenters": [],
        "segments": []
    }
    
    # Sérialiser les présentateurs
    for presenter in show.presenters:
        show_info["presenters"].append({
            "id": presenter.id,
            "name": presenter.name,
            "biography": presenter.biography,
            "contact_info": presenter.contact_info
        })
    
    # Sérialiser les segments avec leurs invités
    for segment in show.segments:
        segment_info = {
            "id": segment.id,
            "title": segment.title,
            "type": segment.type,
            "duration": segment.duration,
            "position": segment.position,
            "startTime": segment.startTime.isoformat() if segment.startTime else None,
            "guests": []
        }
        
        # Invités du segment
        for guest in segment.guests:
            segment_info["guests"].append({
                "id": guest.id,
                "name": guest.name,
                "bio": guest.bio,
                "contact_info": guest.contact_info
            })
        
        show_info["segments"].append(segment_info)
    
    show_details.append(show_info)

return show_details
```

**Format de retour :**
```json
[
  {
    "id": 1,
    "emission": "Morning Radio",
    "emission_id": 1,
    "title": "Morning Show - 11 Dec",
    "type": "Talk Show",
    "broadcast_date": "2025-12-11",
    "duration": 120,
    "frequency": "Daily",
    "description": "...",
    "status": "published",
    "presenters": [
      {
        "id": 1,
        "name": "Jean Dupont",
        "biography": "...",
        "contact_info": "..."
      }
    ],
    "segments": [
      {
        "id": 1,
        "title": "Actualités",
        "type": "News",
        "duration": 15,
        "position": 1,
        "startTime": "08:00:00",
        "guests": [
          {
            "id": 1,
            "name": "Dr. Sophie Martin",
            "bio": "...",
            "contact_info": "..."
          }
        ]
      }
    ]
  }
]
```

**⚠️ Problèmes de performances :**
Cette fonction charge TOUT en mémoire ! Pour des milliers de shows :
- Mémoire : Peut atteindre plusieurs GB
- Temps : Plusieurs secondes voire minutes
- Réseau : JSON très volumineux

**Solution recommandée : Pagination**
```python
def get_show_details_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str = None
) -> dict:
    query = db.query(Show).options(
        joinedload(Show.emission),
        joinedload(Show.presenters),
        joinedload(Show.segments).joinedload(Segment.guests)
    )
    
    # Filtrer par statut si fourni
    if status:
        query = query.filter(Show.status == status)
    
    # Filtrer shows non supprimés
    query = query.filter(Show.is_deleted == False)
    
    # Compter le total
    total = query.count()
    
    # Paginer
    shows = query.offset(skip).limit(limit).all()
    
    # Sérialiser (même logique que get_show_details_all)
    show_details = [...]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "shows": show_details
    }
```

**Cas d'usage :**
- Admin : vue d'ensemble de tous les shows
- Export de données (avec pagination)
- Synchronisation avec systèmes externes

---

## 📏 Règles métier

### 1. Hiérarchie obligatoire
- Un show doit appartenir à une émission (`emission_id` NOT NULL)
- Une émission peut avoir plusieurs shows (épisodes)

### 2. Statuts et workflow
```python
draft → pending → approved → published → live → completed → archived
                     ↓                              ↓
                 cancelled                      archived
```

### 3. Contraintes temporelles
- `duration` doit être > 0
- Somme des durées des segments ≤ durée du show
- `broadcast_date` ne peut pas être dans le passé pour création
- `startTime` des segments doit être chronologique

### 4. Présentateurs
- Au moins un présentateur requis
- Un présentateur principal recommandé (isMainPresenter)
- Un présentateur peut animer plusieurs shows

### 5. Segments
- `position` unique par show
- `position` commence à 1
- Pas de trous dans la numérotation (1, 2, 3... pas 1, 3, 5)

### 6. Soft Delete
- Show jamais supprimé physiquement
- `is_deleted = True`
- Relations préservées
- Segments et associations préservés

---

## 🔗 Relations

### Dépendances entrantes
- **crud_emission.py** : Création d'émissions pour les shows
- **show_route.py** : Routes API
- **crud_dashboard.py** : Statistiques

### Dépendances sortantes
- **crud_presenters.py** : Validation des présentateurs
- **crud_guests.py** : Validation des invités
- **crud_segments.py** : Création des segments
- **crud_audit_logs.py** : Logging

### Schéma relationnel
```
Emission (1) ─────< (N) Show
                      │
                      ├────< (N) Segment
                      │         │
                      │         └────< (N) Guest (via segment_guests)
                      │
                      └────< (N) Presenter (via show_presenters)
```

---

## ⚠️ Contraintes

### Performances
- `get_show_details_all()` très lent sans pagination
- Eager loading obligatoire pour éviter N+1
- Index recommandés sur `status`, `broadcast_date`, `emission_id`

### Limites
- Pas de validation de chevauchement temporel des segments
- Pas de gestion de conflits de présentateurs (double booking)
- Pas de limite sur nombre de segments

### Sécurité
- Permissions requises pour créer/modifier
- Audit log de toutes les modifications
- Validation que emission_id existe

---

## 💡 Exemples d'utilisation

### Créer un show simple
```python
from app.schemas import ShowCreate

@router.post("/shows")
def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    new_show = crud_show.create_show(db, show, current_user.id)
    return new_show
```

### Changer le statut (workflow)
```python
@router.patch("/shows/{show_id}/status")
def change_status(
    show_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    result = crud_show.update_show_status(db, show_id, status)
    return result
```

### Créer un show complet depuis JSON
```python
@router.post("/shows/from-json")
def create_from_json(
    shows_data: List[ShowBase_jsonShow],
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    show = crud_show.create_show_with_elements_from_json(
        db,
        shows_data,
        current_user.id
    )
    return show
```

---

**Navigation :**
- [← USERS.md](USERS.md)
- [→ PRESENTERS.md](PRESENTERS.md)
- [↑ Retour à l'index](README.md)

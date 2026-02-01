# 📻 Domain Radio Rules

> **Skill métier** : Règles spécifiques au domaine radio pour api.audace.

---

## 📋 Contexte du Projet

### Domaine Métier : Gestion Radio

api.audace gère une station de radio avec ces concepts métier :

```
Hiérarchie principale :
├── Emission (programme récurrent)
│   └── Show (épisode/diffusion)
│       └── Segment (partie de l'émission)
│           └── Guest (invité)
└── Presenter (animateur)
```

### Modèles Métier Existants

| Modèle | Description | Relations |
|--------|-------------|-----------|
| `Emission` | Programme radio (série) | 1-N Shows |
| `Show` | Épisode/diffusion | 1-N Segments, N-N Presenters |
| `Segment` | Section d'un show | N-N Guests |
| `Presenter` | Animateur | N-N Shows |
| `Guest` | Invité | N-N Segments |

---

## 🎯 Objectif du Skill

Garantir que tout développement respecte :
1. **La hiérarchie** Emission → Show → Segment
2. **Les relations** métier correctes
3. **Les contraintes** business radio
4. **La terminologie** cohérente

---

## ✅ Règles Obligatoires

### 1. Hiérarchie des Entités

```python
# HIÉRARCHIE STRICTE - NE PAS INVERSER

# Emission = Programme récurrent (ex: "Le Journal du Matin")
class Emission(BaseModel):
    title = Column(String(255), nullable=False)
    synopsis = Column(Text)
    type = Column(Text)  # actualité, musique, débat...
    frequency = Column(Text)  # quotidien, hebdomadaire...

# Show = Épisode d'une Emission (ex: "Journal du 15/01/2025")
class Show(Base):
    title = Column(String, nullable=False)
    broadcast_date = Column(DateTime)
    status = Column(String, default="En préparation")
    emission_id = Column(Integer, ForeignKey("emissions.id"))

# Segment = Partie d'un Show (ex: "Interview du Maire")
class Segment(Base):
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # interview, chronique, musique
    duration = Column(Integer)  # en minutes
    position = Column(Integer)  # ordre dans le show
    show_id = Column(Integer, ForeignKey("shows.id"))
```

### 2. Statuts des Shows

```python
# Statuts autorisés pour un Show
SHOW_STATUSES = [
    "En préparation",    # Création/planification
    "Planifié",          # Date de diffusion fixée
    "En direct",         # En cours de diffusion
    "Terminé",           # Diffusion terminée
    "Annulé",            # Annulé
    "Archivé"            # Archivé
]

# Validation dans le schéma
from pydantic import field_validator

class ShowCreate(ShowBase):
    @field_validator("status")
    def validate_status(cls, v):
        if v not in SHOW_STATUSES:
            raise ValueError(f"Status must be one of: {SHOW_STATUSES}")
        return v
```

### 3. Types de Segments

```python
# Types autorisés pour un Segment
SEGMENT_TYPES = [
    "interview",       # Interview d'un invité
    "chronique",       # Chronique/rubrique
    "musique",         # Plage musicale
    "publicité",       # Coupure pub
    "jingle",          # Jingle/transition
    "actualité",       # Flash info
    "météo",           # Météo
    "débat",           # Débat/discussion
    "autre"            # Autre
]

# Validation
class SegmentCreate(SegmentBase):
    @field_validator("type")
    def validate_type(cls, v):
        if v.lower() not in SEGMENT_TYPES:
            raise ValueError(f"Type must be one of: {SEGMENT_TYPES}")
        return v.lower()
```

### 4. Relations Many-to-Many

```python
# Presenter ↔ Show (animateur peut présenter plusieurs shows)
class ShowPresenter(Base):
    __tablename__ = "show_presenters"
    show_id = Column(Integer, ForeignKey("shows.id"), primary_key=True)
    presenter_id = Column(Integer, ForeignKey("presenters.id"), primary_key=True)

# Segment ↔ Guest (un segment peut avoir plusieurs invités)
class SegmentGuest(Base):
    __tablename__ = "segment_guests"
    segment_id = Column(Integer, ForeignKey("segments.id"), primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), primary_key=True)
```

### 5. Calcul de Durée

```python
# La durée d'un Show = somme des durées de ses Segments
def calculate_show_duration(show: Show) -> int:
    """Calcule la durée totale d'un show."""
    return sum(segment.duration for segment in show.segments)


def validate_show_duration(show: Show, expected_duration: int, tolerance: int = 5):
    """Vérifie que la durée des segments correspond."""
    actual = calculate_show_duration(show)
    if abs(actual - expected_duration) > tolerance:
        logger.warning(
            f"Show {show.id} duration mismatch: "
            f"expected={expected_duration}, actual={actual}"
        )
```

### 6. Ordonnancement des Segments

```python
# Les segments ont un ordre (position)
def reorder_segments(db: Session, show_id: int, segment_order: list[int]):
    """Réordonne les segments d'un show."""
    segments = db.query(Segment).filter(Segment.show_id == show_id).all()
    
    for i, segment_id in enumerate(segment_order):
        segment = next(s for s in segments if s.id == segment_id)
        segment.position = i
    
    db.commit()


def get_ordered_segments(show: Show) -> list[Segment]:
    """Retourne les segments dans l'ordre de diffusion."""
    return sorted(show.segments, key=lambda s: s.position)
```

---

## 🚫 Interdictions Explicites

### ❌ Segment sans Show
```python
# ❌ INTERDIT - Un segment DOIT appartenir à un show
segment = Segment(
    title="Interview",
    type="interview",
    duration=15
    # show_id manquant !
)

# ✅ CORRECT
segment = Segment(
    title="Interview",
    type="interview", 
    duration=15,
    show_id=123  # Obligatoire
)
```

### ❌ Guest directement sur Show
```python
# ❌ INTERDIT - Les invités sont sur les SEGMENTS
show.guests.append(guest)  # FAUX !

# ✅ CORRECT - Les invités sont sur les segments
segment.guests.append(guest)
```

### ❌ Show sans Emission
```python
# ❌ À ÉVITER - Un show devrait avoir une émission parente
show = Show(
    title="Journal",
    broadcast_date=datetime.now()
    # emission_id manquant !
)

# ✅ CORRECT - Rattacher à une émission
show = Show(
    title="Journal du 15 janvier",
    broadcast_date=datetime.now(),
    emission_id=1  # Émission "Journal Quotidien"
)
```

### ❌ Presenter comme Guest
```python
# ❌ INTERDIT - Ne pas confondre les rôles
# Presenter = animateur régulier
# Guest = invité ponctuel

# Un présentateur n'est PAS un invité
segment.guests.append(presenter)  # FAUX !

# ✅ CORRECT
show.presenters.append(presenter)  # Animateur du show
segment.guests.append(guest)       # Invité du segment
```

---

## 📝 Exemples Concrets

### Créer une Émission Complète

```python
# 1. Créer l'émission (programme)
emission = Emission(
    title="Le Journal du Matin",
    synopsis="Actualités matinales",
    type="actualité",
    frequency="quotidien"
)
db.add(emission)
db.commit()

# 2. Créer un show (épisode)
show = Show(
    title="Journal du 15 janvier 2025",
    broadcast_date=datetime(2025, 1, 15, 7, 0),
    duration=60,
    status="Planifié",
    emission_id=emission.id
)
db.add(show)
db.commit()

# 3. Ajouter des présentateurs
presenter = db.query(Presenter).filter(Presenter.name == "Marie").first()
show.presenters.append(presenter)

# 4. Créer des segments
segments = [
    Segment(title="Ouverture", type="jingle", duration=2, position=0, show_id=show.id),
    Segment(title="Titres du jour", type="actualité", duration=10, position=1, show_id=show.id),
    Segment(title="Interview Maire", type="interview", duration=20, position=2, show_id=show.id),
    Segment(title="Météo", type="météo", duration=3, position=3, show_id=show.id),
    Segment(title="Plage musicale", type="musique", duration=15, position=4, show_id=show.id),
    Segment(title="Fermeture", type="jingle", duration=2, position=5, show_id=show.id),
]
db.add_all(segments)
db.commit()

# 5. Ajouter un invité au segment interview
interview_segment = segments[2]
guest = Guest(name="Jean Dupont", role="Maire de la ville")
interview_segment.guests.append(guest)
db.commit()
```

### Requêtes Métier Courantes

```python
# Shows d'une émission
def get_shows_by_emission(db: Session, emission_id: int):
    return db.query(Show).filter(
        Show.emission_id == emission_id,
        Show.is_deleted == False
    ).order_by(Show.broadcast_date.desc()).all()


# Shows à venir
def get_upcoming_shows(db: Session, limit: int = 10):
    return db.query(Show).filter(
        Show.broadcast_date > datetime.utcnow(),
        Show.status.in_(["Planifié", "En préparation"])
    ).order_by(Show.broadcast_date).limit(limit).all()


# Segments avec invités
def get_segments_with_guests(db: Session, show_id: int):
    return db.query(Segment).filter(
        Segment.show_id == show_id
    ).options(
        joinedload(Segment.guests)
    ).order_by(Segment.position).all()


# Historique d'un présentateur
def get_presenter_history(db: Session, presenter_id: int):
    return db.query(Show).join(
        Show.presenters
    ).filter(
        Presenter.id == presenter_id,
        Show.status == "Terminé"
    ).order_by(Show.broadcast_date.desc()).all()
```

---

## ✅ Checklist de Validation

### Entités

- [ ] Show rattaché à une Emission
- [ ] Segment rattaché à un Show
- [ ] Guest rattaché à un Segment (pas au Show)
- [ ] Presenter rattaché au Show

### Contraintes

- [ ] Statut de Show valide
- [ ] Type de Segment valide
- [ ] Durée de Segment > 0
- [ ] Position de Segment définie

### Logique Métier

- [ ] Durée du Show = somme des Segments
- [ ] Segments ordonnés par position
- [ ] Pas de chevauchement de diffusion

---

## 📚 Ressources Associées

- [model-generator](../model-generator/skill.md) - Création de modèles
- [endpoint-creator](../endpoint-creator/skill.md) - Routes métier
- [architecture-guardian](../architecture-guardian/skill.md) - Structure projet

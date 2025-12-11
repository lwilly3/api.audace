# 🛠️ Modules Utilitaires - SEARCH & DASHBOARD

Documentation des fonctionnalités transversales de recherche et statistiques.

---

## 📋 Table des matières

1. [Module SEARCH - Recherche](#module-search)
2. [Module DASHBOARD - Tableau de bord](#module-dashboard)

---

# 🔍 Module SEARCH

## Vue d'ensemble

### Responsabilités
- Recherche multi-critères dans les shows
- Recherche d'utilisateurs
- Recherche de présentateurs
- Recherche d'invités

### Fichier source
`routeur/search_route/` (plusieurs fichiers)

---

## Fonctions de recherche

### 1. search_shows()

**Description :** Recherche de shows par titre, type, statut, date.

**Exemple d'implémentation :**
```python
from sqlalchemy import or_

def search_shows(
    db: Session,
    query: str,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Recherche avancée de shows.
    
    Args:
        query: Terme de recherche (titre, description)
        status: Filtrer par statut
        start_date: Date de début
        end_date: Date de fin
    """
    search_query = db.query(Show).filter(Show.is_deleted == False)
    
    # Recherche textuelle
    if query:
        search_term = f"%{query}%"
        search_query = search_query.filter(
            or_(
                Show.title.ilike(search_term),
                Show.description.ilike(search_term),
                Show.type.ilike(search_term)
            )
        )
    
    # Filtrer par statut
    if status:
        search_query = search_query.filter(Show.status == status)
    
    # Filtrer par dates
    if start_date:
        search_query = search_query.filter(Show.broadcast_date >= start_date)
    if end_date:
        search_query = search_query.filter(Show.broadcast_date <= end_date)
    
    # Pagination et tri
    total = search_query.count()
    results = search_query.order_by(
        Show.broadcast_date.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "results": results,
        "query": query
    }
```

---

### 2. search_users()

**Description :** Recherche d'utilisateurs par nom, email, username.

**Exemple :**
```python
def search_users(
    db: Session,
    query: str,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Recherche d'utilisateurs"""
    search_term = f"%{query}%"
    
    search_query = db.query(User).filter(
        User.is_deleted == False,
        or_(
            User.username.ilike(search_term),
            User.email.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term)
        )
    )
    
    # Filtrer par rôle
    if role:
        search_query = search_query.join(UserRole).join(Role).filter(
            Role.name == role
        )
    
    total = search_query.count()
    results = search_query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "results": results
    }
```

---

### 3. global_search()

**Description :** Recherche globale dans toutes les entités.

**Exemple :**
```python
def global_search(db: Session, query: str, limit: int = 5):
    """
    Recherche dans shows, users, guests, presenters.
    
    Returns:
        {
            "shows": [...],
            "users": [...],
            "guests": [...],
            "presenters": [...]
        }
    """
    search_term = f"%{query}%"
    
    # Shows
    shows = db.query(Show).filter(
        Show.is_deleted == False,
        Show.title.ilike(search_term)
    ).limit(limit).all()
    
    # Users
    users = db.query(User).filter(
        User.is_deleted == False,
        or_(
            User.username.ilike(search_term),
            User.email.ilike(search_term)
        )
    ).limit(limit).all()
    
    # Guests
    guests = db.query(Guest).filter(
        Guest.is_deleted == False,
        Guest.name.ilike(search_term)
    ).limit(limit).all()
    
    # Presenters
    presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False,
        Presenter.name.ilike(search_term)
    ).limit(limit).all()
    
    return {
        "shows": shows,
        "users": users,
        "guests": guests,
        "presenters": presenters
    }
```

---

## Optimisations de recherche

### Full-Text Search (PostgreSQL)
```python
from sqlalchemy import func

def search_shows_fulltext(db: Session, query: str):
    """Recherche full-text avec PostgreSQL"""
    results = db.query(Show).filter(
        func.to_tsvector('english', Show.title + ' ' + Show.description).match(query)
    ).all()
    
    return results
```

### Recherche avec score de pertinence
```python
from sqlalchemy import case

def search_shows_ranked(db: Session, query: str):
    """Recherche avec score de pertinence"""
    search_term = f"%{query}%"
    
    # Score de pertinence
    relevance = case(
        (Show.title.ilike(query), 3),  # Correspondance exacte titre
        (Show.title.ilike(f"{query}%"), 2),  # Commence par
        else_=1  # Contient
    )
    
    shows = db.query(Show).filter(
        Show.is_deleted == False,
        Show.title.ilike(search_term)
    ).order_by(relevance.desc(), Show.broadcast_date.desc()).all()
    
    return shows
```

---

# 📊 Module DASHBOARD

## Vue d'ensemble

### Responsabilités
- Statistiques globales de l'application
- KPIs (Key Performance Indicators)
- Graphiques et rapports

### Fichier source
`routeur/dashbord_route.py`

---

## Fonction principale

### get_dashboard()

**Description :** Récupère toutes les statistiques pour le tableau de bord.

**Implémentation complète :**
```python
from sqlalchemy import func, distinct

def get_dashboard(db: Session):
    """
    Tableau de bord complet avec toutes les statistiques.
    """
    # 1. Statistiques Shows
    total_shows = db.query(Show).filter(Show.is_deleted == False).count()
    published_shows = db.query(Show).filter(
        Show.status == "published",
        Show.is_deleted == False
    ).count()
    draft_shows = db.query(Show).filter(
        Show.status == "draft",
        Show.is_deleted == False
    ).count()
    
    # 2. Statistiques Utilisateurs
    total_users = db.query(User).filter(User.is_deleted == False).count()
    active_users = db.query(User).filter(
        User.is_deleted == False,
        User.last_login >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # 3. Statistiques Présentateurs
    total_presenters = db.query(Presenter).filter(
        Presenter.is_deleted == False
    ).count()
    
    # 4. Statistiques Invités
    total_guests = db.query(Guest).filter(Guest.is_deleted == False).count()
    unique_guests = db.query(func.count(distinct(Guest.id))).join(
        SegmentGuest
    ).scalar()
    
    # 5. Statistiques Segments
    total_segments = db.query(Segment).filter(
        Segment.is_deleted == False
    ).count()
    
    # 6. Statistiques Émissions
    total_emissions = db.query(Emission).filter(
        Emission.is_deleted == False
    ).count()
    
    # 7. Shows par statut
    shows_by_status = db.query(
        Show.status,
        func.count(Show.id).label("count")
    ).filter(Show.is_deleted == False).group_by(Show.status).all()
    
    # 8. Top 5 présentateurs (par nombre de shows)
    top_presenters = db.query(
        Presenter.name,
        func.count(ShowPresenter.show_id).label("show_count")
    ).join(ShowPresenter).group_by(Presenter.id).order_by(
        desc("show_count")
    ).limit(5).all()
    
    # 9. Top 5 invités (par nombre d'apparitions)
    top_guests = db.query(
        Guest.name,
        func.count(SegmentGuest.segment_id).label("appearance_count")
    ).join(SegmentGuest).group_by(Guest.id).order_by(
        desc("appearance_count")
    ).limit(5).all()
    
    # 10. Shows à venir (prochains 7 jours)
    upcoming_shows = db.query(Show).filter(
        Show.broadcast_date >= datetime.utcnow().date(),
        Show.broadcast_date <= datetime.utcnow().date() + timedelta(days=7),
        Show.status == "published",
        Show.is_deleted == False
    ).order_by(Show.broadcast_date).all()
    
    # 11. Activité récente (derniers logs)
    recent_activity = db.query(AuditLog).filter(
        AuditLog.is_deleted == False
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return {
        "global_stats": {
            "total_shows": total_shows,
            "published_shows": published_shows,
            "draft_shows": draft_shows,
            "total_users": total_users,
            "active_users": active_users,
            "total_presenters": total_presenters,
            "total_guests": total_guests,
            "unique_guests": unique_guests,
            "total_segments": total_segments,
            "total_emissions": total_emissions
        },
        "shows_by_status": [
            {"status": status, "count": count}
            for status, count in shows_by_status
        ],
        "top_presenters": [
            {"name": name, "show_count": count}
            for name, count in top_presenters
        ],
        "top_guests": [
            {"name": name, "appearance_count": count}
            for name, count in top_guests
        ],
        "upcoming_shows": [
            {
                "id": show.id,
                "title": show.title,
                "broadcast_date": show.broadcast_date.isoformat(),
                "status": show.status
            }
            for show in upcoming_shows
        ],
        "recent_activity": [
            {
                "action": log.action,
                "user_id": log.user_id,
                "table_name": log.table_name,
                "timestamp": log.timestamp.isoformat()
            }
            for log in recent_activity
        ]
    }
```

---

## Graphiques et rapports

### Shows par mois
```python
def get_shows_per_month(db: Session, year: int):
    """Nombre de shows par mois pour une année"""
    shows = db.query(
        func.extract('month', Show.broadcast_date).label('month'),
        func.count(Show.id).label('count')
    ).filter(
        func.extract('year', Show.broadcast_date) == year,
        Show.is_deleted == False
    ).group_by('month').order_by('month').all()
    
    return [
        {"month": int(month), "count": count}
        for month, count in shows
    ]
```

### Taux de publication
```python
def get_publication_rate(db: Session):
    """Pourcentage de shows publiés vs brouillons"""
    total = db.query(Show).filter(Show.is_deleted == False).count()
    published = db.query(Show).filter(
        Show.status == "published",
        Show.is_deleted == False
    ).count()
    
    rate = (published / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "published": published,
        "rate": round(rate, 2)
    }
```

---

## Route Dashboard

```python
@router.get("/dashboard")
def get_dashboard_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    """Tableau de bord principal"""
    
    # Vérifier permission
    if not crud_permissions.check_permissions(db, current_user.id, "view_dashboard"):
        raise HTTPException(403, "Permission denied")
    
    return get_dashboard(db)
```

---

**Navigation :**
- [← AUDIT.md](AUDIT.md)
- [↑ Retour à l'index](README.md)

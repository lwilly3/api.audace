# 🔔 Module NOTIFICATIONS - Système de Notifications

Documentation de la gestion des notifications utilisateurs.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctions métier](#fonctions-métier)
4. [Règles métier](#règles-métier)
5. [Exemples](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

### Responsabilités
- Création de notifications
- Récupération des notifications par utilisateur
- Marquage lu/non lu
- Suppression (soft delete)

### Fichier source
`app/db/crud/crud_notifications.py`

---

## 🏗️ Architecture

### Modèle Notification

```python
Notification:
    id: int (PK)
    user_id: int (FK → User, NOT NULL)
    title: str (NOT NULL)
    message: text
    type: str  # "info", "warning", "success", "error"
    read: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Relation
    user: User (Many-to-One)
```

### Types de notifications

```python
NOTIFICATION_TYPES = {
    "info": "Information générale",
    "warning": "Avertissement",
    "success": "Action réussie",
    "error": "Erreur"
}
```

---

## 🔧 Fonctions métier

### 1. create_notification()

```python
def create_notification(
    notification: NotificationCreate,
    db: Session,
    current_user: User
) -> Notification
```

**Description :** Crée une nouvelle notification.

**Logique :**
```python
def create_notification(notification: NotificationCreate, db: Session, current_user: User):
    try:
        new_notification = Notification(**notification.model_dump())
        
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        
        return new_notification
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating notification: {str(e)}")
```

**Usage typique :**
```python
# Notification de bienvenue
crud_notifications.create_notification(
    NotificationCreate(
        user_id=new_user.id,
        title="Bienvenue !",
        message="Votre compte a été créé avec succès.",
        type="success"
    ),
    db,
    current_user
)
```

---

### 2. get_user_notifications()

```python
def get_user_notifications(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session
) -> List[Notification]
```

**Description :** Récupère les notifications d'un utilisateur.

**Logique :**
```python
def get_user_notifications(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session
):
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_deleted == False
        ).order_by(
            Notification.created_at.desc()  # Plus récentes en premier
        ).offset(skip).limit(limit).all()
        
        return notifications if notifications else []
        
    except Exception as e:
        raise HTTPException(500, f"Error fetching notifications: {str(e)}")
```

**Version avec filtres :**
```python
def get_user_notifications_filtered(
    user_id: int,
    read: Optional[bool] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Filtrer par statut lu/non lu et type"""
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_deleted == False
    )
    
    # Filtrer par statut lu/non lu
    if read is not None:
        query = query.filter(Notification.read == read)
    
    # Filtrer par type
    if type:
        query = query.filter(Notification.type == type)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return notifications
```

---

### 3. update_notification()

```python
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session
) -> Notification
```

**Description :** Met à jour une notification (typiquement pour marquer comme lue).

**Logique :**
```python
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session
):
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(404, "Notification not found")
        
        # Appliquer les modifications
        update_data = notification_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(notification, key, value)
        
        db.commit()
        db.refresh(notification)
        
        return notification
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error updating notification: {str(e)}")
```

---

### 4. mark_as_read()

```python
def mark_as_read(notification_id: int, db: Session) -> Notification
```

**Description :** Raccourci pour marquer une notification comme lue.

**Logique :**
```python
def mark_as_read(notification_id: int, db: Session):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(404, "Notification not found")
    
    notification.read = True
    db.commit()
    db.refresh(notification)
    
    return notification
```

---

### 5. mark_all_as_read()

```python
def mark_all_as_read(user_id: int, db: Session) -> int
```

**Description :** Marque toutes les notifications d'un utilisateur comme lues.

**Logique :**
```python
def mark_all_as_read(user_id: int, db: Session):
    """Retourne le nombre de notifications marquées"""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False,
        Notification.is_deleted == False
    ).update({"read": True})
    
    db.commit()
    
    return count
```

---

### 6. delete_notification()

```python
def delete_notification(
    notification_id: int,
    db: Session
) -> bool
```

**Description :** Suppression logique d'une notification.

**Logique :**
```python
def delete_notification(notification_id: int, db: Session):
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(404, "Notification not found")
        
        # Soft delete
        notification.is_deleted = True
        db.commit()
        
        return True
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error deleting notification: {str(e)}")
```

---

### 7. get_notification_by_id()

```python
def get_notification_by_id(notification_id: int, db: Session) -> Notification
```

**Description :** Récupère une notification spécifique.

**Logique :**
```python
def get_notification_by_id(notification_id: int, db: Session):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.is_deleted == False
    ).first()
    
    if not notification:
        raise HTTPException(404, "Notification not found")
    
    return notification
```

---

## 📏 Règles métier

### 1. Création automatique
Notifications créées automatiquement lors de :
- Création de compte
- Assignation à un show
- Changement de statut de show
- Ajout/retrait de permissions

### 2. Durée de vie
- Garder 30 jours
- Archive/suppression automatique après 30 jours

### 3. Badge non lu
```python
def get_unread_count(user_id: int, db: Session) -> int:
    """Nombre de notifications non lues"""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False,
        Notification.is_deleted == False
    ).count()
```

---

## 💡 Exemples d'utilisation

### Envoyer une notification
```python
@router.post("/shows/{show_id}/publish")
def publish_show(show_id: int, db: Session = Depends(get_db)):
    show = crud_show.update_show_status(db, show_id, "published")
    
    # Notifier tous les présentateurs
    for presenter in show.presenters:
        crud_notifications.create_notification(
            NotificationCreate(
                user_id=presenter.user_id,
                title="Show publié",
                message=f"Le show '{show.title}' a été publié.",
                type="success"
            ),
            db,
            None
        )
    
    return show
```

### Récupérer avec badge
```python
@router.get("/me/notifications")
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    notifications = crud_notifications.get_user_notifications(
        current_user.id,
        db=db
    )
    
    unread_count = crud_notifications.get_unread_count(current_user.id, db)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }
```

---

**Navigation :**
- [← ROLES.md](ROLES.md)
- [→ AUDIT.md](AUDIT.md)
- [↑ Retour à l'index](README.md)

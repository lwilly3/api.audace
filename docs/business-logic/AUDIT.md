# 📝 Module AUDIT - Journalisation et Traçabilité

Documentation du système d'audit log pour tracer toutes les actions critiques.

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
- Enregistrement de toutes les actions critiques
- Archivage des logs anciens
- Récupération des logs pour audit
- Traçabilité complète des modifications

### Fichier source
`app/db/crud/crud_audit_logs.py`

---

## 🏗️ Architecture

### Modèle AuditLog (Logs actifs)

```python
AuditLog:
    id: int (PK)
    user_id: int (FK → User, optional)  # Peut être NULL (actions système)
    action: str (NOT NULL)  # "CREATE", "UPDATE", "DELETE", etc.
    table_name: str  # Table concernée
    record_id: int  # ID de l'enregistrement modifié
    timestamp: datetime (timezone-aware)
    is_deleted: bool = False
    deleted_at: datetime (optional)
    
    # Relation
    user: User (Many-to-One)
```

### Modèle ArchivedAuditLog (Logs archivés)

```python
ArchivedAuditLog:
    id: int (PK)
    user_id: int (optional)
    action: str
    table_name: str
    record_id: int
    timestamp: datetime
    archived_at: datetime (auto)
```

**Stratégie d'archivage :**
- Logs > 90 jours → Archivés
- Logs actifs : consultation rapide
- Logs archivés : conservation légale

---

## 🔧 Fonctions métier

### 1. create_audit_log()

```python
def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int],
    details: Optional[str]
) -> AuditLog
```

**Description :** Crée une entrée d'audit.

**Logique :**
```python
from datetime import datetime, timezone

def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int],
    table_name: str,
    record_id: int,
    details: Optional[str] = None
):
    try:
        new_log = AuditLog(
            action=action,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            timestamp=datetime.now(timezone.utc)  # Timezone-aware
        )
        
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return new_log
        
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Erreur lors de la création du log d'audit : {str(e)}")
```

**Actions courantes :**
```python
AUDIT_ACTIONS = {
    "CREATE": "Création d'un enregistrement",
    "UPDATE": "Modification d'un enregistrement",
    "DELETE": "Suppression d'un enregistrement",
    "LOGIN": "Connexion utilisateur",
    "LOGOUT": "Déconnexion utilisateur",
    "PERMISSION_CHANGE": "Modification de permissions",
    "ROLE_ASSIGN": "Assignation de rôle",
    "PASSWORD_RESET": "Réinitialisation mot de passe"
}
```

---

### 2. get_all_audit_logs()

```python
def get_all_audit_logs(db: Session) -> List[AuditLog]
```

**Description :** Récupère tous les logs d'audit actifs.

**Logique :**
```python
def get_all_audit_logs(db: Session):
    try:
        return db.query(AuditLog).filter(
            AuditLog.is_deleted == False
        ).order_by(AuditLog.timestamp.desc()).all()
        
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des logs : {str(e)}")
```

**Version avec pagination :**
```python
def get_audit_logs_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Logs avec filtres avancés"""
    query = db.query(AuditLog).filter(AuditLog.is_deleted == False)
    
    # Filtrer par utilisateur
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Filtrer par action
    if action:
        query = query.filter(AuditLog.action == action)
    
    # Filtrer par date
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    total = query.count()
    
    logs = query.order_by(
        AuditLog.timestamp.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": logs
    }
```

---

### 3. get_audit_log()

```python
def get_audit_log(db: Session, id: int) -> AuditLog
```

**Description :** Récupère un log spécifique.

**Logique :**
```python
def get_audit_log(db: Session, id: int):
    try:
        log = db.query(AuditLog).filter(
            AuditLog.id == id,
            AuditLog.is_deleted == False
        ).first()
        
        if not log:
            raise HTTPException(404, "Audit log not found")
        
        return log
        
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération du log : {str(e)}")
```

---

### 4. archive_audit_log()

```python
def archive_audit_log(db: Session, id: int) -> Optional[ArchivedAuditLog]
```

**Description :** Archive un log d'audit (déplace vers table d'archivage).

**Logique :**
```python
def archive_audit_log(db: Session, id: int):
    try:
        log = db.query(AuditLog).filter(
            AuditLog.id == id,
            AuditLog.is_deleted == False
        ).first()
        
        if not log:
            return None
        
        # Créer l'entrée archivée
        archived_log = ArchivedAuditLog(
            user_id=log.user_id,
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            timestamp=log.timestamp
        )
        
        db.add(archived_log)
        db.commit()
        
        # Marquer comme supprimé dans les logs actifs
        log.is_deleted = True
        log.deleted_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(log)
        
        return archived_log
        
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Erreur lors de l'archivage : {str(e)}")
```

---

### 5. archive_old_logs()

```python
def archive_old_logs(db: Session, days: int = 90) -> int
```

**Description :** Archive automatiquement tous les logs de plus de X jours.

**Logique :**
```python
from datetime import timedelta

def archive_old_logs(db: Session, days: int = 90):
    """
    Archive les logs de plus de X jours.
    
    Args:
        days: Nombre de jours à conserver dans les logs actifs
    
    Returns:
        int: Nombre de logs archivés
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    old_logs = db.query(AuditLog).filter(
        AuditLog.timestamp < cutoff_date,
        AuditLog.is_deleted == False
    ).all()
    
    archived_count = 0
    
    for log in old_logs:
        archived = archive_audit_log(db, log.id)
        if archived:
            archived_count += 1
    
    return archived_count
```

**Tâche cron recommandée :**
```python
# scripts/archive_audit_logs.py

from app.db.database import SessionLocal
from app.db.crud import crud_audit_logs
from datetime import datetime

def archive_logs_task():
    """Script à exécuter mensuellement"""
    db = SessionLocal()
    try:
        count = crud_audit_logs.archive_old_logs(db, days=90)
        print(f"Archived {count} audit logs")
    finally:
        db.close()

if __name__ == "__main__":
    archive_logs_task()
```

---

### 6. get_all_archived_audit_logs()

```python
def get_all_archived_audit_logs(db: Session) -> List[ArchivedAuditLog]
```

**Description :** Récupère tous les logs archivés.

**Logique :**
```python
def get_all_archived_audit_logs(db: Session):
    try:
        return db.query(ArchivedAuditLog).order_by(
            ArchivedAuditLog.timestamp.desc()
        ).all()
        
    except SQLAlchemyError as e:
        raise Exception(f"Erreur lors de la récupération des logs archivés : {str(e)}")
```

---

### 7. get_user_audit_trail()

```python
def get_user_audit_trail(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[AuditLog]
```

**Description :** Historique complet des actions d'un utilisateur.

**Logique :**
```python
def get_user_audit_trail(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Trace complète des actions d'un utilisateur"""
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.is_deleted == False
    ).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return logs
```

---

## 📏 Règles métier

### 1. Actions à logger obligatoirement
- Toutes les modifications de données (CREATE, UPDATE, DELETE)
- Changements de permissions
- Connexions/déconnexions
- Réinitialisations de mot de passe
- Assignations de rôles

### 2. Conservation
- Logs actifs : 90 jours
- Logs archivés : 7 ans (conformité légale)

### 3. Timezone
- **TOUJOURS** utiliser `datetime.now(timezone.utc)`
- Jamais de `datetime.utcnow()` (deprecated)

### 4. Anonymisation
- user_id peut être NULL (actions système)
- Pas de données sensibles dans les logs

---

## 💡 Exemples d'utilisation

### Logger une création
```python
@router.post("/shows")
def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Créer le show
    new_show = crud_show.create_show(db, show, current_user.id)
    
    # Logger l'action
    crud_audit_logs.create_audit_log(
        db,
        action="CREATE",
        user_id=current_user.id,
        table_name="shows",
        record_id=new_show.id,
        details=f"Created show: {new_show.title}"
    )
    
    return new_show
```

### Visualiser l'historique d'un utilisateur
```python
@router.get("/admin/users/{user_id}/audit-trail")
def get_user_history(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)
):
    """Historique complet d'un utilisateur"""
    logs = crud_audit_logs.get_user_audit_trail(db, user_id, skip, limit)
    
    return {
        "user_id": user_id,
        "logs": [
            {
                "action": log.action,
                "table": log.table_name,
                "record_id": log.record_id,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }
```

### Archivage automatique
```bash
# Cron job : tous les 1er du mois à 2h
0 2 1 * * /usr/bin/python3 /path/to/scripts/archive_audit_logs.py
```

---

**Navigation :**
- [← NOTIFICATIONS.md](NOTIFICATIONS.md)
- [→ UTILITIES.md](UTILITIES.md)
- [↑ Retour à l'index](README.md)

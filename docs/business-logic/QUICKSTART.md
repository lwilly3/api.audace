# 🚀 Guide de Démarrage Rapide

Guide pour comprendre rapidement l'architecture et commencer à utiliser la documentation.

---

## 📖 Par où commencer ?

### Pour un nouveau développeur

**1. Comprendre la structure générale**
- Lire [README.md](README.md) pour voir l'organisation
- Consulter [docs/architecture/README.md](../architecture/README.md) pour l'architecture globale

**2. Comprendre l'authentification (ESSENTIEL)**
- Lire [AUTH.md](AUTH.md) pour comprendre les tokens JWT
- Lire [PERMISSIONS.md](PERMISSIONS.md) pour le système de contrôle d'accès
- Lire [ROLES.md](ROLES.md) pour les rôles utilisateurs

**3. Comprendre les entités principales**
- Lire [USERS.md](USERS.md) pour la gestion des utilisateurs
- Lire [SHOWS.md](SHOWS.md) pour la logique métier centrale
- Lire [EMISSIONS.md](EMISSIONS.md) et [SEGMENTS.md](SEGMENTS.md) pour la hiérarchie

**4. Explorer les fonctionnalités avancées**
- [PRESENTERS.md](PRESENTERS.md) et [GUESTS.md](GUESTS.md) pour les participants
- [NOTIFICATIONS.md](NOTIFICATIONS.md) pour les alertes
- [AUDIT.md](AUDIT.md) pour la traçabilité

---

## 🔍 Recherche par cas d'usage

### "Je dois créer une nouvelle route"

1. Identifier l'entité concernée (User, Show, Guest...)
2. Consulter le fichier correspondant (ex: USERS.md)
3. Vérifier les permissions requises dans PERMISSIONS.md
4. Utiliser les fonctions CRUD existantes
5. Ajouter un audit log (voir AUDIT.md)

**Exemple :**
```python
# Créer une route pour lister les shows
@router.get("/shows")
def list_shows(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # 1. Vérifier permission (voir PERMISSIONS.md)
    if not crud_permissions.check_permissions(db, current_user.id, "view_show"):
        raise HTTPException(403, "Permission denied")
    
    # 2. Utiliser la fonction CRUD (voir SHOWS.md)
    shows = crud_show.get_shows(db)
    
    # 3. Logger l'action (voir AUDIT.md)
    crud_audit_logs.create_audit_log(
        db,
        action="LIST_SHOWS",
        user_id=current_user.id,
        table_name="shows",
        record_id=None
    )
    
    return shows
```

---

### "Je dois comprendre une erreur"

1. Vérifier le module concerné dans la documentation
2. Consulter la section "Erreurs" de la fonction
3. Vérifier les contraintes dans "Règles métier"

**Exemple : "User not found"**
→ Consulter [USERS.md](USERS.md) → Fonction `get_user_or_404()` → Voir que user_id doit exister et is_deleted=False

---

### "Je dois ajouter une permission"

1. Consulter [PERMISSIONS.md](PERMISSIONS.md) → Section "Modèle UserPermission"
2. Ajouter le champ dans le modèle SQLAlchemy
3. Créer une migration Alembic
4. Mettre à jour `initialize_user_permissions()`
5. Utiliser `check_permissions()` dans les routes

---

### "Je dois optimiser une requête lente"

1. Identifier la fonction dans la documentation
2. Consulter la section "Contraintes" → "Performances"
3. Appliquer eager loading (voir exemples dans SHOWS.md)
4. Ajouter des index si nécessaire

**Exemple :**
```python
# ❌ LENT : N+1 queries
shows = db.query(Show).all()
for show in shows:
    presenters = show.presenters  # +1 query par show

# ✅ RAPIDE : Eager loading
from sqlalchemy.orm import joinedload

shows = db.query(Show).options(
    joinedload(Show.presenters)
).all()
```

---

## 🗺️ Cartographie des modules

### Modules Core (lecture obligatoire)
```
AUTH ──→ PERMISSIONS ──→ USERS
  │           │
  └───────────┴──────→ ROLES
```

### Modules Entités
```
EMISSIONS (séries)
    └── SHOWS (épisodes)
           ├── SEGMENTS (parties)
           │     └── GUESTS (invités par segment)
           └── PRESENTERS (animateurs)
```

### Modules Support
```
NOTIFICATIONS ──→ Alertes utilisateurs
AUDIT ──────────→ Traçabilité
UTILITIES ──────→ Recherche + Dashboard
```

---

## 📋 Checklist de développement

Avant de créer une nouvelle fonctionnalité :

- [ ] J'ai vérifié les permissions requises
- [ ] J'ai consulté la documentation du module concerné
- [ ] J'ai compris le flux de données
- [ ] J'ai vérifié les contraintes d'intégrité
- [ ] J'ai prévu la gestion des erreurs
- [ ] J'ai ajouté un audit log
- [ ] J'ai testé avec différents rôles (Admin, Presenter, Viewer)
- [ ] J'ai vérifié les performances (pas de N+1)

---

## 🔗 Liens rapides

### Documentation architecture
- [Architecture globale](../architecture/README.md)
- [Modèles de données](../architecture/DATA_MODELS.md)
- [Endpoints API](../architecture/API_ENDPOINTS.md)

### Documentation business logic
- [Index des modules](README.md)
- [Référence des fonctions](../architecture/FUNCTIONS_REFERENCE.md)

---

## 💡 Bonnes pratiques

### 1. Toujours utiliser les fonctions CRUD existantes
```python
# ✅ BON
user = crud_users.get_user_or_404(db, user_id)

# ❌ MAUVAIS : query directe
user = db.query(User).filter(User.id == user_id).first()
```

### 2. Toujours vérifier les permissions
```python
# ✅ BON
if not crud_permissions.check_permissions(db, user.id, "create_show"):
    raise HTTPException(403, "Permission denied")

# ❌ MAUVAIS : pas de vérification
# (risque de sécurité)
```

### 3. Toujours utiliser soft delete
```python
# ✅ BON
show.is_deleted = True
db.commit()

# ❌ MAUVAIS : suppression physique
db.delete(show)
db.commit()
```

### 4. Toujours logger les actions critiques
```python
# ✅ BON
crud_audit_logs.create_audit_log(
    db,
    action="DELETE_SHOW",
    user_id=current_user.id,
    table_name="shows",
    record_id=show_id
)

# ❌ MAUVAIS : pas de log
```

### 5. Toujours utiliser eager loading pour les relations
```python
# ✅ BON
from sqlalchemy.orm import joinedload

shows = db.query(Show).options(
    joinedload(Show.presenters),
    joinedload(Show.segments)
).all()

# ❌ MAUVAIS : lazy loading (N+1)
shows = db.query(Show).all()
```

---

## 🆘 Aide et support

### Questions fréquentes

**Q: Comment ajouter un nouveau rôle ?**
→ Voir [ROLES.md](ROLES.md) → Fonction `create_role()`

**Q: Comment envoyer une notification ?**
→ Voir [NOTIFICATIONS.md](NOTIFICATIONS.md) → Fonction `create_notification()`

**Q: Comment rechercher dans toute l'application ?**
→ Voir [UTILITIES.md](UTILITIES.md) → Fonction `global_search()`

**Q: Comment voir l'historique d'un utilisateur ?**
→ Voir [AUDIT.md](AUDIT.md) → Fonction `get_user_audit_trail()`

---

## 📚 Glossaire

| Terme | Définition | Voir |
|-------|------------|------|
| **CRUD** | Create, Read, Update, Delete | Tous les modules |
| **Soft Delete** | Suppression logique (is_deleted=True) | Tous les modules |
| **Hard Delete** | Suppression physique (db.delete) | À éviter |
| **Eager Loading** | Chargement anticipé des relations | SHOWS.md, USERS.md |
| **N+1 Problem** | Problème de performance (queries multiples) | SHOWS.md |
| **RBAC** | Role-Based Access Control | PERMISSIONS.md |
| **JWT** | JSON Web Token (authentification) | AUTH.md |
| **Audit Log** | Journal de traçabilité | AUDIT.md |

---

**Prêt à commencer ? Consultez [README.md](README.md) pour l'index complet !**

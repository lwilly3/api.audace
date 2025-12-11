# 👥 Module USERS - Gestion des Utilisateurs

Documentation complète de la logique métier pour la gestion des utilisateurs.

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
- Gestion du cycle de vie des utilisateurs (CRUD complet)
- Initialisation des permissions par défaut
- Gestion de l'historique de connexion
- Gestion des notifications utilisateur
- Filtrage des utilisateurs (présentateurs vs non-présentateurs)
- Soft delete et archivage
- Audit des actions utilisateur

### Fichier source
`app/db/crud/crud_users.py`

### Dépendances
```python
# Modèles
from app.models import User, LoginHistory, Notification, AuditLog
from app.models import Presenter, Guest, ArchivedAuditLog

# CRUD externes
from app.db.crud.crud_permissions import initialize_user_permissions

# Utilitaires
from app.utils import utils  # Hash passwords
from app.schemas import UserUpdate, UserCreate
```

---

## 🏗️ Architecture

### Modèle User

```python
User:
    id: int (PK)
    username: str
    name: str
    family_name: str
    email: str (unique)
    phone_number: str
    password: str (hashed)
    profilePicture: str (URL)
    is_active: bool (default: True)
    is_deleted: bool (default: False)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime (nullable)
    
    # Relations
    permissions: UserPermissions (One-to-One)
    roles: List[Role] (Many-to-Many)
    login_history: List[LoginHistory]
    notifications: List[Notification]
    audit_logs: List[AuditLog]
    shows_created: List[Show]
    emissions_created: List[Emission]
```

### Flux de données

```
Client Request
      ↓
Route (users_route.py)
      ↓
Schema Validation (UserCreate/UserUpdate)
      ↓
CRUD Function (crud_users.py)
      ↓
├─→ Hash Password (utils.hash)
├─→ Create User in DB
├─→ Initialize Permissions (crud_permissions)
└─→ Create Audit Log
      ↓
Response to Client
```

---

## 🔧 Fonctions métier

### 1. get_non_presenters()

**Signature :**
```python
def get_non_presenters(db: Session) -> List[dict]
```

**Description :**
Récupère tous les utilisateurs qui ne sont pas associés à un présentateur.

**Logique métier :**
1. Sous-requête pour obtenir les `users_id` de tous les présentateurs actifs
2. Query principale pour récupérer les users NON présents dans la sous-requête
3. Filtre `is_deleted = False` sur les deux queries
4. Sérialisation complète des données utilisateur

**Paramètres :**
- `db` (Session) : Session SQLAlchemy active

**Retour :**
```python
[
    {
        "id": 1,
        "username": "john_doe",
        "name": "John",
        "family_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+33612345678",
        "profilePicture": "https://...",
        "is_active": True,
        "created_at": "2025-12-11T10:00:00"
    },
    ...
]
```

**Contraintes :**
- Exclut les utilisateurs avec `is_deleted = True`
- Exclut les présentateurs avec `is_deleted = True`
- Utilise `NOT IN` pour l'exclusion (attention aux performances si beaucoup de présentateurs)

**Optimisations possibles :**
```python
# Avec LEFT JOIN pour meilleures performances
non_presenters = (
    db.query(User)
    .outerjoin(Presenter, Presenter.users_id == User.id)
    .filter(
        User.is_deleted == False,
        Presenter.id == None  # Pas de présentateur associé
    )
    .all()
)
```

**Erreurs possibles :**
- `Exception` : Erreur SQL générique (loggée automatiquement)

**Cas d'usage :**
- Affichage liste d'utilisateurs éligibles pour devenir présentateurs
- Attribution de rôles spécifiques
- Statistiques utilisateurs

---

### 2. get_user_or_404_with_permissions()

**Signature :**
```python
def get_user_or_404_with_permissions(db: Session, user_id: int) -> dict
```

**Description :**
Récupère un utilisateur avec toutes ses permissions chargées en une seule requête.

**Logique métier :**
1. Eager loading des permissions avec `joinedload(User.permissions)`
2. Filtre `is_active = True` (les inactifs sont considérés comme supprimés)
3. Lève HTTPException 404 si non trouvé ou inactif
4. Sérialise les permissions dans un format flat pour facilité d'utilisation

**Paramètres :**
- `db` (Session) : Session SQLAlchemy
- `user_id` (int) : ID de l'utilisateur

**Retour :**
```python
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "can_create_showplan": True,
    "can_edit_showplan": True,
    "can_archive_showplan": False,
    "can_delete_showplan": False,
    "can_destroy_showplan": False,
    "can_changestatus_showplan": True,
    # ... toutes les autres permissions
}
```

**Contraintes :**
- Utilisateur doit être actif (`is_active = True`)
- Permissions doivent exister (créées à l'inscription)

**Relations chargées :**
- `user.permissions` (One-to-One avec UserPermissions)

**Erreurs :**
- `HTTPException(404)` : Utilisateur introuvable ou inactif
- `NoResultFound` : Converti en HTTPException 404

**Cas d'usage :**
- Vérification des droits dans les routes
- Affichage du profil avec permissions
- Middleware de contrôle d'accès

**Optimisation :**
```python
# Évite le N+1 query problem
# Sans joinedload:
user = db.query(User).get(user_id)  # 1 query
permissions = user.permissions       # +1 query (lazy loading)

# Avec joinedload:
user = db.query(User).options(joinedload(User.permissions)).get(user_id)  # 1 query
permissions = user.permissions  # Déjà chargé !
```

---

### 3. get_user_or_404()

**Signature :**
```python
def get_user_or_404(db: Session, user_id: int) -> User | None
```

**Description :**
Version simplifiée sans chargement des permissions. Retourne None au lieu de lever une exception.

**Logique métier :**
1. Query simple sur `User.id` et `User.is_active`
2. Retourne l'objet User complet ou None
3. Log des erreurs SQL mais ne propage pas

**Paramètres :**
- `db` (Session)
- `user_id` (int)

**Retour :**
- `User` : Objet SQLAlchemy complet
- `None` : Si introuvable ou inactif

**Contraintes :**
- Filtre automatique sur `is_active = True`
- Ne lève PAS d'exception (caller doit vérifier le None)

**Différence avec get_user_or_404_with_permissions :**
```python
# Version avec permissions (lève exception)
try:
    user = get_user_or_404_with_permissions(db, 1)
    # user est un dict
except HTTPException:
    # User introuvable

# Version simple (retourne None)
user = get_user_or_404(db, 1)
if user is None:
    # User introuvable
# user est un objet User (ORM)
```

**Cas d'usage :**
- Vérifications internes où None est acceptable
- Éviter les exceptions dans les boucles
- Opérations batch

---

### 4. get_all_users()

**Signature :**
```python
def get_all_users(db: Session) -> List[User]
```

**Description :**
Récupère tous les utilisateurs actifs avec leurs rôles chargés.

**Logique métier :**
1. Query avec `joinedload(User.roles)` pour eager loading
2. Filtre `is_active = True`
3. Retourne liste complète (attention à la taille !)

**Paramètres :**
- `db` (Session)

**Retour :**
- `List[User]` : Liste complète ou liste vide si erreur

**Contraintes :**
- Pas de pagination (peut être très lourd !)
- Charge tous les rôles en mémoire
- Ne filtre PAS par `is_deleted` (seulement `is_active`)

**⚠️ Problème de performances :**
```python
# Mauvais : charge tout en mémoire
users = get_all_users(db)  # Peut être 10,000+ users !

# Meilleur : avec pagination
users = db.query(User).filter(User.is_active == True).limit(100).all()

# Ou itérer par batch
from sqlalchemy import func
total = db.query(func.count(User.id)).scalar()
batch_size = 1000
for offset in range(0, total, batch_size):
    users_batch = db.query(User).offset(offset).limit(batch_size).all()
    # Traiter le batch
```

**Recommandation :**
Créer une version paginée :
```python
def get_all_users_paginated(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
```

**Cas d'usage :**
- Admin : liste complète des utilisateurs (avec pagination côté frontend)
- Export de données
- Statistiques globales

---

### 5. create_user()

**Signature :**
```python
def create_user(db: Session, user_data: dict) -> User
```

**Description :**
Crée un nouvel utilisateur avec initialisation automatique des permissions par défaut.

**Logique métier :**
1. Vérification unicité de l'email
2. Hash du mot de passe avec bcrypt
3. Création de l'utilisateur en base
4. Flush pour obtenir l'ID
5. Appel à `initialize_user_permissions(db, user.id)`
6. Création d'un log d'audit
7. Commit final

**Paramètres :**
```python
user_data: dict = {
    "username": str,        # Obligatoire
    "name": str,            # Obligatoire
    "family_name": str,     # Obligatoire
    "email": str,           # Obligatoire, unique
    "phone_number": str,    # Optionnel
    "password": str,        # Obligatoire (sera hashé)
    "profilePicture": str   # Optionnel, URL
}
```

**Retour :**
- `User` : Utilisateur créé avec permissions initialisées

**Workflow complet :**
```python
def create_user(db: Session, user_data: dict) -> User:
    try:
        # 1. Vérifier email unique
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            raise HTTPException(409, "Email already exists")
        
        # 2. Hash password
        hashed_password = utils.hash(user_data["password"])
        
        # 3. Créer user
        new_user = User(
            username=user_data["username"],
            name=user_data["name"],
            family_name=user_data["family_name"],
            email=user_data["email"],
            phone_number=user_data.get("phone_number"),
            password=hashed_password,
            profilePicture=user_data.get("profilePicture"),
            is_active=True
        )
        db.add(new_user)
        db.flush()  # Obtenir l'ID sans commit
        
        # 4. Initialiser permissions
        initialize_user_permissions(db, new_user.id)
        
        # 5. Audit log
        create_audit_log(
            db,
            action="CREATE",
            user_id=None,  # Système
            details=json.dumps({
                "entity_type": "User",
                "entity_id": new_user.id,
                "email": new_user.email
            })
        )
        
        # 6. Commit final
        db.commit()
        db.refresh(new_user)
        
        return new_user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(500, "Error creating user")
```

**Contraintes :**
- Email unique (contrainte DB)
- Password minimum 8 caractères (validation Pydantic)
- Username unique (recommandé mais pas implémenté)

**Erreurs possibles :**
- `HTTPException(409)` : Email déjà utilisé
- `HTTPException(500)` : Erreur SQL
- `ValidationError` : Données invalides (Pydantic)

**Cascade d'effets :**
1. Création de `User`
2. Création de `UserPermissions` (par initialize_user_permissions)
3. Création de `AuditLog`

**Cas d'usage :**
- Inscription (signup)
- Création par admin
- Import utilisateurs

---

### 6. update_user()

**Signature :**
```python
def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]
```

**Description :**
Met à jour les informations d'un utilisateur avec validation et audit.

**Logique métier :**
1. Récupération de l'utilisateur existant
2. Si password fourni, le hasher avant sauvegarde
3. Mise à jour uniquement des champs fournis (exclude_unset)
4. `updated_at` mis à jour automatiquement (trigger DB ou ORM)
5. Création d'un audit log avec les changements
6. Commit et refresh

**Paramètres :**
```python
user_update: UserUpdate = {
    "username": str,      # Optionnel
    "name": str,          # Optionnel
    "family_name": str,   # Optionnel
    "email": str,         # Optionnel
    "phone_number": str,  # Optionnel
    "password": str,      # Optionnel (sera hashé)
    "profilePicture": str # Optionnel
}
```

**Retour :**
- `User` : Utilisateur mis à jour
- `None` : Si utilisateur introuvable

**Workflow avec audit :**
```python
def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    user = get_user_or_404(db, user_id)
    if not user:
        return None
    
    # Capturer les changements pour audit
    changes = {}
    for field, new_value in user_update.dict(exclude_unset=True).items():
        old_value = getattr(user, field)
        if old_value != new_value:
            if field == "password":
                changes[field] = {"old": "***", "new": "***"}  # Masquer
                new_value = utils.hash(new_value)
            else:
                changes[field] = {"old": old_value, "new": new_value}
            setattr(user, field, new_value)
    
    if changes:
        db.commit()
        db.refresh(user)
        
        # Audit log
        create_audit_log(
            db,
            action="UPDATE",
            user_id=user_id,
            details=json.dumps({
                "entity_type": "User",
                "entity_id": user_id,
                "changes": changes
            })
        )
    
    return user
```

**Contraintes :**
- Email unique si modifié
- Password hashé automatiquement
- `updated_at` mis à jour automatiquement

**Cas d'usage :**
- Modification de profil
- Changement de mot de passe
- Mise à jour administrative

---

### 7. delete_user()

**Signature :**
```python
def delete_user(db: Session, user_id: int) -> bool
```

**Description :**
Soft delete d'un utilisateur. Met `is_deleted = True` et `is_active = False`.

**Logique métier :**
1. Récupération de l'utilisateur
2. Mise à jour `is_deleted = True`
3. Mise à jour `is_active = False`
4. Mise à jour `deleted_at = datetime.now()`
5. Création audit log
6. Commit

**Paramètres :**
- `user_id` (int)

**Retour :**
- `True` : Suppression réussie
- `False` : Utilisateur introuvable

**Implémentation complète :**
```python
def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_or_404(db, user_id)
    if not user:
        return False
    
    # Soft delete
    user.is_deleted = True
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    
    # Audit
    create_audit_log(
        db,
        action="DELETE",
        user_id=user_id,
        details=json.dumps({
            "entity_type": "User",
            "entity_id": user_id,
            "email": user.email
        })
    )
    
    db.commit()
    return True
```

**Contraintes :**
- Données préservées en base
- Relations préservées (Foreign Keys restent valides)
- Filtrage automatique dans les queries (`is_active = True`)

**Effets sur les relations :**
- `shows_created` : Toujours visibles (FK préservée)
- `login_history` : Préservé (audit)
- `notifications` : Préservées
- `permissions` : Préservées mais non actives

**Restauration possible :**
```python
def restore_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_deleted:
        return False
    
    user.is_deleted = False
    user.is_active = True
    user.deleted_at = None
    db.commit()
    return True
```

**Cas d'usage :**
- Suppression par admin
- Désactivation compte utilisateur
- Conformité RGPD (soft delete, pas suppression physique)

---

### 8. get_user_logins()

**Signature :**
```python
def get_user_logins(db: Session, user_id: int) -> List[LoginHistory]
```

**Description :**
Récupère l'historique complet des connexions d'un utilisateur.

**Logique métier :**
1. Query sur `LoginHistory.user_id`
2. Tri par `login_time DESC` (plus récent en premier)
3. Retourne liste complète (considérer pagination)

**Paramètres :**
- `user_id` (int)

**Retour :**
```python
[
    LoginHistory(
        id=1,
        user_id=5,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
        login_time=datetime(2025, 12, 11, 10, 30),
        success=True
    ),
    ...
]
```

**Cas d'usage :**
- Sécurité : détection d'accès suspects
- Audit : traçabilité des connexions
- Statistiques : analyse d'activité

**Optimisation avec pagination :**
```python
def get_user_logins_paginated(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 50
) -> List[LoginHistory]:
    return (
        db.query(LoginHistory)
        .filter(LoginHistory.user_id == user_id)
        .order_by(LoginHistory.login_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
```

---

### 9. get_user_notifications()

**Signature :**
```python
def get_user_notifications(db: Session, user_id: int) -> List[Notification]
```

**Description :**
Récupère toutes les notifications d'un utilisateur.

**Retour :**
```python
[
    Notification(
        id=1,
        user_id=5,
        message="Nouvelle émission ajoutée",
        read=False,
        created_at=datetime(2025, 12, 11, 14, 00)
    ),
    ...
]
```

**Cas d'usage :**
- Centre de notifications
- Badge de notifications non lues
- Historique des alertes

---

### 10. get_user_audit_logs()

**Signature :**
```python
def get_user_audit_logs(db: Session, user_id: int) -> List[AuditLog]
```

**Description :**
Récupère tous les logs d'audit des actions effectuées par un utilisateur.

**Retour :**
```python
[
    AuditLog(
        id=1,
        user_id=5,
        action="CREATE",
        entity_type="Show",
        entity_id=10,
        changes={"name": "Morning Show", ...},
        timestamp=datetime(2025, 12, 11, 9, 0)
    ),
    ...
]
```

**Cas d'usage :**
- Audit de sécurité
- Traçabilité des modifications
- Historique d'activité utilisateur

---

## 📏 Règles métier

### 1. Unicité
- **Email** : Unique dans toute la base (contrainte DB)
- **Username** : Recommandé unique mais non contraint actuellement

### 2. Soft Delete
- Utilisateur jamais supprimé physiquement
- `is_deleted = True` ET `is_active = False`
- `deleted_at` contient la date de suppression
- Relations préservées

### 3. Permissions
- Initialisées automatiquement à la création
- Toutes à `False` par défaut
- Admin doit les activer manuellement

### 4. Audit
- Toutes les actions (CREATE, UPDATE, DELETE) loguées
- Changements détaillés dans le log
- Mots de passe masqués dans les logs

### 5. Sécurité
- Passwords toujours hashés (bcrypt)
- Jamais de mot de passe en clair dans les logs
- Token JWT pour authentification
- Vérification `is_active` sur toutes les queries

---

## 🔗 Relations

### Dépendances entrantes (qui utilise Users ?)
- **crud_auth.py** : Login, vérification credentials
- **crud_show.py** : `created_by` foreign key
- **crud_presenter.py** : Association user ↔ presenter
- **crud_permissions.py** : Gestion permissions user
- **crud_audit_logs.py** : Logging actions user

### Dépendances sortantes (Users utilise quoi ?)
- **crud_permissions.py** : `initialize_user_permissions()`
- **utils.py** : `hash()`, `verify()`
- **crud_audit_logs.py** : `create_audit_log()`

### Relations de base de données
```
User (1) ──────< (N) LoginHistory
  │
  ├─────< (N) Notification
  │
  ├─────< (N) AuditLog
  │
  ├─────< (N) Show (created_by)
  │
  ├─────< (N) Emission (created_by)
  │
  ├────> (1) UserPermissions
  │
  └────< (N) Role (Many-to-Many via user_roles)
```

---

## ⚠️ Contraintes

### Performances
- `get_all_users()` peut être très lent (pas de pagination)
- `get_non_presenters()` utilise NOT IN (lent si beaucoup de présentateurs)
- Toujours utiliser `joinedload()` pour éviter N+1 queries

### Limites
- Pas de vérification de doublon sur `username`
- Pas de validation de format d'email (délégué à Pydantic)
- Pas de limite sur le nombre de tentatives de login
- Pas de rate limiting

### Sécurité
- Pas de vérification de force du mot de passe (délégué à Pydantic)
- Pas de double authentification (2FA)
- Pas d'expiration forcée des mots de passe

---

## 💡 Exemples d'utilisation

### Scénario 1 : Inscription complète

```python
from app.db.crud import crud_users
from app.schemas import UserCreate

# Dans la route
@router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Validation automatique par Pydantic
    
    # Création avec initialisation permissions
    new_user = crud_users.create_user(db, user_data.dict())
    
    # Générer token JWT
    token = create_access_token({"user_id": new_user.id})
    
    return {
        "user": new_user,
        "access_token": token,
        "token_type": "bearer"
    }
```

### Scénario 2 : Vérification permissions

```python
@router.post("/shows")
def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Récupérer user avec permissions
    user_with_perms = crud_users.get_user_or_404_with_permissions(db, current_user.id)
    
    # Vérifier permission
    if not user_with_perms["can_create_showplan"]:
        raise HTTPException(403, "Permission denied")
    
    # Créer le show
    new_show = crud_show.create_show(db, show, current_user.id)
    return new_show
```

### Scénario 3 : Liste utilisateurs disponibles pour présentateurs

```python
@router.get("/users/available-for-presenter")
def get_available_users(db: Session = Depends(get_db)):
    # Récupérer les non-présentateurs
    available_users = crud_users.get_non_presenters(db)
    
    return {
        "count": len(available_users),
        "users": available_users
    }
```

### Scénario 4 : Audit utilisateur

```python
@router.get("/users/{user_id}/activity")
def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Vérifier droits (admin ou self)
    if current_user.id != user_id and not is_admin(current_user):
        raise HTTPException(403, "Access denied")
    
    # Récupérer toutes les activités
    logins = crud_users.get_user_logins(db, user_id)
    notifications = crud_users.get_user_notifications(db, user_id)
    audit_logs = crud_users.get_user_audit_logs(db, user_id)
    
    return {
        "user_id": user_id,
        "recent_logins": logins[:10],
        "unread_notifications": [n for n in notifications if not n.read],
        "recent_actions": audit_logs[:20]
    }
```

---

**Navigation :**
- [← Retour à l'index](README.md)
- [AUTH.md →](AUTH.md)
- [PERMISSIONS.md →](PERMISSIONS.md)

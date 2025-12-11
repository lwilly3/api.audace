# 📚 Référence des fonctions

Documentation complète de toutes les fonctions de l'API Audace organisée par module.

---

## Table des matières

1. [Base de données](#base-de-données)
2. [Authentification et sécurité](#authentification-et-sécurité)
3. [Gestion des utilisateurs](#gestion-des-utilisateurs)
4. [Shows et émissions](#shows-et-émissions)
5. [Présentateurs et invités](#présentateurs-et-invités)
6. [Segments](#segments)
7. [Permissions et rôles](#permissions-et-rôles)
8. [Audit et logs](#audit-et-logs)
9. [Notifications](#notifications)
10. [Recherche](#recherche)
11. [Tableau de bord](#tableau-de-bord)
12. [Utilitaires](#utilitaires)

---

## 🗄️ Base de données

### Module : `app/db/database.py`

#### `get_db()`
Crée et gère une session de base de données.

**Utilisation :**
```python
from app.db.database import get_db
from fastapi import Depends

@router.get("/")
def my_route(db: Session = Depends(get_db)):
    # db est une session SQLAlchemy active
    users = db.query(User).all()
    return users
```

**Comportement :**
- Crée une session SQLAlchemy
- Yield la session (disponible pendant la requête)
- Ferme automatiquement la session après la requête
- Gère les erreurs avec try/finally

**Type de retour :** `Generator[Session]`

---

## 🔐 Authentification et sécurité

### Module : `app/utils/utils.py`

#### `hash(password: str) -> str`
Hash un mot de passe avec bcrypt.

**Paramètres :**
- `password` (str) : Mot de passe en clair

**Retour :**
- `str` : Hash bcrypt du mot de passe

**Exemple :**
```python
from app.utils import utils

hashed = utils.hash("MonMotDePasse123!")
# Retourne : "$2b$12$..."
```

**Utilisation :**
- Lors de la création d'un utilisateur
- Lors du changement de mot de passe

---

#### `verify(plain_password: str, hashed_password: str) -> bool`
Vérifie qu'un mot de passe correspond à son hash.

**Paramètres :**
- `plain_password` (str) : Mot de passe en clair
- `hashed_password` (str) : Hash bcrypt

**Retour :**
- `bool` : True si le mot de passe est correct

**Exemple :**
```python
is_valid = utils.verify("MonMotDePasse123!", user.password)
if not is_valid:
    raise HTTPException(401, "Invalid credentials")
```

**Utilisation :**
- Lors du login
- Lors de la vérification de l'ancien mot de passe

---

### Module : `app/db/crud/crud_auth.py`

#### `revoke_token(db: Session, token: str) -> RevokedToken`
Révoque un token JWT (logout).

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : Token JWT à révoquer

**Retour :**
- `RevokedToken` : Instance du token révoqué

**Exemple :**
```python
revoked = crud_auth.revoke_token(db, jwt_token)
# Le token est maintenant dans la table revoked_tokens
```

**Comportement :**
- Vérifie si le token existe déjà
- Crée une entrée dans `revoked_tokens`
- Commit la transaction
- Retourne l'objet créé

**Erreurs possibles :**
- `HTTPException(400)` : Token déjà révoqué

---

#### `is_token_revoked(db: Session, token: str) -> bool`
Vérifie si un token a été révoqué.

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : Token JWT à vérifier

**Retour :**
- `bool` : True si le token est révoqué

**Exemple :**
```python
if crud_auth.is_token_revoked(db, token):
    raise HTTPException(401, "Token has been revoked")
```

**Utilisation :**
- Lors de la vérification du JWT
- Middleware d'authentification

---

#### `delete_expired_tokens(db: Session, current_time: datetime) -> None`
Supprime les tokens révoqués expirés (nettoyage).

**Paramètres :**
- `db` (Session) : Session de base de données
- `current_time` (datetime) : Date/heure actuelle

**Retour :**
- `None`

**Exemple :**
```python
from datetime import datetime

# Supprimer les tokens révoqués depuis plus de 7 jours
delete_expired_tokens(db, datetime.now())
```

**Comportement :**
- Supprime les entrées de `revoked_tokens` plus anciennes que `current_time`
- Optimise la taille de la table
- À exécuter périodiquement (cron job)

---

### Module : `app/db/crud/crud_invite_token.py`

#### `create_invite_token(db: Session, email: str, expires_in_minutes: int = 1440) -> InviteToken`
Crée un token d'invitation pour un nouvel utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `email` (str) : Email de l'utilisateur à inviter
- `expires_in_minutes` (int) : Durée de validité (défaut: 1440 = 24h)

**Retour :**
- `InviteToken` : Token créé

**Exemple :**
```python
token = create_invite_token(db, "newuser@example.com", expires_in_minutes=2880)
# Envoyer un email avec le lien : /auth/signup?token={token.token}
```

**Comportement :**
- Génère un UUID unique
- Calcule la date d'expiration
- Sauvegarde en base
- Retourne le token

---

#### `get_invite_token(db: Session, token: str) -> InviteToken`
Récupère un token d'invitation.

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : UUID du token

**Retour :**
- `InviteToken` : Token trouvé

**Erreurs :**
- `HTTPException(404)` : Token introuvable
- `HTTPException(400)` : Token expiré ou déjà utilisé

---

#### `mark_token_used(db: Session, token: str) -> None`
Marque un token d'invitation comme utilisé.

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : UUID du token

**Retour :**
- `None`

**Exemple :**
```python
# Après inscription réussie
mark_token_used(db, invite_token)
```

---

### Module : `app/db/crud/crud_password_reset_token.py`

#### `create_reset_token(db: Session, user_id: int, expires_in_minutes: int = 15) -> PasswordResetToken`
Crée un token de réinitialisation de mot de passe.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur
- `expires_in_minutes` (int) : Durée de validité (défaut: 15 min)

**Retour :**
- `PasswordResetToken` : Token créé

**Exemple :**
```python
user = get_user_by_email(db, "user@example.com")
token = create_reset_token(db, user.id, expires_in_minutes=30)
# Envoyer un email avec le lien : /auth/reset-password?token={token.token}
```

---

#### `get_reset_token(db: Session, token: str) -> PasswordResetToken`
Récupère un token de reset.

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : UUID du token

**Retour :**
- `PasswordResetToken` : Token trouvé

**Erreurs :**
- `HTTPException(404)` : Token introuvable
- `HTTPException(400)` : Token expiré ou déjà utilisé

---

#### `mark_reset_token_used(db: Session, token: str) -> None`
Marque un token de reset comme utilisé.

**Paramètres :**
- `db` (Session) : Session de base de données
- `token` (str) : UUID du token

**Retour :**
- `None`

---

## 👥 Gestion des utilisateurs

### Module : `app/db/crud/crud_users.py`

#### `create_user(db: Session, user_data: dict) -> User`
Crée un nouvel utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_data` (dict) : Données de l'utilisateur
  - `email` (str) : Email unique
  - `password` (str) : Mot de passe (sera hashé)

**Retour :**
- `User` : Utilisateur créé

**Exemple :**
```python
new_user = create_user(db, {
    "email": "user@example.com",
    "password": "SecurePass123!"
})
```

**Comportement :**
1. Vérifie que l'email n'existe pas
2. Hash le mot de passe avec bcrypt
3. Crée l'utilisateur en base
4. Initialise les permissions par défaut
5. Retourne l'utilisateur créé

**Erreurs :**
- `HTTPException(409)` : Email déjà utilisé

---

#### `get_user_or_404(db: Session, user_id: int) -> User`
Récupère un utilisateur ou lève une erreur 404.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `User` : Utilisateur trouvé

**Exemple :**
```python
user = get_user_or_404(db, 5)
# Si user n'existe pas, HTTPException(404) est levée automatiquement
```

**Erreurs :**
- `HTTPException(404)` : Utilisateur introuvable ou supprimé

---

#### `get_user_or_404_with_permissions(db: Session, user_id: int) -> dict`
Récupère un utilisateur avec ses permissions.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `dict` : Utilisateur avec permissions
  ```python
  {
      "id": 1,
      "email": "user@example.com",
      "created_at": "...",
      "permissions": [
          {
              "permission_id": 1,
              "name": "create_show",
              "granted": true
          },
          ...
      ]
  }
  ```

**Exemple :**
```python
user_data = get_user_or_404_with_permissions(db, 5)
can_create = any(p["name"] == "create_show" and p["granted"] for p in user_data["permissions"])
```

---

#### `get_all_users(db: Session) -> List[User]`
Liste tous les utilisateurs (non supprimés).

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[User]` : Liste des utilisateurs

**Exemple :**
```python
users = get_all_users(db)
print(f"Nombre d'utilisateurs : {len(users)}")
```

**Comportement :**
- Filtre automatiquement `is_deleted = False`
- Retourne une liste vide si aucun utilisateur

---

#### `get_non_presenters(db: Session) -> List[User]`
Liste les utilisateurs qui ne sont pas présentateurs.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[User]` : Utilisateurs non-présentateurs

**Utilisation :**
- Pour affecter un présentateur à un show
- Pour filtrer les utilisateurs disponibles

---

#### `update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]`
Met à jour un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur
- `user_update` (UserUpdate) : Données à mettre à jour
  - `email` (str, optional) : Nouvel email
  - `password` (str, optional) : Nouveau mot de passe

**Retour :**
- `User | None` : Utilisateur mis à jour ou None

**Exemple :**
```python
from app.schemas.schema_user import UserUpdate

updated = update_user(db, 5, UserUpdate(email="newemail@example.com"))
if updated:
    print("Utilisateur mis à jour")
```

**Comportement :**
- Vérifie que l'utilisateur existe
- Si `password` fourni, le hash avant sauvegarde
- Met à jour `updated_at` automatiquement
- Retourne None si utilisateur introuvable

---

#### `delete_user(db: Session, user_id: int) -> bool`
Supprime un utilisateur (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `bool` : True si supprimé, False sinon

**Exemple :**
```python
if delete_user(db, 5):
    print("Utilisateur supprimé")
else:
    print("Utilisateur introuvable")
```

**Comportement :**
- Met `is_deleted = True`
- Ne supprime PAS physiquement
- Conserve les données pour audit

---

#### `get_user_logins(db: Session, user_id: int) -> List[LoginHistory]`
Récupère l'historique de connexion d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `List[LoginHistory]` : Historique des connexions

**Exemple :**
```python
logins = get_user_logins(db, 5)
for login in logins:
    print(f"Login : {login.login_time} - IP: {login.ip_address}")
```

---

#### `get_user_notifications(db: Session, user_id: int) -> List[Notification]`
Récupère les notifications d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `List[Notification]` : Notifications de l'utilisateur

---

#### `get_user_audit_logs(db: Session, user_id: int) -> List[AuditLog]`
Récupère les logs d'audit d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `List[AuditLog]` : Actions effectuées par l'utilisateur

---

## 📻 Shows et émissions

### Module : `app/db/crud/crud_show.py`

#### `create_show(db: Session, show: ShowCreate, user_id: int) -> Show`
Crée un nouveau show.

**Paramètres :**
- `db` (Session) : Session de base de données
- `show` (ShowCreate) : Données du show
  - `name` (str) : Nom du show
  - `description` (str) : Description
  - `presenter_ids` (List[int]) : IDs des présentateurs
- `user_id` (int) : ID du créateur

**Retour :**
- `Show` : Show créé avec présentateurs

**Exemple :**
```python
from app.schemas.schema_show import ShowCreate

new_show = create_show(db, ShowCreate(
    name="Morning Show",
    description="Émission matinale",
    presenter_ids=[1, 2]
), user_id=5)
```

**Comportement :**
1. Crée le show en base
2. Associe les présentateurs (table `show_presenters`)
3. Crée un log d'audit
4. Commit la transaction
5. Retourne le show avec relations chargées

---

#### `get_show(db: Session, show_id: int) -> Optional[Show]`
Récupère un show par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `show_id` (int) : ID du show

**Retour :**
- `Show | None` : Show trouvé ou None

**Exemple :**
```python
show = get_show(db, 1)
if show:
    print(f"Show : {show.name}")
    print(f"Présentateurs : {[p.name for p in show.presenters]}")
```

---

#### `get_shows(db: Session, skip: int = 0, limit: int = 100) -> List[Show]`
Liste tous les shows avec pagination.

**Paramètres :**
- `db` (Session) : Session de base de données
- `skip` (int) : Nombre à sauter (offset)
- `limit` (int) : Nombre max à retourner

**Retour :**
- `List[Show]` : Liste des shows

**Exemple :**
```python
# Page 1 (10 shows)
shows_p1 = get_shows(db, skip=0, limit=10)

# Page 2
shows_p2 = get_shows(db, skip=10, limit=10)
```

---

#### `update_show(db: Session, show_id: int, show_update: ShowUpdate) -> Optional[Show]`
Met à jour un show.

**Paramètres :**
- `db` (Session) : Session de base de données
- `show_id` (int) : ID du show
- `show_update` (ShowUpdate) : Données à mettre à jour
  - `name` (str, optional)
  - `description` (str, optional)
  - `presenter_ids` (List[int], optional)

**Retour :**
- `Show | None` : Show mis à jour

**Exemple :**
```python
updated = update_show(db, 1, ShowUpdate(
    name="Good Morning Show",
    presenter_ids=[1, 3]  # Remplace les présentateurs
))
```

**Comportement :**
- Met à jour les champs fournis uniquement
- Si `presenter_ids`, remplace tous les présentateurs
- Crée un log d'audit avec les changements
- Retourne None si show introuvable

---

#### `delete_show(db: Session, show_id: int) -> bool`
Supprime un show (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `show_id` (int) : ID du show

**Retour :**
- `bool` : True si supprimé

**Comportement :**
- Met `is_deleted = True`
- Crée un log d'audit
- Les émissions liées restent accessibles

---

### Module : `app/db/crud/crud_emission.py`

#### `create_emission(db: Session, emission_create: EmissionCreate) -> EmissionResponse`
Crée une nouvelle émission.

**Paramètres :**
- `db` (Session) : Session de base de données
- `emission_create` (EmissionCreate) : Données de l'émission
  - `title` (str) : Titre
  - `date` (date) : Date de diffusion
  - `show_id` (int) : ID du show parent
  - `user_id` (int) : ID du créateur

**Retour :**
- `EmissionResponse` : Émission créée

**Exemple :**
```python
from datetime import date

emission = create_emission(db, EmissionCreate(
    title="Morning Show - 11 Dec 2025",
    date=date(2025, 12, 11),
    show_id=1,
    user_id=5
))
```

---

#### `get_emissions(db: Session, skip: int = 0, limit: int = 10) -> List[EmissionResponse]`
Liste toutes les émissions avec pagination.

**Paramètres :**
- `db` (Session) : Session de base de données
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[EmissionResponse]` : Liste des émissions

---

#### `get_emission_by_id(db: Session, emission_id: int) -> EmissionResponse`
Récupère une émission par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `emission_id` (int) : ID de l'émission

**Retour :**
- `EmissionResponse` : Émission avec show et segments

**Erreurs :**
- `HTTPException(404)` : Émission introuvable

---

#### `update_emission(db: Session, emission_id: int, emission_update: EmissionCreate) -> EmissionResponse`
Met à jour une émission.

**Paramètres :**
- `db` (Session) : Session de base de données
- `emission_id` (int) : ID de l'émission
- `emission_update` (EmissionCreate) : Nouvelles données

**Retour :**
- `EmissionResponse` : Émission mise à jour

---

#### `delete_emission(db: Session, emission_id: int) -> bool`
Supprime une émission (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `emission_id` (int) : ID de l'émission

**Retour :**
- `bool` : True si supprimée

---

#### `soft_delete_emission(db: Session, emission_id: int) -> bool`
Alternative de soft delete pour émission.

**Paramètres :**
- `db` (Session) : Session de base de données
- `emission_id` (int) : ID de l'émission

**Retour :**
- `bool` : True si supprimée

---

## 🎤 Présentateurs et invités

### Module : `app/db/crud/crud_presenters.py`

#### `create_presenter(db: Session, presenter: PresenterCreate, user_id: int) -> Presenter`
Crée un nouveau présentateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `presenter` (PresenterCreate) : Données du présentateur
  - `name` (str) : Nom
  - `bio` (str, optional) : Biographie
- `user_id` (int) : ID du créateur

**Retour :**
- `Presenter` : Présentateur créé

**Exemple :**
```python
presenter = create_presenter(db, PresenterCreate(
    name="Jean Dupont",
    bio="Journaliste avec 10 ans d'expérience"
), user_id=5)
```

---

#### `get_presenter(db: Session, presenter_id: int) -> Optional[Presenter]`
Récupère un présentateur par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `presenter_id` (int) : ID du présentateur

**Retour :**
- `Presenter | None` : Présentateur trouvé

---

#### `get_presenters(db: Session, skip: int = 0, limit: int = 100) -> List[Presenter]`
Liste tous les présentateurs.

**Paramètres :**
- `db` (Session) : Session de base de données
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[Presenter]` : Liste des présentateurs

---

#### `update_presenter(db: Session, presenter_id: int, presenter_update: PresenterUpdate) -> Optional[Presenter]`
Met à jour un présentateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `presenter_id` (int) : ID du présentateur
- `presenter_update` (PresenterUpdate) : Nouvelles données

**Retour :**
- `Presenter | None` : Présentateur mis à jour

---

#### `delete_presenter(db: Session, presenter_id: int) -> bool`
Supprime un présentateur (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `presenter_id` (int) : ID du présentateur

**Retour :**
- `bool` : True si supprimé

---

### Module : `app/db/crud/crud_guests.py`

#### `create_guest(db: Session, guest: GuestCreate) -> GuestResponse`
Crée un nouvel invité.

**Paramètres :**
- `db` (Session) : Session de base de données
- `guest` (GuestCreate) : Données de l'invité
  - `name` (str) : Nom
  - `bio` (str, optional) : Biographie
  - `contact_info` (str, optional) : Contact

**Retour :**
- `GuestResponse` : Invité créé

**Exemple :**
```python
guest = create_guest(db, GuestCreate(
    name="Dr. Sophie Martin",
    bio="Experte en climatologie",
    contact_info="sophie.martin@example.com"
))
```

---

#### `get_guest_by_id(db: Session, guest_id: int) -> Optional[GuestResponse]`
Récupère un invité par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `guest_id` (int) : ID de l'invité

**Retour :**
- `GuestResponse | None` : Invité trouvé

---

#### `get_guests(db: Session, skip: int = 0, limit: int = 10) -> List[GuestResponse]`
Liste tous les invités.

**Paramètres :**
- `db` (Session) : Session de base de données
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[GuestResponse]` : Liste des invités

---

#### `update_guest(db: Session, guest_id: int, guest_update: GuestUpdate) -> GuestResponse`
Met à jour un invité.

**Paramètres :**
- `db` (Session) : Session de base de données
- `guest_id` (int) : ID de l'invité
- `guest_update` (GuestUpdate) : Nouvelles données

**Retour :**
- `GuestResponse` : Invité mis à jour

---

#### `delete_guest(db: Session, guest_id: int) -> bool`
Supprime un invité (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `guest_id` (int) : ID de l'invité

**Retour :**
- `bool` : True si supprimé

---

#### `search_guest(session: Session, query: str) -> Dict[str, Any]`
Recherche des invités par nom.

**Paramètres :**
- `session` (Session) : Session de base de données
- `query` (str) : Terme de recherche

**Retour :**
- `Dict[str, Any]` : Résultats de recherche
  ```python
  {
      "count": 2,
      "guests": [
          {"id": 1, "name": "Dr. Sophie Martin", ...},
          {"id": 5, "name": "Sophie Durand", ...}
      ]
  }
  ```

**Exemple :**
```python
results = search_guest(db, "Sophie")
print(f"Trouvé {results['count']} invité(s)")
```

---

## ⏱️ Segments

### Module : `app/db/crud/crud_segments.py`

#### `create_segment(db: Session, segment: SegmentCreate, user_id: int) -> Segment`
Crée un nouveau segment.

**Paramètres :**
- `db` (Session) : Session de base de données
- `segment` (SegmentCreate) : Données du segment
  - `title` (str) : Titre
  - `description` (str) : Description
  - `start_time` (time) : Heure de début
  - `end_time` (time) : Heure de fin
  - `emission_id` (int) : ID de l'émission
  - `guest_ids` (List[int]) : IDs des invités
- `user_id` (int) : ID du créateur

**Retour :**
- `Segment` : Segment créé avec invités

**Exemple :**
```python
from datetime import time

segment = create_segment(db, SegmentCreate(
    title="Actualités",
    description="Tour d'horizon de l'actualité",
    start_time=time(8, 0, 0),
    end_time=time(8, 15, 0),
    emission_id=101,
    guest_ids=[1, 2]
), user_id=5)
```

---

#### `get_segment(db: Session, segment_id: int) -> Optional[Segment]`
Récupère un segment par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `segment_id` (int) : ID du segment

**Retour :**
- `Segment | None` : Segment trouvé

---

#### `get_segments(db: Session, skip: int = 0, limit: int = 100) -> List[Segment]`
Liste tous les segments.

**Paramètres :**
- `db` (Session) : Session de base de données
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[Segment]` : Liste des segments

---

#### `update_segment(db: Session, segment_id: int, segment_update: SegmentUpdate) -> Optional[Segment]`
Met à jour un segment.

**Paramètres :**
- `db` (Session) : Session de base de données
- `segment_id` (int) : ID du segment
- `segment_update` (SegmentUpdate) : Nouvelles données

**Retour :**
- `Segment | None` : Segment mis à jour

---

#### `delete_segment(db: Session, segment_id: int) -> bool`
Supprime un segment (soft delete).

**Paramètres :**
- `db` (Session) : Session de base de données
- `segment_id` (int) : ID du segment

**Retour :**
- `bool` : True si supprimé

---

## 🔑 Permissions et rôles

### Module : `app/db/crud/crud_permissions.py`

#### `check_permission(user: User, action: str, db: Session) -> bool`
Vérifie si un utilisateur a une permission.

**Paramètres :**
- `user` (User) : Utilisateur à vérifier
- `action` (str) : Nom de la permission (ex: "create_show")
- `db` (Session) : Session de base de données

**Retour :**
- `bool` : True si l'utilisateur a la permission

**Exemple :**
```python
from app.utils import oauth2

@router.post("/shows")
def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    if not check_permission(current_user, "create_show", db):
        raise HTTPException(403, "Permission denied")
    # ...
```

---

#### `get_user_permissions(db: Session, user_id: int) -> Dict[str, Any]`
Récupère toutes les permissions d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `Dict[str, Any]` : Permissions de l'utilisateur
  ```python
  {
      "user_id": 5,
      "permissions": [
          {
              "permission_id": 1,
              "name": "create_show",
              "description": "Créer un show",
              "granted": True
          },
          ...
      ]
  }
  ```

**Exemple :**
```python
perms = get_user_permissions(db, 5)
can_create = any(p["name"] == "create_show" and p["granted"] for p in perms["permissions"])
```

---

#### `initialize_user_permissions(db: Session, user_id: int) -> None`
Initialise les permissions par défaut pour un nouvel utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur

**Retour :**
- `None`

**Comportement :**
- Récupère toutes les permissions disponibles
- Crée une `UserPermission` pour chaque permission
- Met `granted = False` par défaut
- Appelé automatiquement lors de la création d'un utilisateur

---

#### `update_user_permissions(db: Session, user_id: int, permissions: Dict[str, bool], user_connected_id: int) -> Dict[str, Any]`
Met à jour les permissions d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur à modifier
- `permissions` (Dict[str, bool]) : Permissions à mettre à jour
  ```python
  {
      "create_show": True,
      "delete_show": False,
      "create_user": True
  }
  ```
- `user_connected_id` (int) : ID de l'admin effectuant la modification

**Retour :**
- `Dict[str, Any]` : Résultat de l'opération

**Exemple :**
```python
result = update_user_permissions(
    db,
    user_id=5,
    permissions={
        "create_show": True,
        "update_show": True,
        "delete_show": False
    },
    user_connected_id=1  # Admin
)
```

---

#### `get_all_permissions(db: Session) -> List[Permission]`
Liste toutes les permissions disponibles.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[Permission]` : Liste des permissions

**Exemple :**
```python
permissions = get_all_permissions(db)
for perm in permissions:
    print(f"{perm.name}: {perm.description}")
```

---

#### `get_permission(id: int, db: Session) -> Permission`
Récupère une permission par ID.

**Paramètres :**
- `id` (int) : ID de la permission
- `db` (Session) : Session de base de données

**Retour :**
- `Permission` : Permission trouvée

**Erreurs :**
- `HTTPException(404)` : Permission introuvable

---

### Module : `app/db/crud/crud_roles.py`

#### `get_all_roles(db: Session) -> List[Role]`
Liste tous les rôles.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[Role]` : Liste des rôles

---

#### `get_role(id: int, db: Session) -> Role`
Récupère un rôle par ID.

**Paramètres :**
- `id` (int) : ID du rôle
- `db` (Session) : Session de base de données

**Retour :**
- `Role` : Rôle trouvé

---

#### `create_role(name: str, description: Optional[str], permissions: List[int], db: Session) -> Role`
Crée un nouveau rôle.

**Paramètres :**
- `name` (str) : Nom du rôle (ex: "editor", "admin")
- `description` (str, optional) : Description
- `permissions` (List[int]) : IDs des permissions
- `db` (Session) : Session de base de données

**Retour :**
- `Role` : Rôle créé

**Exemple :**
```python
editor_role = create_role(
    name="editor",
    description="Peut créer et modifier des shows",
    permissions=[1, 2, 3, 6, 7],  # IDs des permissions
    db=db
)
```

---

#### `update_role(id: int, name: Optional[str], description: Optional[str], permissions: Optional[List[int]], db: Session) -> Role`
Met à jour un rôle.

**Paramètres :**
- `id` (int) : ID du rôle
- `name` (str, optional) : Nouveau nom
- `description` (str, optional) : Nouvelle description
- `permissions` (List[int], optional) : Nouvelles permissions
- `db` (Session) : Session de base de données

**Retour :**
- `Role` : Rôle mis à jour

---

#### `delete_role(id: int, db: Session) -> None`
Supprime un rôle.

**Paramètres :**
- `id` (int) : ID du rôle
- `db` (Session) : Session de base de données

**Retour :**
- `None`

---

#### `get_role_permissions(id: int, db: Session) -> List[Permission]`
Récupère les permissions d'un rôle.

**Paramètres :**
- `id` (int) : ID du rôle
- `db` (Session) : Session de base de données

**Retour :**
- `List[Permission]` : Permissions du rôle

---

## 📝 Audit et logs

### Module : `app/db/crud/crud_audit_logs.py`

#### `create_audit_log(db: Session, action: str, user_id: Optional[int], details: Optional[str]) -> AuditLog`
Crée un log d'audit.

**Paramètres :**
- `db` (Session) : Session de base de données
- `action` (str) : Action effectuée (ex: "CREATE", "UPDATE", "DELETE")
- `user_id` (int, optional) : ID de l'utilisateur
- `details` (str, optional) : Détails supplémentaires (JSON)

**Retour :**
- `AuditLog` : Log créé

**Exemple :**
```python
import json

log = create_audit_log(
    db,
    action="UPDATE",
    user_id=5,
    details=json.dumps({
        "entity_type": "Show",
        "entity_id": 1,
        "changes": {
            "name": {"old": "Morning Show", "new": "Good Morning Show"}
        }
    })
)
```

**Utilisation :**
- Tracer toutes les modifications importantes
- Audit de sécurité
- Débogage

---

#### `get_all_audit_logs(db: Session) -> List[AuditLog]`
Liste tous les logs d'audit.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[AuditLog]` : Liste des logs

---

#### `get_audit_log(db: Session, id: int) -> AuditLog`
Récupère un log par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `id` (int) : ID du log

**Retour :**
- `AuditLog` : Log trouvé

---

#### `archive_audit_log(db: Session, id: int) -> Optional[ArchivedAuditLog]`
Archive un log d'audit.

**Paramètres :**
- `db` (Session) : Session de base de données
- `id` (int) : ID du log à archiver

**Retour :**
- `ArchivedAuditLog | None` : Log archivé

**Comportement :**
- Copie le log dans `archived_audit_logs`
- Supprime le log de `audit_logs`
- Utilisé pour alléger la table principale

---

#### `get_all_archived_audit_logs(db: Session) -> List[ArchivedAuditLog]`
Liste tous les logs archivés.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `List[ArchivedAuditLog]` : Liste des logs archivés

---

#### `get_archived_audit_log(db: Session, id: int) -> ArchivedAuditLog`
Récupère un log archivé par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `id` (int) : ID du log archivé

**Retour :**
- `ArchivedAuditLog` : Log trouvé

---

## 🔔 Notifications

### Module : `app/db/crud/crud_notifications.py`

#### `create_notification(db: Session, notification: NotificationCreate) -> Notification`
Crée une nouvelle notification.

**Paramètres :**
- `db` (Session) : Session de base de données
- `notification` (NotificationCreate) : Données de la notification
  - `user_id` (int) : ID de l'utilisateur destinataire
  - `message` (str) : Message de la notification
  - `read` (bool) : Lue ou non (défaut: False)

**Retour :**
- `Notification` : Notification créée

**Exemple :**
```python
notif = create_notification(db, NotificationCreate(
    user_id=5,
    message="Nouvelle émission ajoutée à votre show",
    read=False
))
```

---

#### `get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[Notification]`
Récupère les notifications d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[Notification]` : Notifications de l'utilisateur

**Exemple :**
```python
notifications = get_user_notifications(db, user_id=5, skip=0, limit=20)
unread_count = sum(1 for n in notifications if not n.read)
```

---

#### `update_notification(db: Session, notification_id: int, read: bool) -> Optional[Notification]`
Met à jour le statut de lecture d'une notification.

**Paramètres :**
- `db` (Session) : Session de base de données
- `notification_id` (int) : ID de la notification
- `read` (bool) : Nouvelle valeur (True = lue)

**Retour :**
- `Notification | None` : Notification mise à jour

**Exemple :**
```python
# Marquer comme lue
update_notification(db, notification_id=10, read=True)
```

---

#### `delete_notification(db: Session, notification_id: int) -> bool`
Supprime une notification.

**Paramètres :**
- `db` (Session) : Session de base de données
- `notification_id` (int) : ID de la notification

**Retour :**
- `bool` : True si supprimée

---

#### `get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]`
Récupère une notification par ID.

**Paramètres :**
- `db` (Session) : Session de base de données
- `notification_id` (int) : ID de la notification

**Retour :**
- `Notification | None` : Notification trouvée

---

## 🔍 Recherche

### Module : `app/db/crud/crud_searche_conducteur.py`

#### `search_shows(db: Session, keyword: str = None, status: str = None, date_from: date = None, date_to: date = None, presenter_ids: List[int] = None, guest_ids: List[int] = None, skip: int = 0, limit: int = 10) -> List[Show]`
Recherche avancée de shows avec filtres multiples.

**Paramètres :**
- `db` (Session) : Session de base de données
- `keyword` (str, optional) : Mot-clé (recherche dans nom/description)
- `status` (str, optional) : Statut du show
- `date_from` (date, optional) : Date de début
- `date_to` (date, optional) : Date de fin
- `presenter_ids` (List[int], optional) : IDs des présentateurs
- `guest_ids` (List[int], optional) : IDs des invités
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[Show]` : Shows correspondants

**Exemple :**
```python
from datetime import date

# Rechercher shows avec "morning" présentés par Jean (id=1)
shows = search_shows(
    db,
    keyword="morning",
    presenter_ids=[1],
    date_from=date(2025, 1, 1),
    date_to=date(2025, 12, 31),
    skip=0,
    limit=20
)
```

---

### Module : `app/db/crud/crud_search_user.py`

#### `search_users(db: Session, query: str) -> List[User]`
Recherche des utilisateurs par email.

**Paramètres :**
- `db` (Session) : Session de base de données
- `query` (str) : Terme de recherche

**Retour :**
- `List[User]` : Utilisateurs correspondants

**Exemple :**
```python
users = search_users(db, "john")
# Retourne tous les users avec "john" dans l'email
```

---

### Module : `app/db/crud/crud_search_presenter.py`

#### `search_presenters(db: Session, query: str) -> List[Presenter]`
Recherche des présentateurs par nom.

**Paramètres :**
- `db` (Session) : Session de base de données
- `query` (str) : Terme de recherche

**Retour :**
- `List[Presenter]` : Présentateurs correspondants

---

## 📊 Tableau de bord

### Module : `app/db/crud/crud_dashbord.py`

#### `get_dashboard(db: Session) -> Dict[str, Any]`
Récupère les statistiques du tableau de bord.

**Paramètres :**
- `db` (Session) : Session de base de données

**Retour :**
- `Dict[str, Any]` : Statistiques globales
  ```python
  {
      "total_shows": 15,
      "total_emissions": 342,
      "total_presenters": 8,
      "total_guests": 127,
      "total_users": 12,
      "recent_emissions": [
          {"id": 101, "title": "Morning Show - 11 Dec", ...},
          ...
      ],
      "recent_shows": [
          {"id": 1, "name": "Morning Show", ...},
          ...
      ]
  }
  ```

**Exemple :**
```python
dashboard = get_dashboard(db)
print(f"Total shows: {dashboard['total_shows']}")
print(f"Total émissions: {dashboard['total_emissions']}")
```

**Utilisation :**
- Page d'accueil de l'admin
- Vue d'ensemble des données
- Métriques de l'application

---

## 🛠️ Utilitaires

### Module : `app/utils/format_datetime.py`

#### `format_datetime(dt: datetime) -> str`
Formate une date/heure pour l'affichage.

**Paramètres :**
- `dt` (datetime) : Date/heure à formater

**Retour :**
- `str` : Date formatée

**Exemple :**
```python
from datetime import datetime
from app.utils.format_datetime import format_datetime

formatted = format_datetime(datetime.now())
# Retourne : "11 décembre 2025 14:30"
```

---

### Module : `app/utils/exceptions.py`

Contient les exceptions personnalisées de l'application.

#### `GuestNotFoundException`
Exception levée quand un invité n'est pas trouvé.

**Exemple :**
```python
from app.utils.exceptions import GuestNotFoundException

guest = db.query(Guest).get(guest_id)
if not guest:
    raise GuestNotFoundException(f"Guest {guest_id} not found")
```

---

## 📋 Historique de connexion

### Module : `app/db/crud/crud_login_history.py`

#### `create_login_history(db: Session, login: LoginHistoryCreate) -> LoginHistory`
Enregistre une connexion utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `login` (LoginHistoryCreate) : Données de connexion
  - `user_id` (int) : ID de l'utilisateur
  - `ip_address` (str) : Adresse IP
  - `user_agent` (str) : User agent du navigateur
  - `login_time` (datetime) : Heure de connexion

**Retour :**
- `LoginHistory` : Enregistrement créé

**Exemple :**
```python
from datetime import datetime

login_record = create_login_history(db, LoginHistoryCreate(
    user_id=5,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    login_time=datetime.now()
))
```

**Utilisation :**
- Traçabilité des connexions
- Sécurité (détection d'accès suspect)
- Statistiques d'utilisation

---

#### `get_user_login_history(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[LoginHistory]`
Récupère l'historique de connexion d'un utilisateur.

**Paramètres :**
- `db` (Session) : Session de base de données
- `user_id` (int) : ID de l'utilisateur
- `skip` (int) : Offset
- `limit` (int) : Limite

**Retour :**
- `List[LoginHistory]` : Historique des connexions

**Exemple :**
```python
history = get_user_login_history(db, user_id=5, limit=20)
for login in history:
    print(f"{login.login_time} - {login.ip_address}")
```

---

## 🔧 Vérification des permissions

### Module : `app/db/crud/crud_check_permission.py`

#### `check_permission(user: User, action: str, db: Session) -> bool`
Vérifie si un utilisateur a une permission spécifique.

**Paramètres :**
- `user` (User) : Utilisateur à vérifier
- `action` (str) : Nom de la permission
- `db` (Session) : Session de base de données

**Retour :**
- `bool` : True si autorisé

**Exemple :**
```python
if not check_permission(current_user, "delete_show", db):
    raise HTTPException(403, "You don't have permission to delete shows")
```

**Utilisation :**
- Protection des routes sensibles
- Vérification avant actions critiques
- Contrôle d'accès granulaire

---

## 📊 Résumé des modules

### Récapitulatif par catégorie

| Module | Nombre de fonctions | Usage principal |
|--------|---------------------|-----------------|
| `crud_users.py` | 15+ | Gestion des utilisateurs |
| `crud_show.py` | 5 | CRUD des shows |
| `crud_emission.py` | 6 | CRUD des émissions |
| `crud_presenters.py` | 5 | CRUD des présentateurs |
| `crud_guests.py` | 6 | CRUD des invités |
| `crud_segments.py` | 5 | CRUD des segments |
| `crud_permissions.py` | 10+ | Gestion des permissions |
| `crud_roles.py` | 7 | Gestion des rôles |
| `crud_auth.py` | 3 | Tokens JWT |
| `crud_invite_token.py` | 3 | Invitations |
| `crud_password_reset_token.py` | 3 | Reset password |
| `crud_audit_logs.py` | 6 | Logs d'audit |
| `crud_notifications.py` | 5 | Notifications |
| `crud_dashbord.py` | 1 | Statistiques |
| `crud_searche_conducteur.py` | 1 | Recherche avancée |
| `utils.py` | 2 | Hash passwords |
| **TOTAL** | **80+** | |

---

## 💡 Bonnes pratiques d'utilisation

### 1. Toujours utiliser get_db() en dépendance

```python
# ✅ Bon
@router.get("/")
def my_route(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return users

# ❌ Mauvais
@router.get("/")
def my_route():
    db = SessionLocal()  # Session non gérée
    users = get_all_users(db)
    return users
```

---

### 2. Vérifier les permissions systématiquement

```python
# ✅ Bon
@router.post("/shows")
def create_show(
    show: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    if not check_permission(current_user, "create_show", db):
        raise HTTPException(403, "Permission denied")
    return crud_show.create_show(db, show, current_user.id)
```

---

### 3. Logger les actions importantes

```python
# ✅ Bon
def delete_show(db: Session, show_id: int, user_id: int):
    show = get_show(db, show_id)
    if not show:
        return False
    
    # Soft delete
    show.is_deleted = True
    db.commit()
    
    # Log l'action
    create_audit_log(
        db,
        action="DELETE",
        user_id=user_id,
        details=json.dumps({
            "entity_type": "Show",
            "entity_id": show_id,
            "name": show.name
        })
    )
    return True
```

---

### 4. Utiliser les transactions pour opérations multiples

```python
# ✅ Bon
from sqlalchemy.exc import SQLAlchemyError

def create_show_with_emissions(db: Session, show_data: dict):
    try:
        # Créer le show
        show = Show(**show_data)
        db.add(show)
        db.flush()  # Obtenir l'ID sans commit
        
        # Créer les émissions
        for emission_data in show_data["emissions"]:
            emission = Emission(**emission_data, show_id=show.id)
            db.add(emission)
        
        db.commit()
        return show
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
```

---

## 📖 Conventions de nommage

### Fonctions CRUD

- `create_*` : Créer une nouvelle entité
- `get_*` : Récupérer une ou plusieurs entités
- `update_*` : Mettre à jour une entité
- `delete_*` : Supprimer (soft delete) une entité
- `search_*` : Rechercher avec critères
- `check_*` : Vérifier une condition

### Exemples

```python
create_user(db, user_data)          # Créer
get_user(db, user_id)               # Récupérer un
get_all_users(db)                   # Récupérer tous
get_users(db, skip, limit)          # Récupérer avec pagination
update_user(db, user_id, data)      # Mettre à jour
delete_user(db, user_id)            # Supprimer
search_users(db, query)             # Rechercher
check_permission(user, action, db)  # Vérifier
```

---

**Dernière mise à jour :** 11 décembre 2025

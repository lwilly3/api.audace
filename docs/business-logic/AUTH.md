# 🔑 Module AUTH - Authentification et Tokens

Documentation de la gestion des tokens JWT, tokens de réinitialisation de mot de passe et tokens d'invitation.

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
- Révocation de tokens JWT (blacklist)
- Nettoyage des tokens expirés
- Gestion des tokens de réinitialisation de mot de passe
- Gestion des tokens d'invitation (invite users)
- Vérification de la validité des tokens

### Fichiers sources
- `app/db/crud/crud_auth.py` : Gestion tokens révoqués
- `core/auth/oauth2.py` : Génération et validation JWT
- `routeur/auth.py` : Routes d'authentification

### Dépendances
```python
# Modèles
from app.models import RevokedToken, PasswordResetToken, InviteToken, User

# Libraries
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
```

---

## 🏗️ Architecture

### Modèle RevokedToken (Blacklist JWT)

```python
RevokedToken:
    id: int (PK)
    token: str (UNIQUE, TEXT)  # Token JWT complet
    revoked_at: datetime (default: now())
    
    # Index pour performances
    CREATE INDEX idx_revoked_token ON revoked_tokens(token);
```

**Usage :** Lors de la déconnexion ou compromission, ajouter le token à cette table.

### Modèle PasswordResetToken

```python
PasswordResetToken:
    id: int (PK)
    user_id: int (FK → User)
    token: str (UNIQUE, generated)
    expires_at: datetime (24h par défaut)
    used: bool (default: False)
    created_at: datetime
    
    # Relation
    user: User (Many-to-One)
```

**Usage :** Réinitialisation de mot de passe via email.

### Modèle InviteToken

```python
InviteToken:
    id: int (PK)
    email: str (NOT NULL)
    token: str (UNIQUE, generated)
    role_id: int (FK → Role, optional)
    expires_at: datetime (7 jours par défaut)
    used: bool (default: False)
    created_by: int (FK → User)
    created_at: datetime
    
    # Relations
    creator: User (Many-to-One)
    role: Role (Many-to-One)
```

**Usage :** Invitation de nouveaux utilisateurs par les admins.

### Flux d'authentification

```
1. Login
   ├─→ Vérifier credentials (username/password)
   ├─→ Vérifier token non révoqué
   └─→ Générer JWT (access_token)

2. Requêtes authentifiées
   ├─→ Extraire token du header Authorization
   ├─→ Décoder JWT et extraire user_id
   ├─→ Vérifier token non révoqué (is_token_revoked)
   └─→ Charger utilisateur et permissions

3. Logout
   ├─→ Ajouter token à RevokedToken
   └─→ Token désormais invalide

4. Reset Password
   ├─→ Générer PasswordResetToken
   ├─→ Envoyer email avec lien
   ├─→ Vérifier token valide et non utilisé
   └─→ Réinitialiser mot de passe + marquer used=True
```

---

## 🔧 Fonctions métier

### 1. revoke_token()

**Signature :**
```python
def revoke_token(db: Session, token: str) -> RevokedToken
```

**Description :**
Ajoute un token JWT à la blacklist pour l'invalider immédiatement.

**Logique métier :**
```python
def revoke_token(db: Session, token: str) -> RevokedToken:
    """
    Révoque un token en l'ajoutant à la blacklist.
    
    Args:
        db: Session SQLAlchemy
        token: Token JWT complet (pas juste le payload)
    
    Returns:
        RevokedToken: Objet créé
    """
    # Vérifier que le token n'est pas déjà révoqué
    existing = db.query(RevokedToken).filter(RevokedToken.token == token).first()
    if existing:
        return existing  # Déjà révoqué
    
    # Créer l'entrée de révocation
    revoked_token = RevokedToken(
        token=token,
        revoked_at=datetime.utcnow()
    )
    
    db.add(revoked_token)
    db.commit()
    db.refresh(revoked_token)
    
    return revoked_token
```

**Cas d'usage :**
- Déconnexion utilisateur (logout)
- Changement de mot de passe (invalider tous les anciens tokens)
- Compromission de compte

**Exemple - Route logout :**
```python
@router.post("/auth/logout")
def logout(
    token: str = Depends(oauth2.oauth2_scheme),  # Extraire token du header
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Révoquer le token
    crud_auth.revoke_token(db, token)
    
    return {"message": "Successfully logged out"}
```

---

### 2. is_token_revoked()

**Signature :**
```python
def is_token_revoked(db: Session, token: str) -> bool
```

**Description :**
Vérifie si un token est dans la blacklist.

**Logique métier :**
```python
def is_token_revoked(db: Session, token: str) -> bool:
    """
    Vérifie si un token a été révoqué.
    
    Args:
        db: Session SQLAlchemy
        token: Token JWT à vérifier
    
    Returns:
        bool: True si révoqué, False sinon
    """
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first() is not None
```

**Intégration dans oauth2.get_current_user() :**
```python
# core/auth/oauth2.py

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Récupère l'utilisateur actuel depuis le JWT"""
    
    # Vérifier si le token est révoqué
    if is_token_revoked(db, token):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Décoder le JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
    
    except JWTError:
        raise credentials_exception
    
    # Charger l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user
```

---

### 3. delete_expired_tokens()

**Signature :**
```python
def delete_expired_tokens(db: Session, current_time: datetime) -> None
```

**Description :**
Supprime les tokens révoqués qui sont expirés. **Fonction de maintenance à exécuter périodiquement.**

**Logique métier :**
```python
def delete_expired_tokens(db: Session, current_time: datetime) -> None:
    """
    Nettoie les tokens révoqués expirés.
    
    Args:
        db: Session SQLAlchemy
        current_time: Date actuelle pour comparaison
    
    Note:
        À appeler périodiquement (ex: tâche cron quotidienne)
    """
    revoked_tokens = db.query(RevokedToken).all()
    deleted_count = 0
    
    for revoked_token in revoked_tokens:
        try:
            # Décoder le token pour vérifier sa date d'expiration
            payload = jwt.decode(
                revoked_token.token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
            
            # Si le token est expiré OU révoqué depuis longtemps
            if exp < current_time or revoked_token.revoked_at < current_time:
                db.delete(revoked_token)
                deleted_count += 1
        
        except JWTError:
            # Token invalide ou corrompu, le supprimer
            db.delete(revoked_token)
            deleted_count += 1
    
    db.commit()
    
    print(f"Deleted {deleted_count} expired revoked tokens")
```

**Tâche cron recommandée :**
```python
# scripts/cleanup_tokens.py

from app.db.database import SessionLocal
from app.db.crud import crud_auth
from datetime import datetime

def cleanup_tokens():
    """Script de nettoyage à exécuter quotidiennement"""
    db = SessionLocal()
    try:
        crud_auth.delete_expired_tokens(db, datetime.utcnow())
        print("Token cleanup completed successfully")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_tokens()
```

**Configuration cron (Linux/Mac) :**
```bash
# Exécuter tous les jours à 3h du matin
0 3 * * * /usr/bin/python3 /path/to/scripts/cleanup_tokens.py
```

---

### 4. create_password_reset_token()

**Signature :**
```python
def create_password_reset_token(db: Session, user_id: int) -> PasswordResetToken
```

**Description :**
Génère un token de réinitialisation de mot de passe.

**Logique métier :**
```python
import secrets

def create_password_reset_token(db: Session, user_id: int):
    # Invalider tous les tokens précédents
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False
    ).update({"used": True})
    
    # Générer un nouveau token sécurisé
    token = secrets.token_urlsafe(32)
    
    # Créer l'entrée
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),  # 24h de validité
        used=False
    )
    
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    
    return reset_token
```

**Route de demande :**
```python
from app.utils.email import send_reset_email

@router.post("/auth/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    # Trouver l'utilisateur
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Ne pas révéler si l'email existe (sécurité)
        return {"message": "If email exists, reset link sent"}
    
    # Créer le token
    reset_token = crud_auth.create_password_reset_token(db, user.id)
    
    # Envoyer l'email
    reset_url = f"https://yourapp.com/reset-password?token={reset_token.token}"
    send_reset_email(user.email, reset_url)
    
    return {"message": "If email exists, reset link sent"}
```

---

### 5. verify_reset_token()

**Signature :**
```python
def verify_reset_token(db: Session, token: str) -> PasswordResetToken
```

**Description :**
Vérifie la validité d'un token de réinitialisation.

**Logique métier :**
```python
def verify_reset_token(db: Session, token: str):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if not reset_token:
        raise HTTPException(404, "Invalid reset token")
    
    # Vérifier qu'il n'est pas déjà utilisé
    if reset_token.used:
        raise HTTPException(400, "Reset token already used")
    
    # Vérifier qu'il n'est pas expiré
    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(400, "Reset token expired")
    
    return reset_token
```

**Route de réinitialisation :**
```python
@router.post("/auth/reset-password")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    # Vérifier le token
    reset_token = crud_auth.verify_reset_token(db, token)
    
    # Réinitialiser le mot de passe
    user = reset_token.user
    user.hashed_password = pwd_context.hash(new_password)
    
    # Marquer le token comme utilisé
    reset_token.used = True
    
    # Révoquer tous les tokens JWT existants de cet utilisateur
    # (force re-login après changement de mot de passe)
    
    db.commit()
    
    return {"message": "Password successfully reset"}
```

---

### 6. create_invite_token()

**Signature :**
```python
def create_invite_token(
    db: Session,
    email: str,
    role_id: Optional[int],
    created_by: int
) -> InviteToken
```

**Description :**
Crée un token d'invitation pour un nouvel utilisateur.

**Logique métier :**
```python
def create_invite_token(
    db: Session,
    email: str,
    role_id: Optional[int],
    created_by: int
):
    # Vérifier que l'email n'existe pas déjà
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(400, "User with this email already exists")
    
    # Vérifier qu'il n'y a pas déjà une invitation active
    existing_invite = db.query(InviteToken).filter(
        InviteToken.email == email,
        InviteToken.used == False,
        InviteToken.expires_at > datetime.utcnow()
    ).first()
    
    if existing_invite:
        raise HTTPException(400, "Active invitation already exists for this email")
    
    # Générer le token
    token = secrets.token_urlsafe(32)
    
    # Créer l'invitation
    invite = InviteToken(
        email=email,
        token=token,
        role_id=role_id,
        expires_at=datetime.utcnow() + timedelta(days=7),  # 7 jours
        used=False,
        created_by=created_by
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    return invite
```

**Route d'invitation :**
```python
@router.post("/admin/invite-user")
def invite_user(
    email: str,
    role_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin)
):
    # Créer l'invitation
    invite = crud_auth.create_invite_token(db, email, role_id, current_user.id)
    
    # Envoyer l'email
    invite_url = f"https://yourapp.com/accept-invite?token={invite.token}"
    send_invite_email(email, invite_url)
    
    return {
        "message": "Invitation sent",
        "email": email,
        "expires_at": invite.expires_at
    }
```

---

## 📏 Règles métier

### 1. Tokens JWT
- Durée de vie : 1 heure (configurable)
- Révocation : blacklist obligatoire
- Nettoyage automatique des tokens expirés

### 2. Tokens de réinitialisation
- Durée de validité : 24 heures
- Un seul token actif par utilisateur
- Usage unique (used = True après utilisation)

### 3. Tokens d'invitation
- Durée de validité : 7 jours
- Email unique (pas de double invitation)
- Rôle assigné automatiquement à l'acceptation

---

## 🔗 Relations

```
User ←──── PasswordResetToken (Many-to-One)
User ←──── InviteToken (created_by, Many-to-One)
RevokedToken (standalone, pas de FK)
```

---

## ⚠️ Contraintes

### Sécurité
- Tokens générés avec `secrets.token_urlsafe()` (cryptographiquement sûrs)
- Jamais exposer les tokens en clair dans les logs
- Toujours utiliser HTTPS pour les échanges

### Performances
- Index sur `revoked_tokens.token` (lookup rapide)
- Nettoyage périodique obligatoire (croissance infinie sinon)

---

## 💡 Exemples d'utilisation

### Workflow complet de reset password

```python
# 1. Demande de réinitialisation
POST /auth/forgot-password
{"email": "user@example.com"}

# 2. Utilisateur reçoit email avec token

# 3. Vérifier le token (optionnel)
GET /auth/verify-reset-token?token=abc123

# 4. Réinitialiser le mot de passe
POST /auth/reset-password
{
  "token": "abc123",
  "new_password": "newSecurePassword123"
}
```

---

**Navigation :**
- [← PERMISSIONS.md](PERMISSIONS.md)
- [→ GUESTS.md](GUESTS.md)
- [↑ Retour à l'index](README.md)

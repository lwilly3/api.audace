# Module Citations - Permissions

## Vue d'ensemble

Le module Citations permet de capturer, gérer et publier des citations depuis les émissions radio en direct. Il s'intègre avec Firebase et offre des fonctionnalités de transcription en temps réel.

## Nouvelles Permissions

8 nouvelles permissions ont été ajoutées au système :

| Permission | Description | Usage |
|------------|-------------|-------|
| `quotes_view` | Visualiser les citations | Liste, détails, recherche |
| `quotes_create` | Créer de nouvelles citations | Formulaire création manuelle ou depuis stream |
| `quotes_edit` | Modifier les citations existantes | Édition contenu, métadonnées, tags |
| `quotes_delete` | Supprimer des citations | Suppression définitive (attention aux cascades) |
| `quotes_publish` | Publier sur réseaux sociaux | Génération contenu, publication Facebook/Twitter/Instagram |
| `stream_transcription_view` | Voir les transcriptions en direct | Accès au composant de transcription live |
| `stream_transcription_create` | Démarrer une transcription | Bouton "Transcrire le stream" |
| `quotes_capture_live` | Capturer depuis transcription live | Bouton capture pendant transcription active |

## Matrice des Permissions par Rôle

| Rôle | quotes_view | quotes_create | quotes_edit | quotes_delete | quotes_publish | stream_transcription_view | stream_transcription_create | quotes_capture_live |
|------|-------------|---------------|-------------|---------------|----------------|---------------------------|----------------------------|---------------------|
| **Admin** | ✅ | ✅ | ✅ Toutes | ✅ Toutes | ✅ | ✅ | ✅ | ✅ |
| **Éditeur** | ✅ | ✅ | ✅ Siennes* | ✅ Siennes* | ✅ | ✅ | ✅ | ✅ |
| **Animateur** | ✅ | ✅ | ✅ Siennes* | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Community Manager** | ✅ | ✅ | ✅ Toutes | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Invité** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

*Note : Les restrictions "Siennes" signifient que l'utilisateur ne peut modifier/supprimer que les citations qu'il a créées. Cette logique doit être implémentée dans le code métier en vérifiant le `created_by`.

## Installation

### 1. Appliquer la Migration

Exécutez la migration Alembic pour ajouter les nouvelles colonnes à la base de données :

```bash
cd /Users/happi/App/API/FASTAPI
alembic upgrade head
```

### 2. Initialiser les Permissions

Appliquez les permissions par défaut à tous les utilisateurs existants selon leur rôle :

```bash
python scripts/init_quotes_permissions.py
```

Ce script :
- Parcourt tous les rôles définis (Admin, Éditeur, Animateur, Community Manager, Invité)
- Applique la matrice de permissions à chaque utilisateur selon son rôle
- Affiche un résumé des permissions appliquées

### 3. Vérification

Vous pouvez vérifier que les permissions ont été correctement appliquées en consultant la table `user_permissions` :

```sql
SELECT 
    u.username,
    r.name as role,
    p.quotes_view,
    p.quotes_create,
    p.quotes_edit,
    p.quotes_delete,
    p.quotes_publish,
    p.stream_transcription_view,
    p.stream_transcription_create,
    p.quotes_capture_live
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN user_permissions p ON u.id = p.user_id
WHERE u.is_deleted = false;
```

## Utilisation dans le Code

### Vérification des Permissions

```python
from app.models.model_user_permissions import UserPermissions

def can_user_view_quotes(user_id: int, db: Session) -> bool:
    """Vérifie si l'utilisateur peut voir les citations."""
    permissions = db.query(UserPermissions).filter(
        UserPermissions.user_id == user_id
    ).first()
    return permissions.quotes_view if permissions else False

def can_user_edit_quote(user_id: int, quote_created_by: int, db: Session) -> bool:
    """
    Vérifie si l'utilisateur peut éditer une citation.
    
    Pour Éditeur et Animateur, vérifie aussi que l'utilisateur
    est le créateur de la citation.
    """
    permissions = db.query(UserPermissions).filter(
        UserPermissions.user_id == user_id
    ).first()
    
    if not permissions or not permissions.quotes_edit:
        return False
    
    # Admin et Community Manager peuvent éditer toutes les citations
    user_roles = db.query(User).filter(User.id == user_id).first().roles
    role_names = [role.name for role in user_roles]
    
    if "Admin" in role_names or "Community Manager" in role_names:
        return True
    
    # Éditeur et Animateur ne peuvent éditer que leurs propres citations
    return user_id == quote_created_by
```

### Décorateur de Route (exemple)

```python
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission_name: str):
    """
    Décorateur pour vérifier les permissions sur une route.
    
    Usage:
        @router.get("/quotes")
        @require_permission("quotes_view")
        async def get_quotes(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), 
                         db: Session = Depends(get_db), **kwargs):
            permissions = db.query(UserPermissions).filter(
                UserPermissions.user_id == current_user.id
            ).first()
            
            if not permissions or not getattr(permissions, permission_name, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' requise"
                )
            
            return await func(*args, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator
```

## Gestion des Nouveaux Utilisateurs

Lorsqu'un nouvel utilisateur est créé, ses permissions Citations doivent être initialisées automatiquement :

```python
from app.db.init_quotes_permissions import apply_quotes_permissions_to_user

# Dans votre fonction de création d'utilisateur
def create_user(db: Session, user_data: UserCreate):
    # ... création de l'utilisateur ...
    
    # Initialiser les permissions standard
    initialize_user_permissions(db, new_user.id)
    
    # Appliquer les permissions Citations selon le rôle
    if new_user.roles:
        role_name = new_user.roles[0].name  # Premier rôle
        apply_quotes_permissions_to_user(db, new_user.id, role_name)
    
    return new_user
```

## Changement de Rôle

Lors du changement de rôle d'un utilisateur, mettez à jour ses permissions Citations :

```python
from app.db.init_quotes_permissions import apply_quotes_permissions_to_user

def update_user_role(db: Session, user_id: int, new_role_name: str):
    # ... mise à jour du rôle ...
    
    # Appliquer les nouvelles permissions Citations
    apply_quotes_permissions_to_user(db, user_id, new_role_name)
    
    db.commit()
```

## Sécurité et Bonnes Pratiques

### 1. Validation Côté Backend

Toujours valider les permissions côté backend, même si le frontend les cache :

```python
# ❌ Mauvais
@router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: int):
    # Pas de vérification de permission
    db.delete(quote)
    return {"message": "Deleted"}

# ✅ Bon
@router.delete("/quotes/{quote_id}")
@require_permission("quotes_delete")
async def delete_quote(quote_id: int, current_user: User = Depends(get_current_user)):
    # Vérification supplémentaire pour Éditeur/Animateur
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not can_user_delete_quote(current_user.id, quote.created_by, db):
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    db.delete(quote)
    return {"message": "Deleted"}
```

### 2. Audit des Actions

Loguez toutes les actions sensibles :

```python
from app.models.model_audit_log import AuditLog

def delete_quote(quote_id: int, user_id: int, db: Session):
    # ... suppression ...
    
    # Logger l'action
    audit_log = AuditLog(
        user_id=user_id,
        action="quote_delete",
        resource="quotes",
        resource_id=quote_id,
        details={"quote_title": quote.title}
    )
    db.add(audit_log)
    db.commit()
```

### 3. Gestion des Restrictions "Siennes"

Créez des fonctions utilitaires pour la logique de propriété :

```python
def is_owner_or_admin(user_id: int, resource_created_by: int, db: Session) -> bool:
    """Vérifie si l'utilisateur est propriétaire ou admin."""
    user = db.query(User).filter(User.id == user_id).first()
    role_names = [role.name for role in user.roles]
    
    return user_id == resource_created_by or "Admin" in role_names
```

## Fichiers Modifiés

Les fichiers suivants ont été créés/modifiés :

1. **Migration** : `alembic/versions/75574b1232db_add_quotes_permissions.py`
2. **Modèle** : `app/models/model_user_permissions.py`
3. **Initialisation Admin** : `app/db/init_admin.py`
4. **Module d'initialisation** : `app/db/init_quotes_permissions.py`
5. **Script d'initialisation** : `scripts/init_quotes_permissions.py`
6. **Documentation** : `QUOTES_PERMISSIONS.md`

## Support

Pour toute question ou problème concernant les permissions du module Citations, consultez :

- La matrice des permissions ci-dessus
- Les logs lors de l'exécution du script d'initialisation
- La table `user_permissions` dans la base de données

## Notes Importantes

⚠️ **Restrictions "Siennes"** : Les permissions `quotes_edit` et `quotes_delete` pour les rôles Éditeur et Animateur permettent l'action, mais la logique métier doit vérifier que l'utilisateur est bien le créateur de la ressource (`created_by === current_user.id`).

⚠️ **Intégration Firebase** : Ces permissions sont conçues pour être utilisées avec le module frontend Firebase. Assurez-vous que le frontend respecte également ces permissions dans l'interface utilisateur.

⚠️ **Sécurité** : Ne jamais se fier uniquement aux vérifications côté frontend. Toujours valider les permissions côté backend.

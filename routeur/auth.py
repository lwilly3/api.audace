from fastapi import HTTPException, Response, Request, status, Depends, APIRouter, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
# import app.database as database, app.schemas as schemas, app.table_models as table_models, app.utils as utils, app.oauth2 as oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from app.models import table_models
from app.models import model_user
from core.auth import oauth2
from app.db import database
from app.db.database import get_db  # Cette fonction obtient une session de base de données

from app.schemas.schema_users import UserInDB
from app.utils import utils
from app.db.crud.crud_permissions import get_user_permissions
from app.db.crud.crud_auth import revoke_token
from pydantic import BaseModel, EmailStr
from app.db.crud.crud_users import create_user
from routeur.users_route import assign_default_role_to_user
from app.schemas.schema_invite import InviteRequest, InviteResponse, ValidateInviteResponse, SignupWithInviteRequest, InviteTokenListItem
from app.db.crud.crud_invite_token import create_invite_token, get_invite_token, mark_token_used, get_all_invite_tokens
from app.models.model_user_permissions import UserPermissions
from datetime import datetime
from pydantic import BaseModel, EmailStr
from core.auth.oauth2 import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from core.auth.oauth2 import create_2fa_temp_token
from app.db.crud.crud_password_reset_token import create_reset_token, get_reset_token, mark_reset_token_used
from app.db.crud.crud_audit_logs import log_action
from app.config.config import settings
from app.db.crud.crud_2fa import verify_trusted_device, create_trusted_device, get_trusted_devices, revoke_trusted_device, revoke_trusted_devices

# pour la creation du token, intallation du package  pip install python-jose[cryptography]  7h01
# 6h05 installation des librairie pour hacher le pass pip install passlib[bcrypt]

router=APIRouter(
    prefix='/auth',
    tags=['Authentication']
)

# response_model=schemas.Token
@router.post('/login')
# 7h10
# def login(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
# sur la solution au on accede par user_credentials.email ..  pour la deuxieme solution il retourne un dict avec username et password
# la cle du dict username retourner peux soscker nimporte quoi email, id... en fonction de cequi a ete envoye par lutilisateur
# les info ne seront plus en voye en json par le body clien mais en form-date 7h12
def login(request: Request, user_credentials_receved: OAuth2PasswordRequestForm=Depends(), db: Session = Depends(database.get_db)):
# username contien le mail
   user_to_log_on_db= db.query(model_user.User).filter(model_user.User.email== user_credentials_receved.username).first() 

   if not user_to_log_on_db:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"authentification invalide")
   
#    virification si le pass hacher et sauver en base de donnee est similaire a la version hash de celui fourni par lutilisateur
   # Vérification du mot de passe avec fallback si le hash n'est pas au format bcrypt
   stored_pw = user_to_log_on_db.password or ""
   # Si le mot de passe en DB ne commence pas par prefixe bcrypt, comparer en clair
   if not stored_pw.startswith("$2"):
       valid = (user_credentials_receved.password == stored_pw)
   else:
       from passlib.exc import UnknownHashError
       try:
           valid = utils.verify(user_credentials_receved.password, stored_pw)
       except UnknownHashError:
           valid = False
   if not valid:
       raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="authentification invalide")

   # Verifier si le 2FA est active
   if user_to_log_on_db.two_factor_enabled:
       # Verifier si un appareil de confiance est presente
       device_token = request.headers.get("X-Trusted-Device")
       if device_token and verify_trusted_device(db, user_to_log_on_db.id, device_token):
           # Appareil de confiance valide → bypass 2FA
           log_action(db, user_to_log_on_db.id, "login_trusted_device", "users", user_to_log_on_db.id)
       else:
           # Pas de device token ou invalide → demander le 2FA
           temp_token = create_2fa_temp_token(user_to_log_on_db.id)
           log_action(db, user_to_log_on_db.id, "login_2fa_required", "users", user_to_log_on_db.id)
           return {
               "requires_2fa": True,
               "temp_token": temp_token,
               "token_type": "bearer",
           }


# creation du token
#    le data contien ce que je veux inclure dans le  payloard
#    le token peut etre visualiser dans https://jwt.io/  9h09
   access_token= oauth2.create_acces_token(data={'user_id':user_to_log_on_db.id})

   permissions= get_user_permissions(db, user_to_log_on_db.id)
   log_action(db, user_to_log_on_db.id, "login", "users", user_to_log_on_db.id)

   response_data = {
       "access_token": access_token,
       "token_type": "bearer",
       "user_id": user_to_log_on_db.id,
       "username": user_to_log_on_db.username,
       "email": user_to_log_on_db.email,
       "family_name": user_to_log_on_db.family_name,
       "name": user_to_log_on_db.name,
       "phone_number": user_to_log_on_db.phone_number,
       "profilePicture": user_to_log_on_db.profilePicture,
       "permissions": permissions,
   }

   # Si l'utilisateur souhaite enregistrer cet appareil de confiance
   remember_device = request.headers.get("X-Remember-Device")
   if remember_device and remember_device.lower() == "true":
       user_agent = request.headers.get("User-Agent", "Unknown")
       device_token = create_trusted_device(db, user_to_log_on_db.id, user_agent)
       response_data["trusted_device_token"] = device_token
       log_action(db, user_to_log_on_db.id, "register_trusted_device", "users", user_to_log_on_db.id)

   return response_data



# Endpoint pour déconnecter un utilisateur
@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(token: str = Depends(oauth2.oauth2_scheme), db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    # Ajoute le token à la liste noire pour l'invalider
    revoke_token(db, token)
    log_action(db, current_user.id, "logout", "users", current_user.id)

    # Retourne une réponse 204 (No Content) pour indiquer que la déconnexion a réussi
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/refresh')
def refresh_token(request: Request, token: str = Depends(oauth2.oauth2_scheme), db: Session = Depends(get_db)):
    """Renouvelle un token d'acces. Accepte les tokens valides ou recemment expires (fenetre de grace).
    Si un appareil de confiance est presente via X-Trusted-Device, la fenetre de grace est etendue."""
    # Verifier si un appareil de confiance est presente pour etendre la grace
    device_token = request.headers.get("X-Trusted-Device")
    grace_minutes = None  # default (5 min)

    if device_token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM, options={"verify_exp": False})
            temp_user_id = payload.get("user_id")
            if temp_user_id and verify_trusted_device(db, temp_user_id, device_token):
                grace_minutes = settings.TRUSTED_DEVICE_REFRESH_GRACE_MINUTES
        except JWTError:
            pass  # fallback to default grace

    user_id = oauth2.decode_token_allow_expired(token, db, grace_minutes=grace_minutes)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user = db.query(model_user.User).filter(model_user.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    # Revoquer l'ancien token
    revoke_token(db, token)

    # Creer un nouveau token
    new_access_token = oauth2.create_acces_token(data={'user_id': user.id})
    permissions = get_user_permissions(db, user.id)
    log_action(db, user.id, "token_refresh", "auth", user.id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "family_name": user.family_name,
        "name": user.name,
        "phone_number": user.phone_number,
        "profilePicture": user.profilePicture,
        "permissions": permissions,
    }

# Gestion des appareils de confiance
@router.get('/devices')
def list_devices(db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    """Liste les appareils de confiance de l'utilisateur connecte."""
    return get_trusted_devices(db, current_user.id)

@router.delete('/devices/{device_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_device(device_id: int, db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    """Revoque un appareil de confiance specifique."""
    revoke_trusted_device(db, current_user.id, device_id)
    log_action(db, current_user.id, "revoke_trusted_device", "users", current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete('/devices', status_code=status.HTTP_204_NO_CONTENT)
def remove_all_devices(db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    """Revoque tous les appareils de confiance de l'utilisateur."""
    revoke_trusted_devices(db, current_user.id)
    log_action(db, current_user.id, "revoke_all_trusted_devices", "users", current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

@router.post('/signup', status_code=status.HTTP_201_CREATED, response_model=UserInDB)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Créer un utilisateur minimal avec email comme username
    # Hasher le mot de passe avant stockage
    hashed_pw = utils.hash(request.password)
    user_data = {
        'username': request.email,
        'name': '',
        'family_name': '',
        'email': request.email,
        'password': hashed_pw,
        'phone_number': ''
    }
    new_user = create_user(db, user_data)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User creation failed")
    # Correction : assigner le rôle public et initialiser les permissions
    assign_default_role_to_user(new_user.id, db)
    from app.db.crud.crud_permissions import initialize_user_permissions
    initialize_user_permissions(db, new_user.id)
    log_action(db, new_user.id, "signup", "users", new_user.id)
    return new_user

# Génération d'un lien d'invitation temporaire
@router.post('/invite', response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def generate_invite(
    request: InviteRequest,
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Crée un token d'invitation temporaire valable une seule fois (permission can_create_users requise)"""
    # Vérifier la permission can_create_users
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == current_user.id).first()
    if not perms or not perms.can_acces_users_section:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission can_create_users requise")
    invite = create_invite_token(db, request.email)
    return invite

# Validation d'un token d'invitation
@router.get('/invite/validate', response_model=ValidateInviteResponse)
def validate_invite(token: str = Query(...), db: Session = Depends(get_db)):
    """Vérifie si le token est valide, non expiré et non utilisé"""
    invite = get_invite_token(db, token)
    if not invite or invite.used or invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token invalide, expiré ou déjà utilisé")
    return {'valid': True, 'email': invite.email}

# Inscription via lien d'invitation
@router.post('/signup-with-invite', response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def signup_with_invite(request: SignupWithInviteRequest, db: Session = Depends(get_db)):
    """Crée un utilisateur à partir d'un token d'invitation"""
    invite = get_invite_token(db, request.token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token non trouvé")
    if invite.used or invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token expiré ou déjà utilisé")
    if invite.email != request.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ne correspond pas au token")
    # Création de l'utilisateur enrichi
    user_data = request.model_dump()
    # Hasher le mot de passe avant stockage
    if 'password' in user_data:
        user_data['password'] = utils.hash(user_data['password'])
    new_user = create_user(db, user_data)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Echec création utilisateur")
    assign_default_role_to_user(new_user.id, db)
    from app.db.crud.crud_permissions import initialize_user_permissions
    initialize_user_permissions(db, new_user.id)
    # Marquer le token comme utilisé
    mark_token_used(db, request.token)
    log_action(db, new_user.id, "signup_with_invite", "users", new_user.id)
    return new_user


# Liste des invitations
@router.get('/invitations', response_model=List[InviteTokenListItem], status_code=status.HTTP_200_OK)
def list_invitations(
    status_filter: Optional[str] = Query(None, alias="status", regex="^(pending|used|expired)$"),
    db: Session = Depends(get_db),
    current_user: model_user.User = Depends(oauth2.get_current_user)
):
    """Liste toutes les invitations avec filtre optionnel par statut (pending, used, expired)"""
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == current_user.id).first()
    if not perms or not perms.can_acces_users_section:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission requise")
    return get_all_invite_tokens(db, token_status=status_filter)


class ResetTokenRequest(BaseModel):
    user_id: int

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post('/generate-reset-token', status_code=status.HTTP_200_OK)
def generate_reset_token(request: ResetTokenRequest, db: Session = Depends(get_db)):
    """
    Génère un token temporaire pour réinitialiser le mot de passe à partir de l'ID utilisateur.
    """
    # Création et enregistrement du token en base
    reset = create_reset_token(db, request.user_id)
    return {"reset_token": reset.token, "expires_at": reset.expires_at.isoformat()}

# Validation d'un token de réinitialisation
@router.get('/reset-token/validate', status_code=status.HTTP_200_OK)
def validate_reset_token(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Vérifie si un token de réinitialisation est valide, non expiré et non utilisé.
    """
    reset = get_reset_token(db, token)
    if not reset or reset.used or reset.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token invalide, expiré ou déjà utilisé")
    return {"valid": True, "user_id": reset.user_id}

@router.post('/reset-password', status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Réinitialise le mot de passe à partir d'un token de réinitialisation.
    """
    # Récupérer le token en base
    reset = get_reset_token(db, request.token)
    if not reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token non trouvé")
    if reset.used or reset.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token expiré ou déjà utilisé")
    # Marquer comme utilisé
    mark_reset_token_used(db, request.token)
    # Mettre à jour le mot de passe de l'utilisateur
    user = db.query(model_user.User).filter(model_user.User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    user.password = utils.hash(request.new_password)
    db.commit()
    log_action(db, user.id, "reset_password", "users", user.id)
    return {"message": "Mot de passe réinitialisé avec succès"}
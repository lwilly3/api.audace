from fastapi import HTTPException, Response, status, Depends, APIRouter, Query
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
from app.schemas.schema_invite import InviteRequest, InviteResponse, ValidateInviteResponse, SignupWithInviteRequest
from app.db.crud.crud_invite_token import create_invite_token, get_invite_token, mark_token_used
from app.models.model_user_permissions import UserPermissions

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
def login(user_credentials_receved: OAuth2PasswordRequestForm=Depends(), db: Session = Depends(database.get_db)): 
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
 
    
# creation du token
#    le data contien ce que je veux inclure dans le  payloard
#    le token peut etre visualiser dans https://jwt.io/  9h09
   access_token= oauth2.create_acces_token(data={'user_id':user_to_log_on_db.id})

   permissions= get_user_permissions(db, user_to_log_on_db.id)
   
   return{"access_token" :access_token, "token_type":"bearer" ,
          "user_id":user_to_log_on_db.id,
           "username":user_to_log_on_db.username,
             "email":user_to_log_on_db.email,
             "family_name":user_to_log_on_db.family_name,
             "name":user_to_log_on_db.name,
             "phone_number":user_to_log_on_db.phone_number,
               "permissions":permissions}



# Endpoint pour déconnecter un utilisateur
@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(token: str = Depends(oauth2.oauth2_scheme), db: Session = Depends(get_db), current_user: model_user.User = Depends(oauth2.get_current_user)):
    # Ajoute le token à la liste noire pour l'invalider
    revoke_token(db, token)

    # Retourne une réponse 204 (No Content) pour indiquer que la déconnexion a réussi
    return Response(status_code=status.HTTP_204_NO_CONTENT)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

@router.post('/signup', status_code=status.HTTP_201_CREATED, response_model=UserInDB)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Créer un utilisateur minimal avec email comme username
    user_data = {
        'username': request.email,
        'name': '',
        'family_name': '',
        'email': request.email,
        'password': request.password,
        'phone_number': ''
    }
    new_user = create_user(db, user_data)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User creation failed")
    # Correction : assigner le rôle public et initialiser les permissions
    assign_default_role_to_user(new_user.id, db)
    from app.db.crud.crud_permissions import initialize_user_permissions
    initialize_user_permissions(db, new_user.id)
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
    new_user = create_user(db, user_data)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Echec création utilisateur")
    assign_default_role_to_user(new_user.id, db)
    from app.db.crud.crud_permissions import initialize_user_permissions
    initialize_user_permissions(db, new_user.id)
    # Marquer le token comme utilisé
    mark_token_used(db, request.token)
    return new_user
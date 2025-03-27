from fastapi import HTTPException, Response, status, Depends, APIRouter
from sqlalchemy.orm import Session
# import app.database as database, app.schemas as schemas, app.table_models as table_models, app.utils as utils, app.oauth2 as oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from app.models import table_models
from app.models import model_user
from core.auth import oauth2
from app.db import database
from app.db.database import get_db  # Cette fonction obtient une session de base de données

from app.schemas import schemas
from app.utils import utils
from app.db.crud.crud_permissions import get_user_permissions
from app.db.crud.crud_auth import revoke_token

# pour la creation du token, intallation du package  pip install python-jose[cryptography]  7h01
# 6h05 installation des librairie pour hacher le pass pip install passlib[bcrypt]

router=APIRouter(
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
   if not utils.verify(user_credentials_receved.password, user_to_log_on_db.password ):
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"authentification invalide")
 
    
# creation du token
#    le data contien ce que je veux inclure dans le  payloard
#    le token peut etre visualiser dans https://jwt.io/  9h09
   access_token= oauth2.create_acces_token(data={'user_id':user_to_log_on_db.id})

   permissions= get_user_permissions(db, user_to_log_on_db.id)
   
   return{"access_token" :access_token, "token_type":"bearer" ,
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
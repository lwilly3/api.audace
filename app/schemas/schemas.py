from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from pydantic.types import conint

# pour la validation ce model pydantic permet de faire des validations de  requettes envoye par lutilisateur
# defini la structure de la requete et de la reponse
# permet de definir ce que doit envoyer  l'utilisateur
# defini egalement a quoi ressemblera une reponse venant de fastapi 

class PostBase(BaseModel):
    title:str
    content:str
    published:bool=True


class PostCreate(PostBase):
    pass


class UserOutResponse(BaseModel):
    id:int
    email:EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# 9h50 ajout des votes dans le post de retour
# structure pour les resultat des requettes de publications
class Post(PostBase):
    id:int
    owner_id: int # pour la creation des post on utilisera deans le routage l'id depuis le token pa besoin de lenvoyer lors de la creation de posts
    created_at: datetime
    # 8h36 on retourne dans le model de repondse une class alchemy les information de l'utilisateur renvoyer relationship("User")
    owner: UserOutResponse
    # 5h44 transforme le model sqlalcheny en dictionnaire a fin de pouvoir lutiliser dans la requette comme disctioonaire
    model_config = ConfigDict(from_attributes=True)
    # votes:int

# 10h25
class PostAvecVote(BaseModel):
    post:Post
    votes:int
    model_config = ConfigDict(from_attributes=True)
    

    # class Config():
    #     from_attributes = True
    pass
    





class UserCreate(BaseModel):
    email:EmailStr
    password:str
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token:str
    token_type:str
    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    id: Optional[int]=None
    model_config = ConfigDict(from_attributes=True)

# 9h37 implementation de conint pour s'assurer que la direction soit soit 0 soit 1 le=1 renvoie a pas superieur a 1
class Votes(BaseModel):
    post_id:int
    direction:conint(le=1) # type: ignore
    model_config = ConfigDict(from_attributes=True)
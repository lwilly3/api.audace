
from functools import lru_cache
from fastapi import FastAPI
# import app.table_models 
# import app.database 
from routeur import posts,users,auth, votes
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware

# import os

# implementation du middleware pour autoriser des requettes exterieurs 11h22
# demarrage du serveur uvicorn maintest:app --reload  
# print (os.path)
# @lru_cache est utilisé pour décorer la fonction get_settings().
# Cela permettra de mettre en cache le résultat retourné par la fonction, 
# de sorte que si la fonction est appelée à nouveau avec les mêmes arguments, 
# le résultat précédemment calculé sera renvoyé à la place de recalculer le résultat. 
# Cela améliorera les performances en évitant de charger les paramètres à chaque appel.
@lru_cache  #https://fastapi.tiangolo.com/yo/advanced/settings/#__tabbed_5_1     mise a jour python 3.9
def get_settings():
    return settings()
# settings = Settings()
 
#  11h14
# vue que nous utilisons alembic nous navons plus besoin de cette comende que demandait a sql alchemy de dexecuter la creation des table
# table_models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()


# 11h22 implementation du midelware pour permetre au domaines exterieur d'acceder a notre API
# on peu faire le test sur consol dans inspection de google.com avec la commande fetch("http://localhost:8000/").then(res=>res.json()).then(console.log)
# https://fastapi.tiangolo.com/tutorial/cors/ pour la Doc
# origins = [ "https://www.google.com" ]    si je veux limiter mon appi accecible a google uniquement
# en utilisant * en argument j'autorise nimporte quelle application web a acceder a mon api
origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# permet d'inclure toutes le liens de post dans la liste des lien de mon app 6h26
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(auth.router)   
app.include_router(votes.router)

@app.get("/")
def par_defaut():
    return {"BIEBVENUE":"HAPSON API   222!!!!!!!!!"}
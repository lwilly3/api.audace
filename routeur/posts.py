import app.schemas.schemas as schemas, app.models.table_models as table_models, core.auth.oauth2 as oauth2
from fastapi import  HTTPException, Response, status, Depends, APIRouter
from app.db.database import get_db
from sqlalchemy.orm import Session
from typing import Union, List, Optional
from sqlalchemy import func #10h19
# from fastapi.encoders import jsonable_encoder


# comme on as pas directement acces a @APP pour @app.get on utilisera router.get pour cree la route
# prefix="/posts" permet de ne pase le repeter sur les chement il sera jouter automatiquement 6h29
# tags=['POST'] est util au niveau de la secmentation sur la documentation
router=APIRouter(
    prefix="/posts",
    tags=['POST']
)
# ////////////////////////////


@router.get("/all",  response_model= List[schemas.PostAvecVote])
def get_posts(db: Session = Depends(get_db), limit: int=100, skip: int=0, search: Optional[str] =""):
  

    posts_and_counts = db.query(table_models.Posts, func.count(table_models.Posts.id).label("votes")).join(table_models.Votes, table_models.Votes.post_id == table_models.Posts.id, isouter=True).group_by(table_models.Posts.id).all()
   
# Sérialiser chaque résultat
    serialized_results = []
    for post_and_count in posts_and_counts:
        post = post_and_count.Posts
        votes_count = post_and_count.votes
        # Créer un dictionnaire pour chaque résultat
        serialized_post = {
            "post": {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "published": post.published,
                "created_at": post.created_at,
                'owner_id':post.owner_id,
                "owner": {
                    "id": post.owner.id,
                    "email":post.owner.email,
                    "created_at": post.owner.created_at,  # ou tout autre attribut de l'utilisateur
                    # Ajoutez d'autres attributs de l'utilisateur si nécessaire
                },
            },
            "votes": votes_count
        }
        serialized_results.append(serialized_post)


    return serialized_results



# /////////////////////////////////////

# 8h30 pour retourner les poste d'un utilisateur en particulier (le proprietaire) le lien a ete a jouter par moi
@router.get("/owne",  response_model= List[schemas.Post])
def get_Owner_posts(db: Session = Depends(get_db),current_user: int= Depends(oauth2.get_current_user)):
    # cursor.execute(''' SELECT * FROM posts   ''')
    # posts= cursor.fetchall()
    # if table_models.Posts.owner_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Vous n'ete pas proprietaire de ce post")


    posts= db.query(table_models.Posts).filter(table_models.Posts.owner_id== current_user.id).all()

#  bien que la bariable  soit un dictionnaire python, en faisant return FastAPI va le serialiser en Json avant de retourner 5h40 de la video
    return posts




# 8h40 ajour des query parameter (parametre de requettes) qui permettent d'envoyer par lien des filtres suplementaires
# le parametre .ofset(int) permetra de faire la pagination
# current_user: int bien que cela soit definit comme int cela n'afecte pas le fait que current_user est un dictionaire 8h29
# comme le resultat est une liste de Post on utilise la librery List : List[schemas.Post]   5h50 de la video
# @router.get("/",  response_model= List[schemas.Post])
@router.get("/",  response_model= List[schemas.PostAvecVote])
def get_posts(db: Session = Depends(get_db),current_user: int= Depends(oauth2.get_current_user),
              limit: int=100, skip: int=0, search: Optional[str] =""):
  
    # cursor.execute(''' SELECT * FROM posts   ''')  PostAvecVote
    # posts= cursor.fetchall()
    # # 8h48 inplementation de .filter(table_models.Posts.title.contains(search))
    # posts= db.query(table_models.Posts).filter(table_models.Posts.title.contains(search)).limit(limit).offset(skip).all()

      # 10h15 implementation de la fonction join
    # posts= db.query(table_models.Posts, func.sum(table_models.Votes.post_id).label("total_score") ).join(table_models.Votes, table_models.Votes.post_id==table_models.Posts.id, isouter=True).group_by(table_models.Posts.id).all()

    # posts= db.query(table_models.Posts, func.count(table_models.Posts.id).label("votes")).join(table_models.Votes, table_models.Votes.post_id==table_models.Posts.id, isouter=True).group_by(table_models.Posts.id).all()
        # Effectuer la requête avec la jointure et le groupage
    posts_and_counts = db.query(table_models.Posts, func.count(table_models.Posts.id).label("votes")).join(table_models.Votes, table_models.Votes.post_id == table_models.Posts.id, isouter=True).group_by(table_models.Posts.id).all()
   
# Sérialiser chaque résultat
    serialized_results = []
    for post_and_count in posts_and_counts:
        post = post_and_count.Posts
        votes_count = post_and_count.votes
        # Créer un dictionnaire pour chaque résultat
        serialized_post = {
            "post": {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "published": post.published,
                "created_at": post.created_at,
                'owner_id':post.owner_id,
                "owner": {
                    "id": post.owner.id,
                    "email":post.owner.email,
                    "created_at": post.owner.created_at,  # ou tout autre attribut de l'utilisateur
                    # Ajoutez d'autres attributs de l'utilisateur si nécessaire
                },
            },
            "votes": votes_count
        }
        serialized_results.append(serialized_post)


    return serialized_results
        # pass
# FastAPI a du mal a serialiser les dictionnaires complexe cree par func.count(table_models.Posts.id).label("votes")) on pass par la boucle de transformation des donee en une structure serialisable en JSON
#  bien que la variable  soit un dictionnaire python, en faisant return FastAPI va le serialiser en Json avant de retourner 5h40 de la video


# pour cree le post dans le header de la requette on introduira : la cle Authorization avec pour valeur: Bearer <token>
# response_model permet de controller ce qui sera renvoyer a l'utilisateur
@router.post('/', status_code=status.HTTP_201_CREATED,  response_model= schemas.Post )
def create_post(post:schemas.PostCreate, db: Session = Depends(get_db),current_user: int= Depends(oauth2.get_current_user)):
    # cursor.execute(''' INSERT INTO posts (title, content, published) VALUES (%s,%s,%s) RETURNING *''',(post.title, post.content, post.published))
    # new_post=cursor.fetchone()
    # connexion.commit()
    # new_to_post=table_models.Posts(title=post.title, content=post.content, published=post.published)
    # print(**post.model_dump()) 5h14min de la video

    # dans le but deviter a lutilisater de fournir son id lors de la creation de post on la recupere dans le token et lajoute a la requete 8h20
    new_to_post=table_models.Posts(owner_id=current_user.id, **post.model_dump())

    db.add(new_to_post)
    db.commit()
    db.refresh(new_to_post)
    return  new_to_post

@router.get("/{id}",  response_model= schemas.Post)
def get_post_by_id(id: int, db: Session = Depends(get_db),  response_model= schemas.Post, current_user: int= Depends(oauth2.get_current_user)):
    #la virgule apres str(id) a pour bur deviter devantuelle erreur qui pourais se produire
    # cursor.execute(''' SELECT * FROM posts WHERE id=%s ''',(str(id),))
    # result_post = cursor.fetchone()
    result_post= db.query(table_models.Posts).filter(table_models.Posts.id==id).one()
    if not result_post :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"le post avec l'indexe No {id} n'existe pas")
    
    return result_post











@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def suprimer_post(id: int, db: Session = Depends(get_db),current_user: int= Depends(oauth2.get_current_user)):
    # cursor.execute(''' DELETE FROM posts WHERE id=%s RETURNING *''',(str(id),))
    # deleted_post= cursor.fetchone()
    # connexion.commit()
    requette_post_to_delete= db.query(table_models.Posts).filter(table_models.Posts.id==id)
    post_to_delete= requette_post_to_delete.first()

    if  post_to_delete == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"le post avec l'index No {id} n\'existe pas")
    
    # on se rassure que celui qui suprime le post est le proprietaire 8h22
    if post_to_delete.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Vous n'ete pas proprietaire de ce post")



    

    #5h21 de la video
    requette_post_to_delete.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}",  response_model= schemas.Post)
def modifier_post(id:int, post:schemas.PostCreate, db: Session = Depends(get_db),  response_model= schemas.Post,current_user: int= Depends(oauth2.get_current_user)):
    # cursor.execute("""   UPDATE posts SET title=%s, content=%s, published=%s   WHERE id=%s RETURNING * """,(post.title, post.content, post.published, str(id),))
    # result_modif=cursor.fetchone()
    # connexion.commit()

    requete_modif_post= db.query(table_models.Posts).filter(table_models.Posts.id==id)
    post_a_modifier=requete_modif_post.first()


    if post_a_modifier == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"le post avec le Id No {id} n'existe pas")
        # on se rassure que celui qui suprime le post est le proprietaire 8h22
    if post_a_modifier.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Vous n'ete pas proprietaire de ce post") #8h22
    
    # requete_modif.update({'title':"titre de mise a jour", "content":"contenue de mise a jour"}, synchronize_session=False)
    requete_modif_post.update(post.model_dump(), synchronize_session=False)
    db.commit()
    return  requete_modif_post.first()

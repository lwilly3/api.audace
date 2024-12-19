# # 9h34

# from fastapi import  HTTPException,  status, Depends, APIRouter
# # import app.schemas as schemas, app.table_models as table_models, app.oauth2 as oauth2
# from core.auth import oauth2
# from app.db.database import get_db
# from sqlalchemy.orm import Session
# # from typing import Union, List, Optional
# # from sqlalchemy.exc import SQLAlchemyError
# from app.models import table_models
# from app.schemas import schemas



# router=APIRouter(
#     prefix="/vote",
#     tags=['Vote']
# )

# @router.post("/", status_code=status.HTTP_201_CREATED)

# def vote(vote: schemas.Votes, db: Session=Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

# # verification si le post existe
#     verification_existance_post= db.query(table_models.Posts).filter(table_models.Posts.id== vote.post_id).first()
#     if not verification_existance_post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="le post n'existe pas")


#     requette_vote= db.query(table_models.Votes).filter(table_models.Votes.post_id== vote.post_id, table_models.Votes.user_id==current_user.id)

#     resultat_requette= requette_vote.first()

#     # HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="le vote que vous souhaitez modifier n'existe pas")

#     if(vote.direction==1):

#         if resultat_requette:
#             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"vous avez dejas voté ce post")
#         nouveau_vote= table_models.Votes(post_id=vote.post_id, user_id=current_user.id)
#         db.add(nouveau_vote)
#         db.commit()
#         return {"message": "vote ajouté avec succes"}

#     else:
#         if not resultat_requette:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="le vote que vous souhaitez modifier n'existe pas")
        
#         requette_vote.delete(synchronize_session=False)
#         db.commit()
#         return { "message": "vote suprimé avec succes"}
    

#         #  autre apporche pour detecter une erreur de requette comme celle dun post inexistant
#     # try:
            
#     # except SQLAlchemyError:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="le Post que vous souhaitez voter n'existe pas")
 
        
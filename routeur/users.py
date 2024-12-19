
# import app.schemas.schemas as schemas, app.models.table_models as table_models, app.utils.utils as utils
# from fastapi import HTTPException, status, Depends, APIRouter
# from app.db.database import get_db
# from sqlalchemy.orm import Session
# from typing import Union, List



# router=APIRouter(
#      prefix="/users",
#      tags=['USERS']
# )

# @router.post('/', status_code=status.HTTP_201_CREATED , response_model=schemas.UserOutResponse)
# def create_user(user_to_create:schemas.UserCreate, db: Session = Depends(get_db)):
#     #    creatio du hash du mot de pass et sauvegarde dans lobjer user_to_create.password
#       hashed_password=utils.hash(user_to_create.password)
#       user_to_create.password=hashed_password


#     #   converti les donnee recu dans le schemas dictionnaire eteclate chaques assignation avant d'appeler table_model_user
#       new_user=table_models.UserPost(**user_to_create.model_dump())

#       db.add(new_user)
#       db.commit()
#     #   pour retourner les element cree
#       db.refresh(new_user)
#       return  new_user


# @router.get("/{id}",response_model=schemas.UserOutResponse)
# def get_user(id:int, db: Session = Depends(get_db)):
#     user=db.query(table_models.UserPost).filter(table_models.UserPost.id==id).first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"l'utilisateur avec le id {id} n'existe pas")
    
#     return user

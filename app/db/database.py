from functools import lru_cache
# from app.models import  Role, Permission, RolePermission
from fastapi import  Depends
from urllib.parse import quote_plus


from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
# import config
from app.config import config
# suite: 9h19 ok
from sqlalchemy import MetaData

# URL-encoder le mot de passe pour gerer les caracteres speciaux (@, #, %, etc.)
_encoded_password = quote_plus(config.settings.DATABASE_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"postgresql://{config.settings.DATABASE_USERNAME}:{_encoded_password}@{config.settings.DATABASE_HOSTNAME}:{config.settings.DATABASE_PORT}/{config.settings.DATABASE_NAME}"


engine=create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)
# donne acces a tout le model  SQLAlchemy dans le projet
Base = declarative_base()

metadata = MetaData()

# Dependency (cree une session sur la db et donne une connectivite a la db et ferme la session a la fin de la requette)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# create_default_role_and_permission(Depends(get_db))
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# import config 
from . import config
# suite: 9h19 ok

# @lru_cache  #https://fastapi.tiangolo.com/yo/advanced/settings/#__tabbed_5_1     mise a jour python 3.9
# def get_settings():
#     return Settings()

# setting=get_settings()
# 8h54 creation de la variable denvirionement pour securiser les infos sensibles de mon code tel les pass
# SQLALCHEMY_DATABASE_URL = "postgresql://<username>:<password>@p<ip-address/hostname>/<database name>"
SQLALCHEMY_DATABASE_URL = f"postgresql://{config.settings.DATABASE_USERNAME}:{config.settings.DATABASE_PASSWORD}@{config.settings.DATABASE_HOSTNAME}:{config.settings.DATABASE_PORT}/{config.settings.DATABASE_NAME}"
# SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:Wcz9pylh@localhost/fastapi"


engine=create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)
# donne acces a tout le model  SQLAlchemy dans le projet
Base = declarative_base()

# Dependency (cree une session sur la db et donne une connectivite a la db et ferme la session a la fin de la requette)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
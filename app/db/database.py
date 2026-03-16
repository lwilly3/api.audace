from functools import lru_cache
from fastapi import Depends

from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import config

# Utiliser URL.create() pour gerer nativement les caracteres speciaux
# dans le mot de passe (@, *, #, %, etc.) sans encoding manuel
SQLALCHEMY_DATABASE_URL = URL.create(
    drivername="postgresql",
    username=config.settings.DATABASE_USERNAME,
    password=config.settings.DATABASE_PASSWORD,
    host=config.settings.DATABASE_HOSTNAME,
    port=int(config.settings.DATABASE_PORT),
    database=config.settings.DATABASE_NAME,
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
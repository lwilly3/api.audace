# https://fastapi.tiangolo.com/yo/advanced/settings/    9h10 a ete mis a jour
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOSTNAME:str
    DATABASE_PORT:str
    DATABASE_PASSWORD:str
    DATABASE_NAME:str
    DATABASE_USERNAME:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRATION_MINUTE:int

    model_config = SettingsConfigDict(env_file=".env")
   
    # class Config:
    #     env_file=".env"

settings=Settings()
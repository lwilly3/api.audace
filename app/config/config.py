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

    # OVH API
    OVH_ENDPOINT:str = "ovh-eu"
    OVH_APPLICATION_KEY:str = ""
    OVH_APPLICATION_SECRET:str = ""
    OVH_CONSUMER_KEY:str = ""

    # Scaleway Dedibox API (token prive from console.online.net/en/api/access)
    SCW_SECRET_KEY:str = ""

    # URLs frontend / backend (pour OAuth callback redirect)
    FRONTEND_URL:str = "http://localhost:5173"
    BACKEND_URL:str = "http://localhost:8000"

    # Facebook / Instagram OAuth (meme Meta App pour les deux)
    FACEBOOK_APP_ID:str = ""
    FACEBOOK_APP_SECRET:str = ""
    FACEBOOK_CONFIG_ID:str = ""
    FACEBOOK_REDIRECT_URI:str = ""

    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID:str = ""
    LINKEDIN_CLIENT_SECRET:str = ""

    # Twitter/X OAuth 2.0
    TWITTER_CLIENT_ID:str = ""
    TWITTER_CLIENT_SECRET:str = ""

    model_config = SettingsConfigDict(env_file=".env")
   
    # class Config:
    #     env_file=".env"

settings=Settings()
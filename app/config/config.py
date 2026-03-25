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

    # 2FA TOTP encryption key (Fernet)
    # Generer via: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    TOTP_ENCRYPTION_KEY:str = ""

    # Delai de grace (en minutes) pour le refresh de token apres expiration
    REFRESH_GRACE_MINUTES:int = 5

    # Grace etendue pour appareils de confiance (7 jours = 10080 min)
    TRUSTED_DEVICE_REFRESH_GRACE_MINUTES:int = 10080

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

    # WordPress integration (cross-posting P5)
    WORDPRESS_SITE_URL:str = ""
    WORDPRESS_SYNC_SECRET:str = ""

    # WordPress Articles (proxy vers wp-json)
    WP_AUDACEMAGAZINE_URL:str = "https://www.audacemagazine.com"
    WP_AUDACEMAGAZINE_USER:str = ""
    WP_AUDACEMAGAZINE_APP_PASSWORD:str = ""
    WP_RADIOAUDACE_URL:str = "https://www.radioaudace.com"
    WP_RADIOAUDACE_USER:str = ""
    WP_RADIOAUDACE_APP_PASSWORD:str = ""

    # RadioDJ integration (Now Playing track info)
    RADIODJ_API_KEY:str = ""

    # Mistral AI (generation de posts depuis URL)
    MISTRAL_API_KEY:str = ""

    # Cloudflare Worker pour extraction sous-titres YouTube (legacy, remplace par yt-dlp)
    YOUTUBE_WORKER_URL:str = ""
    YOUTUBE_WORKER_SECRET:str = ""

    # yt-dlp : proxy residentiel pour contourner le blocage IP YouTube en production
    YTDLP_PROXY:str = ""

    # yt-dlp : chemin vers le fichier cookies.txt (JSON Chrome ou Netscape) pour YouTube auth
    # Exporter depuis le navigateur via l'extension "Get cookies.txt LOCALLY"
    # Le service convertit automatiquement le JSON Chrome en format Netscape
    YTDLP_COOKIES_PATH:str = "/app/data/cookies.txt"

    # Firebase Storage (nettoyage fichiers temporaires apres publication)
    # Accepte soit le contenu JSON direct, soit un chemin vers le fichier JSON
    FIREBASE_SERVICE_ACCOUNT:str = ""

    # Google OAuth (Backup Management — Google Drive)
    GOOGLE_CLIENT_ID:str = ""
    GOOGLE_CLIENT_SECRET:str = ""

    # Google Analytics Data API v1 (GA4)
    # Contenu JSON du Service Account (coller le JSON complet dans la variable)
    # Le Service Account doit avoir l'acces "Lecteur" dans chaque propriete GA4
    GA_SERVICE_ACCOUNT_JSON:str = ""

    model_config = SettingsConfigDict(env_file=".env")
   
    # class Config:
    #     env_file=".env"

settings=Settings()
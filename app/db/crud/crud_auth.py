# from sqlalchemy.orm import Session
# from datetime import datetime
# from app.models.model_auth_token import AuthToken  # Import des modèles de la base de données
# from jose import JWTError, jwt, ExpiredSignatureError, InvalidTokenError
# from app.config.config import settings


# SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = settings.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRATION_MINUTE

# # Fonction de validation des tokens
# def validate_token(db: Session, token: str):
#     try:
#         # Décodage du token JWT
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("user_id")

#         # Recherche du token dans la base de données
#         db_token = db.query(AuthToken).filter(AuthToken.user_id == user_id, AuthToken.access_token == token).first()

#         if not db_token:
#             return {"error": "Invalid token"}

#         # Vérification de l'expiration
#         if db_token.expires_at < datetime.utcnow():
#             # Suppression du token expiré
#             db.delete(db_token)
#             db.commit()
#             return {"error": "Token expired and removed from database"}

#         return {"user_id": user_id, "valid": True}

#     except ExpiredSignatureError:
#         return {"error": "Token expired"}
#     except JWTError:
#         return {"error": "JWTError -> Invalid token"}

# # Fonction pour supprimer les tokens expirés de la base de données
# def delete_expired_tokens(db: Session):
#     now = datetime.utcnow()
#     expired_tokens = db.query(AuthToken).filter(AuthToken.expires_at < now).all()

#     if expired_tokens:
#         for token in expired_tokens:
#             db.delete(token)  # Supprime le token
#         db.commit()  # Commit les changements
#         return {"message": f"{len(expired_tokens)} expired tokens deleted."}
#     return {"message": "No expired tokens found."}

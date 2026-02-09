
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.model_auth_token import RevokedToken
from jose import JWTError, jwt
from app.config.config import settings

# Ajoute un token à la liste noire
def revoke_token(db: Session, token: str) -> RevokedToken:
    """
    Ajoute un token à la table RevokedToken pour l'invalider.
    Si le token est déjà révoqué, retourne l'entrée existante sans erreur.

    Args:
        db (Session): Session SQLAlchemy pour accéder à la base de données.
        token (str): Token JWT à révoquer.

    Returns:
        RevokedToken: Objet représentant le token révoqué.
    """
    # Vérifier si le token est déjà révoqué pour éviter une IntegrityError (duplicate key)
    existing = db.query(RevokedToken).filter(RevokedToken.token == token).first()
    if existing:
        return existing

    revoked_token = RevokedToken(token=token)
    db.add(revoked_token)
    db.commit()
    db.refresh(revoked_token)
    return revoked_token

# Vérifie si un token est dans la liste noire
def is_token_revoked(db: Session, token: str) -> bool:
    """
    Vérifie si un token a été révoqué (présent dans la table RevokedToken).

    Args:
        db (Session): Session SQLAlchemy pour accéder à la base de données.
        token (str): Token JWT à vérifier.

    Returns:
        bool: True si le token est révoqué, False sinon.
    """
    return db.query(RevokedToken).filter(RevokedToken.token == token).first() is not None

# Supprime les tokens révoqués qui sont expirés
def delete_expired_tokens(db: Session, current_time: datetime) -> None:
    """
    Supprime les tokens révoqués qui sont expirés (basé sur le payload JWT et la date de révocation).

    Args:
        db (Session): Session SQLAlchemy pour accéder à la base de données.
        current_time (datetime): Date actuelle pour comparaison.

    Note:
        Cette fonction peut être appelée périodiquement pour nettoyer la table RevokedToken.
    """
    revoked_tokens = db.query(RevokedToken).all()
    for revoked_token in revoked_tokens:
        try:
            # Décode le token pour vérifier sa date d'expiration
            payload = jwt.decode(revoked_token.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)

            # Si le token est expiré ou si sa date de révocation est antérieure à current_time
            if exp < current_time or revoked_token.revoked_at < current_time:
                db.delete(revoked_token)
        except JWTError:
            # Si le token est invalide, on le supprime
            db.delete(revoked_token)
    db.commit()












# from datetime import datetime, timezone
# from sqlalchemy.orm import Session
# from app.models.model_auth_token import RevokedToken

# from jose import JWTError, jwt
# from app.config.config import settings


# def delete_expired_tokens(db: Session, current_time: datetime):
#     revoked_tokens = db.query(RevokedToken).all()
#     for revoked_token in revoked_tokens:
#         try:
#             payload = jwt.decode(revoked_token.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#             exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)

#             # exp = datetime.utcfromtimestamp(payload['exp'])
#             if exp < current_time:
#                 db.delete(revoked_token)
#         except JWTError:
#             # Si le token est invalide, on peut le supprimer
#             db.delete(revoked_token)
#     db.commit()

# # Ajoute un token à la liste noire
# def revoke_token(db: Session, token: str):
#     revoked_token = RevokedToken(token=token)
#     db.add(revoked_token)
#     db.commit()
#     db.refresh(revoked_token)
#     return revoked_token

# # Vérifie si un token est dans la liste noire
# def is_token_revoked(db: Session, token: str) -> bool:
#     return db.query(RevokedToken).filter(RevokedToken.token == token).first() is not None

# # Supprime les tokens révoqués qui sont expirés (optionnel, pour nettoyer la base)
# def delete_expired_tokens(db: Session, current_time: datetime):
#     db.query(RevokedToken).filter(RevokedToken.revoked_at < current_time).delete()
#     db.commit()
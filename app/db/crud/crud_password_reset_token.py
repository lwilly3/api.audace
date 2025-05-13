from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException
from starlette import status
from app.models.model_password_reset_token import PasswordResetToken


def create_reset_token(db: Session, user_id: int, expires_in_minutes: int = 15) -> PasswordResetToken:
    """
    Génère un token unique pour réinitialisation de mot de passe, l'enregistre et le retourne.
    """
    token_str = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    reset = PasswordResetToken(token=token_str, user_id=user_id, expires_at=expires_at)
    db.add(reset)
    db.commit()
    db.refresh(reset)
    return reset


def get_reset_token(db: Session, token: str) -> PasswordResetToken:
    """
    Récupère un PasswordResetToken par son token.
    """
    return db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()


def mark_reset_token_used(db: Session, token: str) -> None:
    """
    Marque un token de réinitialisation comme utilisé.
    """
    reset = get_reset_token(db, token)
    if not reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token non trouvé")
    if reset.used:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token déjà utilisé")
    reset.used = True
    db.commit()
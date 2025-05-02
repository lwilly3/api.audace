from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException
from starlette import status
from app.models.model_invite_token import InviteToken


def create_invite_token(db: Session, email: str, expires_in_minutes: int = 1440) -> InviteToken:
    """
    Génère un token unique, enregistre un InviteToken et le retourne.
    """
    token_str = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    invite = InviteToken(token=token_str, email=email, expires_at=expires_at)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invite_token(db: Session, token: str) -> InviteToken:
    """
    Récupère un InviteToken par son token.
    """
    return db.query(InviteToken).filter(InviteToken.token == token).first()


def mark_token_used(db: Session, token: str) -> None:
    """
    Marque un token comme utilisé.
    """
    invite = get_invite_token(db, token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token non trouvé")
    if invite.used:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token déjà utilisé")
    invite.used = True
    db.commit()

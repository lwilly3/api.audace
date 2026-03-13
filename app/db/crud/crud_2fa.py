"""
CRUD pour la gestion du 2FA (TOTP).

Operations : setup, confirm, verify, disable, admin reset, backup codes.
"""

import io
import base64
import pyotp
import qrcode
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.model_user import User
from app.utils.crypto import (
    encrypt_totp_secret,
    decrypt_totp_secret,
    generate_backup_codes,
    hash_backup_codes,
    verify_backup_code,
)


# Nom affiche dans l'app TOTP (Google Authenticator, Authy, etc.)
TOTP_ISSUER = "RadioManager"


def setup_totp(db: Session, user_id: int) -> dict:
    """
    Genere un secret TOTP pour l'utilisateur (ne l'active PAS encore).
    Retourne le secret, l'URI otpauth:// et le QR code en base64.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    # Generer un nouveau secret TOTP
    secret = pyotp.random_base32()

    # Stocker le secret chiffre (pas encore active)
    user.totp_secret_encrypted = encrypt_totp_secret(secret)
    db.commit()

    # Generer l'URI otpauth://
    totp = pyotp.TOTP(secret)
    otpauth_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=TOTP_ISSUER,
    )

    # Generer le QR code en base64
    qr = qrcode.make(otpauth_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "otpauth_uri": otpauth_uri,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}",
    }


def confirm_totp_setup(db: Session, user_id: int, otp_code: str) -> dict:
    """
    Verifie le premier code OTP pour confirmer le setup.
    Active le 2FA et genere les backup codes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.totp_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun setup 2FA en cours")

    # Dechiffrer le secret et verifier le code
    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    totp = pyotp.TOTP(secret)

    if not totp.verify(otp_code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Generer les backup codes
    backup_codes = generate_backup_codes(8)

    # Activer le 2FA
    user.two_factor_enabled = True
    user.backup_codes_hash = hash_backup_codes(backup_codes)
    db.commit()

    return {"backup_codes": backup_codes}


def verify_totp(db: Session, user_id: int, otp_code: str) -> bool:
    """
    Verifie un code TOTP pendant le login.
    Fenetre de tolerance : ±1 periode (30s).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.two_factor_enabled or not user.totp_secret_encrypted:
        return False

    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    totp = pyotp.TOTP(secret)
    return totp.verify(otp_code, valid_window=1)


def verify_and_consume_backup_code(db: Session, user_id: int, code: str) -> bool:
    """
    Verifie et consomme un code de secours.
    Le code est retire de la liste apres utilisation.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.backup_codes_hash:
        return False

    valid, updated_json = verify_backup_code(code, user.backup_codes_hash)
    if valid and updated_json is not None:
        user.backup_codes_hash = updated_json
        db.commit()
        return True

    return False


def disable_totp(db: Session, user_id: int, otp_code: str) -> None:
    """
    Desactive le 2FA (requiert un code OTP valide).
    Supprime le secret et les backup codes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA non active")

    # Verifier le code OTP
    if not verify_totp(db, user_id, otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Desactiver le 2FA
    user.two_factor_enabled = False
    user.totp_secret_encrypted = None
    user.backup_codes_hash = None
    db.commit()


def admin_reset_totp(db: Session, user_id: int) -> None:
    """
    Reset admin du 2FA d'un utilisateur (pas besoin de code OTP).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    user.two_factor_enabled = False
    user.totp_secret_encrypted = None
    user.backup_codes_hash = None
    db.commit()


def regenerate_backup_codes(db: Session, user_id: int, otp_code: str) -> dict:
    """
    Regenere les codes de secours (requiert un code OTP valide).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA non active")

    # Verifier le code OTP
    if not verify_totp(db, user_id, otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Generer de nouveaux codes
    backup_codes = generate_backup_codes(8)
    user.backup_codes_hash = hash_backup_codes(backup_codes)
    db.commit()

    return {"backup_codes": backup_codes}
